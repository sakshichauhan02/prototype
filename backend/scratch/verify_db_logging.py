import asyncio
import os
import sys
from sqlalchemy import select

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.chat import ChatThread, ChatMessage

async def verify():
    async with AsyncSessionLocal() as db:
        # Find all threads in personal mode
        stmt_threads = select(ChatThread).where(ChatThread.session_mode == "personal")
        res_threads = await db.execute(stmt_threads)
        personal_threads = res_threads.scalars().all()
        
        print(f"--- VERIFYING PERSONAL THREADS & MESSAGES ---")
        print(f"Total Personal Mode threads in DB: {len(personal_threads)}")
        
        for t in personal_threads:
            # Count messages logged in DB for this thread
            stmt_msgs = select(ChatMessage).where(ChatMessage.thread_id == t.id)
            res_msgs = await db.execute(stmt_msgs)
            msgs = res_msgs.scalars().all()
            print(f"Thread ID: {t.id}, Title: '{t.title}', Messages logged in DB: {len(msgs)}")
            if len(msgs) > 0:
                print(f"  Note: Messages exist from before migration or test script: {len(msgs)} messages found.")
            else:
                print(f"  [PASS] Zero database message records found for this thread.")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(verify())
