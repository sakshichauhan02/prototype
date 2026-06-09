import httpx
import base64
import json
import asyncio
import time

api_key = "c2Frc2hpY2hhdWhhbjY0NzcxQGdtYWlsLmNvbQ:6ks5KciXbJ82aMKXRRmkG"
auth_str = f"{api_key}:"
auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

headers = {
    "Authorization": f"Basic {auth_b64}",
    "Content-Type": "application/json",
    "accept": "application/json"
}

async def generate_and_poll_talk():
    url = "https://api.d-id.com/talks"
    payload = {
        "source_url": "https://picsum.photos/id/64/500/500.jpg",
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {
                "type": "microsoft",
                "voice_id": "hi-IN-SwaraNeural"
            },
            "input": "Namaste Sakshi, aapka talking avatar ab ready hai."
        },
        "config": {
            "fluent": "false",
            "pad_audio": "0.0"
        }
    }
    
    print("Sending request to POST /talks...")
    start_time = time.time()
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        print(f"Post Response Status: {response.status_code}")
        if response.status_code not in (200, 201):
            print(f"Error: {response.text}")
            return
            
        data = response.json()
        talk_id = data.get("id")
        print(f"Talk ID: {talk_id}, Status: {data.get('status')}")
        
        poll_url = f"https://api.d-id.com/talks/{talk_id}"
        print(f"Polling status from {poll_url}...")
        
        # Poll for 80 times with 3.0s interval (240 seconds total)
        for i in range(80):
            await asyncio.sleep(3.0)
            poll_resp = await client.get(poll_url, headers=headers)
            if poll_resp.status_code == 200:
                poll_data = poll_resp.json()
                status = poll_data.get("status")
                elapsed = time.time() - start_time
                print(f"Poll #{i+1} ({elapsed:.1f}s) status: {status}")
                if status == "done":
                    print(f"Video generated successfully in {elapsed:.1f} seconds!")
                    print(f"Result URL: {poll_data.get('result_url')}")
                    return
                elif status == "failed":
                    print(f"Video generation failed: {poll_data}")
                    return
            else:
                print(f"Error polling: {poll_resp.status_code} - {poll_resp.text}")

if __name__ == "__main__":
    asyncio.run(generate_and_poll_talk())
