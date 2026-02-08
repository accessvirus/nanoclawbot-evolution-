-- Event Bus Slice Database Schema

-- Events
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    source_slice TEXT NOT NULL,
    payload TEXT DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_source ON events(source_slice);

-- Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    subscriber_slice TEXT NOT NULL,
    callback_url TEXT,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subs_type ON subscriptions(event_type);

-- Event Queues (with bounded size)
CREATE TABLE IF NOT EXISTS event_queues (
    id TEXT PRIMARY KEY,
    queue_name TEXT UNIQUE NOT NULL,
    event_type TEXT,
    max_size INTEGER DEFAULT 1000,
    current_size INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Event Metrics
CREATE TABLE IF NOT EXISTS event_metrics (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    date DATE NOT NULL,
    total_events INTEGER DEFAULT 0,
    successful_events INTEGER DEFAULT 0,
    failed_events INTEGER DEFAULT 0,
    avg_processing_ms REAL DEFAULT 0
);

CREATE INDEX idx_metrics_date ON event_metrics(date);

-- Dead Letter Queue
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id TEXT PRIMARY KEY,
    original_event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT DEFAULT '{}',
    error_message TEXT,
    failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0
);
