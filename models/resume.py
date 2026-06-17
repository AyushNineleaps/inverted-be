import uuid
from sqlalchemy import Column, ForeignKey, String, DateTime, Text, UniqueConstraint
from datetime import datetime, timezone
from database import Base 
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

class Resume(Base):
    __tablename__= "resumes"
    id= Column(String, primary_key=True, index = True, default = lambda:str(uuid.uuid4()))
    file_name= Column(String, unique=True, nullable=False)
    summary= Column(Text,nullable=True )
    created_at= Column(DateTime,default=lambda: datetime.now(timezone.utc))
    feedback= Column(Text,nullable=True)
    created_by= Column(String, ForeignKey("users.id"), nullable = False)
    updated_at = Column(DateTime, default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))
    skills = relationship(
        "ResumeSkill",
        back_populates="resume",
        cascade="all, delete",
        lazy="selectin"
    )
    user = relationship('User', lazy='joined')    
    created_by_name = association_proxy('user', 'name')
    
class ResumeSkill(Base):
    __tablename__ = 'resume_skills'
    id= Column(String,primary_key=True, default= lambda: str(uuid.uuid4()))
    resume_id = Column(String, ForeignKey('resumes.id'),nullable=False,index= True)
    skill_name= Column(String, nullable=False)
    __table_args__=(UniqueConstraint('resume_id','skill_name',name='unique_resume_skill_per_resume'),)
    resume = relationship("Resume", back_populates="skills")
    