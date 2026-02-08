-- Communication Slice Database Schema

-- Channels
CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    config TEXT DEFAULT '{}',
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_channels_type ON channels(type);
CREATE INDEX idx_channels_enabled ON channels(enabled);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',
    metadata TEXT DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

CREATE INDEX idx_messages_channel ON messages(channel_id);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_time ON messages(timestamp DESC);

-- Message Templates
CREATE TABLE IF NOT EXISTS message_templates (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    template TEXT NOT NULL,
    channel_type TEXT,
    description TEXT
);

-- Channel Analytics
CREATE TABLE IF NOT EXISTS channel_analytics (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    date DATE NOT NULL,
    messages_sent INTEGER DEFAULT 0,
    messages_received INTEGER DEFAULT 0,
    avg_response_time_ms REAL DEFAULT 0,
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

CREATE INDEX idx_analytics_channel ON channel_analytics(date);
