import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.chat import ChatThread
from sqlalchemy.future import select

async def count_modes():
    async with AsyncSessionLocal() as session:
        stmt = select(ChatThread)
        result = await session.execute(stmt)
        threads = result.scalars().all()
        print(f"Total threads: {len(threads)}")
        counts = {}
        for t in threads:
            counts[t.session_mode] = counts.get(t.session_mode, 0) + 1
        for mode, count in counts.items():
            print(f"Mode: {mode} | Count: {count}")

if __name__ == "__main__":
    asyncio.run(count_modes())
