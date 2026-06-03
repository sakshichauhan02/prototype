import asyncio
import os
import sys

# Ensure backend folder is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.web_research_service import web_research_service

async def main():
    print("=== Testing DuckDuckGo Search Library & Groq Summarization ===")
    
    query = "SpaceX Starship"
    print(f"\nQuery: '{query}'")
    
    # 1. Test raw structured search results
    print("\n--- Test Case 1: Structured Search Results ---")
    results = await web_research_service.perform_ddg_search(query, max_results=3)
    print(f"Retrieved {len(results)} results:")
    for i, r in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Title: {r['title']}")
        print(f"Link:  {r['link']}")
        print(f"Snippet: {r['snippet'][:120]}...")
        
    if len(results) > 0 and all(k in results[0] for k in ["title", "snippet", "link"]):
        print("\n✅ Test Case 1 Passed: Structured DDG search returns conforming objects.")
    else:
        print("\n❌ Test Case 1 Failed.")
        
    # 2. Test summarization context
    print("\n--- Test Case 2: Summarized Search Context ---")
    context = await web_research_service.search_and_summarize(query)
    print("\nGenerated Search Context Output:\n", context)
    
    if "[Injected Real-time Web Search Results & Summary]" in context and "[Sources Referenced]" in context:
        print("\n✅ Test Case 2 Passed: Successfully structured and summarized search context.")
    else:
        print("\n❌ Test Case 2 Failed.")

if __name__ == "__main__":
    asyncio.run(main())
