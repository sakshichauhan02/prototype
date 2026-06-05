import sys
import os
import asyncio

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agent_service import agent_service
from app.services.ai_service import ai_service

async def run_tests():
    print("--- TESTING ROUTING INSTRUCTIONS ---")
    modes = ["personal", "professional", "academic", "researcher", "playground"]
    mock_emotion = {"language": "English", "communication_style": "Casual", "primary_emotion": "neutral"}
    
    for mode in modes:
        instructions = agent_service.route_session_mode(mode, mock_emotion)
        print(f"\nMode: '{mode}'")
        print(f"Injected Instruction Header:\n{instructions.strip()[:180]}...")

    print("\n--- TESTING SIMULATION RESPONSES BY MODE ---")
    
    # 1. Academic mode test
    print("\n[Input in Academic Mode]: 'Explain how APIs work.'")
    academic_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="Explain how APIs work.",
        tone_analysis={"language": "English", "communication_style": "Casual", "session_mode": "academic"}
    )
    print(f"Aria Reply:\n{academic_reply}")

    # 2. Professional mode test
    print("\n[Input in Professional Mode]: 'Give me interview preparation tips for a senior software engineer role.'")
    professional_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="Give me interview preparation tips for a senior software engineer role.",
        tone_analysis={"language": "English", "communication_style": "Casual", "session_mode": "professional"}
    )
    print(f"Aria Reply:\n{professional_reply}")

    # 3. Researcher mode test
    print("\n[Input in Researcher Mode]: 'What is the latest price of Bitcoin?'")
    researcher_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="What is the latest price of Bitcoin?",
        tone_analysis={"language": "English", "communication_style": "Casual", "session_mode": "researcher"}
    )
    print(f"Aria Reply:\n{researcher_reply}")

    # 4. Playground mode test
    print("\n[Input in Playground Mode]: 'Brainstorm 3 creative story titles about time travel.'")
    playground_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="Brainstorm 3 creative story titles about time travel.",
        tone_analysis={
            "language": "English",
            "communication_style": "Casual",
            "session_mode": "playground",
            "cognitive_engine": "aetheria-large-v2",
            "temperature": 0.8
        }
    )
    print(f"Aria Reply:\n{playground_reply}")

if __name__ == "__main__":
    # Fix stdout for windows emojis
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(run_tests())
