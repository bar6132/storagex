from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Boolean, BigInteger, Text
from sqlalchemy.orm import relationship, backref
from database import Base
import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    storage_limit = Column(BigInteger, default=524288000)
    videos = relationship("VideoJob", back_populates="owner")

class VideoJob(Base):
    __tablename__ = "video_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)        
    category = Column(String, default="Other")       
    is_shared = Column(Boolean, default=False)       
    filename = Column(String, nullable=False)
    file_size = Column(BigInteger, default=0) 
    status = Column(String, default="pending") 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    s3_key = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False) 
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="videos")
    summary_data = relationship(
        "VideoSummary", 
        back_populates="video", 
        uselist=False, 
        cascade="all, delete-orphan" 
    )
    @property
    def summary(self):
        if self.summary_data:
            return self.summary_data.summary_text
        return None


class VideoSummary(Base):
    __tablename__ = "video_summaries"
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, ForeignKey("video_jobs.id"), unique=True, nullable=False)
    summary_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    video = relationship("VideoJob", back_populates="summary_data")