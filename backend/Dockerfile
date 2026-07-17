FROM python:3.9-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY seed_demo_data.py .

# Create data directory for SQLite
RUN mkdir -p /app/data

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/modelgate.db
ENV EXECUTION_MODE=live
ENV WORKSPACE_ROOT=/workspace
ENV APP_NAME="ModelGate Agent Studio"
ENV DEBUG=true
ENV API_V1_PREFIX=/api/v1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
