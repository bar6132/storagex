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
    created_at: Optional[datetime]
    storage_limit: int 
    class Config:
        from_attributes = True

class VideoOut(BaseModel):
    id: str  
    filename: str
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = "Other"
    is_shared: bool
    status: str
    s3_key: Optional[str] = None
    created_at: datetime
    owner_id: int
    file_size: int
    is_deleted: bool
    owner_email: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class NotifySchema(BaseModel):
    user_id: int
    message: str
    video_id: str
    status: str