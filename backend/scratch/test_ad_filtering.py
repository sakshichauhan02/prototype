import asyncio
import sys
import httpx
import urllib.parse
import re
import html

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_ad_filtering():
    query = "latest AI trends in 2026"
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(url, headers=headers)
        html_text = response.text
        
        parts = html_text.split('result__body')
        print(f"Total blocks found: {len(parts) - 1}")
        
        results = []
        for idx, part in enumerate(parts[1:]):
            link = "#"
            # Extract Link
            link_match = re.search(r'href=["\'](?:https?:)?//duckduckgo\.com/l/\?uddg=([^&"\']+)', part)
            if link_match:
                link = urllib.parse.unquote(link_match.group(1))
            
            # Ad checking
            is_ad = False
            if "duckduckgo.com/y.js" in link or "ad_domain" in link or link == "#":
                is_ad = True
                
            # Extract Title
            title = ""
            title_match = re.search(r'class="result__a"[^>]*>(.*?)</a>', part, re.DOTALL)
            if title_match:
                title = title_match.group(1)
                title = re.sub(r'<[^>]+>', '', title)
                title = html.unescape(title).strip()
                
            # Extract Snippet
            snippet = ""
            snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', part, re.DOTALL)
            if snippet_match:
                snippet = snippet_match.group(1)
                snippet = re.sub(r'<[^>]+>', '', snippet)
                snippet = html.unescape(snippet).strip()
                
            status = "AD (Skipped)" if is_ad else "ORGANIC"
            print(f"Block {idx+1}: {status}")
            print(f"  Title: {title}")
            print(f"  Link:  {link}")
            print(f"  Snippet: {snippet[:100]}...")
            
            if not is_ad:
                results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })
                if len(results) >= 3:
                    print("Reached 3 organic results, stopping.")
                    break
        
        print("\n=== Final Organic Results ===")
        for idx, r in enumerate(results):
            print(f"{idx+1}. [{r['title']}] - Source: {r['link']}")

if __name__ == "__main__":
    asyncio.run(test_ad_filtering())
