import httpx
import urllib.parse
from typing import List, Dict, Any
from app.config import settings

class WebResearchService:
    @staticmethod
    async def needs_search(query: str) -> bool:
        """
        Determines if the query asks about real-time, current events, weather, or information
        that requires internet search.
        """
        # Lowercase trigger terms
        triggers = [
            "search", "google", "weather", "news", "current", "latest", "today",
            "yesterday", "price of", "stock", "time in", "live info", "recent"
        ]
        q_lower = query.lower()
        return any(term in q_lower for term in triggers)

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
        except Exception as e:
            print(f"News API call failed: {e}")
        return []

    @staticmethod
    async def perform_ddg_fallback_search(query: str) -> List[Dict[str, Any]]:
        """
        Scrapes DuckDuckGo HTML for search results without requiring keys.
        """
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    html = response.text
                    results = []
                    # Basic snippet parsing
                    parts = html.split('<div class="result__snippet">')
                    for i, part in enumerate(parts[1:4]):
                        snippet = part.split('</div>')[0].strip()
                        snippet = snippet.replace('<b>', '').replace('</b>', '').replace('&amp;', '&').replace('&#x27;', "'")
                        
                        title = f"Web Search Result {i+1}"
                        link = "#"
                        try:
                            link_part = parts[i].split('<a class="result__url" href="')
                            if len(link_part) > 1:
                                link = link_part[1].split('"')[0].strip()
                            title_part = parts[i].split('<a class="result__snippet"')[0].split('class="result__link">')
                            if len(title_part) > 1:
                                title = title_part[1].split('</a>')[0].replace('<b>','').replace('</b>','')
                        except Exception:
                            pass
                            
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "link": link
                        })
                    return results
        except Exception as e:
            print(f"DuckDuckGo fallback search failed: {e}")
        return []

    @staticmethod
    async def search_and_summarize(query: str) -> str:
        """
        Performs web search (News API, SerpAPI, Google Search, or DDG Scraper) and returns formatted search context.
        """
        results = []
        
        # 1. Routing to News API if news query is detected
        news_key = getattr(settings, "NEWS_API_KEY", None)
        if news_key and any(term in query.lower() for term in ["news", "latest", "headline"]):
            results = await WebResearchService.perform_news_search(query, news_key)
            
        # 2. Routing to SerpAPI
        if not results:
            serp_key = getattr(settings, "SERPAPI_API_KEY", None)
            if serp_key:
                results = await WebResearchService.perform_serp_search(query, serp_key)
                
        # 3. Routing to Google Custom Search API
        if not results:
            google_key = getattr(settings, "GOOGLE_API_KEY", None)
            cse_id = getattr(settings, "GOOGLE_CSE_ID", None)
            if google_key and cse_id:
                results = await WebResearchService.perform_google_search(query, google_key, cse_id)
                
        # 4. Fallback DuckDuckGo Scraping
        if not results:
            results = await WebResearchService.perform_ddg_fallback_search(query)
            
        if not results:
            return ""

        context_lines = [
            f"- [{r['title']}] {r['snippet']} (Source: {r['link']})"
            for r in results
        ]
        return (
            "\n[Injected Real-time Web Search Results]:\n" +
            "\n".join(context_lines)
        )

web_research_service = WebResearchService()
