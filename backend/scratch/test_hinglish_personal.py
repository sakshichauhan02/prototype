import asyncio
import httpx
import sys

API_BASE = "http://localhost:8000/api/v1"

async def run_test():
    login_data = {
        "username": "jane.dev2@example.com",
        "password": "aetheria-local-dev"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Login
        login_res = await client.post(f"{API_BASE}/auth/login", data=login_data)
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create personal mode thread
        thread_payload = {
            "title": "Bhai Mode Test Thread",
            "companion_id": "aria",
            "session_mode": "personal"
        }
        create_res = await client.post(f"{API_BASE}/chat/threads", json=thread_payload, headers=headers)
        thread = create_res.json()
        thread_id = thread["id"]
        
        # 3. Send Hinglish message
        msg_payload = {
            "content": "bhai aaj mood kharab hai yaar, coding me problem aa rhi hai",
            "companion_id": "aria"
        }
        print(f"Sending message in personal mode: '{msg_payload['content']}'")
        msg_res = await client.post(f"{API_BASE}/chat/threads/{thread_id}/messages", json=msg_payload, headers=headers)
        reply = msg_res.json()
        print(f"\nResponse:\n{reply['content']}")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(run_test())
