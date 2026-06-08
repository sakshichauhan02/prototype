import asyncio
import sys
import os

# Adjust path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.chat import ChatThread, ChatMessage
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def query():
    async with AsyncSessionLocal() as session:
        # Get the latest 5 threads
        stmt = select(ChatThread).options(selectinload(ChatThread.messages)).order_by(ChatThread.id.desc()).limit(5)
        result = await session.execute(stmt)
        threads = result.scalars().all()
        
        for t in threads:
            print(f"--- Thread ID: {t.id} | Title: {t.title} | Mode: {t.session_mode} ---")
            for m in t.messages:
                print(f"  [{m.sender}]: {m.content}")
            print()

if __name__ == "__main__":
    asyncio.run(query())
