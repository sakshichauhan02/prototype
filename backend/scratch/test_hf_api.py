import httpx
import asyncio
import sys

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_model(model_id):
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    print(f"\n=== Testing Model: {model_id} ===")
    
    payloads = [
        {"inputs": "Hello world"},
        {"inputs": ["Hello world"]}
    ]
    
    for payload in payloads:
        print(f"Payload: {payload}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # We can call without auth key first to see if public endpoints work
                response = await client.post(url, json=payload)
                print("Status code:", response.status_code)
                if response.status_code == 200:
                    data = response.json()
                    # Print types and dimensions
                    if isinstance(data, list):
                        print("Returned a list of length:", len(data))
                        if len(data) > 0:
                            print("Type of first element:", type(data[0]))
                            if isinstance(data[0], list):
                                print("Length of first element:", len(data[0]))
                                if len(data[0]) > 0 and isinstance(data[0][0], list):
                                    print("Length of first-first element:", len(data[0][0]))
                                    print("First 3 nested values:", data[0][0][:3])
                                else:
                                    print("First 3 nested values:", data[0][:3])
                            else:
                                print("First 3 values:", data[:3])
                    else:
                        print("Returned non-list data:", type(data))
                else:
                    print("Error:", response.text)
        except Exception as e:
            print("Exception:", e)

async def main():
    await test_model("sentence-transformers/all-MiniLM-L6-v2")
    await test_model("BAAI/bge-small-en-v1.5")

if __name__ == "__main__":
    asyncio.run(main())
