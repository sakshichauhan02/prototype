import asyncio
import sys
import os

# Adjust path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.memory import Memory
from app.services.memory_service import memory_service
from sqlalchemy.future import select

async def query_memories():
    async with AsyncSessionLocal() as session:
        stmt = select(Memory).order_by(Memory.id.desc())
        result = await session.execute(stmt)
        memories = result.scalars().all()
        
        print(f"Total memories in database: {len(memories)}")
        for m in memories:
            decrypted_fact = memory_service.decrypt_fact(m.fact)
            print(f"  [ID: {m.id} | Cat: {m.category}] {decrypted_fact}")

if __name__ == "__main__":
    asyncio.run(query_memories())
