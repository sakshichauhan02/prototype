import asyncio
import httpx
import sys

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(".")
from app.config import settings

async def test_model(model_name: str):
    print(f"Testing model: {model_name}")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "Hello, Gemini!"}]}]
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.post(url, json=payload, headers=headers)
            print(f"Status Code: {r.status_code}")
            if r.status_code == 200:
                print("✅ Success!")
                data = r.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"Response snippet: {text.strip()[:100]}...")
                return True
            else:
                print(f"❌ Error: {r.text}")
                return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def main():
    print(f"Using GEMINI_API_KEY from config: {settings.GEMINI_API_KEY[:6]}...{settings.GEMINI_API_KEY[-4:]}")
    models = ["gemini-3.5-flash", "gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
    for m in models:
        await test_model(m)
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
