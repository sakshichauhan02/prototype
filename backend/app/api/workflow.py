from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

# Directory for generated PDF resumes
RESUME_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static_resumes")
os.makedirs(RESUME_DIR, exist_ok=True)

class WorkflowRequest(BaseModel):
    pipeline_name: str = Field(..., example="System Refactor Pipeline")
    companion_ids: List[str] = Field(default=["aria", "nova"])
    parameters: Dict[str, Any] = Field(default={})

class WorkflowStep(BaseModel):
    step_num: int
    agent_id: str
    action: str
    output: str
    status: str  # "completed" | "running" | "failed"

class WorkflowResponse(BaseModel):
    pipeline_name: str
    execution_id: str
    steps: List[WorkflowStep]
    status: str

@router.post("/execute", response_model=WorkflowResponse)
async def execute_agent_workflow(
    req: WorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    # Simulated Multi-Agent pipeline steps execution
    if req.pipeline_name.lower() in ["system refactor", "refactor"]:
        steps = [
            WorkflowStep(
                step_num=1,
                agent_id="aria",
                action="Database Architecture Audit",
                output="Identified 3 redundant index scopes and recommended asyncpg migration pathways.",
                status="completed"
            ),
            WorkflowStep(
                step_num=2,
                agent_id="nova",
                action="TypeScript Context Refactoring",
                output="Optimized Next.js client-side context hooks to compile under 500ms Turbopack speeds.",
                status="completed"
            )
        ]
    else:
        steps = [
            WorkflowStep(
                step_num=1,
                agent_id=req.companion_ids[0] if req.companion_ids else "aria",
                action="Initial Prompt Synthesis",
                output=f"Structured the custom pipeline parameters: {req.parameters}",
                status="completed"
            )
        ]
        
    return WorkflowResponse(
        pipeline_name=req.pipeline_name,
        execution_id="exec_94a0293bfb120c42",
        steps=steps,
        status="success"
    )

@router.get("/resume/download/{filename}")
def download_resume(filename: str):
    """
    Serves the locally generated PDF resume.
    """
    file_path = os.path.join(RESUME_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Resume PDF file not found")
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename
    )

@router.get("/diag/db")
async def diag_db(db: AsyncSession = Depends(get_db)):
    """
    Temporary route to inspect active threads in DB and debug Pydantic errors.
    """
    from app.models.chat import ChatThread
    from app.schemas.chat import ThreadResponse
    from sqlalchemy.orm import selectinload
    
    try:
        stmt = select(ChatThread).options(selectinload(ChatThread.messages))
        result = await db.execute(stmt)
        threads = result.scalars().all()
        
        serialized = []
        for t in threads:
            try:
                # Try validation
                pydantic_thread = ThreadResponse.model_validate(t)
                serialized.append({
                    "id": pydantic_thread.id,
                    "title": pydantic_thread.title,
                    "session_mode": pydantic_thread.session_mode,
                    "validation": "success"
                })
            except Exception as val_err:
                import traceback
                # Return validation details to diagnose the 500 error
                return {
                    "error": "Pydantic Validation Error",
                    "exception": str(val_err),
                    "traceback": traceback.format_exc(),
                    "thread_db_values": {
                        "id": t.id,
                        "title": t.title,
                        "companion_id": t.companion_id,
                        "session_mode": t.session_mode,
                        "created_at": str(t.created_at),
                        "updated_at": str(t.updated_at),
                        "messages": [
                            {
                                "id": m.id,
                                "sender": m.sender,
                                "content": m.content,
                                "timestamp": str(m.timestamp)
                            } for m in t.messages
                        ]
                    }
                }
        return {"threads": serialized, "count": len(threads)}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}



