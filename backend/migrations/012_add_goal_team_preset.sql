ALTER TABLE goals ADD COLUMN team_preset VARCHAR(100);

CREATE INDEX IF NOT EXISTS ix_goals_team_preset ON goals(team_preset);
