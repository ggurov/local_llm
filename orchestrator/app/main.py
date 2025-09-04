"""Main FastAPI application for the orchestrator."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import settings
from .models import ChatRequest, ChatResponse, ChatMessage
from .langgraph_agent import LangGraphAgent
from .llm_client import LLMClient
from .vector_store import VectorStore


# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Global agent instance
agent: LangGraphAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global agent
    
    logger.info("Starting orchestrator...")
    
    # Initialize components
    agent = LangGraphAgent()
    
    # Health check
    health = await agent.health_check()
    logger.info(f"Health check: {health}")
    
    # Warm up the model with a dummy request
    try:
        await warm_up_model()
        logger.info("Model warmed up successfully")
    except Exception as e:
        logger.warning(f"Model warm-up failed: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down orchestrator...")


# Create FastAPI app
app = FastAPI(
    title="Local LLM Orchestrator",
    description="Orchestrator for local LLM with tool calling capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def warm_up_model():
    """Warm up the model with a dummy request."""
    try:
        llm_client = LLMClient()
        await llm_client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        await llm_client.close()
    except Exception as e:
        logger.warning(f"Model warm-up failed: {e}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Local LLM Orchestrator is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    health = await agent.health_check()
    return {
        "status": "healthy" if all(health.values()) else "unhealthy",
        "components": health,
        "timestamp": time.time()
    }


@app.get("/models")
async def list_models():
    """List available models."""
    try:
        llm_client = LLMClient()
        response = await llm_client.client.get(f"{llm_client.base_url}/models")
        await llm_client.close()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {e}")


@app.post("/chat/completions")
async def chat_completions(request: ChatRequest):
    """Chat completions endpoint."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Convert request to ChatMessage objects
        messages = [
            ChatMessage(role=msg.role, content=msg.content)
            for msg in request.messages
        ]
        
        # Process through the agent
        result = await agent.process_request(messages)
        
        # Create response in OpenAI format
        response = ChatResponse(
            id=f"chatcmpl-{int(time.time())}",
            created=int(time.time()),
            model=request.model or "Qwen/Qwen2.5-7B-Instruct-AWQ",
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result["response"]
                },
                "finish_reason": "stop"
            }]
        )
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {e}")


@app.post("/chat")
async def simple_chat(request: Dict[str, Any]):
    """Simple chat endpoint."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Create chat request
        chat_request = ChatRequest(
            messages=[ChatMessage(role="user", content=message)]
        )
        
        # Process through the agent
        result = await agent.process_request(chat_request.messages)
        
        return {
            "response": result["response"],
            "status": result["status"],
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Simple chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")


@app.post("/tools/execute")
async def execute_tool(request: Dict[str, Any]):
    """Execute a tool directly."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        tool_name = request.get("tool_name")
        arguments = request.get("arguments", {})
        tool_call_id = request.get("tool_call_id", "direct_call")
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="tool_name is required")
        
        result = await agent.tool_registry.execute_tool(
            tool_name, tool_call_id, arguments
        )
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {e}")


@app.get("/tools/schemas")
async def get_tool_schemas():
    """Get available tool schemas."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return agent.tool_registry.get_tool_schemas()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.orchestrator_port,
        reload=True,
        log_level=settings.log_level.lower()
    )

