"""Data models for the orchestrator."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")


class ToolCall(BaseModel):
    """Tool call model."""
    id: str = Field(..., description="Tool call ID")
    type: str = Field(default="function", description="Tool call type")
    function: Dict[str, Any] = Field(..., description="Function details")


class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    model: Optional[str] = Field(default=None, description="Model to use")
    temperature: Optional[float] = Field(default=0.7, description="Temperature")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens")
    stream: Optional[bool] = Field(default=False, description="Stream response")


class ToolResponse(BaseModel):
    """Tool response model."""
    tool_call_id: str = Field(..., description="Tool call ID")
    result: Any = Field(..., description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error message if any")


class ChatResponse(BaseModel):
    """Chat response model."""
    id: str = Field(..., description="Response ID")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[Dict[str, Any]] = Field(..., description="Response choices")
    usage: Optional[Dict[str, int]] = Field(default=None, description="Token usage")


class ToolSchema(BaseModel):
    """Tool schema model."""
    type: str = Field(default="function", description="Tool type")
    function: Dict[str, Any] = Field(..., description="Function schema")

