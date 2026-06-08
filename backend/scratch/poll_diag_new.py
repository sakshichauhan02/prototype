import httpx
import time

def poll_new():
    url = "https://prototype-afow.onrender.com/api/v1/workflow/diag/db"
    print(f"Waiting for new code to be live on Render...")
    for i in range(30):
        try:
            r = httpx.get(url, timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                # If it's a list (old code), continue
                if isinstance(data, list):
                    print(f"[{i+1}/30] Old code still active. Waiting...")
                else:
                    print("New code is live! Result:")
                    print(r.text)
                    return
            else:
                print(f"[{i+1}/30] Status: {r.status_code}. Waiting...")
        except Exception as e:
            print(f"[{i+1}/30] Error: {e}. Waiting...")
        time.sleep(15)
    print("Timed out waiting for new code deployment.")

if __name__ == "__main__":
    poll_new()
