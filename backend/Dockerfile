ARG PYTHON_VERSION=3.12.8

FROM python:${PYTHON_VERSION}-slim-bookworm AS backend-base

WORKDIR /app

# Git is required by the Agent worktree runtime and its Docker verification.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Install the fully pinned production dependency set first for layer caching.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# Copy application and migration code used by both runtime and verification.
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic/ ./alembic/
COPY alembic.ini alembic_helpers.py ./
COPY seed_demo_data.py .

# Create data directory for SQLite
RUN mkdir -p /app/data

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/modelgate.db
ENV EXECUTION_MODE=live
ENV WORKSPACE_ROOT=/workspace
ENV APP_NAME="ModelGate Agent Studio"
ENV DEBUG=false
ENV API_V1_PREFIX=/api/v1

EXPOSE 8000


FROM backend-base AS verify

# Verification dependencies stay out of the production runtime stage.
COPY requirements-dev.txt pyproject.toml ./
RUN python -m pip install --no-cache-dir --disable-pip-version-check -r requirements-dev.txt
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY evals/ ./evals/

ENV DATABASE_URL=sqlite:////tmp/modelgate-verify.db
ENV EXECUTION_MODE=mock
ENV MODEL_GATE_EXECUTION_MODE=mock

CMD ["sh", "-c", "python -m pip check && python -m alembic upgrade head && python -m alembic current && python -m pytest"]


FROM backend-base AS runtime

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
