from datetime import datetime
import os
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from pydantic import BaseModel
from sqlalchemy import insert, or_, select
from sqlalchemy.orm import Session, joinedload
from database import get_db
from dependencies.auth_dependency import get_current_user
from dependencies.role_dependency import role_required
from models.resume import Resume, ResumeSkill
from schemas.chatbot import ChatbotResponseSchema
from schemas.resume import ResumeJsonSchema, ResumeListSchema, SearchedResumeListSchema
from schemas.user import CurrentUser
from services.resume_helper_service import fetch_resume_details
from services.resume_search_service import resume_search_service
from services.chroma_service import chroma_service
from services.resume_ai_service import SearchIntent, llm_parser, search_chunk_helper
from services.resume_embedding_service import resume_embedding_service
from services.chatbot_service import chatbot_service
# , run_react_agent


from services.resume_check import check_and_save_resume

router = APIRouter(prefix='/resume',tags=['resume'])

TEMP_DIR='resume_temp_folder'

os.makedirs(TEMP_DIR, exist_ok=True)

@router.post('/upload')
def file_upload(file: UploadFile= File(...),current_user: CurrentUser= Depends(role_required('admin','visitor')), db: Session= Depends(get_db)):
    
    unique_filename, file_path, resume_text = (
        check_and_save_resume(file)
    )
    mime_type = file.content_type 
    analysis = llm_parser(file_path,mime_type,resume_text)

    resume = Resume(
        file_name= unique_filename,
        summary= analysis.summary,
        feedback= analysis.feedback,
        created_by= current_user.sub
    )
    db.add(resume)
    db.flush() 
    file.file.close()
    for i in analysis.skills:
        resumeSkill = ResumeSkill(
            skill_name= i,
            resume_id= resume.id,
        )
        db.add(resumeSkill)
    
    db.commit()
    db.refresh(resume)
    full_resume = (
        db.query(Resume)
        .options(joinedload(Resume.skills)) # pre-loads the skills list into memory
        .filter(Resume.id == resume.id)
        .first()
    )
    resume_embedding_service.embed_resume(full_resume)
    return {
        'message':'file Upload successfully',
        'filename': file.filename
    }

@router.get('/resume-list', response_model=list[ResumeListSchema])
def get_resumes(current_user: CurrentUser= Depends(get_current_user), db: Session= Depends(get_db)):
    if(current_user.role == 'admin'):
        resume_list:list[Resume] = db.query(Resume).all()
        return resume_list
    elif(current_user.role == 'visitor'):
        resume_list: list[Resume] = db.query(Resume).filter(Resume.created_by == current_user.sub).all()
        return  resume_list
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail='Action not allowed.')
    
class QuestionRequest(BaseModel):
    question: str


# @router.post('/calc')
# def calculation(questionPayload:QuestionRequest ):
#     result = run_react_agent(
#         questionPayload.question
#     )
#     return {'result':result}

@router.post('/resume-json')
def resume_json(resume_list:list[ResumeJsonSchema],db:Session= Depends(get_db),current_user: CurrentUser= Depends(get_current_user)):
    for resume_entry in resume_list:
        resume = Resume(
            file_name= resume_entry.file_name,
            summary= resume_entry.summary,
            feedback= resume_entry.feedback,
            created_by= current_user.sub
        )
        db.add(resume)
        db.flush() 
        
        skill_data = [
            {   
                'skill_name':skill,
                'resume_id': resume.id
            }
            for skill in resume_entry.skills
        ]
        db.execute(insert(ResumeSkill),skill_data)
        
    db.commit()
    return {
        'message':'Resumes uploaded successfully',
    }
    
@router.get('/start-embedding')
def embedding_start(current_user:CurrentUser= Depends(get_current_user),db:Session= Depends(get_db)):
    stmt = (
            select(Resume)
            .options(joinedload(Resume.skills)) 
            .where(
                or_(
                    Resume.vectored.is_(None),
                    Resume.vectored == False
                )
            )
        )
    resume_list=db.execute(stmt).scalars().unique().all()
    chroma_service.count()

    if len(resume_list) > 0:
        for resume_entry in resume_list:
            resume_embedding_service.embed_resume(resume_entry)
            resume_entry.vectored = True
            db.commit()

@router.get('/search',response_model= list[SearchedResumeListSchema])

def search_vector(search_term:str,current_user:CurrentUser= Depends(role_required('admin')),db:Session= Depends(get_db)):
    query_type:SearchIntent=  search_chunk_helper(search_term)
    result = resume_search_service.search_input(input= search_term,chunk_type=query_type.target_chunk_type)
    metadatas= result['metadatas'][0]
    distance= result['distances'][0]
    print("metadata",metadatas)
    id_rank_map={}
    for meta,dist in zip(metadatas,distance):
        if meta['resume_id'] not in id_rank_map:
            id_rank_map[meta['resume_id']]= dist
            
    resumeIds=list(id_rank_map.keys())    
    distances=list(id_rank_map.values())    
    chroma_service.count()
    if(len(resumeIds)>0):
        stmt = select(Resume).where(Resume.id.in_(resumeIds))
        unordered_resumes = db.scalars(stmt).all()
        new_resume_list=[]
        for resume in unordered_resumes:
            resume_data= {
                ** resume.__dict__,
                'created_by_name': resume.created_by_name,
                'match_percent': (1 - id_rank_map.get(str(resume.id),0.0))*100
            }
            new_resume_list.append(resume_data)
            
        order_mapping = {id_str: index for index, id_str in enumerate(resumeIds)}
        
        ordered_resumes = sorted(
            new_resume_list, 
            key=lambda resume: order_mapping.get(str(resume['id']), len(resumeIds))
        )
        
        return ordered_resumes
    return []

@router.get('/chatbot',response_model=ChatbotResponseSchema)
def chatbot(user_input:str,session_id:str,db:Session= Depends(get_db)):
    print(user_input)
    response =chatbot_service.chatbot_handler(db=db,question=user_input,session_id=session_id)
    table_data:list[ResumeListSchema]=[]
    print("llm response",response)
    if(response.action=='fetch_resume' or response.action=='compare_resume'):
        table_data= fetch_resume_details(response.resume_ids,db)
        print(table_data)
    bot_response: ChatbotResponseSchema={
        'message':response.message,
        'action':response.action,
        'table_data':table_data,
        'creator':'bot'
    }
    return bot_response