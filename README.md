# Local LLM Stack

A complete local LLM stack optimized for RTX 4090 with tool calling capabilities, vector search, and observability.

## Features

- **vLLM Server**: High-performance LLM inference with OpenAI-compatible API
- **Embeddings**: HuggingFace Text Embeddings Inference for vector embeddings
- **Vector Database**: Qdrant for semantic search and RAG
- **Orchestrator**: LangGraph-based agent with tool calling capabilities
- **Observability**: Langfuse for tracing and monitoring
- **Tool Integration**: Extensible tool system for code execution, file operations, and custom functions

## Hardware Requirements

- **GPU**: RTX 4090 (24GB VRAM) - primary LLM inference
- **RAM**: 128GB DDR4 (recommended)
- **Storage**: 500GB+ NVMe SSD (1TB preferred)
- **CPU**: AMD 5950X or equivalent

## Quick Start

1. **Setup**:
   ```bash
   ./scripts/setup.sh
   ```

2. **Start Services**:
   ```bash
   make up
   ```

3. **Check Status**:
   ```bash
   make health
   ```

4. **Run Tests**:
   ```bash
   make smoke
   ```

## Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| vLLM | http://localhost:8000 | LLM inference server |
| Embeddings | http://localhost:8081 | Text embeddings service |
| Qdrant | http://localhost:6333 | Vector database |
| Langfuse | http://localhost:3000 | Observability dashboard |
| Orchestrator | http://localhost:8001 | Main API with tool calling |

## Chat Interfaces

### 🌐 Web Interface (Recommended)
A beautiful, responsive web chat interface with real-time status monitoring.

```bash
./start_chat.sh
# Choose option 1 for web interface
```

Then open: `file:///home/ggurov/local_llm/chat_interface.html`

### 🐍 Streamlit Interface
A rich Python-based interface with sidebar, system monitoring, and tool information.

```bash
./start_chat.sh
# Choose option 2 for Streamlit interface
```

Requires: `pip install streamlit`

## API Usage

### Chat Completions (OpenAI Compatible)

```bash
curl -X POST http://localhost:8001/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
    "messages": [
      {"role": "user", "content": "Hello, can you help me?"}
    ],
    "temperature": 0.7
  }'
```

### Simple Chat

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What tools are available?"}'
```

### Tool Execution

```bash
curl -X POST http://localhost:8001/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "get_map",
    "arguments": {"key": "boost_target"}
  }'
```

### Available Tools

- `get_map`: Fetch data structures by key
- `apply_patch`: Apply code patches and run tests
- `search_logs`: Search through log files
- `run_tests`: Execute unit tests
- `file_operations`: Read, write, list, delete files

## Configuration

Edit `.env` file to customize:

```bash
# Model Configuration
MODEL_ID=Qwen/Qwen2.5-32B-Instruct-AWQ
MAX_MODEL_LEN=16384
GPU_MEM_UTIL=0.92

# Service URLs
OPENAI_COMPAT_URL=http://localhost:8000/v1
EMBED_URL=http://localhost:8081
QDRANT_URL=http://localhost:6333
```

## Management Commands

```bash
make help          # Show all available commands
make up            # Start all services
make down          # Stop all services
make restart       # Restart all services
make logs          # View orchestrator logs
make logs-all      # View all service logs
make health        # Check service health
make smoke         # Run smoke tests
make test-full     # Run complete test suite
make clean         # Clean up containers
make gpu-info      # Show GPU information
make monitor       # Monitor GPU and system resources
```

## Development

### Adding New Tools

1. Add tool function to `orchestrator/app/tools.py`
2. Register tool in `ToolRegistry._register_default_tools()`
3. Add tool schema in `get_tool_schemas()`
4. Test with `make test-tools`

### Custom Models

To use different models, update the `MODEL_ID` in `.env`:

```bash
# For smaller models (faster, less VRAM)
MODEL_ID=Qwen/Qwen2.5-14B-Instruct-AWQ
MAX_MODEL_LEN=32768

# For larger contexts (requires more VRAM)
MODEL_ID=Qwen/Qwen2.5-32B-Instruct-AWQ
MAX_MODEL_LEN=8192
```

## Troubleshooting

### Out of Memory Errors

1. Reduce `MAX_MODEL_LEN` in `.env`
2. Lower `GPU_MEM_UTIL` (e.g., 0.85)
3. Switch to smaller model (14B instead of 32B)

### Service Won't Start

1. Check Docker is running: `docker ps`
2. Check GPU availability: `nvidia-smi`
3. Check logs: `make logs`
4. Run health check: `make health`

### Performance Issues

1. Check GPU utilization: `make monitor`
2. Verify model is loaded: `make smoke`
3. Check system resources: `htop`, `nvidia-smi`

## Network Access

To access from remote clients, update `.env`:

```bash
# Bind to all interfaces
OPENAI_COMPAT_URL=http://0.0.0.0:8000/v1
EMBED_URL=http://0.0.0.0:8081
QDRANT_URL=http://0.0.0.0:6333
LANGFUSE_URL=http://0.0.0.0:3000
```

Then restart services: `make restart`

## Security Notes

- Change default secrets in production
- Use firewall rules for network access
- Consider authentication for production use
- Regularly update Docker images

## License

MIT License - see LICENSE file for details.

