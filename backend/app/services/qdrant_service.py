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
        """
        Generates 768-dimensional embeddings. Uses a fast local deterministic hash-based embedding
        fallback to completely save precious Google Gemini API key quota limits.
        """
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

qdrant_service = QdrantService()
