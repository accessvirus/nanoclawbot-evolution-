-- Skills Slice Database Schema

-- Skills
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    skill_file TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    enabled BOOLEAN DEFAULT 1,
    version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_skills_name ON skills(name);
CREATE INDEX idx_skills_enabled ON skills(enabled);

-- Skill Executions
CREATE TABLE IF NOT EXISTS skill_executions (
    id TEXT PRIMARY KEY,
    skill_id TEXT NOT NULL,
    parameters TEXT DEFAULT '{}',
    result TEXT,
    success BOOLEAN DEFAULT 1,
    error_message TEXT,
    duration_ms INTEGER,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (skill_id) REFERENCES skills(id)
);

CREATE INDEX idx_executions_skill ON skill_executions(skill_id);

-- Skill Dependencies
CREATE TABLE IF NOT EXISTS skill_dependencies (
    id TEXT PRIMARY KEY,
    skill_id TEXT NOT NULL,
    dependency TEXT NOT NULL,
    version_constraint TEXT,
    FOREIGN KEY (skill_id) REFERENCES skills(id)
);

-- Skill Categories
CREATE TABLE IF NOT EXISTS skill_categories (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

-- Skill Analytics
CREATE TABLE IF NOT EXISTS skill_analytics (
    id TEXT PRIMARY KEY,
    skill_id TEXT NOT NULL,
    date DATE NOT NULL,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    avg_duration_ms REAL DEFAULT 0,
    FOREIGN KEY (skill_id) REFERENCES skills(id)
);

CREATE INDEX idx_analytics_skill ON skill_analytics(date);
