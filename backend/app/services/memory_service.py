import json
import httpx
import base64
import os
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from app.config import settings
from app.models.memory import Memory
from app.services.qdrant_service import qdrant_service

class MemoryService:
    @staticmethod
    def encrypt_fact(text: str) -> str:
        """
        Encrypts memory fact using AES-256-GCM symmetric cryptographic encryption.
        """
        try:
            key = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
            iv = os.urandom(12)
            encryptor = Cipher(
                algorithms.AES(key),
                modes.GCM(iv)
            ).encryptor()
            
            ciphertext = encryptor.update(text.encode("utf-8")) + encryptor.finalize()
            combined = iv + encryptor.tag + ciphertext
            encoded = base64.b64encode(combined).decode("utf-8")
            return f"aeth_aes:{encoded}"
        except Exception as e:
            print(f"Encryption failed: {e}")
            encoded = base64.b64encode(text.encode("utf-8")).decode("utf-8")
            return f"aeth_enc:{encoded}"

    @staticmethod
    def decrypt_fact(encrypted_text: str) -> str:
        """
        Decrypts AES-256-GCM encrypted fact (or legacy base64-obfuscated fact).
        """
        if not encrypted_text:
            return encrypted_text
            
        if encrypted_text.startswith("aeth_enc:"):
            try:
                encoded = encrypted_text.split("aeth_enc:")[1]
                return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
            except Exception as e:
                print(f"Legacy decryption failed: {e}")
                return encrypted_text
                
        if encrypted_text.startswith("aeth_aes:"):
            try:
                key = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
                raw_payload = base64.b64decode(encrypted_text.split("aeth_aes:")[1].encode("utf-8"))
                
                iv = raw_payload[:12]
                tag = raw_payload[12:28]
                ciphertext = raw_payload[28:]
                
                decryptor = Cipher(
                    algorithms.AES(key),
                    modes.GCM(iv, tag)
                ).decryptor()
                
                decrypted = decryptor.update(ciphertext) + decryptor.finalize()
                return decrypted.decode("utf-8")
            except Exception as e:
                print(f"AES decryption failed: {e}")
                return encrypted_text
                
        return encrypted_text

    @staticmethod
    async def extract_important_fact(message: str) -> List[Dict[str, str]]:
        """
        Uses Gemini LLM to detect if there is any long-term fact to remember.
        Uses an improved first-pass check to skip simple questions, greetings, and short chat messages.
        """
        msg_lower = message.lower().strip()
        
        # 1. Skip short responses or greetings
        if len(message) < 8:
            return []
            
        greetings = {"hello", "hi", "hey", "hola", "howdy", "good morning", "good afternoon", "good evening", "thanks", "thank you", "ok", "okay", "yes", "no", "cool", "awesome"}
        words = set(msg_lower.split())
        if words.intersection(greetings) and len(words) <= 3:
            return []
            
        # 2. Skip direct questions to the AI
        if "?" in message:
            return []

    @staticmethod
    def _local_fallback_parser(message: str) -> List[Dict[str, str]]:
        msg_lower = message.lower().strip()
        fact_indicators = ["remember that", "i love", "i like", "my favorite", "i work as", "i live in", "my goal is", "i am", "i want to", "prefer", "bought"]
        if not any(indicator in msg_lower for indicator in fact_indicators):
            return []
        
        # Simple splitter for "and" to handle compound sentences in fallback mode
        parts = [message.strip()]
        if " and " in msg_lower:
            idx = msg_lower.find(" and ")
            parts = [message[:idx].strip(), message[idx+5:].strip()]
            
        results = []
        for part in parts:
            part_lower = part.lower().strip()
            fact = part
            if part_lower.startswith("remember that"):
                fact = part[13:].strip()
            
            category = "Preferences"
            if any(w in part_lower for w in ["learn", "code", "build", "typescript", "react", "python", "developer"]):
                category = "Technical"
            elif any(w in part_lower for w in ["goal", "target", "want to", "plan to", "achieve"]):
                category = "Goals"
            elif any(w in part_lower for w in ["live", "work", "name", "from", "bought", "own"]):
                category = "Personal"
            results.append({"fact": fact, "category": category})
        return results

    @staticmethod
    async def extract_important_fact(message: str) -> List[Dict[str, str]]:
        """
        Uses Gemini LLM to detect if there is any long-term fact to remember.
        Uses an improved first-pass check to skip simple questions, greetings, and short chat messages.
        """
        msg_lower = message.lower().strip()
        
        # 1. Skip short responses or greetings
        if len(message) < 8:
            return []
            
        greetings = {"hello", "hi", "hey", "hola", "howdy", "good morning", "good afternoon", "good evening", "thanks", "thank you", "ok", "okay", "yes", "no", "cool", "awesome"}
        words = set(msg_lower.split())
        if words.intersection(greetings) and len(words) <= 3:
            return []
            
        # 2. Skip direct questions to the AI
        if "?" in message:
            return []

        # Fallback local parser when Gemini API key is missing
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
            return MemoryService._local_fallback_parser(message)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
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
            "If the message contains important long-term user information, extract it as one or more concise, objective third-person facts "
            "(e.g., 'Loves football', 'Favorite food is sushi', 'Works as a software engineer', 'Bought a red bicycle') and classify each into one of these: "
            "['Personal', 'Technical', 'Goals', 'Preferences']. Split compound sentences into multiple distinct facts if they belong to different categories.\n"
            "If the message has no long-term significance, respond with the exact word 'IGNORE'.\n"
            "If saving, respond ONLY with a JSON object in this format:\n"
            "{\"memories\": [{\"fact\": \"Concise fact description\", \"category\": \"Personal\"}]}"
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
                            return []
                            
                        try:
                            if text.startswith("```json"):
                                text = text.split("```json")[1].split("```")[0].strip()
                            elif text.startswith("```"):
                                text = text.split("```")[1].split("```")[0].strip()
                            parsed = json.loads(text)
                            if "memories" in parsed:
                                return parsed["memories"]
                            elif "fact" in parsed and "category" in parsed:
                                return [parsed]
                        except json.JSONDecodeError:
                            pass
                else:
                    print(f"Warning: Gemini extraction API returned status {response.status_code}. Using local fallback parser.")
                    return MemoryService._local_fallback_parser(message)
        except Exception as e:
            print(f"Memory extraction error: {e}. Using local fallback parser.")
            return MemoryService._local_fallback_parser(message)
            
        return []

    @staticmethod
    async def process_incoming_message(
        user_id: int,
        message: str,
        db: AsyncSession,
        consent_memory: bool = True
    ) -> List[Memory]:
        """
        Detects, extracts, saves (encrypted), and vectorizes facts from incoming user messages.
        """
        if not consent_memory:
            # Bypassed memory extraction due to settings consent denial
            return []

        extracted_list = await MemoryService.extract_important_fact(message)
        if not extracted_list:
            return []
            
        saved_memories = []
        for extracted in extracted_list:
            if not extracted.get("fact") or not extracted.get("category"):
                continue
                
            plain_fact = extracted["fact"].strip()
            category = extracted["category"]
            
            # Conflict Resolution:
            # If the new fact updates a previous statement (e.g., favorite color, current city, job),
            # clean up old contradicting records.
            try:
                # Find all existing memories for this user
                stmt = select(Memory).where(Memory.user_id == user_id)
                result = await db.execute(stmt)
                existing_records = result.scalars().all()
                
                # Check for conflicts
                conflict_keywords = [
                    ["favorite color"],
                    ["live in", "living in", "reside in", "hometown"],
                    ["work as", "job is", "occupation", "employed as"],
                    ["favorite language", "coding language", "programming language"]
                ]
                
                for keywords in conflict_keywords:
                    # If the new fact matches this group of keywords
                    if any(kw in plain_fact.lower() for kw in keywords):
                        # Find existing records that also match this group of keywords
                        for record in existing_records:
                            decrypted = MemoryService.decrypt_fact(record.fact)
                            if any(kw in decrypted.lower() for kw in keywords):
                                # Delete contradicting memory from SQL & Qdrant
                                print(f"Resolving memory conflict: deleting old memory: '{decrypted}'")
                                await db.delete(record)
                                try:
                                    await qdrant_service.delete_memory(record.id)
                                except Exception:
                                    pass
                await db.commit()
            except Exception as conflict_err:
                print(f"Memory conflict resolution warning: {conflict_err}")
                await db.rollback()
            
            # Encrypt the fact for resting SQL storage
            encrypted_fact = MemoryService.encrypt_fact(plain_fact)
            
            try:
                new_memory = Memory(
                    fact=encrypted_fact,
                    category=category,
                    user_id=user_id,
                    source="chat"
                )
                db.add(new_memory)
                await db.commit()
                await db.refresh(new_memory)
            except Exception as e:
                print(f"Failed to save memory to SQL: {e}")
                await db.rollback()
                continue
            
            # Index in Qdrant (non-blocking — never crashes the request)
            try:
                await qdrant_service.upsert_memory(
                    user_id=user_id,
                    memory_id=new_memory.id,
                    fact=plain_fact,
                    category=category
                )
            except Exception as e:
                print(f"Qdrant upsert skipped (non-fatal): {e}")
                
            # Decrypt back for internal list return
            new_memory.fact = plain_fact
            saved_memories.append(new_memory)
            
        return saved_memories

    @staticmethod
    async def add_memory_manually(user_id: int, fact: str, category: str, db: AsyncSession) -> Memory:
        """
        Creates a manual memory entry in both SQL (encrypted) and Qdrant (plain-text index).
        """
        encrypted_fact = MemoryService.encrypt_fact(fact)
        new_memory = Memory(
            fact=encrypted_fact,
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
                fact=fact,
                category=new_memory.category
            )
        except Exception as e:
            print(f"Failed to sync manual memory to Qdrant: {e}")
            
        # Return plain text to API response
        new_memory.fact = fact
        return new_memory

    @staticmethod
    async def update_memory(user_id: int, memory_id: int, fact: str, category: str, db: AsyncSession) -> Optional[Memory]:
        """
        Modifies a memory entry in SQL (encrypted) and syncs the update to Qdrant.
        """
        stmt = select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
        result = await db.execute(stmt)
        memory = result.scalar_one_or_none()
        
        if not memory:
            return None
            
        memory.fact = MemoryService.encrypt_fact(fact)
        memory.category = category
        await db.commit()
        await db.refresh(memory)
        
        try:
            await qdrant_service.upsert_memory(
                user_id=user_id,
                memory_id=memory.id,
                fact=fact,
                category=memory.category
            )
        except Exception as e:
            print(f"Failed to update memory in Qdrant: {e}")
            
        memory.fact = fact
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
                context_lines.append(f"- [{hit['category']}] {hit['fact']}")
                
            return "\n[Injected User Context Memories]:\n" + "\n".join(context_lines)
        except Exception as e:
            print(f"Qdrant retrieval error: {e}. Falling back to empty context.")
            return ""

memory_service = MemoryService()
