-- Tools Slice Database Schema

-- Tool Registry
CREATE TABLE IF NOT EXISTS tools (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    schema TEXT NOT NULL,
    category TEXT,
    enabled BOOLEAN DEFAULT 1,
    version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tools_name ON tools(name);
CREATE INDEX idx_tools_category ON tools(category);
CREATE INDEX idx_tools_enabled ON tools(enabled);

-- Tool Categories
CREATE TABLE IF NOT EXISTS tool_categories (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    icon TEXT
);

-- Tool Executions
CREATE TABLE IF NOT EXISTS tool_executions (
    id TEXT PRIMARY KEY,
    tool_id TEXT NOT NULL,
    parameters TEXT,
    result TEXT,
    success BOOLEAN DEFAULT 1,
    error_message TEXT,
    duration_ms INTEGER,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tool_id) REFERENCES tools(id)
);

CREATE INDEX idx_executions_tool ON tool_executions(tool_id);
CREATE INDEX idx_executions_time ON tool_executions(executed_at DESC);

-- Tool Schemas
CREATE TABLE IF NOT EXISTS tool_schemas (
    id TEXT PRIMARY KEY,
    tool_id TEXT NOT NULL,
    schema_type TEXT NOT NULL,
    schema_content TEXT NOT NULL,
    FOREIGN KEY (tool_id) REFERENCES tools(id)
);

-- Execution Analytics
CREATE TABLE IF NOT EXISTS tool_analytics (
    id TEXT PRIMARY KEY,
    tool_id TEXT NOT NULL,
    date DATE NOT NULL,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    avg_duration_ms REAL DEFAULT 0,
    FOREIGN KEY (tool_id) REFERENCES tools(id)
);

CREATE INDEX idx_analytics_date ON tool_analytics(date);
