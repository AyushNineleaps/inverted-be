from datetime import datetime
import os
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from database import get_db
from dependencies.auth_dependency import get_current_user
from dependencies.role_dependency import role_required
from models.resume import Resume, ResumeSkill
from schemas.resume import ResumeListSchema
from schemas.user import CurrentUser
from services.resume_ai_service import gemini_content_generator
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
    # print(resume_text)
    mime_type = file.content_type 
    analysis = gemini_content_generator(file_path,mime_type)

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
    print("HERE")
    return {
        'message':'file Upload successfully',
        'filename': file.filename
    }

@router.get('/resume-list', response_model=list[ResumeListSchema])
def get_resumes(current_user: CurrentUser= Depends(get_current_user), db: Session= Depends(get_db)):
    if(current_user.role == 'admin'):
        print ('admin')
        resume_list:list[Resume] = db.query(Resume).all()
        return resume_list
    elif(current_user.role == 'visitor'):
        print ('visitor')
        resume_list: list[Resume] = db.query(Resume).filter(Resume.created_by == current_user.sub).all()
        print(resume_list)
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