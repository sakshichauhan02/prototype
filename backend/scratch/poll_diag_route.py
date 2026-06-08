import httpx
import time

def poll_route():
    url = "https://prototype-afow.onrender.com/api/v1/workflow/diag/db"
    print(f"Polling diagnostic route: {url}")
    for i in range(15):
        try:
            r = httpx.get(url, timeout=5.0)
            if r.status_code == 200:
                print("Deploy is live! Diagnostic data:")
                print(r.text)
                return
            else:
                print(f"[{i+1}/15] Status: {r.status_code}. Waiting for deploy...")
        except Exception as e:
            print(f"[{i+1}/15] Error: {e}. Waiting for deploy...")
        time.sleep(10)
    print("Polling timed out.")

if __name__ == "__main__":
    poll_route()
