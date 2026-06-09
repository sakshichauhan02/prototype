import asyncio
import sys
from app.services.agent_service import agent_service

# Force UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    print("--- Running Backend Image Generation Tests ---")
    
    # Test cases
    cases = [
        {
            "name": "English Prompt (Playground)",
            "message": "Create image of a futuristic city",
            "session_mode": "playground",
            "expect_agent": True
        },
        {
            "name": "Hindi Prompt (Playground)",
            "message": "Ek sundar pahad ka image banao",
            "session_mode": "playground",
            "expect_agent": True
        },
        {
            "name": "English Prompt (Non-playground - should not intercept)",
            "message": "Create image of a futuristic city",
            "session_mode": "personal",
            "expect_agent": False
        }
    ]

    for tc in cases:
        print(f"\n[Test: {tc['name']}]")
        print(f"Input message: \"{tc['message']}\"")
        intent = await agent_service.detect_task_intent(tc["message"], session_mode=tc["session_mode"])
        
        if intent:
            print("-> Detected Agent Workflow:")
            print(f"   Agent: {intent.get('agent')}")
            print(f"   Title: {intent.get('title')}")
            print(f"   Extracted Prompt: \"{intent.get('description')}\"")
            
            # Execute workflow to test URL generation
            # Pass None for db session since Image Agent doesn't interact with DB
            workflow_res = await agent_service.execute_workflow(user_id=1, intent=intent, db=None)
            print(f"   Generated Output URL: {workflow_res.get('output')}")
            
            if not tc["expect_agent"]:
                print("❌ ERROR: Expected standard chat routing but triggered agent!")
        else:
            print("-> Routed to Standard Chat (Standard Conversation)")
            if tc["expect_agent"]:
                print("❌ ERROR: Expected Image Agent routing but standard chat triggered!")

if __name__ == "__main__":
    asyncio.run(main())
