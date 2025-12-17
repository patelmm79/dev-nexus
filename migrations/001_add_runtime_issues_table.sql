-- Migration: Add runtime_issues table to PostgreSQL
-- Timestamp: 2025-12-16
-- Purpose: Migrate runtime issues from JSON-only storage to PostgreSQL

CREATE TABLE IF NOT EXISTS runtime_issues (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    issue_id VARCHAR(100) UNIQUE NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    issue_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    log_snippet TEXT,
    root_cause TEXT,
    suggested_fix TEXT,
    pattern_reference VARCHAR(500),
    github_issue_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'open',
    metrics JSONB,
    resolution_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_runtime_issues_repo_id ON runtime_issues(repo_id);
CREATE INDEX IF NOT EXISTS idx_runtime_issues_detected_at ON runtime_issues(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_runtime_issues_issue_type ON runtime_issues(issue_type);
CREATE INDEX IF NOT EXISTS idx_runtime_issues_severity ON runtime_issues(severity);

-- Composite index for common queries (repo + time range)
CREATE INDEX IF NOT EXISTS idx_runtime_issues_repo_detected ON runtime_issues(repo_id, detected_at DESC);

-- Full-text search on logs and root cause
CREATE INDEX IF NOT EXISTS idx_runtime_issues_log_fts ON runtime_issues USING gin(to_tsvector('english', COALESCE(log_snippet, '')));
CREATE INDEX IF NOT EXISTS idx_runtime_issues_root_cause_fts ON runtime_issues USING gin(to_tsvector('english', COALESCE(root_cause, '')));
