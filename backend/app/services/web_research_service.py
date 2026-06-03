import httpx
import urllib.parse
from typing import List, Dict, Any
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from app.config import settings

class WebResearchService:
    @staticmethod
    async def needs_search(query: str) -> bool:
        """
        Determines if the query asks about real-time, current events, weather, or information
        that requires internet search.
        """
        triggers = [
            "search", "google", "weather", "news", "current", "latest", "today",
            "yesterday", "price of", "stock", "time in", "live info", "recent"
        ]
        q_lower = query.lower()
        return any(term in q_lower for term in triggers)

    @staticmethod
    async def perform_ddg_search(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Runs a web search using the official duckduckgo_search library.
        Returns a list of structured search results: title, snippet, link.
        """
        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))

        try:
            import asyncio
            raw_results = await asyncio.to_thread(_search)
            results = []
            for r in raw_results:
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "link": r.get("href", "")
                })
            return results
        except Exception as e:
            print(f"Warning: DuckDuckGo search library failed: {e}. Falling back to fallback scraping.")
            # Fallback scraping logic
            return await WebResearchService.perform_ddg_fallback_scraping(query)

    @staticmethod
    async def perform_ddg_fallback_scraping(query: str) -> List[Dict[str, Any]]:
        """
        Scrapes DuckDuckGo HTML for search results without requiring keys (fallback scrap).
        """
        import re
        import html
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    html_text = response.text
                    parts = html_text.split('result__body')
                    results = []
                    for part in parts[1:]:
                        link = "#"
                        link_match = re.search(r'href=["\'](?:https?:)?//duckduckgo\.com/l/\?uddg=([^&"\']+)', part)
                        if link_match:
                            link = urllib.parse.unquote(link_match.group(1))
                            
                        if "duckduckgo.com/y.js" in link or "ad_domain" in link or link == "#":
                            continue
                            
                        title = f"Web Search Result {len(results) + 1}"
                        title_match = re.search(r'class="result__a"[^>]*>(.*?)</a>', part, re.DOTALL)
                        if title_match:
                            title = title_match.group(1)
                            title = re.sub(r'<[^>]+>', '', title)
                            title = html.unescape(title).strip()
                            
                        snippet = ""
                        snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', part, re.DOTALL)
                        if snippet_match:
                            snippet = snippet_match.group(1)
                            snippet = re.sub(r'<[^>]+>', '', snippet)
                            snippet = html.unescape(snippet).strip()
                            
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "link": link
                        })
                        if len(results) >= 3:
                            break
                    return results
        except Exception as e:
            print(f"DuckDuckGo fallback scraping failed: {e}")
        return []

    # Re-implemented actual API search logic for SerpAPI, Google Search, and News API
    @staticmethod
    async def perform_serp_search(query: str, api_key: str) -> List[Dict[str, Any]]:
        """
        Runs a search on SerpAPI using the configured key.
        """
        url = "https://serpapi.com/search.json"
        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google"
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for item in data.get("organic_results", [])[:3]:
                        results.append({
                            "title": item.get("title"),
                            "snippet": item.get("snippet"),
                            "link": item.get("link")
                        })
                    return results
                else:
                    print(f"SerpAPI query failed with status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"SerpAPI call failed: {e}")
        return []

    @staticmethod
    async def perform_google_search(query: str, api_key: str, cse_id: str) -> List[Dict[str, Any]]:
        """
        Runs a search on Google Custom Search API.
        """
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for item in data.get("items", [])[:3]:
                        results.append({
                            "title": item.get("title"),
                            "snippet": item.get("snippet"),
                            "link": item.get("link")
                        })
                    return results
                else:
                    print(f"Google Custom Search API failed with status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Google Custom Search API call failed: {e}")
        return []

    @staticmethod
    async def perform_news_search(query: str, api_key: str) -> List[Dict[str, Any]]:
        """
        Runs a search on News API.
        """
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": api_key,
            "pageSize": 3
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for item in data.get("articles", [])[:3]:
                        results.append({
                            "title": item.get("title"),
                            "snippet": item.get("description"),
                            "link": item.get("url")
                        })
                    return results
                else:
                    print(f"News API query failed with status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"News API call failed: {e}")
        return []

    @staticmethod
    async def perform_ddg_fallback_search(query: str) -> List[Dict[str, Any]]:
        """
        Fallback search method that tries DuckDuckGo library, then other available APIs, then DDG scraping.
        """
        results = await WebResearchService.perform_ddg_search(query)
        if not results:
            # Try Google Custom Search if configured
            google_key = getattr(settings, "GOOGLE_API_KEY", None)
            cse_id = getattr(settings, "GOOGLE_CSE_ID", None)
            if google_key and google_key.strip() and cse_id and cse_id.strip():
                results = await WebResearchService.perform_google_search(query, google_key, cse_id)
        if not results:
            # Try News API if configured
            news_key = getattr(settings, "NEWS_API_KEY", None)
            if news_key and news_key.strip():
                results = await WebResearchService.perform_news_search(query, news_key)
        if not results:
            # Try DuckDuckGo scraping
            results = await WebResearchService.perform_ddg_fallback_scraping(query)
        return results

    @staticmethod
    async def search_and_summarize(query: str) -> str:
        """
        Performs web search using DuckDuckGo search library as the primary provider,
        and falls back to SerpAPI, Google Custom Search, News API, or DuckDuckGo scraping.
        Generates a clean, concise summary of the findings using Groq API before sending it to the LLM.
        """
        results = []
        
        # 1. Try DuckDuckGo search (library, which internally tries fallback scraping on exception)
        try:
            results = await WebResearchService.perform_ddg_search(query, max_results=3)
        except Exception as e:
            print(f"DuckDuckGo search attempt failed with exception: {e}")
            
        # 2. If DDG results are empty, try SerpAPI
        if not results:
            serp_key = getattr(settings, "SERPAPI_API_KEY", None)
            if serp_key and serp_key.strip():
                print("DuckDuckGo failed/empty; trying SerpAPI...")
                results = await WebResearchService.perform_serp_search(query, serp_key)
                
        # 3. If SerpAPI results are empty, try Google Custom Search
        if not results:
            google_key = getattr(settings, "GOOGLE_API_KEY", None)
            cse_id = getattr(settings, "GOOGLE_CSE_ID", None)
            if google_key and google_key.strip() and cse_id and cse_id.strip():
                print("DuckDuckGo/SerpAPI failed/empty; trying Google Custom Search...")
                results = await WebResearchService.perform_google_search(query, google_key, cse_id)

        # 4. If Google Search results are empty and it's a news-like query, try News API
        if not results:
            news_key = getattr(settings, "NEWS_API_KEY", None)
            if news_key and news_key.strip() and any(term in query.lower() for term in ["news", "latest", "headline"]):
                print("DuckDuckGo/SerpAPI/Google failed/empty; trying News API...")
                results = await WebResearchService.perform_news_search(query, news_key)
                
        # 5. If still empty, try DuckDuckGo fallback scraping
        if not results:
            results = await WebResearchService.perform_ddg_fallback_scraping(query)

        if not results:
            return ""

        sources_text = "\n".join([
            f"- [{r['title']}] {r['snippet']} (Source: {r['link']})"
            for r in results
        ])

        summary = ""
        # Summarize search results using Groq LLM before sending to chat companion
        if settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip():
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.GROQ_API_KEY}"
            }
            prompt = (
                f"You are a research assistant compiling a fact report for the user's query: '{query}'.\n"
                f"Using the following real-time search results, write a concise, objective summary (max 4 sentences) "
                f"answering the query. Highlight key details. Do not include introductory/concluding remarks.\n\n"
                f"Search Results:\n{sources_text}"
            )
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 512
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0]:
                            summary = choices[0]["message"].get("content", "").strip()
            except Exception as e:
                print(f"Warning: Exception calling Groq for search summarization: {e}")

        # Fallback if no dynamic summary was generated
        if not summary:
            summary = f"Gathered search results regarding '{query}':\n" + sources_text

        return (
            f"\n[Injected Real-time Web Search Results & Summary]:\n"
            f"{summary}\n\n"
            f"[Sources Referenced]:\n{sources_text}"
        )

web_research_service = WebResearchService()
