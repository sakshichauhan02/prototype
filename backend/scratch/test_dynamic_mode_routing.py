import sys
import os
import asyncio

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agent_service import agent_service
from app.services.ai_service import ai_service

async def run_tests():
    print("--- TESTING ROUTING INSTRUCTIONS ---")
    modes = ["casual", "academic", "professional", "creative"]
    mock_emotion = {"language": "English", "communication_style": "Casual", "primary_emotion": "neutral"}
    
    for mode in modes:
        instructions = agent_service.route_session_mode(mode, mock_emotion)
        print(f"\nMode: '{mode}'")
        print(f"Injected Instruction Header:\n{instructions.strip()[:180]}...")

    print("\n--- TESTING SIMULATION RESPONSES BY MODE ---")
    
    # 1. Academic mode test
    print("\n[Input in Academic Mode]: 'Explain machine learning.'")
    academic_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="Explain machine learning.",
        tone_analysis={"language": "English", "communication_style": "Casual", "session_mode": "academic"}
    )
    print(f"Aria Reply: {academic_reply}")

    # 2. Professional mode test
    print("\n[Input in Professional Mode]: 'Explain machine learning.'")
    professional_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="Explain machine learning.",
        tone_analysis={"language": "English", "communication_style": "Casual", "session_mode": "professional"}
    )
    print(f"Aria Reply: {professional_reply}")

if __name__ == "__main__":
    # Fix stdout for windows emojis
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(run_tests())
