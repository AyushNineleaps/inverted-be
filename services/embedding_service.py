from FlagEmbedding import BGEM3FlagModel


class EmbeddingService:

    def __init__(self):
        self.model = BGEM3FlagModel(
            "BAAI/bge-m3",
            use_fp16=False,
            device="cpu"
        )

    def generate_embedding(self, text: str):
        result = self.model.encode(
            [text],
            return_dense=True
        )

        return result["dense_vecs"][0]


embedding_service = EmbeddingService()