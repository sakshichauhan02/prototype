import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database import Base
from app.services.memory_service import memory_service
from app.services.rag_service import rag_service
from app.services.ai_service import ai_service

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_conflict():
    print("=== Testing Memory Conflict Resolution ===")
    
    # 1. Setup local temporary database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as db:
        user_id = 1
        
        # Store initial color: blue
        print("\nStep 1: Storing initial fact: 'My favorite color is blue.'")
        await memory_service.process_incoming_message(
            user_id=user_id,
            message="My favorite color is blue.",
            db=db,
            consent_memory=True
        )
        
        # Verify it is in context
        context_before = await rag_service.retrieve_context(user_id=user_id, query="What is my favorite color?", db=db)
        print(f"RAG Context (before update):\n{context_before}")
        assert "blue" in context_before.lower(), "Initial memory 'blue' not found!"
        
        # Store updated color: red
        print("\nStep 2: Storing updated fact: 'My favorite color is red now.'")
        await memory_service.process_incoming_message(
            user_id=user_id,
            message="My favorite color is red now.",
            db=db,
            consent_memory=True
        )
        
        # Retrieve context again to check conflict resolution
        print("\nStep 3: Retrieving context for query: 'What is my favorite color?'")
        context_after = await rag_service.retrieve_context(user_id=user_id, query="What is my favorite color?", db=db)
        print(f"RAG Context (after update):\n{context_after}")
        
        # Verify conflict resolution
        has_red = "red" in context_after.lower()
        has_blue = "blue" in context_after.lower()
        
        if has_red and not has_blue:
            print("\n✅ Success! Old memory 'blue' was deleted, and new memory 'red' was successfully saved.")
        else:
            print("\n❌ Failure:")
            if not has_red:
                print("  - New memory 'red' was NOT found.")
            if has_blue:
                print("  - Old memory 'blue' was NOT deleted.")

if __name__ == "__main__":
    asyncio.run(test_conflict())
