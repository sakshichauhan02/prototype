import sys
import os
import asyncio
from sqlalchemy import select

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.chat import ChatThread

async def run_tests():
    print("--- TESTING DATABASE COLUMN ---")
    async with AsyncSessionLocal() as db:
        # Check database records
        stmt = select(ChatThread).limit(5)
        result = await db.execute(stmt)
        threads = result.scalars().all()
        
        print(f"Total threads in DB: {len(threads)}")
        for t in threads:
            print(f"Thread ID: {t.id}, Title: '{t.title}', Session Mode: '{t.session_mode}'")
            
        # Create a new test thread manually via DB to test default value
        new_t = ChatThread(
            title="Test Session Mode Default Thread",
            companion_id="aria",
            user_id=1  # Assuming user with ID 1 exists
        )
        db.add(new_t)
        await db.commit()
        await db.refresh(new_t)
        print(f"\nCreated Thread ID: {new_t.id}")
        print(f"Title: {new_t.title}")
        print(f"Default Session Mode: '{new_t.session_mode}' (Expected: 'personal')")
        
        # Update session mode to academic
        new_t.session_mode = "academic"
        await db.commit()
        await db.refresh(new_t)
        print(f"Updated Session Mode: '{new_t.session_mode}' (Expected: 'academic')")

if __name__ == "__main__":
    asyncio.run(run_tests())
