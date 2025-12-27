from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    created_at: datetime
    class Config:
        from_attributes = True

class VideoOut(BaseModel):
    id: str  
    filename: str
    title: Optional[str] = None
    status: str
    s3_key: Optional[str] = None
    created_at: datetime
    owner_id: int
    is_deleted: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str