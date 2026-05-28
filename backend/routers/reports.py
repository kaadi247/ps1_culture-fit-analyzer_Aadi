"""
Router: /reports
Handles the full RAG + web search + Gemini generation pipeline.

Endpoints:
  POST /reports/generate/{company_id}  — run full pipeline, store report
  GET  /reports/{company_id}           — retrieve stored report for a company
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from models.db import Company, Report, get_db
from services.retriever import retrieve_relevant_chunks
from services.searcher import search_company_research
from services.generator import generate_culture_report

router = APIRouter(prefix="/reports", tags=["reports"])


def _to_str(value: Any) -> str:
    """Serialize value to a JSON string if it is a list or dict; return as-is if already a string."""
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return value or ""


def _parse_quiz_questions(value: Any) -> List[Dict[str, Any]]:
    """Ensure quiz_questions is a Python list for Pydantic/ReportOut consumption.

    The DB column stores a JSON string; Gemini returns a native list.
    Handles both cases safely.
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ReportOut(BaseModel):
    id: int
    company_id: int
    culture_report: Optional[str]
    values_to_thrive: Optional[str]
    research_insights: Optional[str]
    quiz_questions: Optional[List[Dict[str, Any]]]
    created_at: Optional[str]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/generate/{company_id}", response_model=ReportOut, status_code=201)
async def generate_report(
    company_id: int,
    db: Session = Depends(get_db),
):
    """
    Full RAG + web search + Gemini generation pipeline:

    1. Load company row (validates company exists and has chunks).
    2. Fire five parallel semantic retrieval queries via pgvector.
    3. Fire two Serper web search queries for real citations.
    4. Call Gemini 2.5 Flash with all retrieved context.
    5. Persist the structured JSON response as a Report row.
    6. Return the stored report.
    """
    # 1. Validate company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found.")

    # 2. Semantic retrieval
    chunks = await retrieve_relevant_chunks(company_id, db)
    if not chunks:
        raise HTTPException(
            status_code=422,
            detail=(
                "No embedded chunks found for this company. "
                "Please run POST /companies/analyze first."
            ),
        )

    # 3. Web search
    values: List[str] = company.extracted_values or []
    company_name: str = company.name or "Unknown Company"
    try:
        search_results = await search_company_research(company_name, values)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # 4. Gemini generation
    try:
        generated = await generate_culture_report(chunks, search_results)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        # Handle Gemini 429 / transient errors gracefully
        raise HTTPException(status_code=503, detail=str(exc))

    # 5. Persist report — keep original list for response, store JSON strings in DB
    raw_values_to_thrive = generated.get("values_to_thrive", "")
    raw_research_insights = generated.get("research_insights", "")
    raw_quiz_questions = generated.get("quiz_questions", [])

    # DB storage: psycopg2 requires strings, not raw Python lists/dicts
    quiz_questions_str = _to_str(raw_quiz_questions)
    # ReportOut: quiz_questions field is List[Dict], so keep as native list
    quiz_questions_list = _parse_quiz_questions(raw_quiz_questions)

    report = Report(
        company_id=company_id,
        culture_report=generated.get("culture_report", ""),
        values_to_thrive=_to_str(raw_values_to_thrive),
        research_insights=_to_str(raw_research_insights),
        quiz_questions=quiz_questions_str,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportOut(
        id=report.id,
        company_id=report.company_id,
        culture_report=report.culture_report,
        values_to_thrive=report.values_to_thrive,
        research_insights=report.research_insights,
        quiz_questions=quiz_questions_list,
        created_at=str(report.created_at) if report.created_at else None,
    )


@router.get("/{company_id}", response_model=ReportOut)
def get_report(company_id: int, db: Session = Depends(get_db)):
    """Return the most recent stored report for a company."""
    report = (
        db.query(Report)
        .filter(Report.company_id == company_id)
        .order_by(Report.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for company {company_id}.",
        )

    return ReportOut(
        id=report.id,
        company_id=report.company_id,
        culture_report=report.culture_report,
        values_to_thrive=report.values_to_thrive,
        research_insights=report.research_insights,
        # DB stores quiz_questions as a JSON string — parse back to list for ReportOut
        quiz_questions=_parse_quiz_questions(report.quiz_questions),
        created_at=str(report.created_at) if report.created_at else None,
    )
