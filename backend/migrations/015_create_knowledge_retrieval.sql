-- P1 Shared Context: source documents, chunks, retrieval evidence and snapshots.
CREATE TABLE IF NOT EXISTS knowledge_sources (
 id VARCHAR(36) PRIMARY KEY, name VARCHAR(255) NOT NULL, type VARCHAR(50) NOT NULL,
 uri TEXT NOT NULL, workspace_scope TEXT, status VARCHAR(30) NOT NULL DEFAULT 'active',
 sync_policy VARCHAR(30) NOT NULL DEFAULT 'manual', checksum VARCHAR(128),
 extra_metadata TEXT NOT NULL DEFAULT '{}', last_synced_at DATETIME, error_message TEXT,
 created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_knowledge_sources_type ON knowledge_sources(type);
CREATE INDEX IF NOT EXISTS ix_knowledge_sources_status ON knowledge_sources(status);

CREATE TABLE IF NOT EXISTS knowledge_documents (
 id VARCHAR(36) PRIMARY KEY, source_id VARCHAR(36) NOT NULL, path TEXT NOT NULL,
 title VARCHAR(500) NOT NULL, checksum VARCHAR(128) NOT NULL, mime_type VARCHAR(100),
 extra_metadata TEXT NOT NULL DEFAULT '{}', status VARCHAR(30) NOT NULL DEFAULT 'indexed',
 indexed_at DATETIME NOT NULL, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL,
 CONSTRAINT uq_knowledge_document_source_path UNIQUE(source_id, path)
);
CREATE INDEX IF NOT EXISTS ix_knowledge_documents_source_id ON knowledge_documents(source_id);
CREATE INDEX IF NOT EXISTS ix_knowledge_documents_checksum ON knowledge_documents(checksum);
CREATE INDEX IF NOT EXISTS ix_knowledge_documents_status ON knowledge_documents(status);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
 id VARCHAR(36) PRIMARY KEY, document_id VARCHAR(36) NOT NULL, content TEXT NOT NULL,
 chunk_index INTEGER NOT NULL, token_count INTEGER NOT NULL DEFAULT 0, embedding TEXT,
 symbol_path TEXT, extra_metadata TEXT NOT NULL DEFAULT '{}', status VARCHAR(30) NOT NULL DEFAULT 'active',
 created_at DATETIME NOT NULL,
 CONSTRAINT uq_knowledge_chunk_document_index UNIQUE(document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_document_id ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_status ON knowledge_chunks(status);

CREATE TABLE IF NOT EXISTS retrieval_runs (
 id VARCHAR(36) PRIMARY KEY, goal_id VARCHAR(36), task_id VARCHAR(36), agent_id VARCHAR(36),
 query TEXT NOT NULL, policy VARCHAR(100) NOT NULL, filters TEXT NOT NULL DEFAULT '{}',
 latency_ms INTEGER NOT NULL DEFAULT 0, token_budget INTEGER NOT NULL DEFAULT 0,
 status VARCHAR(30) NOT NULL DEFAULT 'completed', created_at DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_retrieval_runs_goal_id ON retrieval_runs(goal_id);
CREATE INDEX IF NOT EXISTS ix_retrieval_runs_task_id ON retrieval_runs(task_id);
CREATE INDEX IF NOT EXISTS ix_retrieval_runs_agent_id ON retrieval_runs(agent_id);
CREATE INDEX IF NOT EXISTS ix_retrieval_runs_policy ON retrieval_runs(policy);
CREATE INDEX IF NOT EXISTS ix_retrieval_runs_status ON retrieval_runs(status);
CREATE INDEX IF NOT EXISTS ix_retrieval_runs_created_at ON retrieval_runs(created_at);

CREATE TABLE IF NOT EXISTS retrieved_context_items (
 id VARCHAR(36) PRIMARY KEY, retrieval_run_id VARCHAR(36) NOT NULL,
 source_type VARCHAR(50) NOT NULL, source_id VARCHAR(36) NOT NULL, chunk_id VARCHAR(36),
 score FLOAT NOT NULL, rank INTEGER NOT NULL, used BOOLEAN NOT NULL DEFAULT 0,
 citation TEXT, token_count INTEGER NOT NULL DEFAULT 0, created_at DATETIME NOT NULL,
 CONSTRAINT uq_retrieved_item_run_rank UNIQUE(retrieval_run_id, rank)
);
CREATE INDEX IF NOT EXISTS ix_retrieved_context_items_run_id ON retrieved_context_items(retrieval_run_id);
CREATE INDEX IF NOT EXISTS ix_retrieved_context_items_source_type ON retrieved_context_items(source_type);
CREATE INDEX IF NOT EXISTS ix_retrieved_context_items_source_id ON retrieved_context_items(source_id);
CREATE INDEX IF NOT EXISTS ix_retrieved_context_items_chunk_id ON retrieved_context_items(chunk_id);
CREATE INDEX IF NOT EXISTS ix_retrieved_context_items_used ON retrieved_context_items(used);

CREATE TABLE IF NOT EXISTS context_package_snapshots (
 id VARCHAR(36) PRIMARY KEY, worker_id VARCHAR(36) NOT NULL, plan_version_id VARCHAR(36),
 retrieval_run_id VARCHAR(36), payload TEXT NOT NULL, token_count INTEGER NOT NULL DEFAULT 0,
 checksum VARCHAR(128) NOT NULL, created_at DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_context_package_snapshots_worker_id ON context_package_snapshots(worker_id);
CREATE INDEX IF NOT EXISTS ix_context_package_snapshots_plan_version_id ON context_package_snapshots(plan_version_id);
CREATE INDEX IF NOT EXISTS ix_context_package_snapshots_retrieval_run_id ON context_package_snapshots(retrieval_run_id);
CREATE INDEX IF NOT EXISTS ix_context_package_snapshots_checksum ON context_package_snapshots(checksum);
