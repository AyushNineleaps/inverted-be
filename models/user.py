from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, String, Boolean, DateTime
from database import Base 

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String,nullable=False)
    email = Column(String,unique=True,nullable=False)
    password_hash= Column(String,nullable=True)
    google_sub= Column(String, nullable=True)
    role= Column(String,nullable=False, default='visitor')
    theme= Column(String,nullable=False, default='light')
    is_active = Column(Boolean, nullable= False, default= True)
    created_at = Column (DateTime, nullable= False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),onupdate=lambda: datetime.now(timezone.utc))
