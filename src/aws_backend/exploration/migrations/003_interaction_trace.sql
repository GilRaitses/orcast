ALTER TABLE exploration_turns
  ADD COLUMN IF NOT EXISTS interaction_id UUID,
  ADD COLUMN IF NOT EXISTS managed_agent_id TEXT,
  ADD COLUMN IF NOT EXISTS agent_version TEXT,
  ADD COLUMN IF NOT EXISTS resolved_spec_hash TEXT,
  ADD COLUMN IF NOT EXISTS hydration_mode TEXT,
  ADD COLUMN IF NOT EXISTS skills_invoked TEXT[];

CREATE INDEX IF NOT EXISTS idx_exploration_turns_interaction
  ON exploration_turns(interaction_id)
  WHERE interaction_id IS NOT NULL;
