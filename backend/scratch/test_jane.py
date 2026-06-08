import httpx

def test_jane_signup():
    base_url = "https://prototype-afow.onrender.com"
    signup_data = {
        "name": "Jane Developer",
        "email": "jane.dev2@example.com",
        "password": "aetheria-local-dev"
    }
    
    with httpx.Client(timeout=10.0) as client:
        print("--- Testing signup jane.dev2@example.com ---")
        r = client.post(f"{base_url}/api/v1/auth/signup", json=signup_data)
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text}\n")
        
        print("--- Testing login jane.dev2@example.com ---")
        login_data = {
            "username": "jane.dev2@example.com",
            "password": "aetheria-local-dev"
        }
        r_login = client.post(f"{base_url}/api/v1/auth/login", data=login_data)
        print(f"Status: {r_login.status_code}")
        print(f"Body: {r_login.text}\n")

if __name__ == "__main__":
    test_jane_signup()
