import httpx
import base64
import json

api_key = "c2Frc2hpY2hhdWhhbjY0NzcxQGdtYWlsLmNvbQ:6ks5KciXbJ82aMKXRRmkG"
auth_str = f"{api_key}:"
auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

headers = {
    "Authorization": f"Basic {auth_b64}",
    "Content-Type": "application/json",
    "accept": "application/json"
}

def list_all_presenters():
    url = "https://api.d-id.com/clips/presenters"
    response = httpx.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        presenters = data.get("presenters", [])
        print(f"Total presenters found: {len(presenters)}")
        for p in presenters:
            print(f"Name: {p.get('name')}, ID: {p.get('presenter_id')}, Gender: {p.get('gender')}, Image: {p.get('image_url')}")
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    list_all_presenters()
