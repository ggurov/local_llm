#!/usr/bin/env python3
"""Simple embeddings service using sentence-transformers."""

import os
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Load the model
model_name = os.getenv("MODEL_ID", "all-MiniLM-L6-v2")
print(f"Loading embeddings model: {model_name}")
model = SentenceTransformer(model_name)
print("Model loaded successfully!")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "model": model_name}

@app.post("/embed")
async def embed(data: dict):
    """Generate embeddings for input text."""
    inputs = data.get("inputs", [])
    if not inputs:
        return {"error": "No inputs provided"}
    
    try:
        embeddings = model.encode(inputs)
        return {
            "data": [{"embedding": emb.tolist()} for emb in embeddings]
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
