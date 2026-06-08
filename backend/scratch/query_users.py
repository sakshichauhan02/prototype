import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.chat import ChatThread
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def query_users():
    async with AsyncSessionLocal() as session:
        stmt = select(User).options(selectinload(User.threads))
        result = await session.execute(stmt)
        users = result.scalars().all()
        for u in users:
            print(f"User ID: {u.id} | Name: {u.name} | Email: {u.email} | Threads count: {len(u.threads)}")
            for t in u.threads[:3]:
                print(f"  Thread ID: {t.id} | Title: {t.title} | Mode: {t.session_mode}")
            print()

if __name__ == "__main__":
    asyncio.run(query_users())
