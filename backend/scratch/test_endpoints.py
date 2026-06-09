import httpx
import asyncio

async def test_endpoint(url):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            print(f"URL: {url}")
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("-> Success!")
                return True
            else:
                print(f"-> Failed with body: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    return False

async def main():
    urls = [
        "https://image.pollinations.ai/prompt/a+cat",
        "https://image.pollinations.ai/prompt/a-cat?model=flux",
        "https://image.pollinations.ai/prompt/a-cat?model=turbo",
        "https://image.pollinations.ai/prompt/a-cat?nologo=true",
        "https://gen.pollinations.ai/image/a+cat",
        "https://gen.pollinations.ai/image/a-cat?model=flux",
    ]
    for url in urls:
        await test_endpoint(url)
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
