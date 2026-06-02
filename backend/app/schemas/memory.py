from pydantic import BaseModel, Field
from datetime import datetime

class MemoryBase(BaseModel):
    fact: str = Field(..., min_length=1)
    category: str = Field(default="Personal")  # "Personal" | "Technical" | "Goals" | "Preferences"

class MemoryCreate(MemoryBase):
    pass

class MemoryResponse(MemoryBase):
    id: int
    user_id: int
    timestamp: datetime
    source: str = "chat"

    class Config:
        from_attributes = True
