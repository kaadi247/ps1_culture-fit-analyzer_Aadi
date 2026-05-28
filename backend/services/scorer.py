"""
Scorer service — calculates per-dimension fit scores from quiz answers.

The five dimensions are exactly:
  innovation, collaboration, mission, pace, people

For each submitted answer the user supplies:
  - question_index  (int)   index into quiz_questions array
  - selected_option (int)   0-based index of the chosen option (0=A, 1=B, 2=C, 3=D)

The scorer:
  1. Looks up the weight for the selected option in quiz_questions[question_index].weights
  2. Groups all weights by the question's dimension
  3. Averages the weights per dimension
  4. Produces overall_fit_score as the mean of all dimension averages (rounded to nearest int)

Returns:
  {
    "dimension_scores": {
      "innovation": <float>,
      "collaboration": <float>,
      "mission": <float>,
      "pace": <float>,
      "people": <float>
    },
    "overall_fit_score": <int>   (0-10)
  }
"""

import json
from typing import Any, Dict, List

VALID_DIMENSIONS = ["innovation", "collaboration", "mission", "pace", "people"]


def calculate_scores(
    quiz_questions: List[Dict[str, Any]],
    answers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate dimension scores from quiz answers.

    Args:
        quiz_questions: The stored quiz_questions list from the Report row.
                        Each item must have 'dimension' and 'weights' keys.
        answers:        List of answer dicts from the request body.
                        Each must have 'question_index' (int) and
                        'selected_option' (int, 0-based).

    Returns:
        Dict with 'dimension_scores' (dict) and 'overall_fit_score' (int).
    """
    # Deserialise from DB JSON string if necessary
    if isinstance(quiz_questions, str):
        quiz_questions = json.loads(quiz_questions)

    if isinstance(answers, str):
        answers = json.loads(answers)

    # Accumulate weights per dimension
    dim_weights: Dict[str, List[float]] = {d: [] for d in VALID_DIMENSIONS}

    for answer in answers:
        q_idx = answer.get("question_index")
        opt_idx = answer.get("selected_option")

        if q_idx is None or opt_idx is None:
            continue
        if q_idx < 0 or q_idx >= len(quiz_questions):
            continue

        question = quiz_questions[q_idx]
        dimension = question.get("dimension")
        weights = question.get("weights", [])

        if dimension not in VALID_DIMENSIONS:
            continue
        if opt_idx < 0 or opt_idx >= len(weights):
            continue

        dim_weights[dimension].append(float(weights[opt_idx]))

    # Average per dimension (default 0 if no answers for that dimension)
    dimension_scores: Dict[str, float] = {}
    for dim in VALID_DIMENSIONS:
        ws = dim_weights[dim]
        dimension_scores[dim] = round(sum(ws) / len(ws), 2) if ws else 0.0

    # Overall fit score = mean of all dimension averages
    all_scores = list(dimension_scores.values())
    overall_fit_score = round(sum(all_scores) / len(all_scores)) if all_scores else 0

    return {
        "dimension_scores": dimension_scores,
        "overall_fit_score": overall_fit_score,
    }
