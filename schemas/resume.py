from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeSchema(BaseModel):
    model_config= ConfigDict(from_attributes= True)
    id:str
    file_name:str
    summary:str | None = None
    created_at:datetime
    feedback:str | None = None
    created_by:str
    updated_at:datetime
    
class ResumeSkillSchema(BaseModel):
    model_config= ConfigDict(from_attributes= True)
    id:str
    resume_id:str
    skill_name:str
    

class ResumeListSchema(BaseModel):
    model_config= ConfigDict(from_attributes= True)
    id:str
    file_name:str
    summary:str | None = None
    created_at:datetime
    feedback:str | None = None
    created_by:str
    updated_at:datetime
    created_by_name: str | None = None
    skills: list[ResumeSkillSchema]=[]