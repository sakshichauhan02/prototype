import asyncio
import sys
import os

# Adjust path to import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.ai_service import ai_service

async def run_scenario_checks():
    print("====================================================")
    print("RUNNING DYNAMIC ROUTING & BYPASS SIMULATION SCENARIO")
    print("====================================================\n")

    # Temporarily remove OpenRouter API Key to simulate unconfigured state
    original_or_key = settings.OPENROUTER_API_KEY
    settings.OPENROUTER_API_KEY = ""

    print("Step 1: Simulating 'personal_companion' Mode (Should bypass Groq and return mock fallback directly)")
    print("------------------------------------------------------------------------------------------------")
    personal_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="What is machine learning?",
        history=[],
        temperature=0.7,
        tone="Analytical",
        tone_analysis={"session_mode": "personal_companion"}
    )
    print("Resulting Reply:")
    print(personal_reply)
    print("\n------------------------------------------------------------------------------------------------\n")

    print("Step 2: Simulating 'playground' Mode (Should fall through to Groq API call)")
    print("------------------------------------------------------------------------------------------------")
    
    # We temporarily clear Groq API Key as well to trigger Groq's local fallback warning, proving it reached Groq
    original_groq_key = settings.GROQ_API_KEY
    settings.GROQ_API_KEY = ""
    
    playground_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="What is machine learning?",
        history=[],
        temperature=0.7,
        tone="Analytical",
        tone_analysis={"session_mode": "playground"}
    )
    print("Resulting Reply:")
    print(playground_reply)
    print("\n------------------------------------------------------------------------------------------------\n")

    # Restore original keys
    settings.OPENROUTER_API_KEY = original_or_key
    settings.GROQ_API_KEY = original_groq_key
    print("Scenario execution complete. Keys restored successfully.")

if __name__ == "__main__":
    asyncio.run(run_scenario_checks())
