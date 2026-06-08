import httpx

def test_threads():
    base_url = "https://prototype-afow.onrender.com"
    
    # 1. Signup/Login to get token
    login_data = {
        "username": "render.test.user.123@example.com",
        "password": "somepassword123"
    }
    
    with httpx.Client(timeout=10.0) as client:
        r = client.post(f"{base_url}/api/v1/auth/login", data=login_data)
        if r.status_code != 200:
            print(f"Login failed: {r.status_code} {r.text}")
            return
        
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("--- Testing GET /api/v1/chat/threads ---")
        r_threads = client.get(f"{base_url}/api/v1/chat/threads", headers=headers)
        print(f"Status: {r_threads.status_code}")
        print(f"Body: {r_threads.text}\n")

if __name__ == "__main__":
    test_threads()
