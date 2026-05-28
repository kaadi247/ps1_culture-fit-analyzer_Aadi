"""
Generator service — Gemini 2.5 Flash generation calls.

Builds the full RAG + Serper prompt and returns a parsed JSON dict with keys:
  culture_report    (str)
  values_to_thrive  (str)
  research_insights (str)
  quiz_questions    (list of {question, options, dimension, weights})

Quiz dimensions are exactly: innovation, collaboration, mission, pace, people.
Each quiz_question must have:
  - question  (str)
  - options   (array of 4 strings)
  - dimension (one of the five above)
  - weights   (array of 4 integers 1–10)

The generator strips markdown fences and wraps json.loads in try/except as
recommended in CONTEXT.md to handle Gemini's occasional non-pure-JSON output.

Uses the new google.genai SDK (google-genai package).
Do NOT use google.generativeai, genai.configure(), or GenerativeModel().
"""

import asyncio
import json
import os
import re
import time
from typing import Any, Dict, List

from google import genai
from dotenv import load_dotenv

load_dotenv()

_GENERATION_MODEL = "gemini-2.5-flash"

VALID_DIMENSIONS = {"innovation", "collaboration", "mission", "pace", "people"}


def _get_client() -> genai.Client:
    """Create a Gemini client from the environment API key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
    return genai.Client(api_key=api_key)


def _build_prompt(
    chunks: List[Dict[str, Any]],
    search_results: List[Dict[str, Any]],
) -> str:
    """Build the full generation prompt from retrieved chunks and Serper results."""

    chunks_section = "\n".join(
        f"[CHUNK {i + 1}]: {c['chunk_text']}" for i, c in enumerate(chunks)
    )

    search_section = (
        "\n".join(
            f"[SOURCE {i + 1}]: {r['title']} — {r['snippet']} — URL: {r['url']}"
            for i, r in enumerate(search_results)
        )
        if search_results
        else "[No web search results available]"
    )

    prompt = f"""You are analyzing a company's culture based on retrieved text from their About Us page.

Retrieved chunks from the company's About Us:
{chunks_section}

Web search results about this company's culture:
{search_section}

Generate a structured JSON response with these exact keys:
- culture_report: 3-paragraph analysis of company culture grounded ONLY in retrieved chunks. Do NOT reference "chunk 1", "chunk 2" etc in your output. The chunks are your private context only. Never mention them.
- values_to_thrive: bullet list of 5 specific values a person needs to fit in, each explained in 2 sentences. Do NOT reference "chunk 1", "chunk 2" etc in your output. The chunks are your private context only. Never mention them.
- research_insights: Write 2 paragraphs of research insights. For every claim you make, you MUST embed the actual URL inline in the text using this exact format: (source: https://actual-url-here.com). Do NOT write "Source 1" or "Source 2" — always use the real URL from the context provided. If a search result has no URL, skip it entirely. Only cite sources that are genuinely relevant to this company's culture. Do NOT reference "chunk 1", "chunk 2" etc in your output. The chunks are your private context only. Never mention them.
- quiz_questions: array of exactly 8 questions, each with:
    - question: string
    - options: array of 4 plain strings with NO letter prefix (do not start options with "A.", "B.", "C.", or "D.")
    - dimension: one of [innovation, collaboration, mission, pace, people]
    - weights: array of 4 integers 1-10 representing fit score for each option

Rules:
- Distribute quiz_questions across all 5 dimensions (at least 1 question per dimension)
- weights must align with the option order (index 0 = option A weight, etc.)
- IMPORTANT for weights: Do NOT always make option B the highest weighted answer. Vary which option (A, B, C, or D) represents the best cultural fit across different questions. The ideal answer should be unpredictable and distributed across all four options throughout the 8 questions. Each weight array should reflect genuine scoring variation — some questions may have A as best, others C or D.
- Return ONLY valid JSON. No preamble. No markdown. No code fences.
"""
    return prompt


def clean_gemini_json(text: str) -> str:
    """Remove ```json or ``` fences that Gemini sometimes wraps around JSON output."""
    text = text.strip()
    # Remove ```json or ``` fences
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def _generate_sync(prompt: str) -> str:
    """Synchronous Gemini generation call with 3-attempt exponential backoff retry."""
    client = _get_client()
    last_exc: Exception = Exception("Unknown error")

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=_GENERATION_MODEL,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            last_exc = e
            if attempt == 2:
                raise Exception(
                    "Gemini is experiencing high demand. Please try again in a moment."
                ) from last_exc
            wait = 5 * (attempt + 1)
            print(f"Gemini retry attempt {attempt + 1}, waiting {wait}s... ({e})")
            time.sleep(wait)

    # Unreachable, but satisfies type checkers
    raise last_exc


async def generate_culture_report(
    chunks: List[Dict[str, Any]],
    search_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Run the full Gemini generation and return the parsed JSON dict.

    Raises ValueError if the response cannot be parsed as valid JSON.
    Raises RuntimeError on Gemini 429 rate-limit or other API errors.
    """
    prompt = _build_prompt(chunks, search_results)

    loop = asyncio.get_event_loop()
    try:
        raw_text = await loop.run_in_executor(None, _generate_sync, prompt)
    except Exception as exc:
        raise RuntimeError(f"Gemini generation failed: {exc}") from exc

    try:
        data = json.loads(clean_gemini_json(raw_text))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini returned non-JSON output. Raw (first 500 chars): {clean_gemini_json(raw_text)[:500]}"
        ) from exc

    # Validate required keys
    required_keys = {"culture_report", "values_to_thrive", "research_insights", "quiz_questions"}
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(f"Gemini response missing required keys: {missing}")

    # Validate quiz_questions structure
    questions = data.get("quiz_questions", [])
    for i, q in enumerate(questions):
        if q.get("dimension") not in VALID_DIMENSIONS:
            raise ValueError(
                f"quiz_questions[{i}].dimension '{q.get('dimension')}' "
                f"is not one of {sorted(VALID_DIMENSIONS)}"
            )
        if len(q.get("options", [])) != 4:
            raise ValueError(f"quiz_questions[{i}].options must have exactly 4 items.")
        if len(q.get("weights", [])) != 4:
            raise ValueError(f"quiz_questions[{i}].weights must have exactly 4 items.")

    return data
