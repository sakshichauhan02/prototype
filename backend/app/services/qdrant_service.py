import os
import httpx
import hashlib
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.config import settings

class QdrantService:
    def __init__(self):
        self._client = None
        self.collection_name = "user_memories"
        self._qdrant_available = True
        
    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            try:
                if settings.QDRANT_URL and settings.QDRANT_URL.strip():
                    # Use remote Qdrant Cloud instance
                    self._client = QdrantClient(
                        url=settings.QDRANT_URL,
                        api_key=settings.QDRANT_API_KEY
                    )
                else:
                    # Attempt local persistent storage, fallback to in-memory
                    try:
                        os.makedirs(settings.QDRANT_PATH, exist_ok=True)
                        self._client = QdrantClient(path=settings.QDRANT_PATH)
                    except Exception as path_err:
                        print(f"Qdrant local path failed ({path_err}), falling back to in-memory mode.")
                        self._client = QdrantClient(location=":memory:")
                
                self._ensure_collection()
                self._qdrant_available = True
            except Exception as e:
                print(f"Qdrant client initialization failed: {e}. Vector search disabled.")
                self._qdrant_available = False
                self._client = QdrantClient(location=":memory:")
                try:
                    self._ensure_collection()
                except Exception:
                    pass
        return self._client
        
    def _ensure_collection(self):
        try:
            if not self._client.collection_exists(self.collection_name):
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
        except Exception:
            # Fallback safe creation
            try:
                self._client.get_collection(self.collection_name)
            except Exception:
                try:
                    self._client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                    )
                except Exception as e:
                    print(f"Could not create Qdrant collection: {e}")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates 768-dimensional embeddings using the Google Gemini embedding model API
        if GEMINI_API_KEY is configured. Falls back to a deterministic local hash-based embedding.
        """
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": "models/text-embedding-004",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        embedding = data.get("embedding", {}).get("values", [])
                        if len(embedding) == 768:
                            return embedding
                        else:
                            print(f"Warning: Gemini embedding returned vector size {len(embedding)} instead of 768. Trying fallback model.")
                    else:
                        print(f"Warning: Gemini embedding API returned status {response.status_code}. Trying fallback model.")
            except Exception as e:
                print(f"Warning: Exception calling Gemini embedding API: {e}. Trying fallback model.")

            # Fallback to embedding-001
            url_fallback = f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={settings.GEMINI_API_KEY}"
            payload_fallback = {
                "model": "models/embedding-001",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url_fallback, json=payload_fallback, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        embedding = data.get("embedding", {}).get("values", [])
                        if len(embedding) == 768:
                            return embedding
            except Exception as e:
                print(f"Warning: Exception calling fallback embedding-001: {e}")

        return self._generate_hash_fallback_embedding(text)

    def _generate_hash_fallback_embedding(self, text: str) -> List[float]:
        # Trivial deterministic float generation for local offline mode
        h = hashlib.sha256(text.encode('utf-8')).digest()
        embedding = []
        for i in range(768):
            val = ((h[i % 32] * (i + 1)) % 1000) / 1000.0
            # Normalize around 0
            embedding.append(val - 0.5)
        return embedding

    async def upsert_memory(self, user_id: int, memory_id: int, fact: str, category: str):
        try:
            vector = await self.generate_embedding(fact)
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=memory_id,
                        vector=vector,
                        payload={
                            "user_id": user_id,
                            "fact": fact,
                            "category": category
                        }
                    )
                ]
            )
        except Exception as e:
            print(f"Qdrant upsert_memory failed (non-fatal): {e}")

    async def delete_memory(self, memory_id: int):
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[memory_id]
            )
        except Exception as e:
            print(f"Qdrant delete_memory failed (non-fatal): {e}")

    async def search_memories(self, user_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            vector = await self.generate_embedding(query)
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=limit
            )
            
            results = []
            for hit in search_result.points:
                results.append({
                    "id": hit.id,
                    "fact": hit.payload.get("fact"),
                    "category": hit.payload.get("category"),
                    "score": hit.score
                })
            return results
        except Exception as e:
            print(f"Qdrant search_memories failed (non-fatal): {e}")
            return []

qdrant_service = QdrantService()
