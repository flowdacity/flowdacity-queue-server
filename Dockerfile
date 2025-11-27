# --- Build arguments with defaults ---
ARG PYTHON_VERSION=3.12
ARG PORT=8080

# --- Base image ---
FROM python:${PYTHON_VERSION}-slim

# --- Re-declare build args as env for access after FROM ---
ARG PORT
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FQ_CONFIG=/app/docker.conf \
    UV_LINK_MODE=copy \
    PORT=${PORT}

WORKDIR /app

RUN pip install --no-cache-dir --upgrade uv

COPY pyproject.toml uv.lock* ./

RUN uv pip install --system --no-cache .

COPY . .

EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn asgi:app --host 0.0.0.0 --port ${PORT}"]
