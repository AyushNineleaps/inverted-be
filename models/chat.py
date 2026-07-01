from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, String, Text

from database import Base


class ChatMessage(Base):
    __tablename__= 'chat_messages'
    id= Column(String,primary_key= True,default = lambda:str(uuid.uuid4()))
    session_id= Column(String,index =True,nullable=False)
    creator= Column(String, nullable=False)
    content= Column(Text,nullable=False)
    created_at= Column(DateTime,default=lambda:datetime.now(timezone.utc))
    chat_metadata= Column(Text)
    