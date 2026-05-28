"""
Searcher service — Serper API web search calls for real citation-grounded
research insights.

Two queries are fired per company analysis:
  1. "{company_name} company culture research"
  2. "{value1} {value2} {value3} workplace culture studies statistics"

The SERPER_API_KEY is read from the environment. Never hardcoded.
"""

import os
from typing import List, Dict, Any

import httpx
from dotenv import load_dotenv

load_dotenv()

SERPER_ENDPOINT = "https://google.serper.dev/search"
RESULTS_PER_QUERY = 3


async def search_company_research(
    company_name: str, values: List[str]
) -> List[Dict[str, Any]]:
    """
    Fire two Serper searches and return a combined list of result dicts.

    Each result dict contains:
      - title   (str)
      - snippet (str)
      - url     (str)

    Args:
        company_name: Human-readable company name (e.g. "KVGAI Tech").
        values:       List of extracted value keywords from the company text.

    Returns:
        List of search result dicts (up to RESULTS_PER_QUERY * 2 entries).
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise RuntimeError("SERPER_API_KEY environment variable is not set.")

    queries = [
        f"{company_name} company culture research",
        f"{' '.join(values[:3])} workplace culture studies statistics",
    ]

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    results: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        for query in queries:
            try:
                response = await client.post(
                    SERPER_ENDPOINT,
                    json={"q": query, "num": RESULTS_PER_QUERY},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("organic", [])[:RESULTS_PER_QUERY]:
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "url": item.get("link", ""),
                        }
                    )
            except httpx.HTTPStatusError as exc:
                # Log and continue — search failures should not crash generation
                print(f"[searcher] Serper HTTP error for query '{query}': {exc}")
            except Exception as exc:
                print(f"[searcher] Unexpected error for query '{query}': {exc}")

    return results
