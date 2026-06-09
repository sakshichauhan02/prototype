import asyncio
import httpx
from app.config import settings

async def main():
    print("--- Testing Hugging Face Image Generation ---")
    hf_key = settings.HUGGINGFACE_API_KEY
    print(f"HF Key: {hf_key[:10]}...")
    
    # We can use Stable Diffusion XL or RunwayML
    model_id = "stabilityai/stable-diffusion-xl-base-1.0"
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    
    headers = {
        "Authorization": f"Bearer {hf_key}"
    }
    payload = {
        "inputs": "a futuristic city, high resolution, digital art"
    }
    
    try:
        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("-> Success! Received image bytes.")
                print(f"Length of content: {len(resp.content)} bytes")
            else:
                print(f"-> Failed: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
