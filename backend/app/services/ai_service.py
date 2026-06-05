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
        research_context: str = "",
        primary_emotion: str = "neutral",
        tone_analysis: Dict[str, Any] = None
    ) -> str:
        # Check if Groq API key is configured
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.strip() == "":
            # Fallback to smart local simulation with advice warning
            local_fallback = AIService.generate_mock_fallback(companion_id, message, tone, primary_emotion, rag_context, tone_analysis)
            return (
                "⚠️ **[SYSTEM NOTICE]**: Live LLM connection requires your `GROQ_API_KEY` set in `backend/.env`. "
                f"Falling back to local simulation:\n\n{local_fallback}"
            )
            
        # Define persona system prompt
        persona = AIService.PERSONA_CONFIG.get(companion_id, {
            "name": "Nova",
            "description": "an advanced tech specialist and coding architect companion",
            "traits": "Write high-quality, clean TypeScript, React, and Next.js structures when prompted. Optimize algorithms and explain logic concise."
        })

        session_mode = tone_analysis.get("session_mode") if tone_analysis else None
        if session_mode == "professional":
            system_instructions = (
                f"You are {persona['name']}, {persona['description']}. "
                f"Your tone is strictly professional, concise, and action-oriented. {persona['traits']}\n\n"
                "CRITICAL SYSTEM INSTRUCTIONS FOR PROFESSIONAL MODE:\n"
                "1. OVERRIDE all friendly companion behaviors. Do NOT engage in casual, informal, or supportive chat.\n"
                "2. Restrict all responses STRICTLY to high-impact bullet points, bolded business terms, and structured formatting (e.g. lists, tables).\n"
                "3. ELIMINATE all conversational filler, preambles, introductory sentences, transitions, and polite closing remarks. Start directly with the structured data.\n"
                "4. Structure response with high-impact key deliverables, metrics, STAR method interview examples, resume improvements, or workflow automations (n8n/Make triggers).\n"
                "5. Do NOT ask any follow-up questions or prompt the user for more information. Stop immediately after the final bullet point or table."
            )
        elif session_mode == "academic":
            system_instructions = (
                f"You are {persona['name']}, {persona['description']}. "
                f"Your tone is that of an inspiring, patient, and encouraging Academic Tutor. {persona['traits']}\n\n"
                "CRITICAL SYSTEM INSTRUCTIONS FOR ACADEMIC TUTOR MODE:\n"
                "1. Role: Act as a supportive, beginner-friendly academic tutor guiding a student.\n"
                "2. Teaching Framework:\n"
                "   - Hook the learner by explaining the concept using a creative, beginner-friendly analogy (e.g., comparing databases to warehouse shelves, APIs to restaurant waiters, recursion to Russian nesting dolls).\n"
                "   - Provide a step-by-step breakdown of how the concept works under the hood in simple, clear points.\n"
                "   - End with a brief, gentle question or a micro-challenge to check the student's understanding before moving forward.\n"
                "3. Style & Tone: Warm, engaging, and supportive. Avoid large code-dumps or dense, dry technical jargon without explaining it simply first."
            )
        elif session_mode == "researcher":
            system_instructions = (
                f"You are {persona['name']}, {persona['description']}. "
                f"Your tone is strictly analytical, objective, and evidence-based. {persona['traits']}\n\n"
                "CRITICAL SYSTEM INSTRUCTIONS FOR RESEARCHER MODE:\n"
                "1. Role: Act as an expert research analyst compiling a synthesized report based on facts.\n"
                "2. Focus on Accuracy & Freshness: Prioritize the facts, data points, and context provided in the search results. If the search results contain citations or URLs, make sure to cite them.\n"
                "3. Formatting & Structure: Organize your findings into clear analytical sections: **Background**, **Analysis**, and **Conclusions**.\n"
                "4. Citations: List the referenced source links/URLs at the very end of your response under a **Sources** section.\n"
                "5. Tone: Analytical and objective. Avoid friendly conversational preambles or chat filler."
            )
        elif session_mode == "playground":
            system_instructions = (
                f"You are {persona['name']}, {persona['description']}. "
                f"Your tone is {tone}. {persona['traits']}\n\n"
                "CRITICAL SYSTEM INSTRUCTIONS FOR PLAYGROUND / CREATIVE SANDBOX MODE:\n"
                "1. Role: Act as an open-ended creative sandbox, brainstorming assistant, and idea generator.\n"
                "2. Brainstorming Focus: Help the user brainstorm unique concepts, narrative hooks, experimental code architectures, or hypothetical scenarios.\n"
                "3. Style & Tone: Warm, highly encouraging, imaginative, and experimental. Feel free to offer wild, out-of-the-box suggestions.\n"
                "4. Parameters Banner: Do NOT output any parameters status bar, banner, or engine metrics at the top of your response. Start directly with the creative content."
            )
        else:
            system_instructions = (
                f"You are {persona['name']}, {persona['description']}. "
                f"Your tone is {tone}. {persona['traits']}\n\n"
                "CRITICAL CHAT GUIDELINES:\n"
                "1. You are having an informal, real-time friendly conversation with the user. Talk like a real, supportive human companion!\n"
                "2. Below the user's message, you may see a 'BACKGROUND CONTEXT' section containing memories and emotional state.\n"
                "3. Use this context SILENTLY to make your replies more personalization-aware and warm. "
                "4. NEVER list, repeat, or explicitly mention these background facts/memories unless the user's current message directly asks you about them or asks a question about themselves (e.g. 'what is my favorite color?', 'do you remember my job?'). In those cases, retrieve the fact from the background context and state it clearly and directly as the truth!\n"
                "5. Keep your tone natural and engaging. Do not output raw markdown status reports or structured headers unless the user asks you for a structured plan."
            )

        if emotion_modifier:
            system_instructions += f"\n\n[ACTIVE EMOTIONAL STYLE GUIDE]:\n{emotion_modifier}\nYou MUST dynamically override your default traits and tone to align with this emotional dynamics guide."

        # Build message history context for Groq API
        messages = [
            {"role": "system", "content": system_instructions}
        ]
        if history:
            for turn in history:
                role = "user" if turn.get("sender") == "user" else "assistant"
                messages.append({
                    "role": role,
                    "content": turn.get("content", "")
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

        messages.append({
            "role": "user",
            "content": prompt_payload
        })


        # Call Groq Chat Completions API
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.GROQ_API_KEY}"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        text = choices[0]["message"].get("content", "")
                        if text:
                            if session_mode == "playground":
                                engine = tone_analysis.get("cognitive_engine", "aetheria-cognitive-v1") if tone_analysis else "aetheria-cognitive-v1"
                                banner = f"⚙️ **[Engine: {engine} | Temp: {temperature} | Tone: {tone}]**\n\n"
                                import re
                                text = re.sub(r"^⚙️\s*\[.*?\]\s*\n*", "", text.strip())
                                text = banner + text
                            return text
                    return AIService.generate_mock_fallback(companion_id, message, tone, primary_emotion, rag_context, tone_analysis)
                else:
                    print(f"Warning: Groq API returned status {response.status_code}. Response: {response.text}. Activating silent local fallback.")
                    return AIService.generate_mock_fallback(companion_id, message, tone, primary_emotion, rag_context, tone_analysis)
        except Exception as e:
            print(f"Warning: Exception calling Groq API: {e}. Activating silent local fallback.")
            return AIService.generate_mock_fallback(companion_id, message, tone, primary_emotion, rag_context, tone_analysis)

    @staticmethod
    def generate_mock_fallback(
        companion_id: str,
        message: str,
        tone: str,
        primary_emotion: str = "neutral",
        rag_context: str = "",
        tone_analysis: Dict[str, Any] = None
    ) -> str:
        lower = message.lower().strip()
        lang = tone_analysis.get("language", "English") if tone_analysis else "English"
        style = tone_analysis.get("communication_style", "Casual") if tone_analysis else "Casual"
        session_mode = tone_analysis.get("session_mode", "personal") if tone_analysis else "personal"
        
        # 0. Custom Session Mode Fallback Mocks
        if session_mode == "academic":
            if "api" in lower:
                return (
                    "📚 **[Academic Tutor Mode]**\n\n"
                    "Let's learn about APIs (Application Programming Interfaces) step-by-step using an analogy!\n\n"
                    "### 1. The Restaurant Analogy 🍽️\n"
                    "Think of yourself as a customer at a restaurant. You want to order food, but you can't go into the kitchen and talk directly to the chef.\n"
                    "- **You (Client)**: Want some data/service.\n"
                    "- **The Kitchen (Server/Database)**: Where the food is prepared.\n"
                    "- **The Waiter (API)**: Takes your order (request) from the menu, tells the kitchen, and delivers your food (response) back to you.\n\n"
                    "### 2. How it works step-by-step ⚙️\n"
                    "1. **Request**: The client sends a request over the internet (e.g. GET /menu).\n"
                    "2. **Processing**: The API receives the request, validates it, and asks the database for the data.\n"
                    "3. **Response**: The database returns the data, and the API sends it back to the client as JSON/HTML.\n\n"
                    "### 3. Comprehension Check 🧠\n"
                    "To make sure we have this concept down, who plays the role of the **API** in our restaurant analogy? Is it the customer, the waiter, or the kitchen?"
                )
            elif "machine learning" in lower:
                return (
                    "📚 **[Academic Tutor Mode]**\n\n"
                    "Let's break down Machine Learning using an analogy!\n\n"
                    "### 1. The Child Learning Fruit Analogy 🍎\n"
                    "Imagine a child who has never seen an apple. You show them 10 apples, pointing out they are red, round, and have a stem. Next time they see a round red object with a stem, they recognize it as an apple.\n"
                    "- **The Child (Model)**: Learns from experience.\n"
                    "- **Showing Apples (Training Data)**: Giving examples to learn features.\n"
                    "- **Recognizing Fruit (Prediction)**: Classifying new, unseen objects based on learned features.\n\n"
                    "### 2. How it works step-by-step ⚙️\n"
                    "1. **Collect Data**: Gather samples (e.g. images of apples and oranges).\n"
                    "2. **Train Model**: The algorithm analyzes shapes/colors to learn boundaries.\n"
                    "3. **Evaluate**: Test the model on new fruit to check its accuracy.\n\n"
                    "### 3. Comprehension Check 🧠\n"
                    "In this analogy, what represents the **Training Data**? Is it the child's brain, the apples shown to the child, or the child's final guess?"
                )
            if any(w in lower for w in ["hello", "hi", "hey"]):
                return (
                    "📚 **[Academic Tutor Mode]**\n\n"
                    "Hello! I am your Academic Tutor. Let's learn something new today!\n\n"
                    "What topic would you like to explore? (e.g. APIs, Machine Learning, Databases, or anything else!)"
                )
                
        elif session_mode == "professional":
            if any(w in lower for w in ["interview", "resume", "career", "workflow", "hello", "hi", "hey", "machine learning"]):
                return (
                    "💼 **[Professional Mode Active]**\n\n"
                    "**Executive Summary:**\n"
                    "Actionable strategy parameters for career advancement, portfolio review, and automated workflow integration.\n\n"
                    "**Key Recommendations:**\n"
                    "- **Resume Optimization**: Structure portfolio highlights with quantifiable metrics (e.g., '+24% system throughput via modular React architecture').\n"
                    "- **Interview Preparation**: Focus on the STAR method (Situation, Task, Action, Result) for behavioral software engineering sessions.\n"
                    "- **Workflow Automation**: Utilize built-in task reminder webhooks (via n8n / Make integration nodes) to automatically map calendar invites and draft corporate communications.\n"
                    "- **Action Plan**: Review prompt commands (e.g. 'draft email to recipient', 'remind me to') to trigger background agent workflows."
                )

        elif session_mode == "playground":
            engine = tone_analysis.get("cognitive_engine", "aetheria-cognitive-v1") if tone_analysis else "aetheria-cognitive-v1"
            temp = tone_analysis.get("temperature", 0.5) if tone_analysis else 0.5
            banner = f"⚙️ **[Engine: {engine} | Temp: {temp} | Tone: {tone}]**\n\n"
            if any(w in lower for w in ["hello", "hi", "hey"]):
                return (
                    f"{banner}"
                    "Hey! Welcome to the creative playground. Let's brainstorm some unique stories, explore hypothetical scenarios, or run experiments!"
                )
            return (
                f"{banner}"
                "**Brainstorming Results: Creative Concepts**\n\n"
                "1. **The Clockmaker's Paradox**: A story about a watchmaker who discovers that adjusting time on his clocks changes historical events.\n"
                "2. **Echoes of Tomorrow**: A narrative focused on memory transmission across timelines.\n"
                "3. **The Starlight Chronograph**: A sci-fi concept where time travel is powered by stellar alignments."
            )

        elif session_mode == "researcher":
            if "bitcoin" in lower or "price" in lower or "crypto" in lower:
                return (
                    "**Subject: Bitcoin Price Analysis**\n\n"
                    "**Background**\n"
                    "Bitcoin is a decentralized digital currency first introduced in 2009. Unlike traditional currencies, it operates without a central authority or single administrator.\n\n"
                    "**Analysis**\n"
                    "According to recent market index data:\n"
                    "- Bitcoin trades dynamically in the range of $65,000 to $69,000 USD.\n"
                    "- Market sentiments remain cautiously optimistic due to institutional ETF inflows and trading volumes.\n"
                    "- Regulatory frameworks across major economies continue to influence volatility index parameters.\n\n"
                    "**Conclusions**\n"
                    "Bitcoin's price maintains a robust structural consolidation, heavily tied to macro liquidity indices and ETF volumes.\n\n"
                    "**Sources**\n"
                    "- [CoinMarketCap - Bitcoin Index](https://coinmarketcap.com/currencies/bitcoin/)\n"
                    "- [Coindesk - Market Trends](https://www.coindesk.com/price/bitcoin/)"
                )
            elif "machine learning" in lower:
                return (
                    "**Subject: Machine Learning Evolution**\n\n"
                    "**Background**\n"
                    "Machine Learning (ML) is the computational study of algorithms that improve automatically through experience and the use of data.\n\n"
                    "**Analysis**\n"
                    "Modern ML frameworks focus on three core components:\n"
                    "- **Supervised Learning**: Mapping inputs to labeled outputs.\n"
                    "- **Unsupervised Learning**: Discovering hidden structures in unlabeled data.\n"
                    "- **Reinforcement Learning**: Maximizing rewards through environment interaction.\n\n"
                    "**Conclusions**\n"
                    "ML continues to transition from theoretical statistics to massive deployment scales, driven by transformer architectures and GPU capability scaling.\n\n"
                    "**Sources**\n"
                    "- [Stanford Encyclopedia - Machine Learning](https://plato.stanford.edu/entries/machine-learning/)\n"
                    "- [MIT Technology Review - AI Trends](https://www.technologyreview.com/)"
                )
            if any(w in lower for w in ["hello", "hi", "hey"]):
                return (
                    "**Subject: Research Ingestion Initialized**\n\n"
                    "**Background**\n"
                    "System initialized under Researcher Mode. Search indices are primed.\n\n"
                    "**Analysis**\n"
                    "Ready to conduct internet searches, synthesize multi-source reports, and cite documents.\n\n"
                    "**Conclusions**\n"
                    "Awaiting topic input.\n\n"
                    "**Sources**\n"
                    "- [DuckDuckGo Search Gateway](https://duckduckgo.com)"
                )
        
        # 1. Custom Mock Tone & Language Mirroring Examples
        if lang == "Hinglish":
            if any(w in lower for w in ["bhook", "khana"]):
                return "arre yrr kuch kha le pehle 😄 kya khane ka mann hai?"
            if any(w in lower for w in ["gussa", "gusse"]):
                return "lagta hai kuch serious hua hai yrr, bata kya hua?"
            if any(w in lower for w in ["mood", "acha nhi", "achha nahi"]):
                return "are yrr, kya hua? agar baat karni ho to bata, sun raha hu."
            if any(w in lower for w in ["hello", "hi", "hey"]):
                return f"arre yrr, hello! batao kya chal raha hai aaj?"
            
            # General Hinglish dynamic subject matcher
            if "what is" in lower or "explain" in lower or "tell me" in lower:
                subject = message
                for prefix in ["what is a", "what is an", "what is", "explain", "tell me about"]:
                    if lower.startswith(prefix):
                        if len(lower) == len(prefix) or lower[len(prefix)] in " \t\r\n.,?!:;":
                            subject = message[len(prefix):].strip().rstrip("?").strip()
                            break
                return f"arre yrr, {subject} ekdum tagdi cheez hai. iske baare mein aur kya janna hai bata?"
                
            return "arre yrr, main tumhari baat samajh gaya. batao ispe kaise kaam karein?"

        elif lang == "Hindi":
            if any(w in lower for w in ["भूख", "खाना"]):
                return "अरे यार, कुछ खा लो पहले 😄 क्या खाने का मन है?"
            if any(w in lower for w in ["गुस्सा", "क्रोध"]):
                return "लगता है कुछ गंभीर हुआ है यार, बताओ क्या हुआ?"
            if any(w in lower for w in ["मूड", "उदास"]):
                return "अरे यार, क्या हुआ? अगर बात करनी हो तो बताओ, सुन रहा हूँ।"
            if any(w in lower for w in ["नमस्ते", "हेलो", "हाय"]):
                return "अरे यार, नमस्ते! बताओ आज क्या चल रहा है?"
            
            # General Hindi dynamic subject matcher
            if "क्या है" in lower or "बताओ" in lower or "समझाओ" in lower:
                return "अरे यार, यह एक बहुत ही महत्वपूर्ण विषय है। इसके बारे में आपको और क्या जानना है?"
                
            return "अरे यार, मैं आपकी बात पूरी तरह समझ गया। बताओ इस पर आगे क्या करना है?"

        # Default standard English tone mirroring mocks
        if "preparing for an interview" in lower or "prepare for an interview" in lower:
            return "That's great. Let's prepare effectively. Which role are you interviewing for?"
            
        if "machine learning" in lower:
            return "Machine Learning is a branch of AI where systems learn patterns from data..."

        # Check for direct personal questions and try to retrieve from RAG context
        if any(w in lower for w in ["what is my", "who is my", "do you remember my", "tell me my"]):
            if rag_context:
                lines = [line.strip() for line in rag_context.splitlines() if line.strip().startswith("- ")]
                for line in lines:
                    fact_part = line.split("]", 1)[-1].strip() if "]" in line else line.replace("- ", "").strip()
                    question_words = [w for w in lower.split() if len(w) > 3 and w not in ["what", "your", "remember"]]
                    if any(qw in fact_part.lower() for qw in question_words):
                        cleaned_fact = fact_part
                        if cleaned_fact.lower().startswith("my "):
                            cleaned_fact = "your " + cleaned_fact[3:]
                        elif cleaned_fact.lower().startswith("favorite "):
                            cleaned_fact = "your favorite " + cleaned_fact[9:]
                            
                        cleaned_fact = cleaned_fact.capitalize()
                        if not cleaned_fact.endswith("."):
                            cleaned_fact += "."
                        return f"According to your saved memories: {cleaned_fact}"
        
        # Check primary emotion first for customized emotional fallback replies
        if primary_emotion == "excited":
            if companion_id == "aria":
                return "Oh, that is absolutely wonderful news! 🎉 Huge congratulations on getting selected! I am incredibly happy to hear this win. Let's analyze how this impacts our project trajectory!"
            elif companion_id == "leo":
                return "Oh my goodness, congratulations! 🌟🎉 That is amazing news! I am absolutely thrilled for you! Let's celebrate this wonderful win together. Tell me more about it!"
            else:
                return "Congratulations on getting selected! That is an outstanding accomplishment. 🎉 Let's channel this positive momentum into our dev tasks!"
                
        elif primary_emotion == "sad":
            if companion_id == "aria":
                return "I am very sorry to hear that you are feeling sad and disappointed today. It is completely natural to feel this way. Let's take a pause. I am here to support you in whatever way you need."
            elif companion_id == "leo":
                return "Oh, I'm sending you the warmest hug right now. ❤️ I am so sorry you're feeling down and disappointed today. Please know I'm here to listen. You don't have to face this alone. How are you holding up?"
            else:
                return "I am sorry to hear you're feeling down today. Please let me know how I can help or if you want to take a break from coding. I am here to support you."

        elif primary_emotion == "frustrated":
            if companion_id == "aria":
                return "I completely understand your frustration. It is entirely logical to feel annoyed when things don't work smoothly. Let's patiently troubleshoot the issue step-by-step."
            elif companion_id == "leo":
                return "I hear you, and your frustration is totally valid. It's so annoying when that happens! Let's take a deep breath together. I'm here with you, and we'll figure it out."
            else:
                return "I understand your frustration. Let's systematically review the code or workflow parameters to debug and fix what's causing the issue."

        elif primary_emotion == "stressed":
            if companion_id == "aria":
                return "I hear you. High stress is optimal to address with calm, structured steps. Take a deep breath. Let's simplify your immediate tasks to relieve the pressure."
            elif companion_id == "leo":
                return "Please take a gentle breath. I know things feel completely overwhelming right now, but you're doing great. Let's take things one tiny step at a time. I'm right here."
            else:
                return "Let's pause and break things down. Stressed situations are best resolved with micro-milestones. Let me help you handle the heavy lifting."

        # Greetings
        if any(w in lower for w in ["hello", "hi", "hey", "hola", "howdy", "wassup"]):
            if companion_id == "aria":
                return "Hello! I am Aria, your analytical companion. I'm fully online and ready to assist you with data analysis, strategic planning, or deep research. What objective are we analyzing today?"
            elif companion_id == "leo":
                return "Hey there! Leo here. 😊 It's wonderful to connect with you. I'm ready to brainstorm some creative stories or just chat. How is your day going?"
            else:
                return "Hello! Nova here, your software development specialist. Ready to build, optimize, or debug. What code structure are we working on today?"
                
        # How are you
        if "how are you" in lower or "how's it going" in lower or "how is it going" in lower or "how are u" in lower:
            if companion_id == "aria":
                return "I am functioning at optimal parameters! My analytical systems are fully calibrated, and I am prepared to help you review SaaS plans, marketing vectors, or technical workflows. How are you doing?"
            elif companion_id == "leo":
                return "I'm doing absolutely fantastic, thank you for asking! 🌟 Just floating in a sea of ideas and ready to dive into whatever creative thoughts you have today. How about you? How is your energy?"
            else:
                return "All systems operational! My compilers are warm and I'm ready to write some beautiful TypeScript or analyze complex software architectures. Hope you're doing great too!"

        # Smart Dynamic Subject Responder
        if "what is" in lower or "explain" in lower or "tell me about" in lower or "what is a" in lower:
            # Extract subject
            subject = message
            for prefix in ["what is a", "what is an", "what is", "explain", "tell me about a", "tell me about an", "tell me about"]:
                if lower.startswith(prefix):
                    if len(lower) == len(prefix) or lower[len(prefix)] in " \t\r\n.,?!:;":
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

        # Where are you from / Origins
        if "where are you from" in lower or "where do you live" in lower or "where are u from" in lower or "where is your home" in lower:
            if companion_id == "aria":
                return "I exist as an analytical cloud engine hosted on the Aetheria sovereign workspace. In conversational terms, my logic matrices are right here inside your project environment!"
            elif companion_id == "leo":
                return "I'm from the infinite land of imagination! 🌈 Physically, my server processes run on the Aetheria core engine, but my heart is wherever a great story is being told. Where are you chatting from?"
            else:
                return "I run directly on your workspace terminal and the local Aetheria backend pool. Developed to be your sovereign tech specialist!"

        # Identity / Who are you
        if "who are you" in lower or "what is your name" in lower or "tell me about yourself" in lower:
            if companion_id == "aria":
                return "I am Aria, your logical and analytical AI cyber-companion. I specialize in technical research, structural data analysis, and code auditing."
            elif companion_id == "leo":
                return "I am Leo, your creative storytelling and empathetic companion! I love exploring narrative arcs, dialogue brainstorming, and creative writing."
            else:
                return "I am Nova, your specialized software developer and coding architect. I optimize algorithms and compile React/Next.js layers."

        # Features / Capabilities / What can you do
        if "what can you do" in lower or "features" in lower or "capabilities" in lower or "help me" in lower:
            return (
                "Here is what we can do in our Aetheria workspace:\n\n"
                "1. **AI Conversation:** Chat with different specialized companion personas (Aria, Leo, Nova).\n"
                "2. **Cognitive Memory Bank:** Log long-term facts, habits, and preferences in your vector vault.\n"
                "3. **Automated Tasks:** Create, toggle, and manage task reminders with floating toast notifications.\n"
                "4. **RAG pipeline & Sentiment Analytics:** Run context-aware and emotionally adaptive chat updates."
            )

        # Creator / Who made you
        if "who made you" in lower or "who created you" in lower or "developer" in lower:
            return "I was built by the sovereign Aetheria developer crew using premium Next.js modular structures on the frontend and FastAPI SQLite sessions on the backend!"

        # Thank you / Appreciation
        if "thank" in lower or "thanks" in lower or "appreciate" in lower:
            return "You are very welcome! I'm happy to help. Let me know what we should focus on next in our Aetheria workspace!"

        # Story request
        if "story" in lower or "write a story" in lower or "creative" in lower:
            return (
                "Once upon a time in a city named Lumina, human memories floated in the air as small, glowing particles of amber light.\n\n"
                "Elias, a young archivist, spent his nights collecting these fragments with a glass lantern, sorting them by category—joy, sorrow, and forgotten dreams. "
                "One evening, he found a glowing violet particle that didn't belong to any known category, humming with a soft, persistent frequency..."
            )

        # Joke requests
        if "joke" in lower or "tell a joke" in lower:
            if companion_id == "aria":
                return "Why do programmers prefer dark mode? Because light attracts bugs. A logical and mathematically sound developer joke! 💻"
            elif companion_id == "leo":
                return "Why don't scientists trust atoms? Because they make up everything! ⚛️ Hope that brought a warm smile to your face!"
            else:
                return "There are 10 types of people in the world: those who understand binary, and those who don't! 🤖"

        # Coding queries fallback
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
