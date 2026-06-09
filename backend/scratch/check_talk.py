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

def check_talk():
    talk_id = "tlk_AIOX6D_moM2WIobWJa-No"
    url = f"https://api.d-id.com/talks/{talk_id}"
    response = httpx.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    check_talk()
