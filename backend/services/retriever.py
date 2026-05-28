"""
Retriever service — semantic similarity search against stored chunk embeddings
using pgvector's cosine distance operator (<=>).

Five parallel retrieval queries are fired against the chunks table for each
company, one per cultural dimension (from CONTEXT.md):
  1. "What are the core values of this company?"
  2. "What is the mission and long-term vision?"
  3. "What kind of person thrives in this culture?"
  4. "What does this company believe about work and people?"
  5. "What are the behavioural expectations at this company?"
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from services.embedder import embed_query

# The five semantic retrieval queries fired in parallel
RETRIEVAL_QUERIES = [
    "What are the core values of this company?",
    "What is the mission and long-term vision?",
    "What kind of person thrives in this culture?",
    "What does this company believe about work and people?",
    "What are the behavioural expectations at this company?",
]

TOP_K = 3  # top chunks per query


async def retrieve_relevant_chunks(
    company_id: int, db: Session
) -> List[Dict[str, Any]]:
    """
    Run all RETRIEVAL_QUERIES against the chunks for *company_id*.

    Returns a deduplicated list of the most relevant chunk dicts,
    each containing: { chunk_id, chunk_index, chunk_text }.
    """
    seen_ids: set = set()
    results: List[Dict[str, Any]] = []

    for query_text in RETRIEVAL_QUERIES:
        query_embedding = await embed_query(query_text)

        # pgvector cosine distance: embedding <=> '[...]' returns 0 for identical vectors
        sql = text(
            """
            SELECT id, chunk_index, chunk_text,
                   embedding <=> CAST(:vec AS vector) AS distance
            FROM chunks
            WHERE company_id = :company_id
              AND embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT :top_k
            """
        )
        rows = db.execute(
            sql,
            {
                "vec": str(query_embedding),
                "company_id": company_id,
                "top_k": TOP_K,
            },
        ).fetchall()

        for row in rows:
            if row.id not in seen_ids:
                seen_ids.add(row.id)
                results.append(
                    {
                        "chunk_id": row.id,
                        "chunk_index": row.chunk_index,
                        "chunk_text": row.chunk_text,
                    }
                )

    return results
