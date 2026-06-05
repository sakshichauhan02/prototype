import asyncio
import httpx
import sys

API_BASE = "http://localhost:8000/api/v1"

async def run_demo():
    print("=== STARTING SESSION MODE IMPLEMENTATION DEMO ===")
    
    # 1. Log in dev user
    login_data = {
        "username": "jane.dev2@example.com",
        "password": "aetheria-local-dev"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Check if user exists, if not signup
        try:
            login_res = await client.post(f"{API_BASE}/auth/login", data=login_data)
            if login_res.status_code == 200:
                token = login_res.json()["access_token"]
                print("[OK] Logged in successfully.")
            else:
                # Try signup
                signup_res = await client.post(f"{API_BASE}/auth/signup", json={
                    "name": "Jane Developer",
                    "email": "jane.dev2@example.com",
                    "password": "aetheria-local-dev"
                })
                token = signup_res.json()["access_token"]
                print("[OK] Registered and logged in successfully.")
        except Exception as e:
            print(f"Error connecting to backend: {e}")
            return
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test configurations
        test_cases = [
            {"mode": "researcher", "message": "Explain machine learning."},
            {"mode": "playground", "message": "hello"},
            {"mode": "personal", "message": "hello"},
            {"mode": "professional", "message": "Give me interview preparation tips for a senior software engineer role."}
        ]
        
        for case in test_cases:
            mode = case["mode"]
            msg = case["message"]
            print(f"\n--- Testing Session Mode: '{mode}' ---")
            
            # Create Thread
            thread_payload = {
                "title": f"Demo {mode.capitalize()} Thread",
                "companion_id": "aria",
                "session_mode": mode
            }
            create_res = await client.post(f"{API_BASE}/chat/threads", json=thread_payload, headers=headers)
            if create_res.status_code != 201:
                print(f"Failed to create thread: {create_res.text}")
                continue
                
            thread = create_res.json()
            thread_id = thread["id"]
            print(f"[OK] Thread created (ID: {thread_id}, Mode: '{thread['session_mode']}')")
            
            # Send Message
            print(f"Sending User Message: '{msg}'")
            msg_payload = {
                "content": msg,
                "companion_id": "aria"
            }
            msg_res = await client.post(f"{API_BASE}/chat/threads/{thread_id}/messages", json=msg_payload, headers=headers)
            if msg_res.status_code != 200:
                print(f"Failed to send message: {msg_res.text}")
                continue
                
            reply = msg_res.json()
            print(f"Aria Reply (extracted from API response):\n{reply['content']}")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(run_demo())
