import sys
import os
import asyncio

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.emotion_service import emotion_service
from app.services.ai_service import ai_service

async def run_tests():
    # Set console output encoding to utf-8 to print emojis on Windows
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        
    test_cases = [
        # Hinglish cases
        "yrr mujhe bhook lgri h",
        "mujhe gussa aa raha h",
        "are mera mood acha nhi h",
        
        # English cases
        "I am preparing for an interview tomorrow.",
        "Explain machine learning.",
        
        # General checks
        "what is AI?"
    ]

    print("--- TESTING LOCAL DETECTION LOGIC ---")
    for tc in test_cases:
        res = await emotion_service.analyze_emotion(tc)
        print(f"\nUser Input: '{tc}'")
        print(f"Detected Lang: {res.get('language')}")
        print(f"Detected Style: {res.get('communication_style')}")
        print(f"Primary Emotion: {res.get('primary_emotion')}")
        
        # Test simulated fallback reply matching
        reply = await ai_service.generate_reply(
            companion_id="aria",
            message=tc,
            tone_analysis=res
        )
        print(f"Aria Reply: {reply}")

if __name__ == "__main__":
    asyncio.run(run_tests())
