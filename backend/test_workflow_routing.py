import asyncio
import json
import sys
from app.services.agent_service import agent_service
from app.config import settings

# Force UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_routing():
    print("--- Testing Intent Classification Router ---")
    if not settings.GEMINI_API_KEY:
        print("GEMINI_API_KEY is not configured. The test will run in regex fallback mode.")
    else:
        print("Using LLM-based intent classifier.")

    test_cases = [
        {
            "description": "Standard Chat",
            "message": "Hello, how are you doing today? Can you explain how quicksort works?"
        },
        {
            "description": "Web Search Request",
            "message": "research about the latest announcements in quantum computing from this month"
        },
        {
            "description": "Reminder Command",
            "message": "remind me to buy groceries and milk tonight at 8 PM"
        },
        {
            "description": "Scheduling Command",
            "message": "schedule a meeting with Rajat and the design team on Friday at 3 PM"
        },
        {
            "description": "Email Drafting Command",
            "message": "draft an email to Jane explaining the software launch delay and listing the key technical risks"
        }
    ]

    for tc in test_cases:
        print(f"\n[Test Case: {tc['description']}]")
        print(f"Message: \"{tc['message']}\"")
        try:
            intent = await agent_service.detect_task_intent(tc["message"])
            if intent is None:
                print("-> Route: Chat (Standard Conversation)")
            else:
                print("-> Route: Workflow Action / Web Search")
                print(json.dumps(intent, indent=2))
        except Exception as e:
            print(f"Error during routing: {e}")

if __name__ == "__main__":
    asyncio.run(test_routing())
