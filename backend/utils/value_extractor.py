"""
Value extractor utility — extracts company name and value keywords from
plain About Us text using simple heuristics.

These are passed to the Serper searcher to build targeted search queries.
No LLM call is made here — this runs before generation to seed the search.
"""

import re
from typing import Dict, Any, List

# Common value-signal words that indicate culture / values statements
VALUE_SIGNALS = [
    "innovation", "innovative", "collaborate", "collaboration", "transparency",
    "integrity", "excellence", "diversity", "inclusion", "sustainability",
    "customer", "community", "growth", "impact", "trust", "accountability",
    "agility", "passion", "creativity", "empowerment", "respect", "quality",
    "mission", "vision", "purpose", "people", "performance", "leadership",
]


def extract_company_name(text: str, fallback_name: str = "Unknown Company") -> str:
    """
    Attempt to extract a company name from the first two sentences of the text.

    Strategy:
      - Look for capitalised proper-noun sequences in the first 300 chars.
      - Fall back to the caller-supplied name if nothing is found.
    """
    sample = text[:300]
    # Match two or more consecutive capitalised words (e.g. "KVGAI Tech Pvt")
    matches = re.findall(r"(?:[A-Z][a-zA-Z&]+(?:\s+[A-Z][a-zA-Z&]+){1,4})", sample)
    if matches:
        return matches[0]
    return fallback_name


def extract_value_keywords(text: str) -> List[str]:
    """
    Find value-signal words present in the text (case-insensitive).
    Returns a deduplicated list ordered by first occurrence.
    """
    lower = text.lower()
    seen: set = set()
    keywords: List[str] = []
    for word in VALUE_SIGNALS:
        if word in lower and word not in seen:
            seen.add(word)
            keywords.append(word)
    return keywords


def extract_company_info(text: str, supplied_name: str = "") -> Dict[str, Any]:
    """
    High-level helper used by the companies router.

    Returns:
      {
        "company_name": str,
        "extracted_values": [str, ...]   # value keywords found in text
      }
    """
    name = supplied_name.strip() if supplied_name.strip() else extract_company_name(text)
    values = extract_value_keywords(text)
    return {
        "company_name": name,
        "extracted_values": values,
    }
