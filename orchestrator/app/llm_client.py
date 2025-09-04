"""LLM client for communicating with vLLM server."""

import json
import time
from typing import Any, Dict, List, Optional
import httpx
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from .config import settings
from .models import ChatRequest, ChatResponse


class LLMClient:
    """Client for communicating with the vLLM server."""
    
    def __init__(self):
        self.base_url = settings.openai_compat_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.langchain_client = ChatOpenAI(
            base_url=self.base_url,
            api_key="dummy",  # vLLM doesn't require real API key
            model="Qwen/Qwen2.5-7B-Instruct-AWQ"
        )
    
    async def health_check(self) -> bool:
        """Check if the LLM server is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception:
            return False
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send chat completion request to vLLM."""
        
        payload = {
            "model": model or "Qwen/Qwen2.5-7B-Instruct-AWQ",
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if tools:
            payload["tools"] = tools
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"LLM request failed: {e}")
    
    async def chat_with_langchain(
        self,
        messages: List[str],
        system_message: Optional[str] = None
    ) -> str:
        """Use LangChain client for simpler chat interactions."""
        
        langchain_messages = []
        
        if system_message:
            langchain_messages.append(SystemMessage(content=system_message))
        
        for message in messages:
            langchain_messages.append(HumanMessage(content=message))
        
        try:
            response = await self.langchain_client.ainvoke(langchain_messages)
            return response.content
        except Exception as e:
            raise Exception(f"LangChain chat failed: {e}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

