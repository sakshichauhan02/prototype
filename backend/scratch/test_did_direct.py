import httpx
import base64
import json
import sys

api_key = "c2Frc2hpY2hhdWhhbjY0NzcxQGdtYWlsLmNvbQ:6ks5KciXbJ82aMKXRRmkG"
auth_str = f"{api_key}:"
auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

headers = {
    "Authorization": f"Basic {auth_b64}",
    "Content-Type": "application/json",
    "accept": "application/json"
}

def check_presenters():
    url = "https://api.d-id.com/clips/presenters"
    print("Testing GET /clips/presenters...")
    try:
        response = httpx.get(url, headers=headers, timeout=15.0)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Presenters list retrieved successfully!")
            presenters = data.get("presenters", [])
            for p in presenters[:5]:
                print(f"- {p.get('name')} ID: {p.get('presenter_id')} (Gender: {p.get('gender')})")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def create_talk_test():
    url = "https://api.d-id.com/talks"
    print("\nTesting POST /talks...")
    payload = {
        "source_url": "https://picsum.photos/id/64/500/500.jpg",
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {
                "type": "microsoft",
                "voice_id": "en-US-JennyNeural"
            },
            "input": "This is a direct test of the D-ID talks API."
        },
        "config": {
            "fluent": "false",
            "pad_audio": "0.0"
        }
    }
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=15.0)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_presenters()
    create_talk_test()
