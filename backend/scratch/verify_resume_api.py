import httpx
import asyncio
import re
import json
import sys

# Force UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_resume_api():
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # 1. Login to get JWT Token
    login_data = {
        "username": "jane.dev2@example.com",
        "password": "aetheria-local-dev"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        print("Logging in to Aetheria Local Instance...")
        res = await client.post(f"{base_url}/auth/login", data=login_data)
        if res.status_code != 200:
            print("Login failed! Please check if backend is running.")
            return
            
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create a new thread in professional mode
        thread_payload = {
            "title": "Resume Builder Live Test",
            "companion_id": "aria",
            "session_mode": "professional"
        }
        
        print("\nCreating thread in professional mode...")
        res = await client.post(f"{base_url}/chat/threads", json=thread_payload, headers=headers)
        if res.status_code != 201:
            print(f"Failed to create thread: {res.text}")
            return
            
        thread_id = res.json()["id"]
        print(f"Created chat thread ID: {thread_id}")
        
        # 3. Send step 1: Request resume (missing fields)
        print("\n--- Sending request: 'build my resume' ---")
        msg_payload_1 = {
            "content": "build my resume"
        }
        res = await client.post(f"{base_url}/chat/threads/{thread_id}/messages", json=msg_payload_1, headers=headers)
        if res.status_code != 200:
            print(f"Error sending message 1: {res.text}")
            return
            
        reply_1 = res.json()["content"]
        print("AI Reply:")
        print(reply_1)
        
        # Quick validation check on step 1 response
        if "📝 **[Resume Pipeline - Details Needed]**" in reply_1:
            print("✅ Step 1 Success: AI responded with details-needed template.")
        else:
            print("❌ Step 1 Failure: Unexpected AI response.")
            
        # 4. Send step 2: Complete the resume details form
        print("\n--- Sending complete details form ---")
        msg_payload_2 = {
            "content": (
                "Name : Sakshi chauhan\n"
                "contact: 746353\n"
                "education : MCA, UPES\n"
                "Experience : AI Engineer Expected 2026 Pursuing\n"
                "skills: Programming: Python, SQL"
            )
        }
        res = await client.post(f"{base_url}/chat/threads/{thread_id}/messages", json=msg_payload_2, headers=headers)
        if res.status_code != 200:
            print(f"Error sending message 2: {res.text}")
            return
            
        reply_2 = res.json()["content"]
        print("AI Reply:")
        print(reply_2)
        
        # Quick validation check on step 2 response
        if "📄 **[Resume Agent Active]**" in reply_2 and "resume_url:" in reply_2:
            print("✅ Step 2 Success: AI generated the resume and returned a download URL.")
            url_match = re.search(r"resume_url:\s*(https?://[^\s]+)", reply_2)
            if url_match:
                print(f"Verified Resume PDF URL: {url_match.group(1)}")
        else:
            print("❌ Step 2 Failure: Unexpected AI response or missing download link.")

if __name__ == "__main__":
    asyncio.run(test_resume_api())
