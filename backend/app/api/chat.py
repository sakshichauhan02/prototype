from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
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
        user_id=current_user.id,
        session_mode=thread_in.session_mode
    )
    db.add(new_thread)
    await db.commit()
    
    # Pre-fetch the created thread with messages loaded to avoid MissingGreenlet lazy-loading error
    stmt = select(ChatThread).where(ChatThread.id == new_thread.id).options(selectinload(ChatThread.messages))
    result = await db.execute(stmt)
    db_thread = result.scalar_one()
    return db_thread


async def perform_background_memory_extraction(user_id: int, message: str, consent_memory: bool):
    from app.database import AsyncSessionLocal
    from app.services.memory_service import memory_service
    async with AsyncSessionLocal() as db_session:
        try:
            await memory_service.process_incoming_message(
                user_id=user_id,
                message=message,
                db=db_session,
                consent_memory=consent_memory
            )
        except Exception as e:
            print(f"Background memory extraction process error: {e}")

@router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def send_message(
    thread_id: int,
    msg_in: MessageCreate,
    background_tasks: BackgroundTasks,
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

    # Handle Playground Mode commands directly
    if thread.session_mode == "playground":
        content_stripped = msg_in.content.strip().lower()
        if content_stripped.startswith("/set ") or (content_stripped.startswith("/") and any(cmd in content_stripped for cmd in ["/temp", "/engine", "/tone"])):
            updated_params = []
            
            import re
            temp_match = re.search(r'(?:/set\s+)?(?:temp|temperature)\s+([0-9.]+)', content_stripped)
            if temp_match:
                try:
                    val = float(temp_match.group(1))
                    if 0.0 <= val <= 2.0:
                        current_user.temperature = val
                        updated_params.append(f"Temperature ➔ **{val}**")
                except ValueError:
                    pass
            
            engine_match = re.search(r'(?:/set\s+)?(?:engine)\s+(\S+)', content_stripped)
            if engine_match:
                val = engine_match.group(1).strip()
                current_user.cognitive_engine = val
                updated_params.append(f"Cognitive Engine ➔ **{val}**")
                
            tone_match = re.search(r'(?:/set\s+)?(?:tone)\s+(\S+)', content_stripped)
            if tone_match:
                val = tone_match.group(1).strip().capitalize()
                current_user.tone = val
                updated_params.append(f"Tone ➔ **{val}**")
                
            if updated_params:
                await db.commit()
                # Create user message
                user_msg = ChatMessage(
                    thread_id=thread.id,
                    sender="user",
                    content=msg_in.content
                )
                # Create AI confirmation message
                ai_reply_content = (
                    f"⚙️ **[Playground Controls Updated]**\n\n"
                    f"Successfully tuned active cognitive engine variables:\n" + \
                    "\n".join([f"- {param}" for param in updated_params]) + \
                    "\n\n*All future responses in this thread will run with these parameters.*"
                )
                ai_msg = ChatMessage(
                    thread_id=thread.id,
                    sender="ai",
                    content=ai_reply_content
                )
                db.add(user_msg)
                db.add(ai_msg)
                await db.commit()
                await db.refresh(ai_msg)
                return ai_msg

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

    # Enforce bypass of memory logging automatically when Personal Companion Mode is active
    if thread.session_mode in ["personal", "personal_companion"]:
        consent_memory = False

    # Run emotion analysis and intent detection in parallel to optimize latency
    import asyncio
    from app.services.emotion_service import emotion_service
    from app.services.agent_service import agent_service
    
    sm = thread.session_mode or "personal"
    emotion_task = emotion_service.analyze_emotion(msg_in.content)
    intent_task = agent_service.detect_task_intent(msg_in.content, session_mode=sm)
    
    emotion_snap, agent_intent = await asyncio.gather(emotion_task, intent_task)
    pe = emotion_snap.get("primary_emotion", "neutral")
    combined_modifier = agent_service.route_session_mode(sm, emotion_snap)

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
 
        # Trigger background memory extraction
        if consent_memory:
            background_tasks.add_task(
                perform_background_memory_extraction,
                current_user.id,
                msg_in.content,
                consent_memory
            )
 
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
        
        # Scan history for active research context or force real-time search in Researcher Mode
        research_context = ""
        if sm == "researcher":
            from app.services.web_research_service import web_research_service
            is_greeting = any(w in msg_in.content.lower().strip() for w in ["hello", "hi", "hey", "hola", "howdy"]) and len(msg_in.content.strip()) < 10
            if not is_greeting:
                try:
                    research_context = await web_research_service.search_and_summarize(msg_in.content)
                except Exception as e:
                    print(f"Warning: Researcher mode auto-search failed: {e}")
        
        if not research_context:
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
            emotion_modifier=combined_modifier,
            research_context=research_context,
            primary_emotion=pe,
            tone_analysis={
                **emotion_snap,
                "session_mode": sm,
                "cognitive_engine": current_user.cognitive_engine,
                "temperature": current_user.temperature
            }
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
    thread.session_mode = thread_in.session_mode
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


@router.post("/sync", status_code=status.HTTP_200_OK)
async def bulk_sync(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import datetime
    import asyncio
    from app.models.memory import Memory
    from app.services.memory_service import memory_service

    mutations = payload.get("mutations", [])
    
    # Sort mutations chronologically by timestamp
    try:
        mutations = sorted(mutations, key=lambda m: m.get("timestamp", ""))
    except Exception:
        pass

    mock_thread_id_map = {}
    mock_memory_id_map = {}
    processed_count = 0

    for mutation in mutations:
        await asyncio.sleep(1)
        m_type = mutation.get("type")
        m_payload = mutation.get("payload", {})
        m_timestamp_str = mutation.get("timestamp")
        
        try:
            m_timestamp = datetime.datetime.fromisoformat(m_timestamp_str.replace("Z", "+00:00"))
        except Exception:
            m_timestamp = datetime.datetime.utcnow()

        if m_type == "CREATE_THREAD":
            mock_id = m_payload.get("id")
            title = m_payload.get("title", "New Chat")
            companion_id = m_payload.get("companionId", "aria")
            session_mode = m_payload.get("sessionMode") or m_payload.get("session_mode") or "personal"
            
            stmt = select(ChatThread).where(
                ChatThread.user_id == current_user.id,
                ChatThread.title == title,
                ChatThread.companion_id == companion_id
            )
            result = await db.execute(stmt)
            existing = result.scalars().first()
            if existing:
                mock_thread_id_map[mock_id] = existing.id
            else:
                new_thread = ChatThread(
                    title=title,
                    companion_id=companion_id,
                    user_id=current_user.id,
                    session_mode=session_mode,
                    created_at=m_timestamp,
                    updated_at=m_timestamp
                )
                db.add(new_thread)
                await db.flush()
                mock_thread_id_map[mock_id] = new_thread.id
            processed_count += 1

        elif m_type == "RENAME_THREAD":
            thread_id_str = m_payload.get("id")
            new_title = m_payload.get("title")
            
            thread_id = mock_thread_id_map.get(thread_id_str)
            if thread_id is None:
                try:
                    thread_id = int(thread_id_str)
                except ValueError:
                    continue
                    
            stmt = select(ChatThread).where(ChatThread.id == thread_id, ChatThread.user_id == current_user.id)
            result = await db.execute(stmt)
            thread = result.scalar_one_or_none()
            if thread:
                thread_updated = thread.updated_at
                if thread_updated.tzinfo is None:
                    thread_updated = thread_updated.replace(tzinfo=datetime.timezone.utc)
                mutation_tz = m_timestamp.replace(tzinfo=datetime.timezone.utc) if m_timestamp.tzinfo is None else m_timestamp
                
                if mutation_tz > thread_updated:
                    thread.title = new_title
                    thread.updated_at = m_timestamp
                    await db.flush()
            processed_count += 1

        elif m_type == "DELETE_THREAD":
            thread_id_str = m_payload.get("id")
            thread_id = mock_thread_id_map.get(thread_id_str)
            if thread_id is None:
                try:
                    thread_id = int(thread_id_str)
                except ValueError:
                    continue
                    
            stmt = select(ChatThread).where(ChatThread.id == thread_id, ChatThread.user_id == current_user.id)
            result = await db.execute(stmt)
            thread = result.scalar_one_or_none()
            if thread:
                await db.delete(thread)
                await db.flush()
            processed_count += 1

        elif m_type == "SEND_MESSAGE":
            thread_id_str = m_payload.get("threadId")
            sender = m_payload.get("sender", "user")
            content = m_payload.get("content")
            
            thread_id = mock_thread_id_map.get(thread_id_str)
            if thread_id is None:
                try:
                    thread_id = int(thread_id_str)
                except ValueError:
                    continue
                    
            stmt = select(ChatMessage).where(
                ChatMessage.thread_id == thread_id,
                ChatMessage.sender == sender,
                ChatMessage.content == content
            )
            result = await db.execute(stmt)
            existing_msg = result.scalars().first()
            if not existing_msg:
                new_msg = ChatMessage(
                    thread_id=thread_id,
                    sender=sender,
                    content=content,
                    timestamp=m_timestamp
                )
                db.add(new_msg)
                await db.flush()
            processed_count += 1

        elif m_type == "ADD_MEMORY":
            mock_id = m_payload.get("id")
            fact = m_payload.get("fact")
            category = m_payload.get("category", "Preferences")
            
            stmt = select(Memory).where(Memory.user_id == current_user.id)
            result = await db.execute(stmt)
            memories = result.scalars().all()
            
            duplicate = False
            for m in memories:
                decrypted = memory_service.decrypt_fact(m.fact)
                if decrypted.lower().strip() == fact.lower().strip():
                    duplicate = True
                    mock_memory_id_map[mock_id] = m.id
                    break
                    
            if not duplicate:
                new_mem = await memory_service.add_memory_manually(
                    user_id=current_user.id,
                    fact=fact,
                    category=category,
                    db=db
                )
                mock_memory_id_map[mock_id] = new_mem.id
            processed_count += 1

        elif m_type == "EDIT_MEMORY":
            memory_id_str = m_payload.get("id")
            fact = m_payload.get("fact")
            category = m_payload.get("category")
            
            memory_id = mock_memory_id_map.get(memory_id_str)
            if memory_id is None:
                try:
                    memory_id = int(memory_id_str)
                except ValueError:
                    continue
                    
            stmt = select(Memory).where(Memory.id == memory_id, Memory.user_id == current_user.id)
            result = await db.execute(stmt)
            memory = result.scalar_one_or_none()
            if memory:
                memory_timestamp = memory.timestamp
                if memory_timestamp.tzinfo is None:
                    memory_timestamp = memory_timestamp.replace(tzinfo=datetime.timezone.utc)
                mutation_tz = m_timestamp.replace(tzinfo=datetime.timezone.utc) if m_timestamp.tzinfo is None else m_timestamp
                
                if mutation_tz > memory_timestamp:
                    await memory_service.update_memory(
                        user_id=current_user.id,
                        memory_id=memory_id,
                        fact=fact,
                        category=category,
                        db=db
                    )
            processed_count += 1

        elif m_type == "DELETE_MEMORY":
            memory_id_str = m_payload.get("id")
            memory_id = mock_memory_id_map.get(memory_id_str)
            if memory_id is None:
                try:
                    memory_id = int(memory_id_str)
                except ValueError:
                    continue
                    
            await memory_service.delete_memory(
                user_id=current_user.id,
                memory_id=memory_id,
                db=db
            )
            processed_count += 1

    await db.commit()
    return {"status": "success", "processed_mutations": processed_count}
