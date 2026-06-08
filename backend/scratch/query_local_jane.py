import httpx

def test_local_threads():
    base_url = "http://127.0.0.1:8000"
    login_data = {
        "username": "jane.dev2@example.com",
        "password": "aetheria-local-dev"
    }
    
    with httpx.Client(timeout=10.0) as client:
        print("--- Logging in locally ---")
        r = client.post(f"{base_url}/api/v1/auth/login", data=login_data)
        print(f"Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Body: {r.text}")
            return
            
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("--- Fetching local threads ---")
        r_threads = client.get(f"{base_url}/api/v1/chat/threads", headers=headers)
        print(f"Status: {r_threads.status_code}")
        threads = r_threads.json()
        for t in threads:
            print(f"ID: {t['id']} | Title: {t['title']} | Mode: {t.get('session_mode')}")

if __name__ == "__main__":
    test_local_threads()
