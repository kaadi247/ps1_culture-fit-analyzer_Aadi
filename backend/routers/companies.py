"""
Router: /companies
Handles text ingestion, chunking, embedding, and storage.

Endpoints:
  POST /companies/analyze   — accept About Us text, chunk, embed, store
  GET  /companies/          — list all analyzed companies
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.db import Company, Chunk, get_db
from services.chunker import chunk_text
from services.embedder import embed_texts
from utils.value_extractor import extract_company_info

router = APIRouter(prefix="/companies", tags=["companies"])

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    about_text: str = Field(..., min_length=1, description="Raw About Us text")
    company_name: Optional[str] = Field(
        default="", description="Optional company name (auto-extracted if blank)"
    )


class ChunkOut(BaseModel):
    chunk_index: int
    chunk_text: str

    class Config:
        from_attributes = True


class CompanyOut(BaseModel):
    id: int
    name: Optional[str]
    extracted_values: Optional[list]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class AnalyzeResponse(BaseModel):
    company_id: int
    company_name: str
    chunks_created: int
    extracted_values: list
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=AnalyzeResponse, status_code=201)
async def analyze_company(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Accept plain About Us text, chunk it into ~300-word segments with
    50-word overlap, embed each chunk via Gemini text-embedding-004,
    and store everything in PostgreSQL.

    Enforces a minimum of 150 words as recommended in CONTEXT.md.
    """
    word_count = len(payload.about_text.split())
    if word_count < 150:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Text too short ({word_count} words). "
                "Please paste at least 150 words from the company's About Us page "
                "for meaningful analysis."
            ),
        )

    # Extract company info
    info = extract_company_info(payload.about_text, payload.company_name or "")

    # Persist company row
    company = Company(
        name=info["company_name"],
        raw_about_text=payload.about_text,
        extracted_values=info["extracted_values"],
    )
    db.add(company)
    db.flush()  # get company.id before committing

    # Chunk the text
    chunks = chunk_text(payload.about_text)
    if not chunks:
        db.rollback()
        raise HTTPException(status_code=422, detail="Chunking produced no segments.")

    # Embed all chunks concurrently
    embeddings = await embed_texts(chunks)

    # Store chunks with embeddings
    chunk_rows = []
    for idx, (chunk_str, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_rows.append(
            Chunk(
                company_id=company.id,
                chunk_index=idx,
                chunk_text=chunk_str,
                embedding=embedding,
            )
        )
    db.add_all(chunk_rows)
    db.commit()
    db.refresh(company)

    return AnalyzeResponse(
        company_id=company.id,
        company_name=company.name or "",
        chunks_created=len(chunk_rows),
        extracted_values=info["extracted_values"],
        message=(
            f"Successfully chunked into {len(chunk_rows)} segments and "
            "embedded via Gemini text-embedding-004."
        ),
    )


@router.get("/", response_model=List[CompanyOut])
def list_companies(db: Session = Depends(get_db)):
    """Return a list of all analyzed companies (most recent first)."""
    companies = (
        db.query(Company)
        .order_by(Company.created_at.desc())
        .all()
    )
    return [
        CompanyOut(
            id=c.id,
            name=c.name,
            extracted_values=c.extracted_values or [],
            created_at=str(c.created_at) if c.created_at else None,
        )
        for c in companies
    ]
