import asyncio
import sys
import os

# Force UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.chat import ChatThread, ChatMessage

async def read_latest():
    async with AsyncSessionLocal() as db:
        # Get latest thread
        stmt = select(ChatThread).order_by(ChatThread.updated_at.desc()).limit(1)
        res = await db.execute(stmt)
        thread = res.scalar_one_or_none()
        if not thread:
            print("No threads found.")
            return
            
        print(f"Latest Thread ID: {thread.id}, Title: {thread.title}, Mode: {thread.session_mode}")
        
        # Get messages in thread
        stmt_msg = select(ChatMessage).where(ChatMessage.thread_id == thread.id).order_by(ChatMessage.timestamp.desc()).limit(5)
        res_msg = await db.execute(stmt_msg)
        messages = res_msg.scalars().all()
        
        print("\nLatest 5 messages:")
        for msg in reversed(messages):
            print(f"[{msg.sender.upper()}]: {msg.content}")

if __name__ == "__main__":
    asyncio.run(read_latest())
