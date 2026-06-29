from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from dependencies.role_dependency import role_required
from models.resume import Resume
from schemas.resume import ResumeListSchema


def fetch_resume_details(resume_ids:list[str], db: Session ):
    stmt= select(Resume).options(joinedload(Resume.skills)).where(Resume.id.in_(resume_ids))
    resumes = db.scalars(stmt).unique().all()

    return [
        ResumeListSchema.model_validate(resume)
        for resume in resumes
    ]