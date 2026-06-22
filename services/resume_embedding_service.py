from typing import List

from .resume_chunk_service import resume_chunk_service

from .embedding_service import embedding_service
from .chroma_service import chroma_service
class ResumeEmbeddingService:
    def create_resume_text(self,resume):
        skills = ', '.join(
            skill.skill_name
            for skill in resume.skills
        )
        return f"""
    Profile
    Summary:{resume.summary}
    skill:{skills}
        """
    
    def embed_resume(self,resume):
        
        chunks:List[dict] = resume_chunk_service.create_chunks(resume)
        
        for chunk in chunks:
            embedding = embedding_service.generate_embedding(chunk['content'])
        
            chroma_service.add_resume(
                resume_id=chunk["chunk_id"],
                document=chunk["content"],
                embedding=embedding.tolist(),
                metadata={
                    "resume_id": resume.id,
                    "chunk_type": chunk["chunk_type"],
                    "file_name": resume.file_name,
                    "created_by": resume.created_by,
                },
            )
        
resume_embedding_service = ResumeEmbeddingService()
