"""
Culture Fit Analyzer — FastAPI application entry point.

Endpoints registered:
  GET  /health                          — UptimeRobot keep-warm check
  POST /companies/analyze               — chunk + embed + store About Us text
  GET  /companies/                      — list all analyzed companies
  POST /reports/generate/{company_id}   — full RAG + search + generation pipeline
  GET  /reports/{company_id}            — fetch stored report
  POST /quiz/submit/{report_id}         — submit quiz answers, calculate scores
  GET  /quiz/results/{result_id}        — fetch quiz result for spider chart

Environment variables (from .env / host):
  GEMINI_API_KEY   — Google AI Studio key
  DATABASE_URL     — PostgreSQL connection string (must support pgvector)
  SERPER_API_KEY   — Serper.dev search API key
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.db import Base, engine, init_db
from routers import companies, reports, quiz

load_dotenv()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Culture Fit Analyzer API",
    description=(
        "Full-stack AI app that analyzes company culture from About Us text "
        "using RAG (pgvector + Gemini embeddings), real web search (Serper), "
        "and Gemini 2.5 Flash generation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow all origins during development; restrict to Vercel URL in prod
# ---------------------------------------------------------------------------

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,*",  # Vite default: 5173
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup: create tables
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    """Ensure pgvector extension and all tables exist on startup."""
    init_db()
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Health check (for UptimeRobot keep-warm monitoring)
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
def health_check():
    """Returns {"status": "ok"} — used by UptimeRobot to prevent Render cold starts."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(companies.router)
app.include_router(reports.router)
app.include_router(quiz.router)
