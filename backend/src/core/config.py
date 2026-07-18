import os


class Settings:
    app_name: str = os.getenv("APP_NAME", "ModelGate Agent Studio API")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./modelgate.db")
    api_v1_prefix: str = "/api/v1"
    # Mock is deliberately not the default.  A deployment without a configured
    # live model must fail visibly instead of presenting a demo response as an
    # agent result.
    execution_mode: str = os.getenv("MODEL_GATE_EXECUTION_MODE", os.getenv("EXECUTION_MODE", "live")).lower()
    workspace_root: str = os.path.abspath(os.getenv("WORKSPACE_ROOT", os.getcwd()))
    tool_timeout_seconds: int = int(os.getenv("TOOL_TIMEOUT_SECONDS", "120"))
    max_tool_output_chars: int = int(os.getenv("MAX_TOOL_OUTPUT_CHARS", "12000"))
    max_file_write_bytes: int = int(os.getenv("MAX_FILE_WRITE_BYTES", str(1024 * 1024)))
    task_lease_seconds: int = int(os.getenv("TASK_LEASE_SECONDS", "300"))
    worktree_root: str = os.path.abspath(os.getenv("WORKTREE_ROOT", "/tmp/modelgate-worktrees"))
    # The runtime always applies its command policy.  Docker is an optional
    # second isolation layer for sandbox runs; local is useful for development
    # machines that do not have a compatible sandbox image yet.
    sandbox_backend: str = os.getenv("SANDBOX_BACKEND", "local").lower()
    sandbox_image: str = os.getenv("SANDBOX_IMAGE", "python:3.12-slim")


settings = Settings()
