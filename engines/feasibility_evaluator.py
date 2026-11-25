
from assessment_models import FeasibilityInput


# Equal weights for the five TELOS dimensions.
FEASIBILITY_WEIGHTS = {
    "technical": 0.20,
    "economic": 0.20,
    "legal": 0.20,
    "operational": 0.20,
    "schedule": 0.20
}


DIMENSION_DESCRIPTIONS = {
    "technical": "Evaluates whether the required technology, infrastructure and technical capabilities are available.",
    "economic": "Evaluates whether the project is financially viable within its available budget and expected costs.",
    "legal": "Evaluates whether the project can satisfy applicable laws, regulations and compliance requirements.",
    "operational": "Evaluates whether the team, resources and operational capabilities are sufficient.",
    "schedule": "Evaluates whether the project can be completed within the proposed timeline."
}


def get_value(data, key, default=None):
    """Read a value from either a dictionary or an object."""

    if isinstance(data, dict):
        return data.get(key, default)

    return getattr(data, key, default)


def convert_rating_to_score(rating):
    """Convert a 1-5 rating into a percentage."""

    return round((rating / 5) * 100, 2)


def determine_feasibility_level(score):
    """Classify the overall feasibility score."""

    if score >= 80:
        return "Highly Feasible"

    elif score >= 60:
        return "Moderately Feasible"

    elif score >= 40:
        return "Limited Feasibility"

    return "Low Feasibility"


def evaluate_dimensions(feasibility_inputs):
    """Calculate individual TELOS dimension scores."""

    dimensions = {}
    available_weight = 0

    for dimension, weight in FEASIBILITY_WEIGHTS.items():

        rating = get_value(feasibility_inputs, dimension)

        if rating is None:
            dimensions[dimension] = {
                "rating": None,
                "score": None,
                "weight": weight,
                "status": "Not Assessed",
                "description": DIMENSION_DESCRIPTIONS[dimension]
            }

            continue

        score = convert_rating_to_score(rating)
        available_weight += weight

        dimensions[dimension] = {
            "rating": rating,
            "score": score,
            "weight": weight,
            "status": (
                "Strong" if rating >= 4
                else "Moderate" if rating == 3
                else "Needs Improvement"
            ),
            "description": DIMENSION_DESCRIPTIONS[dimension]
        }

    return dimensions, available_weight


def calculate_overall_feasibility(dimensions, available_weight):
    """Calculate a weighted score using assessed dimensions only."""

    if available_weight == 0:
        return None

    weighted_total = 0

    for dimension, weight in FEASIBILITY_WEIGHTS.items():

        score = dimensions[dimension]["score"]

        if score is not None:
            weighted_total += score * weight

    # Normalize the score when some dimensions are not assessed.
    overall_score = weighted_total / available_weight

    return round(overall_score, 2)


def evaluate_feasibility(feasibility_inputs):
    """
    Perform a TELOS-based feasibility assessment.

    Only explicitly supplied ratings are scored.
    Missing ratings are excluded rather than assumed to be zero.
    """

    dimensions, available_weight = evaluate_dimensions(
        feasibility_inputs
    )

    overall_score = calculate_overall_feasibility(
        dimensions,
        available_weight
    )

    assessed_count = sum(
        1 for details in dimensions.values()
        if details["rating"] is not None
    )

    completeness = round((assessed_count / 5) * 100, 2)

    if overall_score is None:
        feasibility_level = "Insufficient Information"
    else:
        feasibility_level = determine_feasibility_level(
            overall_score
        )

    return {
        "dimensions": dimensions,
        "overall_feasibility_score": overall_score,
        "feasibility_level": feasibility_level,
        "assessment_completeness": completeness,
        "assessed_dimensions": assessed_count,
        "total_dimensions": 5,
        "missing_dimensions": [
            dimension
            for dimension, details in dimensions.items()
            if details["rating"] is None
        ],
        "method": "TELOS Weighted Feasibility Assessment"
    }
