import json
import re
from typing import Literal

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from models.chat import ChatMessage
from langchain_core.messages import convert_to_messages, trim_messages

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
            model="qwen2.5:1.5b-instruct-q8_0",
            temperature=0,
            format="json",  # Forces the engine to stream raw JSON instantly
            num_thread=4    # Optimized for your 4-core i5 CPU
        )
        
        self.router_prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are a strict query intent classifier and conversation condenser for a Resume Search Engine.
                    Analyze the user's latest question and the provided chat history to determine intent, targeted resume IDs, or standalone keywords.

                    ### CRITICAL CONVERSATION RESOLUTION RULES:
                    1. "intent": 
                    - Set to "compare_resume" if the user explicitly asks to compare, contrast, use "vs"/"versus", OR if they ask value-based choices like "which one is better", "who is a better fit", "best choice", or "differences between them".
                    - Set to "fetch_resume" for generic keyword searches or when looking for a specific skill from scratch.
                    - Set to "fetch_resume" for general searches or if they ask a follow-up question about a specific candidate.

                    2. "target_ids": Look backwards at the "[State: ...]" blocks in the chat history. 
                    - If the user refers to "both", "them", or previous results collectively, extract ALL matching unique string IDs from the most recent state tracking log.
                    - If the user refers to a single specific profile (e.g., "tell me more about the first one" or "show me their skills"), extract ONLY that specific string ID from the state log.
                    - If it is a brand new search query, leave this array empty.

                    3. "standalone_query": 
                    - If it is a text-based search or follow-up question, resolve any conversational pronouns into clean standalone keywords.
                    - If it is a direct request to compare profiles without further context, you can leave this field empty "".

                    ### CRITICAL SCHEMA SAFETY RULE:
                    - If the provided 'chat_history' is completely empty [], or if the user introduces a brand new, standalone keyword query (like "angular" or "python"), you MUST set "target_ids" to an empty list []. 
                    - Absolutely DO NOT invent, guess, hallucinate, or reuse any random UUID hashes under any circumstances if they are not explicitly written in the chat history.

                    ### OUTPUT FORMAT:
                    Output a single raw JSON object only. Do not wrap in markdown backticks or block strings.
                    {{"intent": "compare_resume", "target_ids": ["23a7ffe6-ebcc-461f-82a2-42ac464935fb", "a8c2229a-3f33-4172-93e5-92126e6c0cdb"], "standalone_query": ""}}
                    """),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{question}")
                ])
# PROMPT A: pulling data for a general search
        self.search_extraction_prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are a precise resume data extractor. Your absolute priority is high recall. 
                    Analyze the provided Resume Chunks and extract ALL candidate IDs that contain or relate to the Search Term.

                    ### CRITICAL RULES:
                    1. SCAN EVERY SINGLE CHUNK. If a Resume Chunk explicitly mentions the Search Term anywhere (including raw keyword lists), you MUST extract its ID. Do not skip any matching chunk.
                    2. Even if a chunk only lists skills without a narrative summary, count it as a valid matching candidate and infer their professional focus from those skills.
                    3. Write a short 1-2 sentence collective summary describing the matching candidates under the "message" key. 
                    4. Collect and put the exact string IDs of ALL unique matching candidates inside the "resume_ids" array. Do not duplicate IDs.

                    ### EXPECTED OUTPUT FORMAT:
                    {{"message": "Found candidates with experience matching the requested technology.", "resume_ids": ["23a7ffe6-ebcc-461f-82a2-42ac464935fb"]}}
                    """),
                    ("human", "Search Term: {question}\n\nContext:\n{context}")
                ])

# PROMPT B: comparing candidates
        self.compare_extraction_prompt = ChatPromptTemplate.from_template("""
            You are a strict Resume Comparison Expert. Your task is to contrast candidate profiles using ONLY the provided context.

            ### RULES:
            1. Write a 1-3 sentence analysis for the "message" field highlighting the clear differences, skill trade-offs, or contrasting seniorities between the profiles based strictly on the context.
            2. Put their exact string IDs inside the "resume_ids" array. If no profile matches, leave the array empty.
            3. Do NOT invent outside history or information. If details are missing, contrast only what is explicitly written.
            4. Do NOT mention structural variables like "Resume ID", "Chunk 1", or numeric match counts anywhere within the text of the "message".

            ### EXPECTED OUTPUT FORMAT:
            {{"message": "A short, professional analysis contrasting the skills and experience of the candidates found in the context.", "resume_ids": ["a100e732-2efe-47a9-a7d9-dd6518b083b8"]}}

            Context:
            {context}

            Question:
            {question}
            """)
    def chatbot_handler(self, question: str,session_id:str,db:Session) -> ChatbotResponse:
        
        self.save_chat_helper(session_id=session_id,db=db,message_content=question,creator='user',metadata_dict={})
