ALTER TABLE exploration_turns
  ADD COLUMN IF NOT EXISTS interaction_steps JSONB;

CREATE INDEX IF NOT EXISTS idx_exploration_turns_interaction_steps
  ON exploration_turns USING gin (interaction_steps)
  WHERE interaction_steps IS NOT NULL;
