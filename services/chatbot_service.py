import json
from typing import Literal

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from .chroma_service import chroma_service
from .embedding_service import embedding_service


class ChatbotResponse(BaseModel):
    message: str = Field(description="The textual answer to the user's question.")
    action: Literal["fetch_resume", "compare_resume", "none"] = Field(
        description="Select 'fetch_resume' if one resume matches, 'compare_resume' if multiple match, or 'none' if zero match."
    )
    resume_ids: list[str] = Field(default_factory=list)


class ChatbotService:
    def __init__(self):
        self.llm = ChatOllama(
            model="llama3.2:1b",
            temperature=0,
            format="json",  # Forces the engine to stream raw JSON instantly
            num_thread=4    # Optimized for your 4-core i5 CPU
        )
        
        # Updated to return fetch_resume or compare_resume directly
        self.router_prompt = ChatPromptTemplate.from_template("""
            You are a strict query intent classifier. Categorize the user's question.
        
            Examples:
            Question: python
            Output: {{"intent": "fetch_resume"}}
        
            Question: look for react developers
            Output: {{"intent": "fetch_resume"}}
        
            Question: compare the angular devs
            Output: {{"intent": "compare_resume"}}
        
            Question: what is the difference between profile 1 and profile 2?
            Output: {{"intent": "compare_resume"}}
        
            Question: {question}
            Output:
            """)

        # PROMPT A: pulling data for a general search
        self.search_extraction_prompt = ChatPromptTemplate.from_template("""
            You are a Search Assistant. Your goal is to summarize how the candidates match the user's query.

            Use ONLY the provided context. Do NOT explain, define, or describe what the requested technologies or tools are.

            Return ONLY a JSON object matching this structure:
            {{
                "message": "Your search summary here...",
                "resume_ids": ["id_1", "id_2"]
            }}

            Rules for "message":
            - Summarize in 1-3 sentences exactly what the matching candidates DO with the requested skills based on their profiles (e.g., "The candidates include a Technical Level Designer who builds custom tools in Unreal Engine.").
            - Focus strictly on the candidates' roles, experience, and accomplishments.
            - Do NOT write a generic description or definition of the software/skill itself.
            - Do NOT mention Resume IDs or match counts in this text.

            Context:
            {context}

            Question:
            {question}
            """)
        # PROMPT B: comparing candidates
        self.compare_extraction_prompt = ChatPromptTemplate.from_template("""
            You are a Resume Comparison Expert. Your goal is to contrast the candidates' profiles.

            Use ONLY the provided context. Do NOT invent information.

            Return ONLY a JSON object matching this structure:
            {{
                "message": "Your comparison analysis here...",
                "resume_ids": ["id_1", "id_2"]
            }}

            Rules:
            - "message": Explain clearly in 1-3 sentences the differences, trade-offs, or contrasting experiences between the candidates. Do NOT mention Resume IDs in this text.
            - "resume_ids": An array of unique string IDs found in the context that match the request.

            Context:
            {context}

            Question:
            {question}
            """)

    def chatbot_handler(self, question: str) -> ChatbotResponse:
        
        router_chain = self.router_prompt | self.llm
        
        router_response = router_chain.invoke({
            'question': question
        })
        query_type_json = json.loads(router_response.content)
        
        # Defaulting to fetch_resume if something goes awry
        query_type = query_type_json.get("intent", "fetch_resume")
        
        # Route logic using your updated router intents
        if query_type == 'compare_resume':
            execution_chain = self.compare_extraction_prompt | self.llm 
        else:
            execution_chain = self.search_extraction_prompt | self.llm 
            
        question_vector = embedding_service.generate_embedding(question)
        search_result = chroma_service.search(question_vector, "")

        retrieved_docs = search_result.get("documents", [])
        metadatas = search_result.get("metadatas", [])

        if retrieved_docs and isinstance(retrieved_docs[0], list):
            retrieved_docs = retrieved_docs[0]

        if metadatas and isinstance(metadatas[0], list):
            metadatas = metadatas[0]

        if not retrieved_docs:
            return ChatbotResponse(
                message="No relevant information found.",
                action="none",
                resume_ids=[],
            )

        context_parts = []
        for i, (meta, content) in enumerate(zip(metadatas, retrieved_docs), start=1):
            context_parts.append(
                f"========== Resume Chunk {i} ==========\n"
                f"Resume ID:\n{meta.get('resume_id')}\n\n"
                f"Content:\n{content}\n"
            )

        context = "\n".join(context_parts)
        result = execution_chain.invoke({
            'context': context,
            'question': question
        })
        print("result", result)

        try:
            final_data = json.loads(result.content)
            message = final_data.get("message", "Here are the results.")
            resume_ids = final_data.get("resume_ids", [])
        except Exception:
            message = "Error parsing the model response."
            resume_ids = []

        # If vector search returned nothing, override the original intent action to 'none'
        if not resume_ids:
            query_type = "none"

        return ChatbotResponse(
            message=message,
            action=query_type,  # Direct response using the routed intent
            resume_ids=resume_ids,
        )


chatbot_service = ChatbotService()