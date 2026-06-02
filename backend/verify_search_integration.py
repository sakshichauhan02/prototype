import asyncio
import sys
import httpx
import urllib.parse
from app.config import settings

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def mask_key(key: str) -> str:
    if not key:
        return "<not set>"
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"

async def test_internet_dns():
    print("=== Testing Internet Connectivity & DNS ===")
    endpoints = ["https://www.google.com", "https://html.duckduckgo.com"]
    async with httpx.AsyncClient(timeout=5.0) as client:
        for ep in endpoints:
            try:
                r = await client.get(ep)
                print(f"✅ Successfully reached {ep} (Status: {r.status_code})")
            except Exception as e:
                print(f"❌ Failed to reach {ep}. Error: {e}")
    print()

async def test_google_custom_search():
    print("=== Testing Google Custom Search API ===")
    api_key = getattr(settings, "GOOGLE_API_KEY", "")
    cse_id = getattr(settings, "GOOGLE_CSE_ID", "")
    
    print(f"Configured GOOGLE_API_KEY: {mask_key(api_key)}")
    print(f"Configured GOOGLE_CSE_ID: {mask_key(cse_id)}")
    
    if not api_key or not cse_id:
        print("⚠️ Google Custom Search API is not fully configured (missing API key or CSE ID). Skipping active test.")
        print()
        return

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": "latest AI trends in 2026"
    }
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, params=params)
            print(f"Response Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                items = data.get("items", [])
                print(f"✅ Google Custom Search returned {len(items)} results:")
                for idx, item in enumerate(items[:3]):
                    print(f"  {idx+1}. [{item.get('title')}] - Link: {item.get('link')}")
            else:
                print(f"❌ Google Custom Search returned error. Body:")
                print(r.text)
    except Exception as e:
        print(f"❌ Google Custom Search request threw an exception: {e}")
    print()

async def test_serpapi():
    print("=== Testing SerpAPI Google Search ===")
    api_key = getattr(settings, "SERPAPI_API_KEY", "")
    
    print(f"Configured SERPAPI_API_KEY: {mask_key(api_key)}")
    
    if not api_key:
        print("⚠️ SerpAPI is not configured (missing SERPAPI_API_KEY). Skipping active test.")
        print()
        return

    url = "https://serpapi.com/search.json"
    params = {
        "q": "latest AI trends in 2026",
        "api_key": api_key,
        "engine": "google"
    }
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, params=params)
            print(f"Response Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                items = data.get("organic_results", [])
                print(f"✅ SerpAPI returned {len(items)} results:")
                for idx, item in enumerate(items[:3]):
                    print(f"  {idx+1}. [{item.get('title')}] - Link: {item.get('link')}")
            else:
                print(f"❌ SerpAPI returned error. Body:")
                print(r.text)
    except Exception as e:
        print(f"❌ SerpAPI request threw an exception: {e}")
    print()

async def test_newsapi():
    print("=== Testing News API ===")
    api_key = getattr(settings, "NEWS_API_KEY", "")
    
    print(f"Configured NEWS_API_KEY: {mask_key(api_key)}")
    
    if not api_key:
        print("⚠️ News API is not configured (missing NEWS_API_KEY). Skipping active test.")
        print()
        return

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "latest AI trends in 2026",
        "apiKey": api_key,
        "pageSize": 3
    }
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, params=params)
            print(f"Response Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                items = data.get("articles", [])
                print(f"✅ News API returned {len(items)} articles:")
                for idx, item in enumerate(items[:3]):
                    print(f"  {idx+1}. [{item.get('title')}] - Link: {item.get('url')}")
            else:
                print(f"❌ News API returned error. Body:")
                print(r.text)
    except Exception as e:
        print(f"❌ News API request threw an exception: {e}")
    print()

async def test_duckduckgo_fallback():
    print("=== Testing DuckDuckGo Fallback Scraper ===")
    from app.services.web_research_service import web_research_service
    
    try:
        results = await web_research_service.perform_ddg_fallback_search("latest AI trends in 2026")
        if results:
            print(f"✅ DuckDuckGo fallback returned {len(results)} results:")
            for idx, r in enumerate(results):
                print(f"  {idx+1}. [{r['title']}] - Link: {r['link']}")
        else:
            print("❌ DuckDuckGo fallback returned 0 results.")
    except Exception as e:
        print(f"❌ DuckDuckGo fallback search threw an exception: {e}")
    print()

async def main():
    print("Starting Web Research integration tests...")
    print(f"Settings Source Env File: {settings.Config.env_file}")
    print()
    await test_internet_dns()
    await test_google_custom_search()
    await test_serpapi()
    await test_newsapi()
    await test_duckduckgo_fallback()

if __name__ == "__main__":
    asyncio.run(main())
