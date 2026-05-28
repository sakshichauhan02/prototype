import json
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import settings
from app.models.memory import Memory
from app.services.qdrant_service import qdrant_service

class MemoryService:
    @staticmethod
    async def extract_important_fact(message: str) -> Optional[Dict[str, str]]:
        """
        Uses Gemini LLM to detect if there is any long-term fact to remember.
        Returns a dict with {"fact": "...", "category": "..."} or None if ignored.
        """
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
            # Trivial local fallback for demo mode
            msg_lower = message.lower()
            if "i love" in msg_lower or "i like" in msg_lower or "my favorite" in msg_lower or "i work" in msg_lower:
                fact = message.strip()
                category = "Preferences"
                if "learn" in msg_lower or "code" in msg_lower or "build" in msg_lower:
                    category = "Technical"
                return {"fact": fact, "category": category}
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        system_instruction = (
            "You are a background cognitive memory service for a personal companion AI. "
            "Your job is to analyze the user's message and determine if it contains any important "
            "long-term personal details, preferences, habits, interests, background info, or facts about the user "
            "that the AI companion should remember.\n\n"
            "Examples of important info to SAVE:\n"
            "- 'I love football'\n"
            "- 'My favorite food is sushi'\n"
            "- 'I work as a software engineer'\n"
            "- 'I want to build a startup by next year'\n\n"
            "Examples of transient info to IGNORE:\n"
            "- 'My network is slow today'\n"
            "- 'Hello there'\n"
            "- 'I am going to bed now'\n"
            "- 'This server is not working'\n"
            "- 'How are you?'\n\n"
            "If it contains important long-term user information, extract it as a concise, objective third-person fact "
            "(e.g., 'Loves football', 'Favorite food is sushi', 'Works as a software engineer') and classify it into one of these: "
            "['Personal', 'Technical', 'Goals', 'Preferences'].\n"
            "If the message has no long-term significance, respond with the exact word 'IGNORE'.\n"
            "If saving, respond ONLY with a JSON object in this format:\n"
            "{\"fact\": \"Concise fact description\", \"category\": \"Personal\"}"
        )
        
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": message}]
            }],
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        text = parts[0].get("text", "").strip() if parts else ""
                        
                        if not text or "IGNORE" in text.upper():
                            return None
                            
                        try:
                            if text.startswith("```json"):
                                text = text.split("```json")[1].split("```")[0].strip()
                            elif text.startswith("```"):
                                text = text.split("```")[1].split("```")[0].strip()
                            parsed = json.loads(text)
                            if "fact" in parsed and "category" in parsed:
                                return parsed
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"Memory extraction error: {e}")
            
        return None

    @staticmethod
    async def process_incoming_message(user_id: int, message: str, db: AsyncSession) -> Optional[Memory]:
        """
        Detects, extracts, saves, and vectorizes facts from incoming user messages.
        """
        extracted = await MemoryService.extract_important_fact(message)
        if not extracted:
            return None
            
        new_memory = Memory(
            fact=extracted["fact"],
            category=extracted["category"],
            user_id=user_id,
            source="chat"
        )
        db.add(new_memory)
        await db.commit()
        await db.refresh(new_memory)
        
        try:
            await qdrant_service.upsert_memory(
                user_id=user_id,
                memory_id=new_memory.id,
                fact=new_memory.fact,
                category=new_memory.category
            )
        except Exception as e:
            print(f"Failed to sync message memory to Qdrant: {e}")
            
        return new_memory

    @staticmethod
    async def add_memory_manually(user_id: int, fact: str, category: str, db: AsyncSession) -> Memory:
        """
        Creates a manual memory entry in both SQL and Qdrant.
        """
        new_memory = Memory(
            fact=fact,
            category=category,
            user_id=user_id,
            source="manual"
        )
        db.add(new_memory)
        await db.commit()
        await db.refresh(new_memory)
        
        try:
            await qdrant_service.upsert_memory(
                user_id=user_id,
                memory_id=new_memory.id,
                fact=new_memory.fact,
                category=new_memory.category
            )
        except Exception as e:
            print(f"Failed to sync manual memory to Qdrant: {e}")
            
        return new_memory

    @staticmethod
    async def update_memory(user_id: int, memory_id: int, fact: str, category: str, db: AsyncSession) -> Optional[Memory]:
        """
        Modifies a memory entry in SQL and syncs the update to Qdrant.
        """
        stmt = select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
        result = await db.execute(stmt)
        memory = result.scalar_one_or_none()
        
        if not memory:
            return None
            
        memory.fact = fact
        memory.category = category
        await db.commit()
        await db.refresh(memory)
        
        try:
            await qdrant_service.upsert_memory(
                user_id=user_id,
                memory_id=memory.id,
                fact=memory.fact,
                category=memory.category
            )
        except Exception as e:
            print(f"Failed to update memory in Qdrant: {e}")
            
        return memory

    @staticmethod
    async def delete_memory(user_id: int, memory_id: int, db: AsyncSession) -> bool:
        """
        Deletes a memory entry from SQL and Qdrant.
        """
        stmt = select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
        result = await db.execute(stmt)
        memory = result.scalar_one_or_none()
        
        if not memory:
            return False
            
        await db.delete(memory)
        await db.commit()
        
        try:
            await qdrant_service.delete_memory(memory_id)
        except Exception as e:
            print(f"Failed to delete memory from Qdrant: {e}")
            
        return True

    @staticmethod
    async def retrieve_context(user_id: int, query: str) -> str:
        """
        Queries Qdrant for semantically relevant memories and constructs prompt context.
        """
        try:
            hits = await qdrant_service.search_memories(user_id, query, limit=5)
            if not hits:
                return ""
                
            context_lines = []
            for hit in hits:
                # Include semantic relevance in logs or structure
                context_lines.append(f"- [{hit['category']}] {hit['fact']}")
                
            return "\n[Injected User Context Memories]:\n" + "\n".join(context_lines)
        except Exception as e:
            print(f"Qdrant retrieval error: {e}. Falling back to empty context.")
            return ""

memory_service = MemoryService()
