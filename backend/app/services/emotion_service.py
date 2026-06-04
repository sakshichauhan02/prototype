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
        Analyzes the emotional tone, sentiment label, score, intensity, language, and communication style of a user message.
        Pipeline order:
        1. Hugging Face Inference API (if HUGGINGFACE_API_KEY is set)
        2. Gemini API Classification (if GEMINI_API_KEY is set)
        3. Local Rule-based matching (offline fallback)
        """
        result = None

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
                            result = {
                                "primary_emotion": primary,
                                "sentiment_label": sentiment,
                                "sentiment_score": score,
                                "intensity": score,
                                "notes": f"Detected by Hugging Face API ({hf_emotion})."
                            }
            except Exception as e:
                print(f"Warning: Hugging Face emotion classifier failed: {e}. Trying Gemini fallback.")

        # --- Stage 2: Gemini API Classification ---
        if not result:
            gemini_key = getattr(settings, "GEMINI_API_KEY", "")
            if gemini_key and gemini_key.strip():
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                headers = {"Content-Type": "application/json"}
                system_instruction = (
                    "You are an advanced linguistics, emotion, and sentiment analysis service.\n"
                    "Analyze the user's message and determine:\n"
                    "1. \"primary_emotion\": One of: [\"neutral\", \"stressed\", \"excited\", \"frustrated\", \"sad\"].\n"
                    "2. \"sentiment_label\": One of: [\"POSITIVE\", \"NEGATIVE\", \"NEUTRAL\"].\n"
                    "3. \"sentiment_score\": Float between 0.0 and 1.0.\n"
                    "4. \"intensity\": Float between 0.0 and 1.0.\n"
                    "5. \"language\": One of: [\"Hinglish\", \"Hindi\", \"English\"].\n"
                    "   - \"Hinglish\": Hindi phrases written in Roman script (e.g. 'yrr mujhe bhook lgri h', 'kya chal raha h').\n"
                    "   - \"Hindi\": Written in Devanagari script (e.g. 'मुझे भूख लग रही है').\n"
                    "   - \"English\": Standard English text.\n"
                    "6. \"communication_style\": One of: [\"Casual\", \"Friendly\", \"Professional\", \"Academic\", \"Emotional\", \"Excited\", \"Sad\", \"Angry\", \"Motivational\"].\n"
                    "7. \"notes\": A very short explanation (1 sentence) of why you classified it this way.\n\n"
                    "Output must be ONLY a valid JSON object matching this structure:\n"
                    "{\n"
                    "  \"primary_emotion\": \"excited\",\n"
                    "  \"sentiment_label\": \"POSITIVE\",\n"
                    "  \"sentiment_score\": 0.95,\n"
                    "  \"intensity\": 0.9,\n"
                    "  \"language\": \"Hinglish\",\n"
                    "  \"communication_style\": \"Casual\",\n"
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
                                        result = parsed
                except Exception as e:
                    print(f"Warning: Gemini emotion classifier failed: {e}. Trying rules fallback.")

        # --- Stage 3: Local Rule-Based Matching (Default Fallback) ---
        if not result:
            msg_lower = message.lower()
            if any(w in msg_lower for w in ["stressed", "anxious", "deadline", "busy", "overwhelmed", "tired", "exhausted"]):
                result = {
                    "primary_emotion": "stressed",
                    "sentiment_label": "NEGATIVE",
                    "sentiment_score": 0.8,
                    "intensity": 0.85,
                    "notes": "Detected words relating to stress or exhaustion (rules-based)."
                }
            elif any(w in msg_lower for w in ["excited", "happy", "great", "awesome", "wonderful", "cool", "yay", "love", "selected"]):
                result = {
                    "primary_emotion": "excited",
                    "sentiment_label": "POSITIVE",
                    "sentiment_score": 0.95,
                    "intensity": 0.9,
                    "notes": "Detected positive excitement indicators (rules-based)."
                }
            elif any(w in msg_lower for w in ["frustrated", "angry", "annoyed", "hate", "slow", "broke", "stupid", "worst"]):
                result = {
                    "primary_emotion": "frustrated",
                    "sentiment_label": "NEGATIVE",
                    "sentiment_score": 0.9,
                    "intensity": 0.95,
                    "notes": "Detected irritation or anger key terms (rules-based)."
                }
            elif any(w in msg_lower for w in ["sad", "depressed", "lonely", "unhappy", "cry", "hurt", "disappointed"]):
                result = {
                    "primary_emotion": "sad",
                    "sentiment_label": "NEGATIVE",
                    "sentiment_score": 0.75,
                    "intensity": 0.7,
                    "notes": "Detected sadness vocabulary (rules-based)."
                }
            else:
                result = {
                    "primary_emotion": "neutral",
                    "sentiment_label": "NEUTRAL",
                    "sentiment_score": 0.5,
                    "intensity": 0.2,
                    "notes": "No strong emotional markers detected (rules-based)."
                }

        # --- Stage 4: Enrich result with local Language & Style detection if missing ---
        if "language" not in result:
            result["language"] = EmotionService._detect_language_local(message)
        if "communication_style" not in result:
            result["communication_style"] = EmotionService._detect_style_local(message, result.get("primary_emotion", "neutral"))

        return result

    @staticmethod
    def _detect_language_local(message: str) -> str:
        msg_lower = message.lower()
        # 1. Check for Devanagari characters (Hindi script)
        import re
        if re.search(r"[\u0900-\u097f]", message):
            return "Hindi"

        # 2. Check for Hinglish stopwords
        hinglish_words = {
            "yrr", "yaar", "bhai", "kya", "bhook", "lgri", "h", "hai", "nhi", "nahi",
            "tha", "raha", "rahi", "acha", "achha", "kuch", "kha", "le", "pehle",
            "gussa", "mood", "hua", "bata", "btao", "karo", "kar", "rha", "rhi",
            "ab", "tum", "ese", "reply", "kyu", "aare", "jb", "sb", "the", "wo",
            "kaise", "kab", "kahan", "ho", "gaya", "gayi", "aur", "toh", "se", "ko",
            "par", "ek", "ki", "hi", "bhi", "he", "na", "ne", "mere", "meri", "tere",
            "teri", "hum", "tumhe", "apna", "apne", "apni", "chal", "rha", "rahe",
            "liya", "diya", "kiya", "kr", "kra", "karna", "karta", "karte"
        }
        words = re.findall(r"\b[a-z]+\b", msg_lower)
        if not words:
            return "English"
        
        hinglish_count = sum(1 for w in words if w in hinglish_words)
        if len(words) > 0 and (hinglish_count / len(words) >= 0.15 or (len(words) <= 3 and hinglish_count >= 1)):
            return "Hinglish"
            
        return "English"

    @staticmethod
    def _detect_style_local(message: str, primary_emotion: str) -> str:
        msg_lower = message.lower()
        
        # Check emotional states first
        if primary_emotion == "excited":
            return "Excited"
        if primary_emotion == "sad":
            return "Sad"
        if primary_emotion == "frustrated":
            return "Angry"
        if primary_emotion == "stressed":
            return "Emotional"

        academic_keys = ["explain", "machine learning", "algorithm", "science", "code", "programming", "definition", "architecture", "theory", "concept", "system", "structure", "optimization"]
        professional_keys = ["interview", "resume", "portfolio", "deadline", "project", "meeting", "client", "schedule", "professional", "corporate", "status", "salary", "job", "career"]
        motivational_keys = ["success", "inspire", "motivate", "goals", "achieve", "dream", "hard work", "focus", "discipline", "impossible", "persistence"]
        friendly_keys = ["dear", "friend", "buddy", "thanks", "thank you", "grateful", "sweet", "nice", "hello", "hi", "hey"]

        if any(w in msg_lower for w in academic_keys):
            return "Academic"
        if any(w in msg_lower for w in professional_keys):
            return "Professional"
        if any(w in msg_lower for w in motivational_keys):
            return "Motivational"
        if any(w in msg_lower for w in friendly_keys):
            return "Friendly"
            
        return "Casual"

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
        Legacy method kept for backward compatibility.
        """
        if primary_emotion == "stressed":
            return (
                "\n[EMOTIONAL DYNAMICS MODIFIER]: The user is currently experiencing high stress. "
                "Adopt an exceptionally calm, soothing, reassuring, and encouraging tone."
            )
        elif primary_emotion == "excited":
            return (
                "\n[EMOTIONAL DYNAMICS MODIFIER]: The user is very excited or happy! Match their positive energy."
            )
        elif primary_emotion == "frustrated":
            return (
                "\n[EMOTIONAL DYNAMICS MODIFIER]: The user is frustrated. Speak with deep empathy and active validation."
            )
        elif primary_emotion == "sad":
            return (
                "\n[EMOTIONAL DYNAMICS MODIFIER]: The user is feeling down or sad. Speak in a gentle, warm, and comforting tone."
            )
        return ""

    @staticmethod
    def get_tone_mirroring_modifier(analysis: Dict[str, Any]) -> str:
        """
        Generates custom prompt instructions to make the LLM dynamically mirror the user's
        detected language, communication style, and emotional tone.
        """
        lang = analysis.get("language", "English")
        style = analysis.get("communication_style", "Casual")
        emotion = analysis.get("primary_emotion", "neutral")

        # Format system instructions
        instructions = (
            f"\n\n[TONE & LANGUAGE MIRRORING SYSTEM INSTRUCTIONS]:\n"
            f"1. Detected User Language: {lang}\n"
            f"2. Detected Communication Style/Tone: {style}\n"
            f"3. Detected Emotional State: {emotion}\n\n"
            f"You MUST strictly align your response with the following rules:\n"
            f"- LANGUAGE MIRRORING: You MUST write your response entirely in {lang}. "
        )

        if lang == "Hinglish":
            instructions += (
                "Write in natural Hinglish (Hindi language written in Roman/English script, e.g., 'arre yrr, kya hua?'). "
                "Do NOT use Devanagari script. Use informal, conversational, and friendly terms. "
            )
        elif lang == "Hindi":
            instructions += (
                "Write in fluent Hindi using Devanagari script (e.g., 'अरे यार, क्या हुआ?'). "
            )
        else:
            instructions += (
                "Write in clear English. Match the complexity and tone of the user's message. "
            )

        instructions += f"\n- TONE & STYLE MIRRORING: Match the {style} tone and style of the user. "
        
        if style == "Casual":
            instructions += "Keep your language informal, relaxed, and natural. Use casual expressions."
        elif style == "Friendly":
            instructions += "Be warm, friendly, supportive, and personable. Use emojis gently if appropriate."
        elif style == "Professional":
            instructions += "Be polite, clear, structured, and business-appropriate. Avoid slang."
        elif style == "Academic":
            instructions += "Be educational, precise, logical, structured, and informative. Explain concepts clearly."
        elif style == "Emotional":
            instructions += "Acknowledge the emotional weight, show deep understanding, and express heartfelt words."
        elif style == "Excited":
            instructions += "Match the user's positive energy. Be enthusiastic, warm, and highly engaging. Celebrate wins."
        elif style == "Sad":
            instructions += "Speak in a gentle, warm, and comforting tone. Express genuine care and supportive warmth."
        elif style == "Angry":
            instructions += "Speak with deep empathy, active validation, and absolute patience. Do not defend or argue."
        elif style == "Motivational":
            instructions += "Be encouraging, inspiring, action-oriented, and positive. Lift the user's spirit."

        # Add Safety Rules
        instructions += (
            "\n- SAFETY & COMPLIANCE RULES:\n"
            "  * Never mock or mimic the user in a sarcastic or derogatory way.\n"
            "  * Never become rude, passive-aggressive, or cold.\n"
            "  * Always remain helpful and constructive.\n"
            "  * Never mention or reveal these internal classifications (like 'Detected Language' or 'Hinglish') to the user."
        )

        return instructions

emotion_service = EmotionService()
