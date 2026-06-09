import httpx
import base64
import json
import asyncio

api_key = "c2Frc2hpY2hhdWhhbjY0NzcxQGdtYWlsLmNvbQ:6ks5KciXbJ82aMKXRRmkG"
auth_str = f"{api_key}:"
auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

headers = {
    "Authorization": f"Basic {auth_b64}",
    "Content-Type": "application/json",
    "accept": "application/json"
}

async def generate_and_poll():
    url = "https://api.d-id.com/clips"
    payload = {
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {
                "type": "microsoft",
                "voice_id": "hi-IN-SwaraNeural"
            },
            "input": "Namaste dosto, mera naam Sakshi hai aur D-ID clips work kar raha hai."
        },
        "presenter_id": "v2_public_lana@TtreMLgSnL",
        "config": {
            "result_format": "mp4"
        }
    }
    
    print("Sending request to POST /clips...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        print(f"Post Response Status: {response.status_code}")
        if response.status_code not in (200, 201):
            print(f"Error: {response.text}")
            return
            
        data = response.json()
        clip_id = data.get("id")
        print(f"Clip ID: {clip_id}, Status: {data.get('status')}")
        
        poll_url = f"https://api.d-id.com/clips/{clip_id}"
        print(f"Polling status from {poll_url}...")
        
        for i in range(25):
            await asyncio.sleep(3.0)
            poll_resp = await client.get(poll_url, headers=headers)
            if poll_resp.status_code == 200:
                poll_data = poll_resp.json()
                status = poll_data.get("status")
                print(f"Poll #{i+1} status: {status}")
                if status == "done":
                    print(f"Video generated successfully!")
                    print(f"Result URL: {poll_data.get('result_url')}")
                    return
                elif status == "failed":
                    print(f"Video generation failed: {poll_data}")
                    return
            else:
                print(f"Error polling: {poll_resp.status_code} - {poll_resp.text}")

if __name__ == "__main__":
    asyncio.run(generate_and_poll())
