import asyncio
import time
import httpx
import sys
import os
from jose import jwt
from datetime import datetime, timedelta

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure root folder is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# API Config
BASE_URL = "http://127.0.0.1:8000"
SECRET_KEY = "aetheria-super-secret-crypto-elliptic-quantum-key-2026"
ALGORITHM = "HS256"

def generate_token(user_id: int = 1) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def test_sync_engine():
    print("=== Testing Offline-to-Online Sync Engine ===")
    token = generate_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Generate mock timestamps
    base_time = datetime.utcnow()
    t1 = (base_time - timedelta(minutes=5)).isoformat() + "Z"
    t2 = (base_time - timedelta(minutes=4)).isoformat() + "Z"
    t3 = (base_time - timedelta(minutes=3)).isoformat() + "Z"
    t4 = (base_time - timedelta(minutes=2)).isoformat() + "Z"
    
    mock_thread_id = f"mock-thread-{int(time.time())}"
    mock_msg1_id = f"msg-user-{int(time.time())}"
    mock_msg2_id = f"msg-ai-{int(time.time())}"
    mock_mem_id = f"mock-mem-{int(time.time())}"
    
    # Construct bulk sync payload
    payload = {
        "mutations": [
            {
                "type": "CREATE_THREAD",
                "payload": {
                    "id": mock_thread_id,
                    "companionId": "aria",
                    "title": "Offline R&D Discussion"
                },
                "timestamp": t1
            },
            {
                "type": "SEND_MESSAGE",
                "payload": {
                    "id": mock_msg1_id,
                    "threadId": mock_thread_id,
                    "sender": "user",
                    "content": "I am designing a bulk synchronization protocol."
                },
                "timestamp": t2
            },
            {
                "type": "SEND_MESSAGE",
                "payload": {
                    "id": mock_msg2_id,
                    "threadId": mock_thread_id,
                    "sender": "ai",
                    "content": "That sounds highly efficient. Make sure to map frontend mock IDs."
                },
                "timestamp": t3
            },
            {
                "type": "ADD_MEMORY",
                "payload": {
                    "id": mock_mem_id,
                    "fact": "Designing a sync engine protocol in TS.",
                    "category": "Technical"
                },
                "timestamp": t4
            }
        ]
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Send sync payload
        print(f"\nSending {len(payload['mutations'])} offline mutations...")
        sync_resp = await client.post(
            f"{BASE_URL}/api/v1/chat/sync",
            headers=headers,
            json=payload
        )
        print(f"Sync API response status: {sync_resp.status_code}")
        print(f"Sync API body: {sync_resp.text}")
        
        assert sync_resp.status_code == 200, "Sync failed"
        sync_data = sync_resp.json()
        assert sync_data["status"] == "success"
        
        # 2. Verify that thread is created and messages are synced
        print("\nVerifying thread and messages in database...")
        threads_resp = await client.get(f"{BASE_URL}/api/v1/chat/threads", headers=headers)
        assert threads_resp.status_code == 200
        threads = threads_resp.json()
        
        synced_thread = None
        for t in threads:
            if t["title"] == "Offline R&D Discussion":
                synced_thread = t
                break
                
        assert synced_thread is not None, "Synced thread not found in DB"
        print(f"✅ Found synced thread: '{synced_thread['title']}' (ID: {synced_thread['id']})")
        
        # Verify messages
        msgs = synced_thread["messages"]
        assert len(msgs) == 2, f"Expected 2 messages, got {len(msgs)}"
        print("✅ Correctly synced both messages under the translated thread ID:")
        for m in msgs:
            print(f"  - [{m['sender']}]: '{m['content']}'")
            
        # 3. Test Deduplication (Send the exact same payload again)
        print("\nSending same sync payload again to test duplicate prevention...")
        sync_resp2 = await client.post(
            f"{BASE_URL}/api/v1/chat/sync",
            headers=headers,
            json=payload
        )
        assert sync_resp2.status_code == 200
        print(f"Resync body: {sync_resp2.json()}")
        
        # Pull thread again and verify messages count is still 2 (meaning no duplicates were added!)
        threads_resp2 = await client.get(f"{BASE_URL}/api/v1/chat/threads", headers=headers)
        threads2 = threads_resp2.json()
        synced_thread2 = next(t for t in threads2 if t["id"] == synced_thread["id"])
        msgs2 = synced_thread2["messages"]
        assert len(msgs2) == 2, f"Duplicate messages were created! Count: {len(msgs2)}"
        print("✅ Duplicate prevention verified: Resending mutations did not write duplicate records.")
        
        # 4. Test Conflict Resolution (Rename thread with older vs newer timestamp)
        print("\nTesting conflict resolution on RENAME_THREAD...")
        older_time = (base_time - timedelta(minutes=10)).isoformat() + "Z"
        newer_time = (base_time + timedelta(minutes=10)).isoformat() + "Z"
        
        # Older rename (should be ignored)
        print("Sending RENAME_THREAD with older timestamp (should be ignored)...")
        await client.post(
            f"{BASE_URL}/api/v1/chat/sync",
            headers=headers,
            json={"mutations": [{
                "type": "RENAME_THREAD",
                "payload": {"id": str(synced_thread["id"]), "title": "Stale Title"},
                "timestamp": older_time
            }]}
        )
        
        threads_resp3 = await client.get(f"{BASE_URL}/api/v1/chat/threads", headers=headers)
        title_stale = next(t["title"] for t in threads_resp3.json() if t["id"] == synced_thread["id"])
        assert title_stale == "Offline R&D Discussion", f"Stale title was applied: '{title_stale}'"
        print("✅ Conflict Resolution: Stale rename was correctly ignored.")
        
        # Newer rename (should be applied)
        print("Sending RENAME_THREAD with newer timestamp (should be applied)...")
        await client.post(
            f"{BASE_URL}/api/v1/chat/sync",
            headers=headers,
            json={"mutations": [{
                "type": "RENAME_THREAD",
                "payload": {"id": str(synced_thread["id"]), "title": "Synchronized R&D Discussion"},
                "timestamp": newer_time
            }]}
        )
        
        threads_resp4 = await client.get(f"{BASE_URL}/api/v1/chat/threads", headers=headers)
        title_new = next(t["title"] for t in threads_resp4.json() if t["id"] == synced_thread["id"])
        assert title_new == "Synchronized R&D Discussion", f"New title was not applied: '{title_new}'"
        print(f"✅ Conflict Resolution: Newer rename was successfully applied. Title is now '{title_new}'.")
        
        print("\nAll Sync Engine integration tests completed successfully! 🎉")

if __name__ == "__main__":
    asyncio.run(test_sync_engine())
