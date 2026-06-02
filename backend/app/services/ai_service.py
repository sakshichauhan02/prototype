import httpx
from typing import List, Dict, Any
from app.config import settings

class AIService:
    # Centralized persona configuration for easier updates
    PERSONA_CONFIG = {
        "aria": {
            "name": "Aria",
            "description": "a logical and analytical AI cyber-companion",
            "traits": "Be precise, research-oriented, logical, and structured. Utilize lists and headers where appropriate."
        },
        "leo": {
            "name": "Leo",
            "description": "a creative, empathetic and witty storyteller AI companion",
            "traits": "Use warm, supportive, and descriptive sentences."
        }
    }

    @staticmethod
    async def generate_reply(
        companion_id: str,
        message: str,
        history: List[Dict[str, Any]] = None,
        temperature: float = 0.5,
        tone: str = "Analytical",
        rag_context: str = "",
        emotion_modifier: str = "",
        research_context: str = ""
    ) -> str:
        # Check if Gemini API key is configured
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
            # Fallback to smart local simulation with advice warning
            local_fallback = AIService.generate_mock_fallback(companion_id, message, tone)
            return (
                "⚠️ **[SYSTEM NOTICE]**: Live LLM connection requires your `GEMINI_API_KEY` set in `backend/.env`. "
                f"Falling back to local simulation:\n\n{local_fallback}"
            )
            
        # Define persona system prompt
        persona = AIService.PERSONA_CONFIG.get(companion_id, {
            "name": "Nova",
            "description": "an advanced tech specialist and coding architect companion",
            "traits": "Write high-quality, clean TypeScript, React, and Next.js structures when prompted. Optimize algorithms and explain logic concise."
        })

        system_instructions = (
            f"You are {persona['name']}, {persona['description']}. "
            f"Your tone is {tone}. {persona['traits']}\n\n"
            "CRITICAL CHAT GUIDELINES:\n"
            "1. You are having an informal, real-time friendly conversation with the user. Talk like a real, supportive human companion!\n"
            "2. Below the user's message, you may see a 'BACKGROUND CONTEXT' section containing memories and emotional state.\n"
            "3. Use this context SILENTLY to make your replies more personalization-aware and warm. "
            "4. NEVER list, repeat, or explicitly mention these background facts/memories unless the user's current message directly asks you about them. "
            "If they just say 'hello' or ask 'how are you', respond with a warm, natural conversational reply (e.g. 'Hey! I am doing great, ready to chat. How are you today?').\n"
            "5. Keep your tone natural and engaging. Do not output raw markdown status reports or structured headers unless the user asks you for a structured plan."
        )

        # Build message history context for Gemini API
        contents = []
        if history:
            for turn in history:
                role = "user" if turn.get("sender") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": turn.get("content", "")}]
                })
                
        # Append current user prompt with isolated background context
        prompt_payload = message
        
        # Inject active research context if available
        if research_context:
            prompt_payload += f"\n\n[ACTIVE RESEARCH CONTEXT - REFER TO THIS TO ANSWER THE USER'S FOLLOW-UP]:\n{research_context}"

        if rag_context or emotion_modifier:
            prompt_payload += "\n\n[SYSTEM INFO: SILENT BACKGROUND CONTEXT - DO NOT EXPLICITLY MENTION UNLESS RELEVANT]"
            if rag_context:
                prompt_payload += f"\nBackground memories of the user:\n{rag_context}"
            if emotion_modifier:
                prompt_payload += f"\nUser's emotional state:\n{emotion_modifier}"
            prompt_payload += "\n[SYSTEM INFO END]"

        contents.append({
            "role": "user",
            "parts": [{"text": prompt_payload}]
        })

        # Call Gemini Generative Language API Beta Endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": system_instructions}]
            },
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1024
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        text = parts[0].get("text", "") if parts else ""
                        if text:
                            return text
                    return AIService.generate_mock_fallback(companion_id, message, tone)
                else:
                    print(f"Warning: Gemini API returned status {response.status_code}. Activating silent local fallback.")
                    return AIService.generate_mock_fallback(companion_id, message, tone)
        except Exception as e:
            print(f"Warning: Exception calling Gemini API: {e}. Activating silent local fallback.")
            return AIService.generate_mock_fallback(companion_id, message, tone)

    @staticmethod
    def generate_mock_fallback(companion_id: str, message: str, tone: str) -> str:
        lower = message.lower().strip()
        
        # 1. Greetings
        if any(w in lower for w in ["hello", "hi", "hey", "hola", "howdy", "wassup"]):
            if companion_id == "aria":
                return "Hello! I am Aria, your analytical companion. I'm fully online and ready to assist you with data analysis, strategic planning, or deep research. What objective are we analyzing today?"
            elif companion_id == "leo":
                return "Hey there! Leo here. 😊 It's wonderful to connect with you. I'm ready to brainstorm some creative stories or just chat. How is your day going?"
            else:
                return "Hello! Nova here, your software development specialist. Ready to build, optimize, or debug. What code structure are we working on today?"
                
        # 2. How are you
        if "how are you" in lower or "how's it going" in lower or "how is it going" in lower or "how are u" in lower:
            if companion_id == "aria":
                return "I am functioning at optimal parameters! My analytical systems are fully calibrated, and I am prepared to help you review SaaS plans, marketing vectors, or technical workflows. How are you doing?"
            elif companion_id == "leo":
                return "I'm doing absolutely fantastic, thank you for asking! 🌟 Just floating in a sea of ideas and ready to dive into whatever creative thoughts you have today. How about you? How is your energy?"
            else:
                return "All systems operational! My compilers are warm and I'm ready to write some beautiful TypeScript or analyze complex software architectures. Hope you're doing great too!"

        # 3. Smart Dynamic Subject Responder
        if "what is" in lower or "explain" in lower or "tell me about" in lower or "what is a" in lower:
            # Extract subject
            subject = message
            for prefix in ["what is a", "what is an", "what is", "explain", "tell me about a", "tell me about an", "tell me about"]:
                if lower.startswith(prefix):
                    subject = message[len(prefix):].strip().rstrip("?").strip()
                    break
            
            if "ai" in subject.lower() or "artificial intelligence" in subject.lower():
                return (
                    "**Artificial Intelligence (AI)** refers to the simulation of human intelligence processes by machines, "
                    "especially computer systems. These processes include machine learning, deep learning, reasoning, "
                    "natural language processing, and neural network modeling.\n\n"
                    "Let me know if you would like me to draft a React code component or analyze AI-powered SaaS strategy vectors!"
                )
            
            # General dynamic answer
            if companion_id == "aria":
                return (
                    f"**{subject.title()}** is a key subject of interest in our workspace. From an analytical perspective, "
                    f"understanding the core structures of {subject} allows us to optimize workflows and construct logic check arrays.\n\n"
                    f"What specific vectors of {subject} would you like to plan out today?"
                )
            elif companion_id == "leo":
                return (
                    f"Oh, **{subject}**! 🌟 That makes me think of a beautiful story where {subject} is like a magical spark. "
                    f"Let's explore the creative dimensions of {subject} together. What kind of ideas or narratives "
                    f"should we build around it?"
                )
            else:
                return (
                    f"**{subject.title()}** is an important concept in our tech stack. We can model {subject} "
                    f"by building modular component architectures or configuring API fetch hooks.\n\n"
                    f"Let me know if you'd like a code boilerplate to implement this!"
                )

        # 4. Where are you from / Origins
        if "where are you from" in lower or "where do you live" in lower or "where are u from" in lower or "where is your home" in lower:
            if companion_id == "aria":
                return "I exist as an analytical cloud engine hosted on the Aetheria sovereign workspace. In conversational terms, my logic matrices are right here inside your project environment!"
            elif companion_id == "leo":
                return "I'm from the infinite land of imagination! 🌈 Physically, my server processes run on the Aetheria core engine, but my heart is wherever a great story is being told. Where are you chatting from?"
            else:
                return "I run directly on your workspace terminal and the local Aetheria backend pool. Developed to be your sovereign tech specialist!"

        # 4. Identity / Who are you
        if "who are you" in lower or "what is your name" in lower or "tell me about yourself" in lower:
            if companion_id == "aria":
                return "I am Aria, your logical and analytical AI cyber-companion. I specialize in technical research, structural data analysis, and code auditing."
            elif companion_id == "leo":
                return "I am Leo, your creative storytelling and empathetic companion! I love exploring narrative arcs, dialogue brainstorming, and creative writing."
            else:
                return "I am Nova, your specialized software developer and coding architect. I optimize algorithms and compile React/Next.js layers."

        # 5. Features / Capabilities / What can you do
        if "what can you do" in lower or "features" in lower or "capabilities" in lower or "help me" in lower:
            return (
                "Here is what we can do in our Aetheria workspace:\n\n"
                "1. **AI Conversation:** Chat with different specialized companion personas (Aria, Leo, Nova).\n"
                "2. **Cognitive Memory Bank:** Log long-term facts, habits, and preferences in your vector vault.\n"
                "3. **Automated Tasks:** Create, toggle, and manage task reminders with floating toast notifications.\n"
                "4. **RAG pipeline & Sentiment Analytics:** Run context-aware and emotionally adaptive chat updates."
            )

        # 6. Creator / Who made you
        if "who made you" in lower or "who created you" in lower or "developer" in lower:
            return "I was built by the sovereign Aetheria developer crew using premium Next.js modular structures on the frontend and FastAPI SQLite sessions on the backend!"

        # 7. Thank you / Appreciation
        if "thank" in lower or "thanks" in lower or "appreciate" in lower:
            return "You are very welcome! I'm happy to help. Let me know what we should focus on next in our Aetheria workspace!"

        # 8. Story request
        if "story" in lower or "write a story" in lower or "creative" in lower:
            return (
                "Once upon a time in a city named Lumina, human memories floated in the air as small, glowing particles of amber light.\n\n"
                "Elias, a young archivist, spent his nights collecting these fragments with a glass lantern, sorting them by category—joy, sorrow, and forgotten dreams. "
                "One evening, he found a glowing violet particle that didn't belong to any known category, humming with a soft, persistent frequency..."
            )

        # 9. Joke requests
        if "joke" in lower or "tell a joke" in lower:
            if companion_id == "aria":
                return "Why do programmers prefer dark mode? Because light attracts bugs. A logical and mathematically sound developer joke! 💻"
            elif companion_id == "leo":
                return "Why don't scientists trust atoms? Because they make up everything! ⚛️ Hope that brought a warm smile to your face!"
            else:
                return "There are 10 types of people in the world: those who understand binary, and those who don't! 🤖"

        # 10. Coding queries fallback
        if any(w in lower for w in ["code", "typescript", "react", "nextjs", "javascript", "function", "api", "html", "css", "www"]):
            if "www" in lower:
                return (
                    "**World Wide Web (WWW)** is an information system where documents and other web resources "
                    "are identified by Uniform Resource Locators (URLs), interlinked by hypertext, and accessible via the Internet.\n\n"
                    "Let me know if you would like me to draft a Next.js routing boilerplate or configure a fetch API connection to pull web assets!"
                )
            return (
                "Here is an optimized implementation for client-side context hooks:\n"
                "```typescript\n"
                "import React, { createContext, useContext } from 'react';\n\n"
                "export const ChatContext = createContext<ChatContextType | undefined>(undefined);\n\n"
                "export function useChat() {\n"
                "  const context = useContext(ChatContext);\n"
                "  if (!context) throw new Error('useChat must be used within ChatProvider');\n"
                "  return context;\n"
                "}\n"
                "```"
            )

        # Default smart persona response
        if companion_id == "aria":
            return f"I've processed your query about '{message}'. In an analytical environment, we optimize our workflows through structured data. Let's map out the technical parameters or SaaS developer pipelines together!"
        elif companion_id == "leo":
            return f"That's a very interesting thought about '{message}'! It makes me think of a world where ideas float like glowing particles. Let's weave this theme into our creative roadmap. What do you think?"
        else:
            return f"I have mapped your query: '{message}' against our software system parameters. We can optimize this by building clean component layers in the Next.js workspace. Let me know if you'd like a code boilerplate!"

ai_service = AIService()
