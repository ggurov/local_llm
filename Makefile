# Local LLM Stack Makefile
# Quality-of-life commands for managing the local LLM stack

.PHONY: help up down logs smoke test health clean build restart status

# Default target
help: ## Show this help message
	@echo "Local LLM Stack Management"
	@echo "========================="
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services
	@echo "Starting local LLM stack..."
	docker compose up -d --build
	@echo "Services started. Use 'make logs' to view logs or 'make status' to check status."

down: ## Stop all services
	@echo "Stopping local LLM stack..."
	docker compose down
	@echo "Services stopped."

restart: ## Restart all services
	@echo "Restarting local LLM stack..."
	docker compose restart
	@echo "Services restarted."

build: ## Build all services
	@echo "Building local LLM stack..."
	docker compose build
	@echo "Build completed."

logs: ## Follow orchestrator logs
	@echo "Following orchestrator logs (Ctrl+C to exit)..."
	docker compose logs -f orchestrator

logs-all: ## Follow all service logs
	@echo "Following all service logs (Ctrl+C to exit)..."
	docker compose logs -f

status: ## Check status of all services
	@echo "Service Status:"
	@echo "==============="
	@docker compose ps

health: ## Check health of all services
	@echo "Health Check:"
	@echo "============="
	@echo "vLLM Server:"
	@curl -s http://localhost:8000/v1/models | jq '.data[0].id' 2>/dev/null || echo "❌ vLLM not responding"
	@echo "Embeddings Server:"
	@curl -s http://localhost:8081/health | jq '.status' 2>/dev/null || echo "❌ Embeddings not responding"
	@echo "Qdrant:"
	@curl -s http://localhost:6333/collections | jq '.collections' 2>/dev/null || echo "❌ Qdrant not responding"
	@echo "Langfuse:"
	@curl -s http://localhost:3000/api/public/health | jq '.status' 2>/dev/null || echo "❌ Langfuse not responding"
	@echo "Orchestrator:"
	@curl -s http://localhost:8001/health | jq '.status' 2>/dev/null || echo "❌ Orchestrator not responding"

smoke: ## Quick smoke test - send a ping to vLLM
	@echo "Smoke Test - Testing vLLM..."
	@curl -s http://localhost:8000/v1/chat/completions \
		-H 'Content-Type: application/json' \
		-d '{"model":"Qwen/Qwen2.5-32B-Instruct-AWQ","messages":[{"role":"user","content":"ping"}],"max_tokens":10}' | jq '.choices[0].message.content' || echo "❌ Smoke test failed"

test-chat: ## Test the orchestrator chat endpoint
	@echo "Testing orchestrator chat..."
	@curl -s http://localhost:8001/chat \
		-H 'Content-Type: application/json' \
		-d '{"message":"Hello, can you help me?"}' | jq '.response' || echo "❌ Chat test failed"

test-tools: ## Test tool execution
	@echo "Testing tool execution..."
	@curl -s http://localhost:8001/tools/execute \
		-H 'Content-Type: application/json' \
		-d '{"tool_name":"get_map","arguments":{"key":"boost_target"}}' | jq '.result' || echo "❌ Tool test failed"

test-full: ## Run full test suite
	@echo "Running full test suite..."
	@$(MAKE) health
	@$(MAKE) smoke
	@$(MAKE) test-chat
	@$(MAKE) test-tools
	@echo "✅ Full test suite completed"

clean: ## Clean up containers and volumes
	@echo "Cleaning up..."
	docker compose down -v
	docker system prune -f
	@echo "Cleanup completed."

clean-data: ## Clean up data volumes (WARNING: This will delete all data)
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	docker compose down -v
	sudo rm -rf data/qdrant data/langfuse data/hf_cache
	@echo "Data cleanup completed."

setup: ## Initial setup - create directories and set permissions
	@echo "Setting up directories..."
	mkdir -p data/qdrant data/langfuse data/hf_cache
	chmod 755 data/qdrant data/langfuse data/hf_cache
	@echo "Setup completed."

gpu-info: ## Show GPU information
	@echo "GPU Information:"
	@echo "================"
	@nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits

monitor: ## Monitor GPU and system resources
	@echo "Monitoring resources (Ctrl+C to exit)..."
	@watch -n 2 'nvidia-smi --query-gpu=name,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits && echo "" && free -h'

# Development helpers
dev-logs: ## Follow logs for development
	@echo "Following development logs..."
	docker compose logs -f orchestrator vllm

dev-restart: ## Restart only the orchestrator for development
	@echo "Restarting orchestrator..."
	docker compose restart orchestrator

dev-shell: ## Open shell in orchestrator container
	@echo "Opening shell in orchestrator container..."
	docker compose exec orchestrator /bin/bash

# Model management
download-model: ## Download the default model (requires HF token)
	@echo "Downloading model..."
	@echo "Make sure to set HF_TOKEN in .env file"
	docker compose run --rm vllm python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen2.5-32B-Instruct-AWQ')"

# Backup and restore
backup: ## Backup data volumes
	@echo "Creating backup..."
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz data/
	@echo "Backup created."

restore: ## Restore from backup (specify BACKUP_FILE=filename.tar.gz)
	@echo "Restoring from backup..."
	@if [ -z "$(BACKUP_FILE)" ]; then echo "Usage: make restore BACKUP_FILE=backup-YYYYMMDD-HHMMSS.tar.gz"; exit 1; fi
	tar -xzf $(BACKUP_FILE)
	@echo "Restore completed."

