from .chroma_service import chroma_service
from .embedding_service import embedding_service


class ResumeSearchService:
    def search_input(self,input:str,chunk_type:str=''):
        embedding_text= embedding_service.generate_embedding(input)
        resume_list = chroma_service.search(query_embedding= embedding_text.tolist(),chunk_type=chunk_type)
        return resume_list
        
resume_search_service = ResumeSearchService()
