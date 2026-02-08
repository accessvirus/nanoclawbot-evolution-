-- Memory Slice Database Schema

-- Memories
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    embedding TEXT,
    relevance_score REAL DEFAULT 0.0,
    user_id TEXT,
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0
);

CREATE INDEX idx_memories_user ON memories(user_id);
CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_session ON memories(session_id);

-- Memory Consolidation
CREATE TABLE IF NOT EXISTS memory_consolidation (
    id TEXT PRIMARY KEY,
    source_ids TEXT NOT NULL,
    consolidated_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Memory Tags
CREATE TABLE IF NOT EXISTS memory_tags (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id)
);

CREATE INDEX idx_tags_memory ON memory_tags(memory_id);
CREATE INDEX idx_tags_tag ON memory_tags(tag);

-- Memory Retrieval Log
CREATE TABLE IF NOT EXISTS memory_retrieval_log (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    retrieved_ids TEXT,
    relevance_scores TEXT,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Long-term Memory (Persistent)
CREATE TABLE IF NOT EXISTS long_term_memory (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ltm_key ON long_term_memory(key);
