.PHONY: all clean test

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
test:
	@if python -c "import pytest" 2>/dev/null; then \
		python -m pytest -q; \
	else \
		echo 'pytest not installed — running direct test modules'; \
		python -m tests.test_routes; \
	fi
