"""
Router: /quiz
Handles quiz answer submission, score calculation, and result retrieval.

Endpoints:
  POST /quiz/submit/{report_id}    — accept answers, calculate scores, store
  GET  /quiz/results/{result_id}  — retrieve scores for spider chart rendering
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.db import QuizResult, Report, get_db
from services.scorer import calculate_scores

router = APIRouter(prefix="/quiz", tags=["quiz"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class AnswerItem(BaseModel):
    question_index: int = Field(
        ..., ge=0, description="0-based index into quiz_questions array"
    )
    selected_option: int = Field(
        ..., ge=0, le=3, description="0-based option index (0=A, 1=B, 2=C, 3=D)"
    )


class SubmitQuizRequest(BaseModel):
    answers: List[AnswerItem] = Field(
        ..., min_length=1, description="List of quiz answers"
    )


class DimensionScores(BaseModel):
    innovation: float
    collaboration: float
    mission: float
    pace: float
    people: float


class QuizResultOut(BaseModel):
    id: int
    report_id: int
    dimension_scores: DimensionScores
    overall_fit_score: int
    created_at: Optional[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/submit/{report_id}", response_model=QuizResultOut, status_code=201)
def submit_quiz(
    report_id: int,
    payload: SubmitQuizRequest,
    db: Session = Depends(get_db),
):
    """
    Accept quiz answers for a report, calculate per-dimension scores via
    scorer.py, persist the result, and return it.

    Scoring logic:
      - Look up each answer's weight from quiz_questions[question_index].weights[selected_option]
      - Average weights per dimension across all answers
      - Compute overall_fit_score as the mean of the 5 dimension averages
    """
    # Validate report exists
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")

    if not report.quiz_questions:
        raise HTTPException(
            status_code=422,
            detail="This report has no quiz questions. Re-generate the report first.",
        )

    # Convert pydantic models to plain dicts for scorer
    answers_dicts = [a.model_dump() for a in payload.answers]

    scored = calculate_scores(report.quiz_questions, answers_dicts)
    dim_scores = scored["dimension_scores"]
    overall = scored["overall_fit_score"]

    # Persist result
    result = QuizResult(
        report_id=report_id,
        dimension_scores=dim_scores,
        overall_fit_score=overall,
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    return QuizResultOut(
        id=result.id,
        report_id=result.report_id,
        dimension_scores=DimensionScores(
            innovation=dim_scores.get("innovation", 0.0),
            collaboration=dim_scores.get("collaboration", 0.0),
            mission=dim_scores.get("mission", 0.0),
            pace=dim_scores.get("pace", 0.0),
            people=dim_scores.get("people", 0.0),
        ),
        overall_fit_score=result.overall_fit_score,
        created_at=str(result.created_at) if result.created_at else None,
    )


@router.get("/results/{result_id}", response_model=QuizResultOut)
def get_quiz_results(result_id: int, db: Session = Depends(get_db)):
    """Return the stored quiz result for spider chart rendering."""
    result = db.query(QuizResult).filter(QuizResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Quiz result {result_id} not found."
        )

    dim_scores = result.dimension_scores or {}

    return QuizResultOut(
        id=result.id,
        report_id=result.report_id,
        dimension_scores=DimensionScores(
            innovation=dim_scores.get("innovation", 0.0),
            collaboration=dim_scores.get("collaboration", 0.0),
            mission=dim_scores.get("mission", 0.0),
            pace=dim_scores.get("pace", 0.0),
            people=dim_scores.get("people", 0.0),
        ),
        overall_fit_score=result.overall_fit_score or 0,
        created_at=str(result.created_at) if result.created_at else None,
    )
