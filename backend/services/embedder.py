"""
Embedder service — generates 768-dimensional text embeddings via
Gemini text-embedding-004.
"""

import asyncio
import os
from typing import List

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_EMBEDDING_MODEL = "gemini-embedding-001"
_EMBEDDING_DIM = 768
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _embed_sync(text: str) -> List[float]:
    result = _client.models.embed_content(
        model=_EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=_EMBEDDING_DIM,
        )
    )
    return result.embeddings[0].values


def _embed_query_sync(text: str) -> List[float]:
    result = _client.models.embed_content(
        model=_EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=_EMBEDDING_DIM,
        )
    )
    return result.embeddings[0].values


async def embed_text(text: str) -> List[float]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _embed_sync, text)


async def embed_texts(texts: List[str]) -> List[List[float]]:
    tasks = [embed_text(t) for t in texts]
    return await asyncio.gather(*tasks)


async def embed_query(text: str) -> List[float]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _embed_query_sync, text)
