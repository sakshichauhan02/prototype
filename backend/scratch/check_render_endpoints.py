import httpx
import json

def test_endpoints():
    base_url = "https://prototype-afow.onrender.com"
    
    print("--- Testing GET / ---")
    try:
        r = httpx.get(f"{base_url}/")
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text}\n")
    except Exception as e:
        print(f"Error: {e}\n")
        
    print("--- Testing POST /api/v1/auth/signup ---")
    signup_data = {
        "name": "Test Render User",
        "email": "render.test.user.123@example.com",
        "password": "somepassword123"
    }
    try:
        r = httpx.post(f"{base_url}/api/v1/auth/signup", json=signup_data)
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    print("--- Testing POST /api/v1/auth/login ---")
    login_data = {
        "username": "render.test.user.123@example.com",
        "password": "somepassword123"
    }
    try:
        r = httpx.post(f"{base_url}/api/v1/auth/login", data=login_data)
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text}\n")
    except Exception as e:
        print(f"Error: {e}\n")

if __name__ == "__main__":
    test_endpoints()
