from pydantic import BaseModel

from schemas.resume import ResumeListSchema


class ChatbotResponseSchema(BaseModel):
    message:str
    action:str
    creator:str
    table_data:list[ResumeListSchema] 