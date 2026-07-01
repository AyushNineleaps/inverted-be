# # from langchain.chat_models import init_chat_model

# # from config import GEMINI_API_KEY

# # llm= init_chat_model('gemini-2.5-flash',model_provider='google_genai',api_key=GEMINI_API_KEY,temperature=0)

# # response = llm.invoke("tell me about sun in 10 words")

# # print(response.content)
# # from config import GEMINI_API_KEY
# import os
# from langchain_community.document_loaders import TextLoader
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import ChatPromptTemplate
# from langchain.chat_models import init_chat_model
# from langchain_core.documents import Document
# from langchain_ollama import OllamaLLM, OllamaEmbeddings
# from langchain_core.messages import HumanMessage, AIMessage
# script_dir = os.path.dirname(os.path.abspath(__file__))
# from langchain_community.document_loaders.pdf import PyPDFLoader
# # 2. Combine it to point to data.txt in that same folder
# file_path = os.path.join(script_dir, 'data.txt')

# try:
#     with open(file_path, 'r', encoding='utf-8') as f:
#         text_content = f.read()
# except FileNotFoundError:
#     print(f"file not found inside this folder")
#     exit(1)
# documents = [Document(page_content=text_content, metadata={"source": "data.txt"})]

# # splitting

# text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
# docs = text_splitter.split_documents(documents);

# # creating embedding
# embeddings = OllamaEmbeddings(
#     model="nomic-embed-text"
# )

# vectorstore= FAISS.from_documents(docs,embeddings)

# retriever= vectorstore.as_retriever(search_kwargs={'k':3})

# # llm= init_chat_model('gemini-2.5-flash',model_provider='google_genai',api_key=GEMINI_API_KEY,temperature=0.1)
# llm = OllamaLLM(model="qwen2.5:1.5b-instruct-q8_0")

# # prompt
# prompt = ChatPromptTemplate.from_template(
#     """SYSTEM: You are a strict factual reader. Your task is to answer the Question based strictly on the provided Context and the Conversation History.
    
#     CRITICAL RULES:
#     1. If the answer cannot be completely derived from either the Context chunks or the recent Conversation History, you MUST reply with exactly 'Not found'.
#     2. Do not use any outside training knowledge.

#     --- CONVERSATION HISTORY ---
#     {chat_history}

#     --- CONTEXT CHUNKS ---
#     {context}

#     Question: {question}
#     Answer:"""
# )
# # start question/answer loop
# chain = prompt | llm | StrOutputParser()

# chat_history=[]

# query_rewriter_prompt = ChatPromptTemplate.from_template(
#     """SYSTEM: Look at the Conversation History and the Latest Question. 
#     If the Latest Question uses pronouns (like 'it', 'that', 'they') or references previous topics, 
#     rewrite it into a single, standalone question containing all necessary keywords for a search engine.
#     If it is already a standalone question, return it exactly as it is. Do not answer it.

#     History:
#     {chat_history}

#     Latest Question: {question}
#     Standalone Question:"""
# )

# query_rewritter_chain= query_rewriter_prompt |llm|StrOutputParser()

# while True:
#     history_str=""
#     question = input('Ask a question (or type "exit"): ').strip()
#     if question.lower()=='exit':
#         break
    
#     for msg in chat_history[-6:]:
#         prefix = 'User: ' if isinstance(msg,HumanMessage) else "Assistant: "
#         history_str+= f"{prefix}{msg.content}\n"
        
#     if chat_history:
#         search_question=query_rewritter_chain.invoke({
#             'chat_history':history_str,
#             'question':question
#         }).strip()
#     else:
#         search_question= question
#     print(search_question)
#     #retrive relevant chunks
#     retrieved_docs = retriever.invoke(search_question)
#     context = "\n".join([doc.page_content.strip() for doc in retrieved_docs])
    
#     #get response
#     response = chain.invoke({
#         "chat_history": history_str,
#         "context":context,
#         'question': question
#     })
#     chat_history.append(HumanMessage(content=question))
#     chat_history.append(AIMessage(content=response))
#     print(response)

from langchain_ollama import OllamaLLM


def test_json():
    llm = OllamaLLM(
        model="qwen2.5:1.5b-instruct-q8_0",
        temperature=0,
        format="json",
        options={"num_predict": 256}
    )

    prompt = """
Return ONLY this JSON.

{
    "message": "hello"
}
"""

    response = llm.invoke(prompt)

    print("TYPE:")
    print(type(response))

    print("\nREPR:")
    print(repr(response))

    print("\nRESPONSE:")
    print(response)


if __name__ == "__main__":
    test_json()