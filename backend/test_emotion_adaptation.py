import asyncio
import sys
import json
from app.services.emotion_service import emotion_service
from app.services.ai_service import ai_service
from app.config import settings

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_emotion():
    print("=== Testing Emotional Intelligence Adaptation ===")
    
    test_cases = [
        {
            "label": "Positive Input",
            "message": "I am extremely happy because I got selected.",
            "expected_emotion": "excited",
            "expected_tone": "Enthusiastic"
        },
        {
            "label": "Negative Input",
            "message": "I am feeling very sad and disappointed today.",
            "expected_emotion": "sad",
            "expected_tone": "Supportive"
        }
    ]
    
    for tc in test_cases:
        print(f"\n[Test Case: {tc['label']}]")
        print(f"Message: \"{tc['message']}\"")
        
        # 1. Analyze Emotion
        analysis = await emotion_service.analyze_emotion(tc["message"])
        print(f"Analyzed Emotion Snap:")
        print(json.dumps(analysis, indent=2))
        
        pe = analysis.get("primary_emotion", "neutral")
        if pe == tc["expected_emotion"]:
            print(f"✅ Success: Correctly identified emotion as '{pe}' (Expected: '{tc['expected_emotion']}')")
        else:
            print(f"❌ Failure: Identified emotion as '{pe}' (Expected: '{tc['expected_emotion']}')")
            
        # 2. Get prompt modifier
        modifier = emotion_service.get_adaptive_prompt_modifier(pe)
        
        # 3. Determine Tone
        tone = "Analytical"
        if pe == "excited":
            tone = "Enthusiastic"
        elif pe == "sad":
            tone = "Supportive"
            
        print(f"Dynamic Tone override: {tone} (Expected: {tc['expected_tone']})")
        
        # 4. Generate response
        print("Calling ai_service.generate_reply...")
        reply = await ai_service.generate_reply(
            companion_id="leo", # Using Leo for creative/warm persona testing
            message=tc["message"],
            history=[],
            temperature=0.7,
            tone=tone,
            rag_context="",
            emotion_modifier=modifier,
            research_context="",
            primary_emotion=pe
        )
        print(f"Response:\n{reply}")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test_emotion())
