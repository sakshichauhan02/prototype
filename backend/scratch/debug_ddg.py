from duckduckgo_search import DDGS
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("DDGS Import successful.")
import asyncio

from duckduckgo_search import AsyncDDGS
import asyncio

async def test():
    async with AsyncDDGS() as ddgs:
        res = [r for r in await ddgs.text("SpaceX Starship", max_results=3)]
    print("Search results inside AsyncDDGS:")
    print(res)

asyncio.run(test())
