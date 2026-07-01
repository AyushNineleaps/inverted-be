from langchain_community.document_loaders import WebBaseLoader
import os
from langchain_core.prompts import ChatPromptTemplate

from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS

from langchain_text_splitters import RecursiveCharacterTextSplitter
os.environ["USER_AGENT"] = "MyWebScraperApp/1.0"
url='https://en.wikipedia.org/wiki/Gemini_(constellation)'
loader = WebBaseLoader(url)

docs = loader.load()
print(len(docs))
page_text=docs[0].page_content
output_filename = 'trimmed.txt'


if 'From Wikipedia, the free encyclopedia' in page_text:
    page_text = page_text.split('From Wikipedia, the free encyclopedia')[1]
    
sub_title_list = ["See also[edit]","Retrieved from", "This page was last edited"]
for sub_title in sub_title_list:
    if sub_title in page_text:
        page_text = page_text.split(sub_title)[0]
        break


with open(output_filename, "w", encoding="utf-8") as file:
    file.write(f"SOURCE URL: {url}\n")
    file.write("=" * 60 + "\n\n")
    
    file.write(page_text)
    
    # creating embedding
embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,      
    chunk_overlap=120,     
    separators=["\n\n[edit]\n", "\n\n", "\n", " "]
)
chunks = text_splitter.create_documents([page_text])
print(f"Generated {len(chunks)} contextual chunks.")

vectorstore= FAISS.from_documents(chunks,embeddings)

retriever = vectorstore.as_retriever(search_kwargs= {'k':3})

prompt= ChatPromptTemplate.from_template(
    """
    ROLE:
    you are a strict factual reader.
    TASK:
    your task is to answer the question based strictly on the provided context.
    CRITICAL INSTRUCTIONS:
    1. Answer the question using ONLY the facts explicitly stated in the --- CONTEXT CHUNKS ---.
    2. Do NOT assume, extrapolate, or combine facts about different subjects.
    3. If the context does not explicitly contain the exact answer to the question, you must output exactly: Not found
    4. Never say anything that contradicts the context.
    
    --- CONTEXT CHUNKS ---
    {context}

    Question: {question}
    Answer:"""
)
llm = OllamaLLM(model="qwen2.5:1.5b-instruct-q8_0",temperature=0)

chain= prompt | llm | StrOutputParser()

while True:
    question = input("Ask Question:")
    if(question.lower()=='q'):
        break
    found_data =retriever.invoke(question)
    context ='\n'.join([entry.page_content.strip() for entry in found_data])
    response=chain.invoke({
        'question': question.strip(),
        'context':context
    })
    print(response)