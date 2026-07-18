-- Runtime P0-3: persist the Goal-level scheduler concurrency ceiling.
ALTER TABLE goals ADD COLUMN max_parallel_tasks INTEGER NOT NULL DEFAULT 3;
