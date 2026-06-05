import sys
import os
import asyncio
import json
import re

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agent_service import agent_service
from app.config import settings
from app.database import AsyncSessionLocal

# Force UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def run_tests():
    print("====================================================")
    print("        TESTING PROFESSIONAL RESUME PIPELINE        ")
    print("====================================================\n")

    # Ensure GEMINI API key warning is printed
    if not settings.GEMINI_API_KEY:
        print("[Notice]: GEMINI_API_KEY not configured, running in REGEX fallback mode.\n")
    else:
        print("[Notice]: GEMINI_API_KEY is configured, running in LLM-router mode.\n")

    test_steps = [
        {
            "name": "Step 1: Initial Resume Request (Missing all fields)",
            "message": "Hey! Can you build my resume please?",
            "expect_missing": ["Name", "Contact", "Education", "Experience", "Skills"]
        },
        {
            "name": "Step 2: Partial Submission (Missing contact, experience, skills)",
            "message": (
                "Name: John Doe\n"
                "Contact: [Email and/or Phone Number]\n"
                "Education: BS in Computer Science at University of Michigan\n"
                "Experience: [Job Titles, Companies, Dates, Responsibilities]\n"
                "Skills: [Core Skills, Technologies, Certifications]"
            ),
            "expect_missing": ["Contact", "Experience", "Skills"]
        },
        {
            "name": "Step 3: Complete Submission (All fields provided)",
            "message": (
                "Name: John Doe\n"
                "Contact: john.doe@example.com\n"
                "Education: BS in Computer Science at University of Michigan\n"
                "Experience: Software Engineer Intern at Google (Summer 2025)\n"
                "Skills: Python, FastAPI, React, TypeScript, Docker"
            ),
            "expect_missing": []
        }
    ]

    async with AsyncSessionLocal() as db:
        for idx, step in enumerate(test_steps, 1):
            print(f"--- {step['name']} ---")
            print(f"User Message:\n{step['message']}\n")

            # 1. Detect Intent
            intent = await agent_service.detect_task_intent(step["message"])
            print(f"Detected Agent: {intent.get('agent') if intent else 'None'}")
            print(f"Detected Intent Details: {json.dumps(intent, indent=2) if intent else 'None'}\n")

            # 2. Execute Workflow
            if intent and intent.get("agent") == "Resume Agent":
                result = await agent_service.execute_workflow(
                    user_id=1,
                    intent=intent,
                    db=db
                )
                print("Agent Output Content:")
                print(result["output"])
                print("-" * 50)
                
                # Assertions/Verification checks
                output = result["output"]
                success = result.get("success", False)
                
                if step["expect_missing"]:
                    if success:
                        print("❌ ERROR: Expected validation to fail due to missing fields, but it succeeded.")
                    else:
                        print("✅ SUCCESS: Validation failed as expected.")
                    for field in step["expect_missing"]:
                        if field in output:
                            print(f"  - Verified missing field '{field}' was correctly flagged.")
                        else:
                            print(f"  - ❌ ERROR: Missing field '{field}' was NOT flagged in the output.")
                else:
                    if not success:
                        print("❌ ERROR: Expected execution to succeed, but validation failed.")
                    else:
                        print("✅ SUCCESS: Resume generated successfully.")
                        # Verify download URL exists
                        url_match = re.search(r"resume_url:\s*(https?://[^\s]+)", output)
                        if url_match:
                            print(f"  - Generated URL: {url_match.group(1)}")
                        else:
                            print("  - ❌ ERROR: No resume download URL found in output.")
            else:
                print("❌ ERROR: Failed to route to Resume Agent.")
            print("\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
