from sqlalchemy.ext.asyncio import AsyncSession
from app.services.memory_service import memory_service

class RAGService:
    @staticmethod
    async def retrieve_context(user_id: int, query: str, db: AsyncSession = None) -> str:
        # Delegate context retrieval to the semantic Qdrant memory service
        return await memory_service.retrieve_context(user_id, query)

rag_service = RAGService()
