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
        limit: int = 5
    ):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
    def count(self):
        total_records = self.collection.count()
        print("total_records",total_records)


chroma_service = ChromaService()