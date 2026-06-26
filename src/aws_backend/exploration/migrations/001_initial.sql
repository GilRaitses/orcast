CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS exploration_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  client_ip_hash TEXT,
  title TEXT
);

CREATE TABLE IF NOT EXISTS exploration_turns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES exploration_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  tool_calls_json JSONB DEFAULT '[]'::jsonb,
  gate_ids TEXT[] DEFAULT '{}',
  provenance_refs TEXT[] DEFAULT '{}',
  model TEXT,
  source TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_exploration_turns_session
  ON exploration_turns(session_id, created_at);
