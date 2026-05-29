from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.memory import Memory
from app.schemas.memory import MemoryCreate, MemoryResponse

from app.services.memory_service import memory_service

router = APIRouter()

@router.get("", response_model=List[MemoryResponse])
async def get_memories(
    category: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Memory).where(Memory.user_id == current_user.id)
    if category and category != "All":
        stmt = stmt.where(Memory.category == category)
        
    stmt = stmt.order_by(Memory.timestamp.desc())
    result = await db.execute(stmt)
    memories = result.scalars().all()
    for m in memories:
        m.fact = memory_service.decrypt_fact(m.fact)
    return memories

@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def add_memory(
    memory_in: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await memory_service.add_memory_manually(
        user_id=current_user.id,
        fact=memory_in.fact,
        category=memory_in.category,
        db=db
    )

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: int,
    memory_in: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated = await memory_service.update_memory(
        user_id=current_user.id,
        memory_id=memory_id,
        fact=memory_in.fact,
        category=memory_in.category,
        db=db
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Memory fact not found")
    return updated

@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await memory_service.delete_memory(
        user_id=current_user.id,
        memory_id=memory_id,
        db=db
    )
    if not success:
        raise HTTPException(status_code=404, detail="Memory fact not found")
