from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Literal

class MessageBase(BaseModel):
    content: str = Field(..., min_length=1)

class MessageCreate(MessageBase):
    companion_id: Optional[str] = "aria"

class MessageResponse(BaseModel):
    id: int
    thread_id: int
    sender: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ThreadBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    companion_id: str = "aria"
    session_mode: Optional[Literal["casual", "academic", "professional", "creative"]] = "casual"

class ThreadCreate(ThreadBase):
    pass

class ThreadResponse(ThreadBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True
