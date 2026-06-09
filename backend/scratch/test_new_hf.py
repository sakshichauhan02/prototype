import asyncio
import httpx
from app.config import settings

async def main():
    print("--- Testing Hugging Face Router Endpoints ---")
    hf_key = settings.HUGGINGFACE_API_KEY
    print(f"HF Key: {hf_key[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {hf_key}",
        "Content-Type": "application/json"
    }

    # 1. Test Emotion Classifier
    emotion_model = "bhadresh-savani/distilbert-base-uncased-emotion"
    emotion_url = f"https://router.huggingface.co/hf-inference/models/{emotion_model}"
    print(f"\n1. Testing Emotion Model URL: {emotion_url}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(emotion_url, json={"inputs": "I am so excited and happy!"}, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error testing emotion model: {e}")

    # 2. Test Image Generation (Stable Diffusion)
    image_model = "stabilityai/stable-diffusion-xl-base-1.0"
    image_url = f"https://router.huggingface.co/hf-inference/models/{image_model}"
    print(f"\n2. Testing Image Model URL: {image_url}")
    try:
        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(image_url, json={"inputs": "a futuristic city, high resolution, digital art"}, headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"-> Success! Received image bytes: {len(resp.content)} bytes.")
            else:
                print(f"-> Failed: {resp.text}")
    except Exception as e:
        print(f"Error testing image model: {e}")

if __name__ == "__main__":
    asyncio.run(main())
