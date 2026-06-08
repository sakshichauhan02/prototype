import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.chat import ChatThread
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def query_sakshi():
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == "sakshichauhan64771@gmail.com").options(selectinload(User.threads))
        result = await session.execute(stmt)
        user = result.scalars().first()
        if user:
            print(f"Sakshi Threads ({len(user.threads)}):")
            for t in user.threads:
                print(f"  ID: {t.id} | Title: {t.title} | Mode: {t.session_mode}")

if __name__ == "__main__":
    asyncio.run(query_sakshi())
