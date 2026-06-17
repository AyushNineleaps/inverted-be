from datetime import datetime
from typing import Optional
import uuid
from pydantic import ConfigDict, EmailStr, Field
from pydantic import BaseModel

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id : str
    name : str
    email : str
    role: str
    theme: str
    is_active : bool
    created_at : datetime
    updated_at : datetime
    

from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class CurrentUser(BaseModel):
    sub: str
    email: str
    role: str
    name: str
    is_active: bool
    
class ThemePayload(BaseModel):
    theme:str
    
class ActivationPayload(BaseModel):
    activation_status:bool
  
class UserEntry(BaseModel):
    class Config: from_attributes = True
    id :uuid.UUID 
    name : str
    email : str
    role: str
    theme: str
    is_active : bool
    created_at : datetime
    updated_at : datetime
    
class UserListResponse(BaseModel):
    users:list[UserEntry]
    class Config:from_attributes = True
      