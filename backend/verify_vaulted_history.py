import asyncio
import httpx
import sys

async def verify_vaulted_history():
    print("====================================================")
    print("RUNNING VAULTED HISTORY PROTECTION END-TO-END TESTS")
    print("====================================================\n")

    base_url = "http://127.0.0.1:8000/api/v1"
    
    # 1. Login Dev User
    print("Step 1: Logging in Dev User...")
    async with httpx.AsyncClient(timeout=45.0) as client:
        login_res = await client.post(
            f"{base_url}/auth/login",
            data={"username": "jane.dev2@example.com", "password": "aetheria-local-dev"}
        )
        if login_res.status_code != 200:
            # Try signing up first if user doesn't exist
            print("Login failed, attempting signup...")
            signup_res = await client.post(
                f"{base_url}/auth/signup",
                json={"name": "Jane Developer", "email": "jane.dev2@example.com", "password": "aetheria-local-dev"}
            )
            assert signup_res.status_code == 200, f"Signup failed: {signup_res.text}"
            login_res = await client.post(
                f"{base_url}/auth/login",
                data={"username": "jane.dev2@example.com", "password": "aetheria-local-dev"}
            )
            
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful!\n")

        # 2. Get initial memories count
        mem_res = await client.get(f"{base_url}/memory", headers=headers)
        assert mem_res.status_code == 200
        initial_memories = mem_res.json()
        initial_count = len(initial_memories)
        print(f"Initial long-term memories count: {initial_count}")

        # 3. Create a Personal Companion Thread
        print("\nStep 2: Creating a 'personal_companion' thread...")
        thread_res = await client.post(
            f"{base_url}/chat/threads",
            headers=headers,
            json={"title": "Personal Vault Test", "companion_id": "aria", "session_mode": "personal_companion"}
        )
        assert thread_res.status_code == 201, f"Failed to create thread: {thread_res.text}"
        thread_id = thread_res.json()["id"]
        print(f"Thread created! ID: {thread_id}, Mode: {thread_res.json()['session_mode']}")

        # 4. Send "My favorite color is pink"
        print("\nStep 3: Sending 'My favorite color is pink' to Personal Companion thread...")
        msg1_res = await client.post(
            f"{base_url}/chat/threads/{thread_id}/messages",
            headers=headers,
            json={"content": "My favorite color is pink"}
        )
        assert msg1_res.status_code == 200, f"Message 1 failed: {msg1_res.text}"
        msg1_id = msg1_res.json()["id"]
        print(f"Message 1 persisted in SQL chat_history! Message ID: {msg1_id}")
        print(f"Aria Reply: {msg1_res.json()['content'][:100]}...")

        # 5. Wait a moment for background task (which shouldn't run anyway)
        await asyncio.sleep(2)

        # 6. Verify memories count did NOT increase
        mem_res2 = await client.get(f"{base_url}/memory", headers=headers)
        assert mem_res2.status_code == 200
        memories2 = mem_res2.json()
        print(f"Post-message long-term memories count: {len(memories2)} (Expected: {initial_count})")
        
        # Verify no memory contains the word "pink"
        pink_memories = [m for m in memories2 if "pink" in str(m.get("fact", "")).lower()]
        assert len(pink_memories) == 0, f"Error: Memory about 'pink' was extracted! {pink_memories}"
        print("Success: Memory extraction was completely blocked!")

        # 7. Ask "What is my favorite color?" in SAME thread
        print("\nStep 4: Asking 'What is my favorite color?' in the SAME Personal Companion thread...")
        msg2_res = await client.post(
            f"{base_url}/chat/threads/{thread_id}/messages",
            headers=headers,
            json={"content": "What is my favorite color?"}
        )
        assert msg2_res.status_code == 200, f"Message 2 failed: {msg2_res.text}"
        aria_reply2 = msg2_res.json()["content"]
        print(f"Aria Reply (Same Thread): {aria_reply2}")
        
        # In the same thread, she should recall it from the active thread messages list (SQL history)
        assert "pink" in aria_reply2.lower(), "Aria failed to remember favorite color from chat history!"
        print("Success: Aria recalled favorite color from conversation history!")

        # 8. Create a DIFFERENT Professional Thread
        print("\nStep 5: Creating a different 'professional' thread...")
        thread_res2 = await client.post(
            f"{base_url}/chat/threads",
            headers=headers,
            json={"title": "Professional RAG Test", "companion_id": "aria", "session_mode": "professional"}
        )
        assert thread_res2.status_code == 201
        thread_id2 = thread_res2.json()["id"]
        print(f"Professional thread created! ID: {thread_id2}")

        # 9. Ask "What is my favorite color?" in the DIFFERENT thread
        print("\nStep 6: Asking 'What is my favorite color?' in the Professional thread (should NOT know)...")
        msg3_res = await client.post(
            f"{base_url}/chat/threads/{thread_id2}/messages",
            headers=headers,
            json={"content": "What is my favorite color?"}
        )
        assert msg3_res.status_code == 200
        aria_reply3 = msg3_res.json()["content"]
        print(f"Aria Reply (Different Thread): {aria_reply3}")
        
        # In a different thread, since memory database extraction was blocked, she should NOT know it
        assert "pink" not in aria_reply3.lower(), "Aria incorrectly remembered favorite color via long-term memory!"
        print("Success: Aria did NOT know the color in the professional thread because memory extraction was blocked!")

        print("\n=== ALL VAULTED HISTORY PROTECTION TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(verify_vaulted_history())
