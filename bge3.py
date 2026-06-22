# from services.embedding_service import embedding_service
# from services.chroma_service import chroma_service


# resume_text = """
# Candidate Profile

# Summary:
# Backend developer with 5 years experience.

# Skills:
# Python, FastAPI, PostgreSQL, AWS, Docker
# """


# # Create embedding
# embedding = embedding_service.generate_embedding(
#     resume_text
# )


# # Store in Chroma
# chroma_service.add_resume(
#     resume_id="resume_001",
#     document=resume_text,
#     embedding=embedding.tolist(),
#     metadata={
#         "file_name": "john_resume.pdf",
#         "created_by": "test_user"
#     }
# )


# # Search
# query = "Python backend developer with AWS experience"

# query_embedding = embedding_service.generate_embedding(
#     query
# )


# results = chroma_service.search(
#     query_embedding.tolist()
# )


# print(results)