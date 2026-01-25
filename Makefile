.PHONY: all clean test redis-up redis-down

# Default target
all: clean test

# Remove Python + build artifacts
clean:
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*~" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	rm -rf dist build *.egg-info

# Run tests — prefers pytest, falls back to python modules
test: redis-up
	@status=0; \
	uv run pytest tests || uv run python -m unittest discover -s tests || status=$$?; \
	$(MAKE) redis-down; \
	exit $$status

# Start Redis container
redis-up:
	docker compose up -d redis

# Stop Redis container
redis-down:
	docker compose down
