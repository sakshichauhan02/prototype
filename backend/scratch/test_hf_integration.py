import asyncio
import time
import os
import sys

# Ensure backend folder is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.qdrant_service import qdrant_service
from app.config import settings

async def main():
    print("=== Testing Hugging Face Embeddings & Qdrant ===")
    
    # 1. Test local fallback deterministic embedding
    print("\n--- Test Case 1: Local Fallback (384-dimensional) ---")
    text = "Jane Developer loves coding in Python and React."
    
    # Temporarily remove HF key if configured to force fallback
    original_key = settings.HUGGINGFACE_API_KEY
    settings.HUGGINGFACE_API_KEY = ""
    
    t0 = time.perf_counter()
    vector_fallback = await qdrant_service.generate_embedding(text)
    latency_fallback = time.perf_counter() - t0
    
    print(f"Fallback generation latency: {latency_fallback:.4f} seconds")
    print(f"Fallback vector length: {len(vector_fallback)} (Expected: 384)")
    print(f"First 5 values: {vector_fallback[:5]}")
    
    if len(vector_fallback) == 384:
        print("✅ Test Case 1 Passed: Deterministic fallback generated exactly 384 dimensions.")
    else:
        print("❌ Test Case 1 Failed: Fallback vector size is incorrect.")
        
    # Restore HF key
    settings.HUGGINGFACE_API_KEY = original_key

    # 2. Test Qdrant Collection automatic resize & recreation
    print("\n--- Test Case 2: Qdrant Upsert and Retrieval ---")
    user_id = 9999
    memory_id = 8888
    fact = "My favorite programming language is TypeScript."
    category = "Preferences"
    
    try:
        # Re-initialize client properties to trigger _ensure_collection size check
        qdrant_service._ensure_collection()
        print("Qdrant collection checks passed.")
        
        # Test upsert
        print("Upserting memory point...")
        await qdrant_service.upsert_memory(user_id, memory_id, fact, category)
        print("Memory upsert successful.")
        
        # Test search / retrieval
        print("Searching memories...")
        results = await qdrant_service.search_memories(user_id, "What is my favorite language?", limit=2)
        print(f"Search returned {len(results)} results:")
        for r in results:
            print(f"- [ID: {r['id']}, Category: {r['category']}, Score: {r['score']:.4f}] {r['fact']}")
            
        # Verify results contains the upserted fact
        if any(r['id'] == memory_id for r in results):
            print("✅ Test Case 2 Passed: Successfully stored and retrieved 384-dimensional memories.")
        else:
            print("❌ Test Case 2 Failed: Retrieved list does not contain stored memory.")
            
        # Clean up
        await qdrant_service.delete_memory(memory_id)
        print("Cleaned up memory point.")
        
    except Exception as e:
        print(f"❌ Test Case 2 Failed with Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
