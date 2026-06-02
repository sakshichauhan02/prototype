from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.research import ResearchRequest, ResearchResponse
from app.services.web_research_service import web_research_service
from app.config import settings
import httpx

router = APIRouter()

@router.post("/query", response_model=ResearchResponse)
async def query_web_research(
    req: ResearchRequest,
    current_user: User = Depends(get_current_user)
):
    # Perform Search
    serp_key = getattr(settings, "SERPAPI_API_KEY", None)
    if serp_key:
        raw_sources = await web_research_service.perform_serp_search(req.query, serp_key)
    else:
        raw_sources = await web_research_service.perform_ddg_fallback_search(req.query)

    sources = [
        {"title": s["title"], "url": s["link"], "snippet": s["snippet"]}
        for s in raw_sources
    ]

    # Synthesize Summary using Gemini if key exists
    summary = ""
    takeaways = []
    if settings.GEMINI_API_KEY and raw_sources:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            snippets_txt = "\n".join([f"- [{s['title']}] {s['snippet']}" for s in raw_sources])
            prompt = (
                f"Based on the following search results for the query '{req.query}', write a concise, informative summary (max 3 sentences) "
                f"and provide 3 bullet point key takeaways. Respond only in valid JSON format:\n"
                f"{{\n"
                f"  \"summary\": \"Concise summary...\",\n"
                f"  \"takeaways\": [\"Takeaway 1\", \"Takeaway 2\", \"Takeaway 3\"]\n"
                f"}}\n\n"
                f"Search Results:\n{snippets_txt}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(url, json=payload)
                if r.status_code == 200:
                    import json
                    txt = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if txt.startswith("```json"):
                        txt = txt.split("```json")[1].split("```")[0].strip()
                    elif txt.startswith("```"):
                        txt = txt.split("```")[1].split("```")[0].strip()
                    data = json.loads(txt)
                    summary = data.get("summary", "")
                    takeaways = data.get("takeaways", [])
        except Exception as e:
            print(f"Failed to synthesize research report: {e}")

    # Fallback if no dynamic summary was generated
    if not summary:
        if raw_sources:
            summary = f"Gathered {len(raw_sources)} trusted sources regarding '{req.query}'."
            takeaways = [s["snippet"][:80] + "..." for s in raw_sources]
        else:
            summary = f"No search results retrieved for query '{req.query}'."
            takeaways = ["Please ensure internet connection is active.", "Double check search criteria."]

    return {
        "query": req.query,
        "summary": summary,
        "sources": sources,
        "key_takeaways": takeaways
    }
