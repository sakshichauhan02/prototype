import asyncio
import sys
import os

# Ensure backend folder is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.did_service import did_service
from app.config import settings

async def main():
    print("=== Testing D-ID Talking Avatar Service ===")
    
    # Check key config
    key = settings.DID_API_KEY
    if not key:
        print("DID_API_KEY is currently empty. The service will run in Mock Fallback Mode.")
    else:
        print(f"DID_API_KEY is configured: {key[:8]}...")
        
    # Test English prompt
    en_prompt = "Welcome to my channel"
    print(f"\n--- Test Case 1: English Prompt ---")
    print(f"Prompt: {en_prompt}")
    video_url_en = await did_service.generate_avatar_video(en_prompt)
    print(f"Generated Video URL: {video_url_en}")

    # Test Hindi prompt
    hi_prompt = "Namaste dosto mera naam Sakshi hai"
    print(f"\n--- Test Case 2: Hindi Prompt ---")
    print(f"Prompt: {hi_prompt}")
    video_url_hi = await did_service.generate_avatar_video(hi_prompt)
    print(f"Generated Video URL: {video_url_hi}")

if __name__ == "__main__":
    asyncio.run(main())
