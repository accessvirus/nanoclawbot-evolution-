-- Providers Slice Database Schema

-- Providers
CREATE TABLE IF NOT EXISTS providers (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    provider_type TEXT NOT NULL,
    api_endpoint TEXT,
    api_key TEXT,
    models TEXT DEFAULT '[]',
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model Configurations
CREATE TABLE IF NOT EXISTS model_configurations (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    capabilities TEXT DEFAULT '[]',
    cost_per_1k_prompt REAL DEFAULT 0,
    cost_per_1k_completion REAL DEFAULT 0,
    max_tokens INTEGER DEFAULT 4096,
    enabled BOOLEAN DEFAULT 1,
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

CREATE INDEX idx_models_provider ON model_configurations(provider_id);

-- Cost Tracking
CREATE TABLE IF NOT EXISTS cost_tracking (
    id TEXT PRIMARY KEY,
    provider_id TEXT,
    model_name TEXT NOT NULL,
    request_id TEXT,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

CREATE INDEX idx_cost_date ON cost_tracking(timestamp);
CREATE INDEX idx_cost_model ON cost_tracking(model_name);

-- Usage Analytics
CREATE TABLE IF NOT EXISTS usage_analytics (
    id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    date DATE NOT NULL,
    total_requests INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0,
    avg_latency_ms REAL DEFAULT 0
);

CREATE INDEX idx_usage_date ON usage_analytics(date);
