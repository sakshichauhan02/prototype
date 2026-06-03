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
            recreate = False
            if self._client.collection_exists(self.collection_name):
                try:
                    info = self._client.get_collection(self.collection_name)
                    current_size = info.config.params.vectors.size
                    if current_size != 384:
                        print(f"Qdrant collection size mismatch ({current_size} vs 384). Recreating collection.")
                        self._client.delete_collection(self.collection_name)
                        recreate = True
                except Exception as get_err:
                    print(f"Error checking collection config: {get_err}. Attempting delete and recreate.")
                    try:
                        self._client.delete_collection(self.collection_name)
                    except Exception:
                        pass
                    recreate = True
            else:
                recreate = True

            if recreate:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
        except Exception as e:
            # Fallback safe creation
            try:
                self._client.get_collection(self.collection_name)
            except Exception:
                try:
                    self._client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                    )
                except Exception as create_err:
                    print(f"Could not create Qdrant collection: {create_err}")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates 384-dimensional embeddings using the Hugging Face Inference API
        (sentence-transformers/all-MiniLM-L6-v2) if configured. Falls back to a deterministic local hash-based embedding.
        """
        hf_key = getattr(settings, "HUGGINGFACE_API_KEY", "")
        
        # Check if key is present
        if hf_key and hf_key.strip():
            url = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {hf_key}"
            }
            payload = {"inputs": text}
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        # Hugging Face Feature Extraction response can be:
                        # - a 1D list of floats: [0.1, 0.2, ...]
                        # - a 2D list of floats: [[0.1, 0.2, ...]]
                        if isinstance(data, list) and len(data) > 0:
                            embedding = data[0] if isinstance(data[0], list) else data
                            if len(embedding) == 384:
                                return embedding
                            else:
                                print(f"Warning: Hugging Face embedding returned size {len(embedding)} instead of 384. Trying fallback model BAAI/bge-small-en-v1.5.")
                        else:
                            print(f"Warning: Hugging Face API returned unexpected data structure. Trying fallback model BAAI/bge-small-en-v1.5.")
                    else:
                        print(f"Warning: Hugging Face API returned status {response.status_code}. Trying fallback model BAAI/bge-small-en-v1.5.")
            except Exception as e:
                print(f"Warning: Exception calling Hugging Face all-MiniLM-L6-v2 API: {e}. Trying fallback model BAAI/bge-small-en-v1.5.")

            # Fallback model: BAAI/bge-small-en-v1.5
            url_fallback = "https://api-inference.huggingface.co/models/BAAI/bge-small-en-v1.5"
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url_fallback, json=payload, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            embedding = data[0] if isinstance(data[0], list) else data
                            if len(embedding) == 384:
                                return embedding
            except Exception as e:
                print(f"Warning: Exception calling fallback BAAI/bge-small-en-v1.5: {e}")

        # Default local fallback
        return self._generate_hash_fallback_embedding(text)

    def _generate_hash_fallback_embedding(self, text: str) -> List[float]:
        # Trivial deterministic float generation for local offline mode
        h = hashlib.sha256(text.encode('utf-8')).digest()
        embedding = []
        for i in range(384):
            val = ((h[i % 32] * (i + 1)) % 1000) / 1000.0
            # Normalize around 0
            embedding.append(val - 0.5)
        return embedding

    def purge_and_recreate_collection(self):
        try:
            print("Purging Qdrant local files to resolve vector dimension conflict.")
            # Close client to release SQLite file locks
            if self._client is not None:
                try:
                    self._client.close()
                except Exception:
                    pass
                self._client = None
                
            # Delete collection directory on disk
            col_dir = os.path.join(settings.QDRANT_PATH, "collection", self.collection_name)
            import shutil
            if os.path.exists(col_dir):
                shutil.rmtree(col_dir)
                
            # Delete meta.json to clear configuration cache
            meta_path = os.path.join(settings.QDRANT_PATH, "meta.json")
            if os.path.exists(meta_path):
                try:
                    os.remove(meta_path)
                except Exception:
                    pass
                    
            # Re-initialize the client properties and collection schema
            _ = self.client
            print("Qdrant collection successfully purged and re-initialized with 384 dimensions.")
        except Exception as e:
            print(f"Failed to purge and recreate collection: {e}")

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
            err_msg = str(e).lower()
            if any(w in err_msg for w in ["shape", "dim", "aligned", "broadcast", "size"]):
                self.purge_and_recreate_collection()
                try:
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
                except Exception as retry_err:
                    print(f"Retry upsert failed: {retry_err}")

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
            err_msg = str(e).lower()
            if any(w in err_msg for w in ["shape", "dim", "aligned", "broadcast", "size"]):
                self.purge_and_recreate_collection()
                try:
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
                except Exception as retry_err:
                    print(f"Retry search failed: {retry_err}")
                    return []
            return []

qdrant_service = QdrantService()
