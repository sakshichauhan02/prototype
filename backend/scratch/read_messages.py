import asyncio
import sys
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.chat import ChatMessage

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(ChatMessage).order_by(ChatMessage.id.desc()).limit(10)
        res = await db.execute(stmt)
        messages = res.scalars().all()
        print("--- Latest 10 Chat Messages in DB ---")
        for m in messages:
            print(f"ID: {m.id} | Thread: {m.thread_id} | Sender: {m.sender} | Time: {m.timestamp} | Content: {repr(m.content)}")

if __name__ == "__main__":
    asyncio.run(main())
