ALTER TABLE exploration_sessions
  ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

UPDATE exploration_sessions
SET expires_at = created_at + interval '30 days'
WHERE expires_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_exploration_sessions_expires
  ON exploration_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_exploration_sessions_ip_created
  ON exploration_sessions(client_ip_hash, created_at);
