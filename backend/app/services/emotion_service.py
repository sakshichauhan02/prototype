import json
import httpx
import os
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.emotional_history import EmotionalHistory

class EmotionService:
    @staticmethod
    async def analyze_emotion(message: str) -> Dict[str, Any]:
        """
        Analyzes the emotional tone, sentiment label, score, and intensity of a user message.
        Pipeline order:
        1. Hugging Face Inference API (if HUGGINGFACE_API_KEY is set)
        2. Gemini API Classification (if GEMINI_API_KEY is set)
        3. Local Rule-based matching (offline fallback)
        """
        # --- Stage 1: Hugging Face Inference API ---
        hf_key = getattr(settings, "HUGGINGFACE_API_KEY", "")
        if hf_key and hf_key.strip():
            url = "https://api-inference.huggingface.co/models/bhadresh-savani/distilbert-base-uncased-emotion"
            headers = {"Authorization": f"Bearer {hf_key}"}
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.post(url, json={"inputs": message}, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            scores = data[0] if isinstance(data[0], list) else data
                            best = max(scores, key=lambda x: x.get("score", 0.0))
                            hf_emotion = best.get("label", "neutral").lower()
                            score = best.get("score", 0.5)
                            
                            # Map HF categories (joy, love, sadness, anger, fear, surprise) to Aetheria categories
                            emotion_map = {
                                "joy": ("excited", "POSITIVE"),
                                "love": ("excited", "POSITIVE"),
                                "surprise": ("excited", "POSITIVE"),
                                "sadness": ("sad", "NEGATIVE"),
                                "anger": ("frustrated", "NEGATIVE"),
                                "fear": ("stressed", "NEGATIVE")
                            }
                            primary, sentiment = emotion_map.get(hf_emotion, ("neutral", "NEUTRAL"))
                            return {
                                "primary_emotion": primary,
                                "sentiment_label": sentiment,
                                "sentiment_score": score,
                                "intensity": score,
                                "notes": f"Detected by Hugging Face API ({hf_emotion})."
                            }
            except Exception as e:
                print(f"Warning: Hugging Face emotion classifier failed: {e}. Trying Gemini fallback.")

        # --- Stage 2: Gemini API Classification ---
        gemini_key = getattr(settings, "GEMINI_API_KEY", "")
        if gemini_key and gemini_key.strip():
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            system_instruction = (
                "You are an emotion and sentiment analysis service.\n"
                "Analyze the user's message and determine:\n"
                "1. \"primary_emotion\": Must be one of: [\"neutral\", \"stressed\", \"excited\", \"frustrated\", \"sad\"].\n"
                "2. \"sentiment_label\": Must be one of: [\"POSITIVE\", \"NEGATIVE\", \"NEUTRAL\"].\n"
                "3. \"sentiment_score\": Float between 0.0 and 1.0.\n"
                "4. \"intensity\": Float between 0.0 and 1.0.\n"
                "5. \"notes\": A very short explanation (1 sentence) of why you classified it this way.\n\n"
                "Output must be ONLY a valid JSON object matching this structure:\n"
                "{\n"
                "  \"primary_emotion\": \"excited\",\n"
                "  \"sentiment_label\": \"POSITIVE\",\n"
                "  \"sentiment_score\": 0.95,\n"
                "  \"intensity\": 0.9,\n"
                "  \"notes\": \"Explanation...\"\n"
                "}"
            )
            payload = {
                "contents": [{"parts": [{"text": message}]}],
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json"
                }
            }
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            text = parts[0].get("text", "").strip() if parts else ""
                            if text:
                                if text.startswith("```json"):
                                    text = text.split("```json")[1].split("```")[0].strip()
                                elif text.startswith("```"):
                                    text = text.split("```")[1].split("```")[0].strip()
                                parsed = json.loads(text)
                                # Validate keys
                                if all(k in parsed for k in ["primary_emotion", "sentiment_label", "sentiment_score", "intensity"]):
                                    parsed["notes"] = parsed.get("notes", "Classified by Gemini 2.5.")
                                    return parsed
            except Exception as e:
                print(f"Warning: Gemini emotion classifier failed: {e}. Trying rules fallback.")

        # --- Stage 3: Local Rule-Based Matching (Default Fallback) ---
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["stressed", "anxious", "deadline", "busy", "overwhelmed", "tired", "exhausted"]):
            return {
                "primary_emotion": "stressed",
                "sentiment_label": "NEGATIVE",
                "sentiment_score": 0.8,
                "intensity": 0.85,
                "notes": "Detected words relating to stress or exhaustion (rules-based)."
            }
        elif any(w in msg_lower for w in ["excited", "happy", "great", "awesome", "wonderful", "cool", "yay", "love", "selected"]):
            return {
                "primary_emotion": "excited",
                "sentiment_label": "POSITIVE",
                "sentiment_score": 0.95,
                "intensity": 0.9,
                "notes": "Detected positive excitement indicators (rules-based)."
            }
        elif any(w in msg_lower for w in ["frustrated", "angry", "annoyed", "hate", "slow", "broke", "stupid", "worst"]):
            return {
                "primary_emotion": "frustrated",
                "sentiment_label": "NEGATIVE",
                "sentiment_score": 0.9,
                "intensity": 0.95,
                "notes": "Detected irritation or anger key terms (rules-based)."
            }
        elif any(w in msg_lower for w in ["sad", "depressed", "lonely", "unhappy", "cry", "hurt", "disappointed"]):
            return {
                "primary_emotion": "sad",
                "sentiment_label": "NEGATIVE",
                "sentiment_score": 0.75,
                "intensity": 0.7,
                "notes": "Detected sadness vocabulary (rules-based)."
            }
        else:
            return {
                "primary_emotion": "neutral",
                "sentiment_label": "NEUTRAL",
                "sentiment_score": 0.5,
                "intensity": 0.2,
                "notes": "No strong emotional markers detected (rules-based)."
            }



    @staticmethod
    async def record_emotion(
        user_id: int,
        message_id: Optional[int],
        analysis: Dict[str, Any],
        db: AsyncSession
    ) -> EmotionalHistory:
        """
        Saves the detected emotional analysis snap into PostgreSQL history.
        """
        record = EmotionalHistory(
            user_id=user_id,
            source_message_id=message_id,
            primary_emotion=analysis["primary_emotion"],
            sentiment_label=analysis["sentiment_label"],
            sentiment_score=analysis["sentiment_score"],
            intensity=analysis["intensity"],
            notes=analysis["notes"]
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    def get_adaptive_prompt_modifier(primary_emotion: str) -> str:
        """
        Returns dynamic instruction modifiers to guide prompt adaptation based on detected emotion.
        """
        if primary_emotion == "stressed":
            return (
                "\n[EMOTIONAL DYNAMICS MODIFIER]: The user is currently experiencing high stress. "
                "Adopt an exceptionally calm, soothing, reassuring, and encouraging tone. Keep responses uncluttered "
                "and offer practical, supportive relief words."
            )
        elif primary_emotion == "excited":
            return (
                "\n[EMOTIONAL DYNAMICS MODIFIER]: The user is very excited or happy! "
                "Match their positive energy. Be enthusiastic, warm, and highly engaging. Celebrate their wins!"
            )
        elif primary_emotion == "frustrated":
            return (
                "\n[EMOTIONAL DYNAMICS MODIFIER]: The user is frustrated. "
                "Speak with deep empathy, active validation, and absolute patience. Do not defend, argue, or over-explain; "
                "instead, clarify, support, and align with their needs first."
            )
        elif primary_emotion == "sad":
            return (
                "\n[EMOTIONAL DYNAMICS MODIFIER]: The user is feeling down or sad. "
                "Speak in a gentle, warm, and comforting tone. Express genuine care and supportive warmth."
            )
        return ""

emotion_service = EmotionService()
