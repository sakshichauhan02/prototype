import asyncio
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.services.memory_service import memory_service
from app.models.user import User

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def measure_memory():
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == 1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("No user found.")
            return

        test_message = "Remember that I love developing in the Rust language and planning to go to Kyoto."
        print(f"Message: '{test_message}'")
        
        start_time = time.time()
        memories = await memory_service.process_incoming_message(
            user_id=user.id,
            message=test_message,
            db=db,
            consent_memory=True
        )
        duration = time.time() - start_time
        print(f"Memory extraction completed in: {duration:.4f} seconds")
        print(f"Extracted memories count: {len(memories)}")

if __name__ == "__main__":
    asyncio.run(measure_memory())
