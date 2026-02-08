-- Session Slice Database Schema

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_type TEXT DEFAULT 'conversation',
    state TEXT DEFAULT 'active',
    metadata TEXT DEFAULT '{}',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_state ON sessions(state);

-- Conversation History
CREATE TABLE IF NOT EXISTS conversation_history (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tokens INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_history_session ON conversation_history(session_id);

-- Session Analytics
CREATE TABLE IF NOT EXISTS session_analytics (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    total_messages INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    avg_response_time_ms REAL DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Archived Sessions
CREATE TABLE IF NOT EXISTS archived_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_type TEXT,
    metadata TEXT DEFAULT '{}',
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_started_at TIMESTAMP
);
