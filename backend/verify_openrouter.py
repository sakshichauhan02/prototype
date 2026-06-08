import asyncio
import sys
import os

# Adjust path to import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.openrouter_service import openrouter_service
from app.services.ai_service import ai_service

async def test_openrouter_configuration():
    print("--- Testing OpenRouter Settings Configuration ---")
    print(f"OPENROUTER_MODEL in settings: {settings.OPENROUTER_MODEL}")
    print(f"OPENROUTER_API_KEY in settings (length): {len(settings.OPENROUTER_API_KEY) if settings.OPENROUTER_API_KEY else 0}")
    
    if not settings.OPENROUTER_API_KEY:
        print("Note: OPENROUTER_API_KEY is empty (normal for local sandbox). Testing fallback pathways.")
    else:
        print("OPENROUTER_API_KEY is populated.")
    print("Configuration test passed.\n")

async def test_fallback_when_key_missing():
    print("--- Testing Fallback Mechanism when Key is Missing/Invalid ---")
    # Temporarily clear key to force fallback test
    original_key = settings.OPENROUTER_API_KEY
    settings.OPENROUTER_API_KEY = ""
    
    test_messages = [{"role": "user", "content": "Hello Aetheria companion"}]
    reply = await openrouter_service.generate_openrouter_reply(test_messages)
    
    print(f"OpenRouter reply with missing key: {reply} (Expected: None)")
    assert reply is None, "Expected OpenRouter reply to be None when API key is missing"
    
    # Restore original key
    settings.OPENROUTER_API_KEY = original_key
    print("Fallback pathways verification passed.\n")

async def test_direct_openrouter_api_call_with_fake_key():
    print("--- Testing API Call with Invalid Key (Error Handling) ---")
    original_key = settings.OPENROUTER_API_KEY
    settings.OPENROUTER_API_KEY = "sk-or-invalid-test-key-12345"
    
    test_messages = [{"role": "user", "content": "Hi!"}]
    reply = await openrouter_service.generate_openrouter_reply(test_messages)
    
    print(f"OpenRouter reply with invalid key: {reply} (Expected: None because of API error)")
    assert reply is None, "Expected OpenRouter to fail and return None for invalid key"
    
    settings.OPENROUTER_API_KEY = original_key
    print("Error handling verification passed.\n")

async def test_ai_service_routing():
    print("--- Testing ai_service.generate_reply integration ---")
    
    # 1. Test Playground Mode (which should bypass OpenRouter and go straight to Groq/local)
    playground_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="Explain recursion",
        history=[],
        temperature=0.7,
        tone="Analytical",
        tone_analysis={"session_mode": "playground", "cognitive_engine": "test-engine"}
    )
    print("Playground mode reply success (does not trigger OpenRouter).")
    
    # 2. Test Personal Companion Mode (which routes exclusively to OpenRouter and bypasses Groq)
    # Temporarily clear OpenRouter API Key to check if it bypasses Groq and goes directly to mock simulation
    original_key = settings.OPENROUTER_API_KEY
    settings.OPENROUTER_API_KEY = ""
    
    personal_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="Hello! How are you doing today?",
        history=[],
        temperature=0.7,
        tone="Analytical",
        tone_analysis={"session_mode": "personal_companion"}
    )
    print(f"Personal Companion reply (no key): {personal_reply[:100]}...")
    assert "⚠️ **[SYSTEM NOTICE]**" not in personal_reply, "Groq was NOT bypassed! Groq Warning notice was found."
    
    # Check backward compatibility with "personal" mode
    personal_mode_reply = await ai_service.generate_reply(
        companion_id="aria",
        message="Hello!",
        history=[],
        temperature=0.7,
        tone="Analytical",
        tone_analysis={"session_mode": "personal"}
    )
    assert "⚠️ **[SYSTEM NOTICE]**" not in personal_mode_reply, "Groq was NOT bypassed in 'personal' mode!"
    
    settings.OPENROUTER_API_KEY = original_key
    print("Routing integration verification passed.\n")

async def main():
    print("=== STARTING OPENROUTER INTEGRATION TESTS ===")
    try:
        await test_openrouter_configuration()
        await test_fallback_when_key_missing()
        await test_direct_openrouter_api_call_with_fake_key()
        await test_ai_service_routing()
        print("=== ALL TESTS PASSED SUCCESSFULLY ===")
    except AssertionError as ae:
        print(f"Assertion failed: {ae}")
        sys.exit(1)
    except Exception as e:
        print(f"Test runner error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
