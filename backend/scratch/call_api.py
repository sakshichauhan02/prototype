import httpx
import asyncio

async def test_api_call():
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # 1. Login to get JWT Token
    login_data = {
        "username": "jane.dev2@example.com",
        "password": "aetheria-local-dev"
    }
    
    async with httpx.AsyncClient() as client:
        print("Logging in...")
        res = await client.post(f"{base_url}/auth/login", data=login_data)
        if res.status_code != 200:
            print("Login failed! Ensure backend is running and user exists.")
            return
            
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create thread with creative session_mode
        payload = {
            "title": "Novel Outline Brainstorm",
            "companion_id": "leo",
            "session_mode": "creative"
        }
        
        print("\nCreating thread with session_mode='creative'...")
        res = await client.post(f"{base_url}/chat/threads", json=payload, headers=headers)
        if res.status_code == 201:
            data = res.json()
            print("Successfully Created Thread!")
            print(f"ID: {data['id']}")
            print(f"Title: {data['title']}")
            print(f"Companion: {data['companion_id']}")
            print(f"Session Mode: '{data['session_mode']}'")
        else:
            print(f"Failed to create thread: {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(test_api_call())
