# Culture Fit Analyzer

Paste any company's About Us text. Get an AI-generated culture report, real research citations, and a diagnostic quiz that renders your cultural fit as a spider chart across 5 dimensions.

**Live Demo:** https://ps1-culture-fit-analyzer-aadi.vercel.app/

---

## What It Does

1. You paste a company's About Us / Mission / Culture page text
2. The app chunks it, embeds it via Gemini, and stores it in a pgvector database
3. Five semantic retrieval queries fire against the stored chunks to extract cultural signals
4. Real web searches run via Serper API for citation-grounded research insights
5. Gemini 2.5 Flash generates a structured culture report, values breakdown, and 8-question diagnostic quiz
6. You take the quiz and get your cultural fit score visualized as a spider chart across 5 dimensions

Nothing in the output is hallucinated. Every claim traces back to either the company's own text or a real web source.

---

## Architecture

```
User pastes About Us text
        ↓
FastAPI backend receives text
        ↓
Text chunked into ~300-word overlapping segments
        ↓
Each chunk embedded via Gemini text-embedding-001 → 768-dim vector
Vectors stored in PostgreSQL via pgvector
        ↓
Five parallel semantic retrieval queries fired via cosine similarity:
  "What are the core values of this company?"
  "What is the mission and long-term vision?"
  "What kind of person thrives in this culture?"
  "What does this company believe about work and people?"
  "What are the behavioural expectations at this company?"
        ↓
Serper API fires two web searches for real citations
        ↓
Gemini 2.5 Flash generates:
  → Culture Report (3 paragraphs, grounded in retrieved chunks)
  → Values to Thrive (5 specific values with explanations)
  → Research Insights (2 paragraphs with real embedded URLs)
  → 8-question diagnostic quiz calibrated to retrieved company values
        ↓
Frontend renders report, quiz, and spider chart
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Backend | FastAPI + Python 3.12 |
| LLM Generation | Gemini 2.5 Flash |
| Embeddings | gemini-embedding-001 (768 dimensions) |
| Vector Store | pgvector on PostgreSQL 16 |
| Web Search | Serper API |
| Database | PostgreSQL 16 on Render |
| Frontend | Vite + React |
| Spider Chart | Recharts RadarChart |
| Backend Deploy | Render Web Service |
| Frontend Deploy | Vercel |

---

## The 5 Spider Chart Dimensions

Quiz questions map to 5 universal cultural dimensions:

1. **Innovation** — how much does this company value creative risk-taking?
2. **Collaboration** — team-first or independent ownership?
3. **Mission** — values-driven vs commercially driven?
4. **Pace** — fast-moving startup energy or structured stability?
5. **People** — how much does this company invest in its people?

---

## Local Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL with pgvector extension enabled
- Gemini API key (free at aistudio.google.com)
- Serper API key (free at serper.dev)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in `/backend`:

```
GEMINI_API_KEY=your_gemini_key_here
DATABASE_URL=your_postgresql_connection_string_here
SERPER_API_KEY=your_serper_key_here
```

Enable pgvector on your database:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Start the backend:
```bash
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
```

Create a `.env.local` file in `/frontend`:

```
VITE_API_URL=http://localhost:8000
```

Start the frontend:
```bash
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/companies/analyze` | Chunk, embed, and store About Us text |
| POST | `/reports/generate/{company_id}` | Run full RAG + search + generation pipeline |
| GET | `/reports/{company_id}` | Fetch stored report |
| POST | `/quiz/submit/{report_id}` | Submit quiz answers, calculate scores |
| GET | `/quiz/results/{result_id}` | Fetch quiz result for spider chart |

---

## Project Structure

```
culture_fit_analyzer/
├── backend/
│   ├── main.py                  # FastAPI app entry point, CORS config
│   ├── requirements.txt
│   ├── .env.example
│   ├── routers/
│   │   ├── companies.py         # Text ingestion, chunking, embedding
│   │   ├── reports.py           # RAG pipeline, generation
│   │   └── quiz.py              # Quiz submission, scoring
│   ├── services/
│   │   ├── chunker.py           # 300-word overlapping chunks
│   │   ├── embedder.py          # Gemini embedding calls
│   │   ├── retriever.py         # pgvector cosine similarity retrieval
│   │   ├── generator.py         # Gemini 2.5 Flash generation
│   │   ├── searcher.py          # Serper API web search
│   │   └── scorer.py            # Quiz dimension score calculation
│   ├── models/
│   │   └── db.py                # SQLAlchemy models + DB connection
│   └── utils/
│       └── value_extractor.py   # Company name + value keyword extraction
└── frontend/
    └── src/
        ├── App.jsx              # All screens + components
        └── services/
            └── api.js           # API call functions
```

---

## Resume Description

Built a full-stack RAG application that analyzes company culture from About Us text. Implemented document chunking and vector embedding via Gemini text-embedding-001, stored vectors in PostgreSQL via pgvector, and performed semantic retrieval across five cultural dimensions. Integrated real-time web search via Serper API for citation-grounded research insights. Generated dynamic diagnostic quizzes calibrated to retrieved company values, with results visualized as a spider chart across five dimensions. Deployed on Render and Vercel.

---

*Built for PS-I 2026 internship evaluation at KVGAI Tech Pvt. Ltd.*
