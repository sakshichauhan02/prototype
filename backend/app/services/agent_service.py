import httpx
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.task import Task
from app.services.web_research_service import web_research_service

class AgentService:
    @staticmethod
    async def detect_task_intent(message: str) -> Optional[Dict[str, Any]]:
        """
        Detects if the message triggers an agent workflow.
        Returns a dict indicating the agent, arguments, and task description.
        """
        msg_lower = message.lower()
        
        # 1. Reminder Agent
        if any(w in msg_lower for w in ["remind me to", "set a reminder", "create reminder", "remind me"]):
            # Extract content after "remind me to" or "remind me"
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
    async def execute_workflow(
        user_id: int,
        intent: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Executes the agent logic, commits tasks to SQL, triggers n8n if configured, and returns the response.
        """
        agent = intent["agent"]
        title = intent["title"]
        desc = intent["description"]
        
        # Save Task to SQL Database (Reminder & Scheduling)
        saved_task = None
        if agent in ["Reminder Agent", "Scheduling Agent"]:
            due = datetime.utcnow() + timedelta(days=1)  # Default due date tomorrow
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

        # Trigger n8n webhook if configured
        n8n_url = getattr(settings, "N8N_WEBHOOK_URL", None)
        if n8n_url:
            try:
                payload = {
                    "user_id": user_id,
                    "agent": agent,
                    "title": title,
                    "description": desc,
                    "timestamp": datetime.utcnow().isoformat()
                }
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(n8n_url, json=payload)
            except Exception as e:
                print(f"Warning: Failed to trigger n8n workflow webhook: {e}")

        # Construct customized output reports for the chat
        if agent == "Reminder Agent":
            return {
                "success": True,
                "agent": agent,
                "output": (
                    f"⏰ **[Reminder Agent Active]**: I have set a reminder for you!\n"
                    f"- **Task**: {title}\n"
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
                    f"- **Calendar Item Saved** (ID: {saved_task.id})\n"
                    f"I've added this meeting to your schedule dashboard list."
                )
            }
        elif agent == "Email Agent":
            # Call Gemini dynamically if available for professional draft
            draft_prompt = f"Write a professional email draft based on the request: {title}. Focus on clarity and a professional tone."
            draft_text = ""
            if settings.GEMINI_API_KEY:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                    payload = {"contents": [{"parts": [{"text": draft_prompt}]}]}
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        r = await client.post(url, json=payload)
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
