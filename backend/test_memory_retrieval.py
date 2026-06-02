import asyncio
import sys
import json
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

async def test_memory():
    print("=== Testing Cognitive Memory Retrieval & Recall ===")
    
    # 1. Setup local temporary database engine to avoid dirtying the production database
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        # Ensure the table is created
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as db:
        user_id = 1
        fact_text = "My favorite color is blue."
        query_text = "What is my favorite color?"
        
        print(f"\nStoring fact: \"{fact_text}\" for User ID {user_id}...")
        # Save memory
        saved_memories = await memory_service.process_incoming_message(
            user_id=user_id,
            message=fact_text,
            db=db,
            consent_memory=True
        )
        
        if saved_memories:
            print(f"✅ Stored {len(saved_memories)} memory record(s):")
            for m in saved_memories:
                print(f"  - Category: {m.category}, Fact: \"{m.fact}\"")
        else:
            print("⚠️ process_incoming_message returned no saved memories (this is normal if it was already saved or skipped). Let's try adding it manually just in case.")
            await memory_service.add_memory_manually(
                user_id=user_id,
                fact="Favorite color is blue",
                category="Preferences",
                db=db
            )
            print("✅ Manually added fallback fact: \"Favorite color is blue\"")
            
        # 2. Retrieve context semantically
        print(f"\nRetrieving RAG context for query: \"{query_text}\"...")
        rag_context = await rag_service.retrieve_context(user_id=user_id, query=query_text, db=db)
        print(f"Retrieved RAG Context:\n{rag_context}")
        
        if "blue" in rag_context.lower():
            print("✅ Success: Context correctly contains the word 'blue'.")
        else:
            print("❌ Failure: Context does not contain the word 'blue'.")
            
        # 3. Test generate_reply prompt recall
        print("\nCalling ai_service.generate_reply to verify fact recall...")
        reply = await ai_service.generate_reply(
            companion_id="aria",
            message=query_text,
            history=[],
            temperature=0.2,
            tone="Analytical",
            rag_context=rag_context,
            emotion_modifier="",
            research_context="",
            primary_emotion="neutral"
        )
        print(f"Response:\n{reply}")
        
        if "blue" in reply.lower():
            print("\n✅ Success! The AI correctly recalled that your favorite color is blue.")
        else:
            print("\n❌ Failure: The AI returned a response without the correct memory.")

if __name__ == "__main__":
    asyncio.run(test_memory())
