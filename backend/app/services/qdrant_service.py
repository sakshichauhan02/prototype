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
        
    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            if settings.QDRANT_URL:
                self._client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY
                )
            else:
                # Use local persistent storage
                os.makedirs(settings.QDRANT_PATH, exist_ok=True)
                self._client = QdrantClient(path=settings.QDRANT_PATH)
            
            self._ensure_collection()
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
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )

    async def generate_embedding(self, text: str) -> List[float]:
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
            return self._generate_hash_fallback_embedding(text)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "models/text-embedding-004",
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                response = await http_client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("embedding", {}).get("values", [])
                    if embedding:
                        return embedding
                print(f"Warning: Gemini Embedding API returned status {response.status_code}. Using hash fallback.")
        except Exception as e:
            print(f"Warning: Exception calling Gemini Embedding API: {e}. Using hash fallback.")
            
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

    async def delete_memory(self, memory_id: int):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[memory_id]
        )

    async def search_memories(self, user_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        vector = await self.generate_embedding(query)
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
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
        for hit in search_result:
            results.append({
                "id": hit.id,
                "fact": hit.payload.get("fact"),
                "category": hit.payload.get("category"),
                "score": hit.score
            })
        return results

qdrant_service = QdrantService()
