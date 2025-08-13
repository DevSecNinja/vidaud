.PHONY: help build build-optimized analyze-docker test run clean setup deps deps-prod lint lint-fix security health test-docker

# Default target
help:
	@echo "vidaud - Video to Audio Converter"
	@echo "================================="
	@echo ""
	@echo "Available targets:"
	@echo "  setup     - Initial project setup"
	@echo "  deps      - Install Python dependencies (dev + prod)"
	@echo "  deps-prod - Install production dependencies only"
	@echo "  test      - Run all tests with coverage"
	@echo "  test-unit - Run unit tests only (no network)"
	@echo "  test-integration - Run integration tests (requires network)"
	@echo "  test-docker - Run Docker Compose test with sample video"
	@echo "  lint      - Run code linting"
	@echo "  lint-fix  - Fix code formatting issues"
	@echo "  security  - Run security checks"
	@echo "  build     - Build Docker image"
	@echo "  build-optimized - Build optimized Docker image"
	@echo "  analyze-docker - Analyze Docker image size optimizations"
	@echo "  run       - Run with docker-compose"
	@echo "  health    - Check application health status"
	@echo "  clean     - Clean up containers and images"
	@echo "  help      - Show this help"

# Initial setup
setup:
	@echo "Setting up vidaud development environment..."
	./setup.sh
	$(MAKE) deps

# Install dependencies
deps:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

# Install only production dependencies
deps-prod:
	@echo "Installing production dependencies only..."
	pip install -r requirements-prod.txt

# Run tests
test:
	@echo "Running test suite..."
	python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run only unit tests (no network required)
test-unit:
	@echo "Running unit tests..."
	python -m pytest tests/ -v -m "not integration" --cov=src --cov-report=term-missing

# Run integration tests (requires network)
test-integration:
	@echo "Running integration tests (requires network access)..."
	python -m pytest tests/ -v -m integration

# Run Docker Compose test with sample video
test-docker:
	@echo "Running Docker Compose test..."
	@echo "Creating temporary test directory..."
	@mkdir -p /tmp/vidaud_test_input /tmp/vidaud_test_output
	@echo "Copying sample video file..."
	@cp test_input/sample_video.wmv /tmp/vidaud_test_input/ || (echo "Error: sample_video.wmv not found in test_input/"; exit 1)
	@echo "Starting Docker Compose test..."
	@COMPOSE_TEST_INPUT=/tmp/vidaud_test_input COMPOSE_TEST_OUTPUT=/tmp/vidaud_test_output \
		docker-compose -f docker-compose.test.yml up --build -d
	@echo "Waiting for container to start..."
	@sleep 10
	@echo "Checking health..."
	@for i in 1 2 3 4 5; do \
		if curl -s http://localhost:8080/health >/dev/null 2>&1; then \
			echo "✅ Container is healthy"; \
			break; \
		else \
			echo "⏳ Waiting for container... ($$i/5)"; \
			sleep 5; \
		fi; \
	done
	@echo "Getting logs from the last 30 seconds..."
	@docker-compose -f docker-compose.test.yml logs --since=30s
	@echo "Stopping test containers..."
	@docker-compose -f docker-compose.test.yml down
	@echo "Checking output files..."
	@ls -la /tmp/vidaud_test_output/ || echo "No output files found"
	@echo "Cleaning up temporary directories..."
	@rm -rf /tmp/vidaud_test_input /tmp/vidaud_test_output
	@echo "Docker test completed!"

# Run linting
lint:
	@echo "Running code linting..."
	python -m flake8 src/ tests/ || true
	python -m black --check src/ tests/ || true

# Fix code formatting
lint-fix:
	@echo "Fixing code formatting..."
	python -m black src/ tests/

# Run security checks
security:
	@echo "Running security checks..."
	python -m bandit -r src/ || true
	python -m safety check || true

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t vidaud:latest .

# Build optimized Docker image
build-optimized:
	@echo "Building optimized Docker image..."
	docker build -t vidaud:optimized -f Dockerfile.optimized .

# Analyze Docker image size
analyze-docker:
	@echo "Analyzing Docker image size optimizations..."
	./analyze_docker_size.sh

# Build multi-arch image
build-multi:
	@echo "Building multi-architecture Docker image..."
	docker buildx build --platform linux/amd64,linux/arm64 -t vidaud:latest .

# Run with docker-compose
run:
	@echo "Starting vidaud with docker-compose..."
	docker-compose up -d

# Stop docker-compose
stop:
	@echo "Stopping vidaud..."
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Clean up
clean:
	@echo "Cleaning up Docker containers and images..."
	docker-compose down --rmi all --volumes --remove-orphans || true
	docker rmi vidaud:latest vidaud:test || true
	docker system prune -f

# Development mode (run locally)
dev:
	@echo "Running in development mode..."
	PYTHONPATH=. python main.py

# Quick health check
health:
	@echo "Checking application health..."
	@response=$$(curl -s http://localhost:8080/health 2>/dev/null); \
	if [ $$? -eq 0 ] && [ -n "$$response" ]; then \
		status=$$(echo "$$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))"); \
		timestamp=$$(echo "$$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('timestamp', 'unknown'))"); \
		uptime=$$(echo "$$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data.get('uptime_seconds', 0):.1f}s\")"); \
		if [ "$$status" = "healthy" ]; then \
			echo "\033[32m✅ Status: $$status\033[0m"; \
			echo "\033[36mℹ️  Timestamp: $$timestamp\033[0m"; \
			echo "\033[36mℹ️  Uptime: $$uptime\033[0m"; \
		else \
			echo "\033[31m❌ Status: $$status\033[0m"; \
			echo "\033[33m⚠️  Timestamp: $$timestamp\033[0m"; \
			echo "\033[33m⚠️  Uptime: $$uptime\033[0m"; \
		fi; \
	else \
		echo "\033[31m❌ Health check failed - application unavailable\033[0m"; \
		echo "\033[33m⚠️  Is the application running on http://localhost:8080?\033[0m"; \
	fi
