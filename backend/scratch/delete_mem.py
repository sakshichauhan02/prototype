import asyncio
import sys
import os

# Adjust path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.memory import Memory
from sqlalchemy import delete

async def reset():
    async with AsyncSessionLocal() as session:
        # Delete ID 54 which contains the ice cream memory
        stmt = delete(Memory).where(Memory.id == 54)
        result = await session.execute(stmt)
        await session.commit()
        print(f"Deleted memory record with ID 54.")

if __name__ == "__main__":
    asyncio.run(reset())
