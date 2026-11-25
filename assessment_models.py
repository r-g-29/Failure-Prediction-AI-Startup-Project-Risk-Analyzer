
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class RiskInput(BaseModel):
    """Ratings used to evaluate the project's risk profile."""

    budget_adequacy: int = Field(
        ge=1, le=5,
        description="Adequacy of the available project budget. 1 = Very Poor, 5 = Excellent.",
        examples=[3]
    )

    market_validation: int = Field(
        ge=1, le=5,
        description="Evidence of customer demand and market validation. 1 = Very Poor, 5 = Excellent.",
        examples=[4]
    )

    technical_readiness: int = Field(
        ge=1, le=5,
        description="Availability and maturity of required technology. 1 = Very Poor, 5 = Excellent.",
        examples=[4]
    )

    team_experience: int = Field(
        ge=1, le=5,
        description="Relevant skills and experience of the project team. 1 = Very Poor, 5 = Excellent.",
        examples=[3]
    )

    resource_availability: int = Field(
        ge=1, le=5,
        description="Availability of people, infrastructure and other resources. 1 = Very Poor, 5 = Excellent.",
        examples=[3]
    )

    competition_intensity: int = Field(
        ge=1, le=5,
        description="Intensity of competition. 1 = Very Low, 5 = Very High.",
        examples=[3]
    )

    regulatory_complexity: int = Field(
        ge=1, le=5,
        description="Complexity of applicable regulations. 1 = Very Low, 5 = Very High.",
        examples=[2]
    )


class IdentifiedRisk(BaseModel):
    """Details of an individual project risk."""

    title: str = Field(
        min_length=3,
        max_length=150,
        description="Short title describing the identified risk.",
        examples=["Insufficient project funding"]
    )

    category: Literal[
        "Financial",
        "Market",
        "Technical",
        "Operational",
        "Legal",
        "Other"
    ] = Field(
        description="Category to which the identified risk belongs.",
        examples=["Financial"]
    )

    likelihood: int = Field(
        ge=1, le=5,
        description="Likelihood of the risk occurring. 1 = Very Low, 5 = Very High.",
        examples=[4]
    )

    impact: int = Field(
        ge=1, le=5,
        description="Impact if the risk occurs. 1 = Very Low, 5 = Very High.",
        examples=[5]
    )

    description: str = Field(
        min_length=5,
        description="Explanation of the identified risk.",
        examples=["Available funding may not cover development and deployment costs."]
    )

    mitigation: str = Field(
        min_length=5,
        description="Suggested action to reduce or manage the risk.",
        examples=["Prepare a detailed budget and identify additional funding sources."]
    )


class RiskAssessmentRequest(BaseModel):
    ratings: RiskInput

    identified_risks: List[IdentifiedRisk] = Field(
        default_factory=list,
        description="Optional list of risks identified for the project."
    )


class FeasibilityInput(BaseModel):
    """Ratings for the five TELOS feasibility dimensions."""

    technical: Optional[int] = Field(
        default=None, ge=1, le=5,
        description="Technical feasibility: availability of technology and infrastructure. 1 = Very Poor, 5 = Excellent.",
        examples=[4]
    )

    economic: Optional[int] = Field(
        default=None, ge=1, le=5,
        description="Economic feasibility: financial viability and affordability. 1 = Very Poor, 5 = Excellent.",
        examples=[3]
    )

    legal: Optional[int] = Field(
        default=None, ge=1, le=5,
        description="Legal feasibility: ability to satisfy applicable laws and regulations. 1 = Very Poor, 5 = Excellent.",
        examples=[4]
    )

    operational: Optional[int] = Field(
        default=None, ge=1, le=5,
        description="Operational feasibility: availability of team and operational resources. 1 = Very Poor, 5 = Excellent.",
        examples=[3]
    )

    schedule: Optional[int] = Field(
        default=None, ge=1, le=5,
        description="Schedule feasibility: ability to complete the project within the proposed timeline. 1 = Very Poor, 5 = Excellent.",
        examples=[3]
    )


class ProjectEvaluationRequest(BaseModel):
    """Complete request for combined Milestone 2 project evaluation."""

    ratings: RiskInput

    identified_risks: List[IdentifiedRisk] = Field(
        default_factory=list,
        description="Optional risks identified by the project team."
    )

    feasibility: FeasibilityInput

    market_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Market research information such as market trends, demand and competition.",
        examples=[{
            "market_trend": "Growing demand for AI-based solutions",
            "competition": "High competition from established platforms"
        }]
    )

    additional_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional project details such as industry, business model and target users.",
        examples=[{
            "industry": "Healthcare",
            "business_model": "Subscription-based",
            "target_users": "Hospitals and clinics"
        }]
    )

    use_gemini: bool = Field(
        default=True,
        description="Whether to attempt Gemini enhancement of SWOT analysis."
    )
