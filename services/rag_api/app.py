
import os
import hashlib
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

API_TOKEN = os.getenv("API_TOKEN", "rag-local")
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://litellm:4000/v1")
EMBED_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-bge-m3")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "kb")

client = QdrantClient(url=QDRANT_URL)
app = FastAPI(title="Venice RAG API", version="1.0.0")

def _auth(token: Optional[str]):
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

async def embed_texts(texts: List[str]) -> List[List[float]]:
    payload = {"input": texts, "model": EMBED_MODEL}
    async with httpx.AsyncClient(timeout=60) as http:
        r = await http.post(f"{LITELLM_BASE_URL}/embeddings", json=payload)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Embeddings error: {r.text}")
        data = r.json()
        return [item["embedding"] for item in data.get("data", [])]

def _ensure_collection(dim: int):
    try:
        client.get_collection(COLLECTION)
    except Exception:
        client.recreate_collection(
            COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
        )

class IndexItem(BaseModel):
    id: Optional[str] = None
    text: str
    metadata: Optional[dict] = None

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/index")
async def index(items: List[IndexItem], authorization: Optional[str] = Header(None)):
    _auth(authorization.replace("Bearer ", "") if authorization else None)
    texts = [it.text for it in items]
    vectors = await embed_texts(texts)
    if not vectors:
        raise HTTPException(500, "No embeddings returned")
    dim = len(vectors[0])
    _ensure_collection(dim)
    points = []
    for it, vec in zip(items, vectors):
        pid = it.id or hashlib.sha1(it.text.encode()).hexdigest()
        points.append(PointStruct(id=pid, vector=vec, payload=it.metadata or {}))
    client.upsert(collection_name=COLLECTION, points=points)
    return {"upserted": len(points)}

@app.post("/query")
async def query(req: QueryRequest, authorization: Optional[str] = Header(None)):
    _auth(authorization.replace("Bearer ", "") if authorization else None)
    vec = (await embed_texts([req.query]))[0]
    res = client.search(collection_name=COLLECTION, query_vector=vec, limit=req.top_k)
    return {"matches": [{"id": r.id, "score": r.score, "payload": r.payload} for r in res]}