# Added "both" to the compiled pattern
        ambiguity_pattern = re.compile(
            r'\b(them|their|those|they|he|she|him|her|it|both|compare|contrast|versus|vs|difference|better|one|first|second|who|which)\b', 
            re.IGNORECASE
        )
        needs_history = bool(ambiguity_pattern.search(question))
        
        # 2. Conditional History Retrieval
        if needs_history:
            # Only pay the database and token tax if the sentence actually needs context
            trimmed_history = self.get_trimmed_history_helper(db, session_id)
        else:
            trimmed_history = []
        
        # trimmed_history = self.get_trimmed_history_helper(db, session_id)
        print("trimmed_history",trimmed_history)
        router_chain = self.router_prompt | self.llm
        router_response = router_chain.invoke({
            'question': question,
            'chat_history': trimmed_history
        })
        query_type_json = json.loads(router_response.content)
        raw_intent = query_type_json.get("intent")
        
        # 2. Force it to a valid literal option if it's empty or invalid
        VALID_ACTIONS = {"fetch_resume", "compare_resume", "none"}
        query_type = raw_intent if raw_intent in VALID_ACTIONS else "fetch_resume"

        # If the LLM misclassified but we have multiple target IDs and comparison phrasing, force correct it!
        modified_query = query_type_json.get("standalone_query") or question  
        target_ids = query_type_json.get("target_ids", [])
        print("query_type::::",query_type_json)
        comparison_triggers = ["better", "best", "vs", "versus", "compare", "difference", "which one"]
        has_trigger = any(trigger in question.lower() for trigger in comparison_triggers)
        if len(target_ids) >= 2 and has_trigger:
            query_type = "compare_resume"
        
        if target_ids:
            # Decide your execution prompt layer based on the intent
            if query_type == "compare_resume":
                execution_chain = self.compare_extraction_prompt | self.llm
            else:
                execution_chain = self.search_extraction_prompt | self.llm  
            
            # Fetch directly from Chroma via metadata IDs
            search_result = chroma_service.collection.get(
                where={"resume_id": {"$in": target_ids}}
            )
            retrieved_docs = search_result.get("documents", []) or []
            metadatas = search_result.get("metadatas", []) or []
            
        else:
            execution_chain = self.search_extraction_prompt | self.llm
            modified_query_vector = embedding_service.generate_embedding(modified_query)
            
            search_result = chroma_service.search(modified_query_vector, "")
            
            raw_docs = search_result.get("documents", [[]])
            raw_meta = search_result.get("metadatas", [[]])
            
            retrieved_docs = raw_docs[0] if raw_docs else []
            metadatas = raw_meta[0] if raw_meta else []
               
        # print("search_result",search_result)
        # retrieved_docs = search_result.get("documents", [])
        # metadatas = search_result.get("metadatas", [])

        if retrieved_docs and isinstance(retrieved_docs[0], list):
            retrieved_docs = retrieved_docs[0]

        if metadatas and isinstance(metadatas[0], list):
            metadatas = metadatas[0]

        if not retrieved_docs:
            message_content='No relevant information found.'
            self.save_chat_helper(session_id=session_id, db=db, message_content=message_content, creator='ai',metadata_dict={})
            return ChatbotResponse(
                message= message_content,
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
        print("context",context)
        result = execution_chain.invoke({
            'context': context,
            'question': question
        })
        print("result", result.content)

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
        metadata_dict={
            'action':query_type,
            'resume_ids':resume_ids
        }
        self.save_chat_helper(session_id=session_id, db=db, message_content=message, creator='ai',metadata_dict=metadata_dict)
        return ChatbotResponse(
            message=message,
            action=query_type,  # Direct response using the routed intent
            resume_ids=resume_ids,
        )
        
    def save_chat_helper(self,session_id:str, db:Session,message_content:str,creator:str,metadata_dict:dict):
        metadata_text = json.dumps(metadata_dict) if metadata_dict else None
        message:ChatMessage=ChatMessage(
            session_id= session_id,
            creator= creator,
            content= message_content,    
            chat_metadata= metadata_text
        )
        db.add(message)
        db.commit()
        db.refresh(message)
    
        return message
    
    def get_trimmed_history_helper(self, db: Session, session_id: str):
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
        db_messages = db.execute(stmt).scalars().all()
        langchain_messages = []
        for msg in db_messages:
            if msg.creator == "user":
                # Keep what the user said so the model knows the current conversational continuity
                langchain_messages.append(("human", msg.content))
            else:
                # For the AI, if metadata state exists, ONLY pass the state object
                if msg.chat_metadata:
                    content = f"[State: {msg.chat_metadata}]"
                    langchain_messages.append(("ai", content))
                # If there's no metadata state (e.g., "No relevant info found"), skip or pass a blank marker
                else:
                    continue
            
        message_sequence = convert_to_messages(langchain_messages)
        
        # Safe Character-Heuristic Count: 1000 tokens is roughly 4000 raw string characters
        return trim_messages(
            message_sequence,
            max_tokens=4000,           
            strategy="last",           
            token_counter=lambda msgs: sum(len(m.content) for m in msgs), # Fixes the GPT-2 warning perfectly
            start_on="human",          
            include_system=False       
        )
chatbot_service = ChatbotService()