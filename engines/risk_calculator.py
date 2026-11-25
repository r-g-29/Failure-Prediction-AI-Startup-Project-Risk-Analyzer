
from assessment_models import RiskAssessmentRequest


# Relative importance of each risk category.
RISK_WEIGHTS = {
    "financial_risk": 0.20,
    "market_risk": 0.25,
    "technical_risk": 0.20,
    "operational_risk": 0.20,
    "competition_regulatory_risk": 0.15
}


def calculate_category_scores(ratings):
    """Calculate normalized risk scores for each category."""

    financial = ((6 - ratings.budget_adequacy) / 5) * 100

    market = ((6 - ratings.market_validation) / 5) * 100

    technical = ((6 - ratings.technical_readiness) / 5) * 100

    operational = ((6 - ratings.team_experience) + (6 - ratings.resource_availability)) / 10 * 100

    competition_regulatory = (ratings.competition_intensity + ratings.regulatory_complexity - 2) / 8 * 100

    return {
        "financial_risk": round(financial, 2),
        "market_risk": round(market, 2),
        "technical_risk": round(technical, 2),
        "operational_risk": round(operational, 2),
        "competition_regulatory_risk": round(
            competition_regulatory, 2
        )
    }


def calculate_overall_risk(category_scores):
    """Calculate the weighted overall risk score."""

    overall = sum(
        category_scores[category] * weight
        for category, weight in RISK_WEIGHTS.items()
    )

    return round(overall, 2)


def determine_risk_level(score):

    if score < 35:
        return "Low"
    elif score < 65:
        return "Medium"
    else:
        return "High"


def evaluate_individual_risks(identified_risks):
    """Calculate likelihood-impact scores for individual risks."""

    evaluated_risks = []

    for risk in identified_risks:
        score = risk.likelihood * risk.impact

        if score >= 17:
            level = "Critical"
        elif score >= 10:
            level = "High"
        elif score >= 5:
            level = "Medium"
        else:
            level = "Low"

        evaluated_risks.append({
            "title": risk.title,
            "category": risk.category,
            "description": risk.description,
            "likelihood": risk.likelihood,
            "impact": risk.impact,
            "risk_matrix_score": score,
            "risk_level": level,
            "mitigation": risk.mitigation
        })

    return sorted(
        evaluated_risks,
        key=lambda risk: risk["risk_matrix_score"],
        reverse=True
    )


def calculate_risk(request: RiskAssessmentRequest):
    """Execute the complete risk assessment and scoring process."""

    ratings = request.ratings

    category_scores = calculate_category_scores(ratings)

    overall_score = calculate_overall_risk(category_scores)

    risk_level = determine_risk_level(overall_score)

    individual_risks = evaluate_individual_risks(
        request.identified_risks
    )

    top_contributors = sorted(
        category_scores,
        key=category_scores.get,
        reverse=True
    )[:3]

    return {
        **category_scores,

        "overall_risk_score": overall_score,
        "risk_level": risk_level,

        # This is an indicator, not a trained ML prediction.
        "success_potential_indicator": round(
            100 - overall_score, 2
        ),

        "risk_contributors": [
            category.replace("_", " ").title()
            for category in top_contributors
        ],

        "identified_risks": individual_risks,

        "input_data": ratings.dict()
    }
