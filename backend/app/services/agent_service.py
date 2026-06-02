import httpx
import re
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.task import Task
from app.services.web_research_service import web_research_service

class AgentService:
    @staticmethod
    async def _regex_fallback_intent(message: str) -> Optional[Dict[str, Any]]:
        msg_lower = message.lower()
        
        # 1. Reminder Agent
        if any(w in msg_lower for w in ["remind me to", "set a reminder", "create reminder", "remind me"]):
            match = re.search(r"(?:remind me to|remind me)\s+(.*)", msg_lower)
            title = match.group(1).strip() if match else "Task Reminder"
            return {
                "agent": "Reminder Agent",
                "title": title.capitalize(),
                "description": f"Auto-generated reminder: {title}"
            }
            
        # 2. Scheduling Agent
        elif any(w in msg_lower for w in ["schedule a meeting", "book a meeting", "schedule meeting", "book appointment"]):
            match = re.search(r"(?:schedule a meeting|book a meeting|schedule meeting|book appointment)(?:\s+with\s+)?(.*)", msg_lower)
            who_what = match.group(1).strip() if match else "Meeting"
            return {
                "agent": "Scheduling Agent",
                "title": f"Meeting: {who_what.title()}",
                "description": f"Scheduled event via AI Companion: {who_what}"
            }

        # 3. Email Drafting Agent
        elif any(w in msg_lower for w in ["draft an email", "write an email", "compose an email", "email draft"]):
            match = re.search(r"(?:draft an email|write an email|compose an email|email draft)(?:\s+to\s+)?(.*)", msg_lower)
            recipient = match.group(1).strip() if match else "recipient"
            return {
                "agent": "Email Agent",
                "title": f"Draft Email to {recipient.title()}",
                "description": f"Drafting email communication for {recipient}"
            }

        # 4. Research Agent
        elif any(w in msg_lower for w in ["research about", "deep research on", "find details on", "research project"]):
            match = re.search(r"(?:research about|deep research on|find details on|research project)\s+(.*)", msg_lower)
            topic = match.group(1).strip() if match else "topic"
            return {
                "agent": "Research Agent",
                "title": f"Deep Research: {topic.title()}",
                "description": f"Internet research request on: {topic}"
            }
            
        return None

    @staticmethod
    async def detect_task_intent(message: str) -> Optional[Dict[str, Any]]:
        """
        Intelligently detects if the message triggers an agent workflow,
        performs web search, or is a standard chat.
        Uses Gemini LLM for classification, falling back to regex.
        """
        # Check if key is configured
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
            return await AgentService._regex_fallback_intent(message)
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        system_instruction = (
            "You are the central intent classification router for the Aetheria AI companion workspace.\n"
            "Your job is to analyze the user's message and determine if it belongs to one of three categories:\n"
            "1. \"chat\": Standard conversation, questions about general topics, coding/engineering help, explanations, greetings, or friendly chat. These do NOT require any external tool or automated actions.\n"
            "2. \"search\": Real-time queries needing search engine access, such as asking about weather, stock prices, news, recent events, or searching the web.\n"
            "3. \"command\": Actionable commands to automate tasks, set reminders, schedule meetings, or draft emails.\n\n"
            "For \"command\", classify it into one of these agents:\n"
            "- \"Reminder Agent\": Create tasks/reminders (e.g. \"remind me to write code\", \"create a task to buy bread\").\n"
            "- \"Scheduling Agent\": Schedule meetings or appointments (e.g. \"schedule a call with Bob tomorrow at noon\").\n"
            "- \"Email Agent\": Draft, prepare, or send emails (e.g. \"draft an email to the team explaining the delays\").\n\n"
            "If the intent is \"chat\", return ONLY a JSON block with {\"intent\": \"chat\"}.\n"
            "If the intent is \"search\", classify it as \"Research Agent\" and return a JSON block.\n"
            "If the intent is \"command\", classify it under the correct agent.\n\n"
            "Your output must be ONLY a valid JSON object matching the following structure:\n"
            "{\n"
            "  \"intent\": \"chat\" | \"search\" | \"command\",\n"
            "  \"agent\": \"Reminder Agent\" | \"Scheduling Agent\" | \"Email Agent\" | \"Research Agent\" | \"None\",\n"
            "  \"title\": \"A concise title summarizing the task, email subject, or search query (e.g. 'Meeting with Bob', 'Buy bread reminder', 'Deep Research: AI trends')\",\n"
            "  \"description\": \"A detailed description of the command or query\",\n"
            "  \"recipient\": \"Name/email of recipient if Email Agent, otherwise null\",\n"
            "  \"due_time\": \"ISO 8601 timestamp of due date/time if mentioned (e.g. '2026-06-03T12:00:00'), otherwise null\"\n"
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
            async with httpx.AsyncClient(timeout=10.0) as client:
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
                            intent_type = parsed.get("intent", "chat")
                            
                            if intent_type == "chat":
                                return None
                                
                            agent = parsed.get("agent")
                            if agent and agent != "None":
                                return {
                                    "agent": agent,
                                    "title": parsed.get("title", "AI Action"),
                                    "description": parsed.get("description", ""),
                                    "recipient": parsed.get("recipient"),
                                    "due_time": parsed.get("due_time")
                                }
                else:
                    print(f"Warning: Gemini intent routing API returned status {response.status_code}. Using regex fallback.")
        except Exception as e:
            print(f"Warning: Exception in LLM intent routing: {e}. Using regex fallback.")
            
        return await AgentService._regex_fallback_intent(message)

    @staticmethod
    async def execute_workflow(
        user_id: int,
        intent: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Executes the agent logic, commits tasks to SQL, triggers n8n/Make if configured, and returns the response.
        """
        agent = intent["agent"]
        title = intent["title"]
        desc = intent["description"]
        
        # Save Task to SQL Database (Reminder & Scheduling)
        saved_task = None
        if agent in ["Reminder Agent", "Scheduling Agent"]:
            due = datetime.utcnow() + timedelta(days=1)  # Default due date tomorrow
            due_time_str = intent.get("due_time")
            if due_time_str:
                try:
                    # Strip timezone character Z if naive timezone conversion is needed
                    clean_str = due_time_str.replace("Z", "")
                    if "T" in clean_str:
                        due = datetime.fromisoformat(clean_str)
                except Exception:
                    pass
            saved_task = Task(
                user_id=user_id,
                title=title,
                description=desc,
                status="pending",
                priority=2,
                source=f"AI Agent ({agent})",
                due_at=due
            )
            db.add(saved_task)
            await db.commit()
            await db.refresh(saved_task)

        # Trigger n8n/Make webhooks if configured
        n8n_url = getattr(settings, "N8N_WEBHOOK_URL", None)
        make_url = getattr(settings, "MAKE_WEBHOOK_URL", None)
        
        payload = {
            "user_id": user_id,
            "agent": agent,
            "title": title,
            "description": desc,
            "recipient": intent.get("recipient"),
            "due_time": intent.get("due_time"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Trigger n8n webhook
        if n8n_url and n8n_url.strip():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(n8n_url, json=payload)
            except Exception as e:
                print(f"Warning: Failed to trigger n8n workflow webhook: {e}")
                
        # Trigger Make webhook
        if make_url and make_url.strip():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(make_url, json=payload)
            except Exception as e:
                print(f"Warning: Failed to trigger Make workflow webhook: {e}")

        # Construct customized output reports for the chat
        if agent == "Reminder Agent":
            return {
                "success": True,
                "agent": agent,
                "output": (
                    f"⏰ **[Reminder Agent Active]**: I have set a reminder for you!\n"
                    f"- **Task**: {title}\n"
                    f"- **Description**: {desc}\n"
                    f"- **Saved to Workspace Database** under Task ID: {saved_task.id}\n"
                    f"I will alert you when it's due."
                )
            }
        elif agent == "Scheduling Agent":
            return {
                "success": True,
                "agent": agent,
                "output": (
                    f"📅 **[Scheduling Agent Active]**: I've reserved a calendar entry!\n"
                    f"- **Event**: {title}\n"
                    f"- **Details**: {desc}\n"
                    f"- **Calendar Item Saved** (ID: {saved_task.id})\n"
                    f"I've added this meeting to your schedule dashboard list."
                )
            }
        elif agent == "Email Agent":
            # Call Gemini dynamically if available for professional draft
            draft_prompt = f"Write a professional email draft based on the request: {title}. Focus on clarity and a professional tone. Description context: {desc}."
            draft_text = ""
            if settings.GEMINI_API_KEY:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                    payload_api = {"contents": [{"parts": [{"text": draft_prompt}]}]}
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        r = await client.post(url, json=payload_api)
                        if r.status_code == 200:
                            draft_text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                except Exception:
                    pass
            if not draft_text:
                draft_text = (
                    f"Subject: {title}\n\n"
                    f"Dear Recipient,\n\n"
                    f"I am writing to discuss the details regarding: {desc}.\n"
                    f"Please review and let me know your thoughts.\n\n"
                    f"Best regards,\n[Your Name]"
                )
            return {
                "success": True,
                "agent": agent,
                "output": (
                    f"✉️ **[Email Drafting Agent Active]**: Here is the email draft I created for you:\n\n"
                    f"```text\n{draft_text}\n```"
                )
            }
        elif agent == "Research Agent":
            # Conduct real-time web research
            topic = title.replace("Deep Research:", "").strip()
            summary = await web_research_service.search_and_summarize(topic)
            if not summary:
                summary = "I searched the web but was unable to find current results. Please verify your internet connection."
            return {
                "success": True,
                "agent": agent,
                "output": (
                    f"🔍 **[Research Agent Active]**: I have conducted internet research on **{topic}**:\n\n"
                    f"{summary}"
                )
            }
            
        return {"success": False, "agent": agent, "output": "Agent workflow executed."}

agent_service = AgentService()
