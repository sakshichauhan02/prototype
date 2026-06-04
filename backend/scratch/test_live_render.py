import asyncio
import httpx
import sys
import time
from datetime import datetime

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LIVE_URL = "https://prototype-afow.onrender.com"
DEV_USER = {
    "name": "Jane Developer",
    "email": "jane.dev2@example.com",
    "password": "aetheria-local-dev"
}

async def get_production_token(client: httpx.AsyncClient) -> str:
    # 1. Try Login
    print("Attempting to login dev user on production...")
    login_data = {
        "username": DEV_USER["email"],
        "password": DEV_USER["password"]
    }
    try:
        res = await client.post(
            f"{LIVE_URL}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if res.status_code == 200:
            token = res.json().get("access_token")
            print("✅ Successfully logged in dev user.")
            return token
    except Exception as e:
        print(f"Login failed: {e}")
        
    # 2. Try Signup if login failed
    print("User may not exist. Attempting signup on production...")
    try:
        res = await client.post(
            f"{LIVE_URL}/api/v1/auth/signup",
            json=DEV_USER
        )
        if res.status_code in (200, 201):
            token = res.json().get("access_token")
            print("✅ Successfully signed up dev user.")
            return token
        else:
            print(f"Signup failed status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Signup exception: {e}")
        
    return ""

async def test_live_backend():
    print(f"=== Testing Live Render Backend API ===")
    print(f"Target URL: {LIVE_URL}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health check
        print("\n1. Testing Server Root...")
        try:
            r = await client.get(LIVE_URL)
            print(f"Root Status: {r.status_code}")
            assert r.status_code == 200
            print("✅ Live Render Server is online.")
        except Exception as e:
            print(f"❌ Server Root unreachable: {e}")
            return

        # 2. Authenticate
        print("\n2. Authenticating on production...")
        token = await get_production_token(client)
        if not token:
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
            
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Test threads endpoint
        print("\n3. Testing Threads API on production...")
        try:
            threads_resp = await client.get(f"{LIVE_URL}/api/v1/chat/threads", headers=headers)
            print(f"Threads API Status: {threads_resp.status_code}")
            if threads_resp.status_code == 200:
                print(f"✅ Success: Retrieved threads (Count: {len(threads_resp.json())})")
            else:
                print(f"❌ Threads API returned error: {threads_resp.text}")
        except Exception as e:
            print(f"❌ Threads API call failed: {e}")

        # 4. Test memory retrieval endpoint
        print("\n4. Testing Memory Vault API on production...")
        try:
            mem_resp = await client.get(f"{LIVE_URL}/api/v1/memory", headers=headers)
            print(f"Memory API Status: {mem_resp.status_code}")
            if mem_resp.status_code == 200:
                memories = mem_resp.json()
                print(f"✅ Success: Retrieved memories (Count: {len(memories)})")
                if memories:
                    print("Sample decrypted memory fact:", memories[0].get("fact"))
            else:
                print(f"❌ Memory API returned error: {mem_resp.text}")
        except Exception as e:
            print(f"❌ Memory API call failed: {e}")

        # 5. Test sync endpoint
        print("\n5. Testing Sync API on production...")
        mock_thread_id = f"live-sync-thread-{int(time.time())}"
        payload = {
            "mutations": [
                {
                    "type": "CREATE_THREAD",
                    "payload": {
                        "id": mock_thread_id,
                        "companionId": "aria",
                        "title": "Live Production Sync Test"
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            ]
        }
        try:
            sync_resp = await client.post(f"{LIVE_URL}/api/v1/chat/sync", headers=headers, json=payload)
            print(f"Sync API Status: {sync_resp.status_code}")
            print(f"Sync response: {sync_resp.text}")
            if sync_resp.status_code == 200:
                print("✅ Sync endpoint works perfectly on Render.")
            else:
                print(f"❌ Sync API returned error: {sync_resp.text}")
        except Exception as e:
            print(f"❌ Sync API call failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_backend())
