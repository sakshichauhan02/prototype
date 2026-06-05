from sqlalchemy import Column, Integer, BigInteger, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ChatThread(Base):
    __tablename__ = "chat_threads"
    __table_args__ = (
        Index("ix_chat_threads_user_updated", "user_id", "updated_at"),
        Index("ix_chat_threads_user_companion", "user_id", "companion_id"),
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, index=True)
    title = Column(String, index=True, nullable=False)
    companion_id = Column(String, default="aria", nullable=False)
    user_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_mode = Column(String, default="personal", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="threads")
    messages = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_history"
    __table_args__ = (
        Index("ix_chat_history_thread_timestamp", "thread_id", "timestamp"),
        Index("ix_chat_history_sender_timestamp", "sender", "timestamp"),
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, index=True)
    thread_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String, nullable=False)  # "user" or "ai"
    content = Column(Text, nullable=False)
    model_name = Column(String, nullable=True)
    token_count = Column(Integer, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    thread = relationship("ChatThread", back_populates="messages")
    emotional_snapshots = relationship("EmotionalHistory", back_populates="source_message")
