import chromadb


class ChromaService:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="resumes",
            metadata={"hnsw:space": "cosine"}
        )

    def add_resume(
        self,
        resume_id: str,
        document: str,
        embedding: list,
        metadata: dict
    ):
        self.collection.add(
            ids=[resume_id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata]
        )

    def search(
        self,
        query_embedding: list,
        chunk_type:str,
        limit: int = 3
    ):
        where_filter : chromadb.Where | None = None
        if chunk_type != '':
            where_filter = {
                "chunk_type":chunk_type
            }
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter
        )
    def search(
        self,
        query_embedding: list,
        chunk_type: str,
        limit: int = 3,
        resume_ids: list = None
    ):
        conditions = []
        
        # 1. Handle chunk_type filter
        if chunk_type != '':
            conditions.append({"chunk_type": chunk_type})
            
        # 2. Handle resume_ids filter using the $in operator
        if resume_ids:
            conditions.append({"resume_id": {"$in": resume_ids}})
            
        # 3. Construct the final Chroma where_filter
        where_filter = None
        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter
        )
        
    def count(self):
        total_records = self.collection.count()
        print("total_records",total_records)


chroma_service = ChromaService()