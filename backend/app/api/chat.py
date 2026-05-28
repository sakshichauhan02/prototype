from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.chat import ChatThread, ChatMessage
from app.schemas.chat import ThreadCreate, ThreadResponse, MessageCreate, MessageResponse
from app.services.ai_service import ai_service
from app.services.rag_service import rag_service

router = APIRouter()

@router.get("/threads", response_model=List[ThreadResponse])
async def get_threads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatThread).where(
        ChatThread.user_id == current_user.id
    ).options(
        selectinload(ChatThread.messages)
    ).order_by(ChatThread.updated_at.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    thread_in: ThreadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_thread = ChatThread(
        title=thread_in.title,
        companion_id=thread_in.companion_id,
        user_id=current_user.id
    )
    db.add(new_thread)
    await db.commit()
    await db.refresh(new_thread)
    return {
        "id": new_thread.id,
        "title": new_thread.title,
        "companion_id": new_thread.companion_id,
        "user_id": new_thread.user_id,
        "created_at": new_thread.created_at,
        "updated_at": new_thread.updated_at,
        "messages": [],
    }

@router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def send_message(
    thread_id: int,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch thread
    stmt = select(ChatThread).where(
        ChatThread.id == thread_id,
        ChatThread.user_id == current_user.id
    ).options(selectinload(ChatThread.messages))
    
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    # Construct history dictionary list before writing the current user turn
    history = []
    for m in thread.messages:
        history.append({
            "sender": m.sender,
            "content": m.content
        })

    # Log user message
    user_msg = ChatMessage(
        thread_id=thread.id,
        sender="user",
        content=msg_in.content
    )
    db.add(user_msg)
    
    # Selective Memory Detection and Extraction
    try:
        from app.services.memory_service import memory_service
        await memory_service.process_incoming_message(
            user_id=current_user.id,
            message=msg_in.content,
            db=db
        )
    except Exception as e:
        print(f"Memory extraction process error: {e}")
    
    # RAG: Retrieve facts context related to query
    rag_context = await rag_service.retrieve_context(
        user_id=current_user.id,
        query=msg_in.content,
        db=db
    )
    
    # Trigger dynamic companion AI simulation (Awaited async method)
    ai_reply_content = await ai_service.generate_reply(
        companion_id=thread.companion_id,
        message=msg_in.content + rag_context,
        history=history,
        temperature=current_user.temperature,
        tone=current_user.tone
    )
    
    # Log AI message
    ai_msg = ChatMessage(
        thread_id=thread.id,
        sender="ai",
        content=ai_reply_content
    )
    db.add(ai_msg)
    
    await db.commit()
    await db.refresh(ai_msg)
    return ai_msg

@router.put("/threads/{thread_id}", response_model=ThreadResponse)
async def rename_thread(
    thread_id: int,
    thread_in: ThreadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatThread).where(
        ChatThread.id == thread_id,
        ChatThread.user_id == current_user.id
    ).options(selectinload(ChatThread.messages))
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    thread.title = thread_in.title
    await db.commit()
    return {
        "id": thread.id,
        "title": thread.title,
        "companion_id": thread.companion_id,
        "user_id": thread.user_id,
        "created_at": thread.created_at,
        "updated_at": thread.updated_at,
        "messages": thread.messages,
    }

@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatThread).where(
        ChatThread.id == thread_id,
        ChatThread.user_id == current_user.id
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    await db.delete(thread)
    await db.commit()
