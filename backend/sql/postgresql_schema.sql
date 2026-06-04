-- PostgreSQL schema for the AI Companion Platform.
-- Run inside the target database after creating it, for example:
--   psql -U postgres -d aetheria -f backend/sql/postgresql_schema.sql

CREATE EXTENSION IF NOT EXISTS citext;

-- Automatic timestamp update function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Users table for secure authentication and profile management
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    email CITEXT NOT NULL UNIQUE,
    hashed_password VARCHAR NOT NULL,
    bio TEXT DEFAULT '',
    avatar_acronym VARCHAR DEFAULT 'JD',
    cognitive_engine VARCHAR DEFAULT 'aetheria-cognitive-v1',
    temperature DOUBLE PRECISION DEFAULT 0.5,
    tone VARCHAR DEFAULT 'Analytical',
    font_size VARCHAR DEFAULT 'Standard',
    reduce_motion BOOLEAN NOT NULL DEFAULT FALSE,
    api_token_hash VARCHAR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE TRIGGER update_users_modtime BEFORE UPDATE ON users 
FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Chat threads to group messages into logical conversations
CREATE TABLE IF NOT EXISTS chat_threads (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    companion_id VARCHAR NOT NULL DEFAULT 'aria',
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_mode VARCHAR NOT NULL DEFAULT 'casual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER update_chat_threads_modtime BEFORE UPDATE ON chat_threads 
FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Detailed message history
CREATE TABLE IF NOT EXISTS chat_history (
    id BIGSERIAL PRIMARY KEY,
    thread_id BIGINT NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE,
    sender VARCHAR NOT NULL CHECK (sender IN ('user', 'ai', 'system')),
    content TEXT NOT NULL,
    model_name VARCHAR,
    token_count INTEGER,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Memory bank for RAG (Retrieval-Augmented Generation)
CREATE TABLE IF NOT EXISTS memories (
    id BIGSERIAL PRIMARY KEY,
    fact TEXT NOT NULL,
    category VARCHAR NOT NULL DEFAULT 'Personal',
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source VARCHAR NOT NULL DEFAULT 'chat',
    importance INTEGER NOT NULL DEFAULT 1 CHECK (importance BETWEEN 1 AND 10),
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER update_memories_modtime BEFORE UPDATE ON memories 
FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Sentiment tracking linked to user interactions
CREATE TABLE IF NOT EXISTS emotional_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_message_id BIGINT REFERENCES chat_history(id) ON DELETE SET NULL,
    primary_emotion VARCHAR NOT NULL,
    sentiment_label VARCHAR NOT NULL,
    sentiment_score DOUBLE PRECISION NOT NULL CHECK (sentiment_score BETWEEN -1 AND 1),
    intensity DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (intensity BETWEEN 0 AND 1),
    notes TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Flexible key-value preferences using JSONB
CREATE TABLE IF NOT EXISTS user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preference_key VARCHAR NOT NULL,
    category VARCHAR NOT NULL DEFAULT 'general',
    value JSONB NOT NULL,
    confidence INTEGER NOT NULL DEFAULT 1 CHECK (confidence BETWEEN 1 AND 10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_preferences_user_key UNIQUE (user_id, preference_key)
);

CREATE TRIGGER update_user_preferences_modtime BEFORE UPDATE ON user_preferences 
FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Scoped system and user settings
CREATE TABLE IF NOT EXISTS settings (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    scope VARCHAR NOT NULL DEFAULT 'user',
    setting_key VARCHAR NOT NULL,
    value JSONB NOT NULL,
    is_secret BOOLEAN NOT NULL DEFAULT FALSE,
    encrypted_value VARCHAR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_settings_user_key UNIQUE (user_id, setting_key)
);

CREATE TRIGGER update_settings_modtime BEFORE UPDATE ON settings 
FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Task management engine
CREATE TABLE IF NOT EXISTS tasks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    source VARCHAR NOT NULL DEFAULT 'manual',
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER update_tasks_modtime BEFORE UPDATE ON tasks 
FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Optimized indexes for scalable queries
CREATE INDEX IF NOT EXISTS ix_users_email_lower ON users (LOWER(email));
CREATE INDEX IF NOT EXISTS ix_chat_threads_user_updated ON chat_threads (user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS ix_chat_threads_user_companion ON chat_threads (user_id, companion_id);
CREATE INDEX IF NOT EXISTS ix_chat_history_thread_timestamp ON chat_history (thread_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_chat_history_sender_timestamp ON chat_history (sender, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_memories_user_category_timestamp ON memories (user_id, category, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_memories_user_importance ON memories (user_id, importance DESC);
CREATE INDEX IF NOT EXISTS ix_emotional_history_user_recorded ON emotional_history (user_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS ix_emotional_history_user_emotion ON emotional_history (user_id, primary_emotion);
CREATE INDEX IF NOT EXISTS ix_user_preferences_user_category ON user_preferences (user_id, category);
CREATE INDEX IF NOT EXISTS ix_settings_user_scope ON settings (user_id, scope);
CREATE INDEX IF NOT EXISTS ix_tasks_user_status_due ON tasks (user_id, status, due_at);
CREATE INDEX IF NOT EXISTS ix_tasks_user_priority ON tasks (user_id, priority);
