import asyncio
import time
import httpx
import sys
from jose import jwt
from datetime import datetime, timedelta

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
SECRET_KEY = "aetheria-super-secret-crypto-elliptic-quantum-key-2026"
ALGORITHM = "HS256"

# Generate JWT Token for User 1
def generate_token(user_id: int = 1) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def test_background_memory():
    token = generate_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Fetch or create a chat thread
        print("Fetching existing chat threads...")
        resp = await client.get(f"{BASE_URL}/api/v1/chat/threads", headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching threads: {resp.text}")
            return
            
        threads = resp.json()
        if threads:
            thread_id = threads[0]["id"]
            print(f"Using existing thread ID: {thread_id}")
        else:
            print("Creating a new thread...")
            create_resp = await client.post(
                f"{BASE_URL}/api/v1/chat/threads",
                headers=headers,
                json={"title": "Test Thread", "companion_id": "aria"}
            )
            if create_resp.status_code != 201:
                print(f"Error creating thread: {create_resp.text}")
                return
            thread_id = create_resp.json()["id"]
            print(f"Created thread ID: {thread_id}")
            
        # 2. Record existing memories before sending the test message
        print("\nChecking existing memories...")
        mem_resp = await client.get(f"{BASE_URL}/api/v1/memory", headers=headers)
        existing_memories = mem_resp.json()
        print(f"Existing memory count: {len(existing_memories)}")
        
        # 3. Send message prompting memory extraction and measure latency
        test_message = "Remember that my favorite programming language is Rust."
        print(f"\nSending message: '{test_message}'")
        
        start_time = time.time()
        msg_resp = await client.post(
            f"{BASE_URL}/api/v1/chat/threads/{thread_id}/messages",
            headers=headers,
            json={"content": test_message}
        )
        latency = time.time() - start_time
        
        print(f"Response Status Code: {msg_resp.status_code}")
        print(f"Request Latency: {latency:.4f} seconds")
        
        if msg_resp.status_code != 200:
            print(f"❌ Error sending message: {msg_resp.text}")
            return
            
        ai_msg = msg_resp.json()
        print(f"Companion Response: {ai_msg['content']}")
        
        # 4. Wait for background task to complete (e.g. LLM extraction + HF embed + Qdrant sync)
        wait_seconds = 4.0
        print(f"\nSleeping for {wait_seconds} seconds to allow the background memory task to finish...")
        await asyncio.sleep(wait_seconds)
        
        # 5. Fetch memories to verify extraction
        print("Checking memories again...")
        mem_resp2 = await client.get(f"{BASE_URL}/api/v1/memory", headers=headers)
        new_memories = mem_resp2.json()
        print(f"New memory count: {len(new_memories)}")
        
        found = False
        for m in new_memories:
            fact = m.get("fact", "")
            if "rust" in fact.lower():
                print(f"✅ Success! Memory successfully extracted and stored in the background:")
                print(f"  - Category: {m.get('category')} | Fact: '{fact}'")
                found = True
                break
                
        if not found:
            print("❌ Failure: Memory not found. Check backend logs for errors in background execution.")

if __name__ == "__main__":
    asyncio.run(test_background_memory())
