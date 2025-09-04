"""Vector store client for Qdrant."""

import json
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import httpx

from .config import settings


class VectorStore:
    """Vector store client for Qdrant."""
    
    def __init__(self):
        self.qdrant_client = QdrantClient(url=settings.qdrant_url)
        self.embed_url = settings.embed_url
        self.collection_name = "documents"
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the collection exists."""
        try:
            collections = self.qdrant_client.get_collections()
            if self.collection_name not in [c.name for c in collections.collections]:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1024,  # BGE-large-en-v1.5 embedding size
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"Warning: Could not ensure collection exists: {e}")
    
    async def embed_text(self, text: str) -> List[float]:
        """Get embeddings for text using the embeddings service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.embed_url}/embed",
                    json={"inputs": [text]}
                )
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["embedding"]
        except Exception as e:
            raise Exception(f"Embedding failed: {e}")
    
    async def add_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a document to the vector store."""
        try:
            embedding = await self.embed_text(text)
            
            point = PointStruct(
                id=document_id,
                vector=embedding,
                payload={
                    "text": text,
                    "metadata": metadata or {}
                }
            )
            
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
        except Exception as e:
            raise Exception(f"Failed to add document: {e}")
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            query_embedding = await self.embed_text(query)
            
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload["text"],
                    "metadata": result.payload.get("metadata", {})
                }
                for result in results
            ]
        except Exception as e:
            raise Exception(f"Search failed: {e}")
    
    async def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            collections = self.qdrant_client.get_collections()
            return True
        except Exception:
            return False

