"""Configuration management for the orchestrator."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service URLs
    openai_compat_url: str = "http://localhost:8000/v1"
    embed_url: str = "http://localhost:8081"
    qdrant_url: str = "http://localhost:6333"
    
    # Langfuse configuration
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = "dev_public_key"
    langfuse_secret_key: str = "dev_secret_key"
    
    # Orchestrator configuration
    orchestrator_port: int = 8001
    log_level: str = "INFO"
    
    # Tool configuration
    tools_dir: str = "/app/tools"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        fields = {
            'openai_compat_url': {'env': 'OPENAI_COMPAT_URL'},
            'embed_url': {'env': 'EMBED_URL'},
            'qdrant_url': {'env': 'QDRANT_URL'},
            'langfuse_host': {'env': 'LANGFUSE_HOST'},
            'langfuse_public_key': {'env': 'LANGFUSE_PUBLIC_KEY'},
            'langfuse_secret_key': {'env': 'LANGFUSE_SECRET_KEY'},
            'orchestrator_port': {'env': 'ORCHESTRATOR_PORT'},
            'log_level': {'env': 'LOG_LEVEL'},
            'tools_dir': {'env': 'TOOLS_DIR'}
        }


# Global settings instance
settings = Settings()
