-- Agent Core Slice Database Schema

-- Agent Sessions
CREATE TABLE IF NOT EXISTS agent_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    context TEXT NOT NULL DEFAULT '{}',
    state TEXT NOT NULL DEFAULT 'active',
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON agent_sessions(user_id);
CREATE INDEX idx_sessions_state ON agent_sessions(state);
CREATE INDEX idx_sessions_created ON agent_sessions(created_at DESC);

-- Agent Executions
CREATE TABLE IF NOT EXISTS agent_executions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    request TEXT NOT NULL,
    response TEXT,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT 1,
    error_message TEXT,
    model_used TEXT,
    metadata TEXT DEFAULT '{}',
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES agent_sessions(id)
);

CREATE INDEX idx_executions_session ON agent_executions(session_id);
CREATE INDEX idx_executions_time ON agent_executions(executed_at DESC);

-- Prompt Templates
CREATE TABLE IF NOT EXISTS prompt_templates (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    template TEXT NOT NULL,
    variables TEXT DEFAULT '[]',
    version INTEGER DEFAULT 1,
    is_default BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_name ON prompt_templates(name);

-- Context Templates
CREATE TABLE IF NOT EXISTS context_templates (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    template TEXT NOT NULL,
    max_tokens INTEGER DEFAULT 8000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent Memory Cache (short-term)
CREATE TABLE IF NOT EXISTS memory_cache (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES agent_sessions(id),
    UNIQUE(session_id, key)
);

CREATE INDEX idx_cache_session ON memory_cache(session_id);
CREATE INDEX idx_cache_expires ON memory_cache(expires_at);

-- Execution Analytics
CREATE TABLE IF NOT EXISTS execution_analytics (
    id TEXT PRIMARY KEY,
    slice_id TEXT NOT NULL DEFAULT 'slice_agent_core',
    date DATE NOT NULL,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    avg_latency_ms REAL DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_date ON execution_analytics(date);
