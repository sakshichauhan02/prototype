import httpx

def test_jane_threads():
    base_url = "https://prototype-afow.onrender.com"
    login_data = {
        "username": "jane.dev2@example.com",
        "password": "aetheria-local-dev"
    }
    
    with httpx.Client(timeout=10.0) as client:
        r = client.post(f"{base_url}/api/v1/auth/login", data=login_data)
        if r.status_code != 200:
            print(f"Login failed: {r.status_code} {r.text}")
            return
        
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("--- Testing GET /api/v1/chat/threads for Jane ---")
        r_threads = client.get(f"{base_url}/api/v1/chat/threads", headers=headers)
        print(f"Status: {r_threads.status_code}")
        print(f"Body: {r_threads.text}\n")

if __name__ == "__main__":
    test_jane_threads()
