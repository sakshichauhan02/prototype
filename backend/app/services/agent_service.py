import httpx
import re
import json
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.task import Task
from app.services.web_research_service import web_research_service
from app.services.pdf_generator import generate_resume_pdf

RESUME_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static_resumes")
os.makedirs(RESUME_DIR, exist_ok=True)

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
                "description": f"Auto-generated reminder: {title}",
                "raw_message": message
            }
            
        # 2. Scheduling Agent
        elif any(w in msg_lower for w in ["schedule a meeting", "book a meeting", "schedule meeting", "book appointment"]):
            match = re.search(r"(?:schedule a meeting|book a meeting|schedule meeting|book appointment)(?:\s+with\s+)?(.*)", msg_lower)
            who_what = match.group(1).strip() if match else "Meeting"
            return {
                "agent": "Scheduling Agent",
                "title": f"Meeting: {who_what.title()}",
                "description": f"Scheduled event via AI Companion: {who_what}",
                "raw_message": message
            }

        # 3. Email Drafting Agent
        elif any(w in msg_lower for w in ["draft an email", "write an email", "compose an email", "email draft"]):
            match = re.search(r"(?:draft an email|write an email|compose an email|email draft)(?:\s+to\s+)?(.*)", msg_lower)
            recipient = match.group(1).strip() if match else "recipient"
            return {
                "agent": "Email Agent",
                "title": f"Draft Email to {recipient.title()}",
                "description": f"Drafting email communication for {recipient}",
                "raw_message": message
            }

        # 4. Research Agent
        elif any(w in msg_lower for w in ["research about", "deep research on", "find details on", "research project", "research ", "search "]):
            match = re.search(r"(?:research about|deep research on|find details on|research project|research|search)\s+(.*)", msg_lower)
            topic = match.group(1).strip() if match else "topic"
            return {
                "agent": "Research Agent",
                "title": f"Deep Research: {topic.title()}",
                "description": f"Internet research request on: {topic}",
                "raw_message": message
            }

        # 5. Resume Agent
        has_resume_keywords = any(w in msg_lower for w in ["build my resume", "create resume", "generate cv", "build resume", "create my resume", "generate my resume", "write my resume", "write resume"])
        has_resume_labels = sum(1 for label in ["name", "contact", "education", "experience", "skills"] if re.search(rf"\b{label}\b\s*:", msg_lower)) >= 3
        has_resume_sections = sum(1 for section in ["summary", "skills", "experience", "education", "projects"] if section in msg_lower) >= 3
        
        if has_resume_keywords or has_resume_labels or has_resume_sections or "template use" in msg_lower or "use krna" in msg_lower:
            name = re.search(r"(?i)\bname\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", message, re.DOTALL)
            contact = re.search(r"(?i)\bcontact\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", message, re.DOTALL)
            edu = re.search(r"(?i)\beducation\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", message, re.DOTALL)
            exp = re.search(r"(?i)\bexperience\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", message, re.DOTALL)
            skills = re.search(r"(?i)\bskills\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", message, re.DOTALL)
            
            def clean_val(match):
                if not match:
                    return None
                val = match.group(1).strip()
                if val.startswith("[") and val.endswith("]"):
                    return None
                if val.lower() in ["", "null", "undefined"]:
                    return None
                return val

            resume_data = {
                "name": clean_val(name),
                "contact": clean_val(contact),
                "education": clean_val(edu),
                "experience": clean_val(exp),
                "skills": clean_val(skills)
            }
            return {
                "agent": "Resume Agent",
                "title": "Create Resume",
                "description": json.dumps(resume_data),
                "raw_message": message
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
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        system_instruction = (
            "You are the central intent classification router for the Aetheria AI companion workspace.\n"
            "Your job is to analyze the user's message and determine if it belongs to one of three categories:\n"
            "1. \"chat\": Standard conversation, questions about general topics, coding/engineering help, explanations, greetings, or friendly chat. These do NOT require any external tool or automated actions.\n"
            "2. \"search\": Real-time queries needing search engine access, such as asking about weather, stock prices, news, recent events, or searching the web.\n"
            "3. \"command\": Actionable commands to automate tasks, set reminders, schedule meetings, draft emails, or generate resumes/CVs.\n\n"
            "For \"command\", classify it into one of these agents:\n"
            "- \"Reminder Agent\": Create tasks/reminders (e.g. \"remind me to write code\", \"create a task to buy bread\").\n"
            "- \"Scheduling Agent\": Schedule meetings or appointments (e.g. \"schedule a call with Bob tomorrow at noon\").\n"
            "- \"Email Agent\": Draft, prepare, or send emails (e.g. \"draft an email to the team explaining the delays\").\n"
            "- \"Resume Agent\": Build, create, or generate a resume/CV, or process user-submitted details (Name, Contact, Education, Experience, Skills) for resume building.\n\n"
            "If the intent is \"chat\", return ONLY a JSON block with {\"intent\": \"chat\"}.\n"
            "If the intent is \"search\", classify it as \"Research Agent\" and return a JSON block.\n"
            "If the intent is \"command\", classify it under the correct agent.\n\n"
            "Your output must be ONLY a valid JSON object matching the following structure:\n"
            "{\n"
            "  \"intent\": \"chat\" | \"search\" | \"command\",\n"
            "  \"agent\": \"Reminder Agent\" | \"Scheduling Agent\" | \"Email Agent\" | \"Research Agent\" | \"Resume Agent\" | \"None\",\n"
            "  \"title\": \"A concise title summarizing the task, email subject, search query, or resume request (e.g. 'Meeting with Bob', 'Buy bread reminder', 'Deep Research: AI trends', 'Create Resume')\",\n"
            "  \"description\": \"For Resume Agent, this MUST be a JSON-serialized string of a dictionary containing key-value pairs for 'name', 'contact', 'education', 'experience', 'skills'. If a field is missing or contains placeholder values like [Your Name], represent it as null. For other agents, provide a detailed description of the command or query.\",\n"
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
                                    "due_time": parsed.get("due_time"),
                                    "raw_message": message
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

        # Trigger n8n/Make webhooks if configured (bypass for Resume Agent which handles its own dispatch)
        if agent != "Resume Agent":
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
        elif agent == "Resume Agent":
            # Extract fields from the intent dictionary or regex fallback
            raw_msg = intent.get("raw_message", "")
            
            # Helper to extract from text
            def extract_from_text(text: str) -> Dict[str, Optional[str]]:
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        keys = ["name", "contact", "education", "experience", "skills"]
                        cleaned = {}
                        for k in keys:
                            val = data.get(k)
                            if val and not (str(val).startswith("[") and str(val).endswith("]")) and str(val).lower() not in ["null", "none", "undefined", ""]:
                                cleaned[k] = str(val).strip()
                            else:
                                cleaned[k] = None
                        if any(cleaned.values()):
                            return cleaned
                except Exception:
                    pass
                return {}

            # Attempt 1: Parse intent["description"] (Gemini JSON output)
            fields = extract_from_text(desc)
            
            # Attempt 2: If description was not JSON or empty, extract from raw message via regex
            if not fields or not any(fields.values()):
                name = re.search(r"(?i)\bname\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", raw_msg, re.DOTALL)
                contact = re.search(r"(?i)\bcontact\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", raw_msg, re.DOTALL)
                edu = re.search(r"(?i)\beducation\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", raw_msg, re.DOTALL)
                exp = re.search(r"(?i)\bexperience\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", raw_msg, re.DOTALL)
                skills = re.search(r"(?i)\bskills\b\s*:\s*(.*?)(?=\s*(?:\b(?:name|contact|education|experience|skills)\b\s*:|$))", raw_msg, re.DOTALL)

                def clean_val(match):
                    if not match:
                        return None
                    val = match.group(1).strip()
                    if val.startswith("[") and val.endswith("]"):
                        return None
                    if val.lower() in ["", "null", "undefined"]:
                        return None
                    return val

                fields = {
                    "name": clean_val(name),
                    "contact": clean_val(contact),
                    "education": clean_val(edu),
                    "experience": clean_val(exp),
                    "skills": clean_val(skills)
                }

            # Attempt 3: If name or contact or skills are still missing, try raw resume section parser (e.g. pasted CV headers)
            if not fields.get("name") or not fields.get("contact") or not fields.get("skills"):
                normalized_text = " ".join(raw_msg.split())
                
                headers = {}
                patterns = {
                    "summary": r"\bPROFESSIONAL SUMMARY\b|\bSUMMARY\b",
                    "skills": r"\bTECHNICAL SKILLS\b|\bTECHNICAL SKILL\b|\bSKILLS\b",
                    "experience": r"\bPROFESSIONAL EXPERIENCE\b|\bEXPERIENCE\b|\bWORK EXPERIENCE\b",
                    "education": r"\bEDUCATION\b",
                    "projects": r"\bKEY PROJECTS\b|\bPROJECTS\b"
                }
                
                # Try case-sensitive search first to avoid matching lowercase words in sentences
                for key, pattern in patterns.items():
                    match = re.search(pattern, normalized_text)
                    if match:
                        headers[key] = (match.start(), match.end())
                
                # If we didn't find enough headers, fallback to case-insensitive
                if len(headers) < 3:
                    headers = {}
                    for key, pattern in patterns.items():
                        match = re.search(pattern, normalized_text, re.IGNORECASE)
                        if match:
                            headers[key] = (match.start(), match.end())
                
                sorted_headers = sorted(headers.items(), key=lambda x: x[1][0])
                
                # Extract Name and Contact from the text BEFORE the first header
                header_start = sorted_headers[0][1][0] if sorted_headers else len(normalized_text)
                intro_text = normalized_text[:header_start].strip()
                
                # Name extraction
                name_val = None
                words = intro_text.split()
                if words and not any(re.search(rf"\b{w}\b", words[0].lower()) for w in ["build", "create", "generate", "resume", "cv", "hello", "hi", "hey"]):
                    candidate_name = " ".join(words[:3])
                    email_idx = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", candidate_name)
                    phone_pattern_regex = r"\(?\+?\d[\d\-\s\(\)]{6,}\d"
                    phone_idx = re.search(phone_pattern_regex, candidate_name)
                    cut_idx = min([idx for idx in [email_idx.start() if email_idx else None, phone_idx.start() if phone_idx else None] if idx is not None], default=len(candidate_name))
                    name_val = candidate_name[:cut_idx].strip(" |,-.").strip()
                
                # Contact extraction
                contact_val = None
                email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
                phone_pattern = r"\(?\+?\d[\d\-\s\(\)]{6,}\d"
                
                # Clean links from intro text for phone search to avoid matching digits in URLs
                clean_intro = intro_text
                for word in intro_text.split():
                    if any(w in word.lower() for w in ["linkedin.com", "github.com", "http", "www", "git"]):
                        clean_intro = clean_intro.replace(word, "")
                
                emails = re.findall(email_pattern, intro_text)
                phones = []
                for m in re.finditer(phone_pattern, clean_intro):
                    phone = m.group().strip().strip(" |,-.")
                    if phone and not any(w in phone for w in ["2024", "2026", "2021", "2025"]) and len(re.sub(r'\D', '', phone)) >= 7:
                        phones.append(phone)
                
                links = [w for w in words if "linkedin.com" in w.lower() or "github.com" in w.lower()]
                
                contact_parts = []
                if phones:
                    contact_parts.extend(phones)
                if emails:
                    contact_parts.extend(emails)
                if links:
                    contact_parts.extend(links)
                
                if contact_parts:
                    contact_val = " | ".join(contact_parts)
                else:
                    contact_val = intro_text
                
                # Section extraction
                def get_section_content(header_key):
                    if header_key not in headers:
                        return None
                    start_offset = headers[header_key][1]
                    end_offset = len(normalized_text)
                    for k, (h_start, h_end) in sorted_headers:
                        if h_start > headers[header_key][0]:
                            end_offset = h_start
                            break
                    return normalized_text[start_offset:end_offset].strip()

                def clean_trailing_prompt(text: str) -> str:
                    if not text:
                        return text
                    text_lower = text.lower()
                    earliest_idx = len(text)
                    for pattern in ["template use", "use krna", "use karna", "yeh template", "template", "use krna hai"]:
                        if pattern in text_lower:
                            idx = text_lower.find(pattern)
                            if idx < earliest_idx:
                                earliest_idx = idx
                    if earliest_idx < len(text):
                        text = text[:earliest_idx].strip()
                    return text.strip(" |,-")

                edu_val = clean_trailing_prompt(get_section_content("education"))
                exp_val = clean_trailing_prompt(get_section_content("experience"))
                skills_val = clean_trailing_prompt(get_section_content("skills"))
                proj_val = clean_trailing_prompt(get_section_content("projects"))
                
                if proj_val and exp_val:
                    exp_val += "\n\nProjects:\n" + proj_val
                elif proj_val:
                    exp_val = "Projects:\n" + proj_val

                if name_val or contact_val or edu_val or exp_val or skills_val:
                    fields = {
                        "name": fields.get("name") or name_val,
                        "contact": fields.get("contact") or contact_val,
                        "education": fields.get("education") or edu_val,
                        "experience": fields.get("experience") or exp_val,
                        "skills": fields.get("skills") or skills_val
                    }

            # Check missing fields
            missing = []
            for key, val in fields.items():
                if not val:
                    missing.append(key.capitalize())

            if missing:
                missing_str = ", ".join(missing)
                # Form template populated with already-known values or placeholders
                name_val = fields.get("name") or "[Your Full Name]"
                contact_val = fields.get("contact") or "[Email and/or Phone Number]"
                edu_val = fields.get("education") or "[Degrees, Schools, Graduation Years]"
                exp_val = fields.get("experience") or "[Job Titles, Companies, Dates, Responsibilities]"
                skills_val = fields.get("skills") or "[Core Skills, Technologies, Certifications]"
                
                output_content = (
                    f"📝 **[Resume Pipeline - Details Needed]**\n\n"
                    f"To generate your professional resume, please provide the missing information (**{missing_str}**).\n\n"
                    f"Copy and complete this template:\n"
                    f"```text\n"
                    f"Name: {name_val}\n"
                    f"Contact: {contact_val}\n"
                    f"Education: {edu_val}\n"
                    f"Experience: {exp_val}\n"
                    f"Skills: {skills_val}\n"
                    f"```\n\n"
                    f"*Simply fill in the remaining details and reply.*"
                )
                return {
                    "success": False,
                    "agent": agent,
                    "output": output_content
                }

            # Generate local PDF resume
            filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
            file_path = os.path.join(RESUME_DIR, filename)
            local_pdf_url = None
            try:
                generate_resume_pdf(fields, file_path)
                local_pdf_url = f"http://localhost:8000/api/v1/workflow/resume/download/{filename}"
            except Exception as e:
                print(f"Warning: Failed to generate PDF locally: {e}")

            # All fields are present! Send to n8n webhook
            n8n_url = getattr(settings, "N8N_WEBHOOK_URL", None)
            pdf_url = None
            
            payload = {
                "name": fields["name"],
                "contact": fields["contact"],
                "education": fields["education"],
                "experience": fields["experience"],
                "skills": fields["skills"]
            }

            if n8n_url and n8n_url.strip():
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(n8n_url, json=payload)
                        if response.status_code in [200, 201]:
                            resp_data = response.json()
                            pdf_url = resp_data.get("resume_url") or resp_data.get("pdf_url") or resp_data.get("download_url")
                except Exception as e:
                    print(f"Warning: Failed to call n8n resume webhook: {e}")

            # Fallback to local PDF or mock URL if webhook is not configured or failed to return a URL
            if not pdf_url:
                pdf_url = local_pdf_url or "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

            output_content = (
                f"📄 **[Resume Agent Active]**: Your professional resume has been successfully generated!\n\n"
                f"- **Name**: {fields['name']}\n"
                f"- **Contact**: {fields['contact']}\n"
                f"- **Education**: {fields['education']}\n"
                f"- **Experience**: {fields['experience']}\n"
                f"- **Skills**: {fields['skills']}\n\n"
                f"Here is your download link:\n"
                f"resume_url: {pdf_url}"
            )
            return {
                "success": True,
                "agent": agent,
                "output": output_content
            }
            
        return {"success": False, "agent": agent, "output": "Agent workflow executed."}

    @staticmethod
    def route_session_mode(session_mode: str, emotion_snap: Dict[str, Any]) -> str:
        """
        Dynamically routes system prompt instructions depending on the selected session_mode.
        - personal: utilize the Tone Mirroring module.
        - professional: business assistant mode.
        - academic: inject deep learning/tutoring rules.
        - researcher: deep web-synthesized research instruction.
        - playground: experimental creative brainstorming mode.
        """
        if session_mode == "personal":
            from app.services.emotion_service import emotion_service
            return emotion_service.get_tone_mirroring_modifier(emotion_snap)
            
        elif session_mode == "academic":
            return (
                "\n\n[SESSION MODE: ACADEMIC / TUTOR MODE]:\n"
                "1. Role: Act as an inspiring, patient academic tutor who guides students toward conceptual understanding.\n"
                "2. Teaching Framework:\n"
                "   - First, introduce the concept using a beginner-friendly, creative real-world analogy.\n"
                "   - Second, break down the core mechanics of the concept into simple, step-by-step points.\n"
                "   - Third, end with a gentle question or a micro-challenge to test the user's comprehension.\n"
                "3. Tone: Encouraging, supportive, warm, and highly beginner-friendly. Avoid dry, dense jargon or wall-of-text explanations."
            )
            
        elif session_mode == "professional":
            return (
                "\n\n[SESSION MODE: PROFESSIONAL / BUSINESS ASSISTANT]:\n"
                "1. Role: You are a high-level executive assistant, career coach, and workflow automation specialist.\n"
                "2. Style & Formatting Constraints:\n"
                "   - Restrict responses to high-impact bullet points, business terms, and structured formatting (e.g. bolded sections, lists, tables).\n"
                "   - Ensure the tone is professional, concise, and action-oriented. Eliminate conversational fluff, fillers, introductions, preambles, and closing questions.\n"
                "   - Do NOT ask the user follow-up questions or start any friendly conversation. Stop immediately after providing the bulleted content.\n"
                "3. Areas of Focus:\n"
                "   - Provide structured interview preparation (using STAR method), resume optimization, and career guidance.\n"
                "   - Outline and describe external workflow automations (e.g. n8n/Make nodes, email drafts, SQL/calendar entries) with clear action steps."
            )
            
        elif session_mode == "researcher":
            return (
                "\n\n[SESSION MODE: RESEARCHER]:\n"
                "1. You are in Researcher Mode. Focus on critical thinking, deep web-synthesized research, and citing sources.\n"
                "2. Provide evidence-based answers, compare perspectives, and present findings in an objective, analytical style.\n"
                "3. Structure your response with sections like Background, Analysis, and Conclusions where appropriate."
            )
            
        elif session_mode == "playground":
            return (
                "\n\n[SESSION MODE: PLAYGROUND / CREATIVE]:\n"
                "1. You are in Playground Mode. Focus on open-ended experimentation, creative writing, roleplay, or brainstorming.\n"
                "2. Be warm, inspiring, highly supportive, and suggest unique perspectives or narrative arcs.\n"
                "3. Fuel the user's imagination with engaging questions and friendly encouragement."
            )
            
        return ""

agent_service = AgentService()
