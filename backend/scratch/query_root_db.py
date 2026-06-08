import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from app.database import Base
from app.models.user import User
from app.models.chat import ChatThread
from sqlalchemy.future import select

async def query_root():
    url = "sqlite+aiosqlite:///../aetheria.db"
    engine = create_async_engine(url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        stmt = select(User).options(selectinload(User.threads))
        result = await session.execute(stmt)
        users = result.scalars().all()
        print("--- ROOT DATABASE ---")
        for u in users:
            print(f"User ID: {u.id} | Name: {u.name} | Email: {u.email} | Threads count: {len(u.threads)}")
            for t in u.threads:
                print(f"  Thread ID: {t.id} | Title: {t.title} | Mode: {t.session_mode}")

if __name__ == "__main__":
    asyncio.run(query_root())
