import asyncio
import os
import sys

# Ensure backend folder is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.ai_service import ai_service
from app.config import settings

async def main():
    print("=== Testing Groq API Integration & Fallback ===")
    print("GROQ_API_KEY value loaded:", repr(settings.GROQ_API_KEY))
    
    # 1. Test case: Empty API Key -> Should fallback gracefully with notice
    print("\n--- Test Case 1: Empty API key (Fallback check) ---")
    # Save original key
    original_key = settings.GROQ_API_KEY
    settings.GROQ_API_KEY = ""
    
    reply = await ai_service.generate_reply(
        companion_id="aria",
        message="Hello! What is your name?",
        history=[],
        temperature=0.5,
        tone="Analytical"
    )
    print("Reply with empty key:\n", reply)
    if "SYSTEM NOTICE" in reply and "Aria" in reply:
        print("✅ Test Case 1 Passed: Fallback notice generated correctly.")
    else:
        print("❌ Test Case 1 Failed.")
        
    # Restore key
    settings.GROQ_API_KEY = original_key
    
    # 2. Test case: Try to call with real key (or invalid key to test network error handling)
    print("\n--- Test Case 2: Custom API key call check ---")
    if not settings.GROQ_API_KEY:
        print("Note: No GROQ_API_KEY set in env. We will set a dummy key to verify error handling fallback.")
        settings.GROQ_API_KEY = "gsk_dummy_test_key_12345"
        
    reply_dummy = await ai_service.generate_reply(
        companion_id="leo",
        message="Hello, can you tell me a story?",
        history=[],
        temperature=0.7,
        tone="Empathetic"
    )
    print("Reply with dummy/invalid key:\n", reply_dummy)
    if "SYSTEM NOTICE" not in reply_dummy and len(reply_dummy) > 10:
        print("✅ Test Case 2 Passed: Silent mock/local fallback triggered on invalid/dummy key.")
    else:
        print("❌ Test Case 2 Failed.")

if __name__ == "__main__":
    asyncio.run(main())
