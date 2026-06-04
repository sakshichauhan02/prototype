from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from sqlalchemy import text
from app import models
from app.api import auth, chat, memory, profile, emotion, research, workflow, tasks

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS for client-side frontend syncs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 router prefix paths
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["AI Conversations"])
app.include_router(memory.router, prefix=f"{settings.API_V1_STR}/memory", tags=["Cognitive Vault"])
app.include_router(profile.router, prefix=f"{settings.API_V1_STR}/profile", tags=["User Profiles"])
app.include_router(emotion.router, prefix=f"{settings.API_V1_STR}/emotion", tags=["Sentiment Analytics"])
app.include_router(research.router, prefix=f"{settings.API_V1_STR}/research", tags=["Web Research Agents"])
app.include_router(workflow.router, prefix=f"{settings.API_V1_STR}/workflow", tags=["Agent Workflows"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["Task Reminders"])

# Automatically spin up DB tables on startup
@app.on_event("startup")
async def on_startup():
    if settings.DATABASE_URL.startswith("postgresql"):
        try:
            from app.init_db import run_schema
            await run_schema()
        except Exception as e:
            print(f"Warning: PostgreSQL schema execution failed: {e}. Falling back to default metadata creation.")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
    else:
        async with engine.begin() as conn:
            # Create all tables if they do not exist
            await conn.run_sync(Base.metadata.create_all)

    # Run inline migration to add column session_mode to chat_threads if it doesn't exist yet
    async with engine.begin() as conn:
        try:
            if settings.DATABASE_URL.startswith("postgresql"):
                await conn.execute(text(
                    "ALTER TABLE chat_threads ADD COLUMN IF NOT EXISTS session_mode VARCHAR NOT NULL DEFAULT 'casual'"
                ))
            else:
                result = await conn.execute(text("PRAGMA table_info(chat_threads)"))
                columns = [row[1] for row in result.fetchall()]
                if "session_mode" not in columns:
                    await conn.execute(text(
                        "ALTER TABLE chat_threads ADD COLUMN session_mode VARCHAR NOT NULL DEFAULT 'casual'"
                    ))
        except Exception as migration_error:
            print(f"Database inline migration warning: {migration_error}")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }
