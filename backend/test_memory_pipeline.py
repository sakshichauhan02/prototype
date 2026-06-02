import asyncio
from app.database import AsyncSessionLocal
from app.services.memory_service import memory_service
from app.models.user import User
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        # First, ensure there's a user to test with
        stmt = select(User).where(User.id == 1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("No user found. Please create a user or login first.")
            return

        print("Testing automated memory extraction...")
        test_message = "Remember that my favorite programming language is Python and I live in Tokyo."
        print(f"User Message: {test_message}")
        
        memories = await memory_service.process_incoming_message(
            user_id=user.id,
            message=test_message,
            db=db,
            consent_memory=True
        )
        
        if memories:
            print("\nSuccessfully extracted and embedded the following facts:")
            for m in memories:
                print(f" - Fact: '{m.fact}' | Category: {m.category}")
        else:
            print("\nFailed to extract any memories. Make sure the GEMINI_API_KEY is correct.")

if __name__ == "__main__":
    asyncio.run(main())
