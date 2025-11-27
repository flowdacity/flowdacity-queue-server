[![Run tests and upload coverage](https://github.com/flowdacity/flowdacity-queue-server/actions/workflows/test.yml/badge.svg)](https://github.com/flowdacity/flowdacity-queue-server/actions/workflows/test.yml)

Flowdacity Queue Server
=======================

An async HTTP API for the [Flowdacity Queue (FQ)](https://github.com/plivo/fq) core, built with Starlette and Uvicorn. It keeps the original SHARQ behavior (leaky-bucket rate limiting and dynamic queues) while modernizing the stack.

## Prerequisites

- Python 3.12+
- Redis 7+ reachable from the server
- A Flowdacity Queue config file (see `default.conf` for a starter)

## Installation

Clone the repo and install the package plus dev tools (uses [`uv`](https://github.com/astral-sh/uv) by default):

```bash
uv sync --group dev
# or: uv pip install --system .
```

If you prefer pip/venv without `uv`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest pytest-cov
```

## Configuration

- Point the server at your FQ config via `FQ_CONFIG` (defaults to `./default.conf`).
- `default.conf` defines three sections:
  - `[fq]` queue behavior (intervals, requeue limits).
  - `[fq-server]` host/port for the HTTP server (used by Docker/local defaults).
  - `[redis]` connection details for your Redis instance.
- Copy and tweak as needed:

```bash
cp default.conf local.conf
# edit local.conf to match your Redis host/port/password
```

## Run the server locally

```bash
# ensure Redis is running (make redis starts a container)
make redis

# start the ASGI server
FQ_CONFIG=./local.conf uv run uvicorn asgi:app --host 0.0.0.0 --port 8080
```

Docker Compose is also available:

```bash
docker compose up --build
```

## API quick start

```bash
# health
curl http://127.0.0.1:8080/

# enqueue a job
curl -X POST http://127.0.0.1:8080/enqueue/sms/user42/ \
  -H "Content-Type: application/json" \
  -d '{"job_id":"job-1","payload":{"message":"hi"},"interval":1000}'

# dequeue
curl http://127.0.0.1:8080/dequeue/sms/

# mark finished
curl -X POST http://127.0.0.1:8080/finish/sms/user42/job-1/

# metrics
curl http://127.0.0.1:8080/metrics/
curl http://127.0.0.1:8080/metrics/sms/user42/
```

All endpoints return JSON; failures surface as HTTP 4xx/5xx with a `status` field in the body.

## Testing

Redis must be available. With dev deps installed:

```bash
uv run pytest
# or
make test
```

## License

MIT — see `LICENSE.txt`.
