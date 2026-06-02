import asyncio
import sys

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend to path
sys.path.append(".")

from app.services.web_research_service import web_research_service

async def main():
    query = "latest AI trends in 2026"
    print(f"Testing search_and_summarize for query: '{query}'")
    summary = await web_research_service.search_and_summarize(query)
    print("\nSummary Output:")
    print(summary)

if __name__ == "__main__":
    asyncio.run(main())
