"""
SQLAlchemy models and database connection for Culture Fit Analyzer.
Tables: companies, chunks, reports, quiz_results
"""

import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    raw_about_text = Column(Text, nullable=False)
    extracted_values = Column(JSONB, nullable=True)          # AI-extracted value keywords
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("Chunk", back_populates="company", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="company", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)           # Gemini text-embedding-004 → 768-dim

    company = relationship("Company", back_populates="chunks")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    culture_report = Column(Text, nullable=True)
    values_to_thrive = Column(Text, nullable=True)
    research_insights = Column(Text, nullable=True)          # includes real URLs from Serper
    quiz_questions = Column(JSONB, nullable=True)            # [{question, options, dimension, weights}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="reports")
    quiz_results = relationship("QuizResult", back_populates="report", cascade="all, delete-orphan")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    dimension_scores = Column(JSONB, nullable=True)          # {innovation: 7, collaboration: 4, ...}
    overall_fit_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    report = relationship("Report", back_populates="quiz_results")


# ---------------------------------------------------------------------------
# DB session dependency (for FastAPI)
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables (and ensure pgvector extension exists)."""
    with engine.connect() as conn:
        conn.execute(
            __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector;")
        )
        conn.commit()
    Base.metadata.create_all(bind=engine)
