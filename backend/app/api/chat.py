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
    
    # Pre-fetch the created thread with messages loaded to avoid MissingGreenlet lazy-loading error
    stmt = select(ChatThread).where(ChatThread.id == new_thread.id).options(selectinload(ChatThread.messages))
    result = await db.execute(stmt)
    db_thread = result.scalar_one()
    return db_thread


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

    # Query user preferences/settings for Private Mode and Consent-based Memory Saving
    private_mode = False
    consent_memory = True
    
    from app.models.settings import Setting
    try:
        stmt_settings = select(Setting).where(Setting.user_id == current_user.id)
        settings_result = await db.execute(stmt_settings)
        db_settings = settings_result.scalars().all()
        for s in db_settings:
            if s.setting_key == "private_mode":
                val = s.value
                private_mode = (val is True or val == "true" or str(val).lower() == "true")
            elif s.setting_key == "consent_memory":
                val = s.value
                consent_memory = not (val is False or val == "false" or str(val).lower() == "false")
    except Exception as e:
        print(f"Failed to query privacy settings: {e}")

    # Run emotion analysis and intent detection in parallel to optimize latency
    import asyncio
    from app.services.emotion_service import emotion_service
    from app.services.agent_service import agent_service
    
    emotion_task = emotion_service.analyze_emotion(msg_in.content)
    intent_task = agent_service.detect_task_intent(msg_in.content)
    
    emotion_snap, agent_intent = await asyncio.gather(emotion_task, intent_task)
    pe = emotion_snap.get("primary_emotion", "neutral")
    emotion_modifier = emotion_service.get_adaptive_prompt_modifier(pe)
    
    # Log user message (if NOT in private mode)
    user_msg = None
    if not private_mode:
        user_msg = ChatMessage(
            thread_id=thread.id,
            sender="user",
            content=msg_in.content
        )
        db.add(user_msg)
        await db.flush() # Populate ID

        # Log emotional snapshot
        try:
            await emotion_service.record_emotion(
                user_id=current_user.id,
                message_id=user_msg.id,
                analysis=emotion_snap,
                db=db
            )
        except Exception as e:
            print(f"Failed to record emotional snapshot: {e}")

        # Trigger background/inline memory extraction
        if consent_memory:
            try:
                from app.services.memory_service import memory_service
                await memory_service.process_incoming_message(
                    user_id=current_user.id,
                    message=msg_in.content,
                    db=db,
                    consent_memory=consent_memory
                )
            except Exception as e:
                print(f"Memory extraction process error: {e}")

    # Determine response content
    if agent_intent:
        # Execute agent workflow directly
        agent_result = await agent_service.execute_workflow(
            user_id=current_user.id,
            intent=agent_intent,
            db=db
        )
        ai_reply_content = agent_result["output"]
    else:
        # RAG Context Retrieval
        rag_context = await rag_service.retrieve_context(
            user_id=current_user.id,
            query=msg_in.content,
            db=db
        )
        
        # Scan history for active research context
        research_context = ""
        for m in reversed(thread.messages):
            if m.sender == "ai" and "🔍 **[Research Agent Active]**" in m.content:
                research_context = m.content
                break
        
        # History formatting
        history = []
        for m in thread.messages:
            history.append({
                "sender": m.sender,
                "content": m.content
            })
        
        # Dynamically adapt tone based on user emotion
        user_tone = current_user.tone
        if pe == "excited":
            user_tone = "Enthusiastic"
        elif pe == "sad":
            user_tone = "Supportive"
        elif pe == "frustrated":
            user_tone = "Patient"
        elif pe == "stressed":
            user_tone = "Reassuring"
            
        # Trigger companion reply generation with modified instruction
        ai_reply_content = await ai_service.generate_reply(
            companion_id=thread.companion_id,
            message=msg_in.content,
            history=history,
            temperature=current_user.temperature,
            tone=user_tone,
            rag_context=rag_context,
            emotion_modifier=emotion_modifier,
            research_context=research_context,
            primary_emotion=pe
        )

    # Log AI message (if NOT in private mode)
    ai_msg = None
    if not private_mode:
        ai_msg = ChatMessage(
            thread_id=thread.id,
            sender="ai",
            content=ai_reply_content
        )
        db.add(ai_msg)
        await db.commit()
        await db.refresh(ai_msg)
    else:
        # Create a mock temporary message model to return to client (not committed to DB)
        import datetime
        ai_msg = ChatMessage(
            id=-1,
            thread_id=thread_id,
            sender="ai",
            content=f"🔒 [Private Mode Active - Not Persisted]\n{ai_reply_content}",
            timestamp=datetime.datetime.utcnow()
        )
    
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
    await db.refresh(thread)
    return thread


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
