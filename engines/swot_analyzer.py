
import json
import os
import re
from typing import Any


# --------------------------------------------------
# SWOT INDICATORS
# --------------------------------------------------

MARKET_OPPORTUNITY_INDICATORS = [
    "growing demand",
    "increasing demand",
    "market growth",
    "market opportunity",
    "low competition",
    "few competitors",
    "limited competition",
    "funding availability",
    "government support",
    "increasing adoption",
    "growing awareness"
]

MARKET_THREAT_INDICATORS = [
    "high competition",
    "strong competitors",
    "market saturation",
    "declining demand",
    "low demand",
    "weak demand",
    "rising costs",
    "inflation",
    "regulatory restrictions",
    "cybersecurity risk",
    "limited funding",
    "legal uncertainty"
]


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def get_value(data: Any, key: str, default=None):
    """Retrieve a value from a dictionary or object."""

    if isinstance(data, dict):
        return data.get(key, default)

    return getattr(data, key, default)


def collect_text(data: Any) -> str:
    """Convert nested dictionaries and lists into searchable text."""

    if data is None:
        return ""

    if isinstance(data, dict):
        return " ".join(
            collect_text(value)
            for value in data.values()
        )

    if isinstance(data, (list, tuple)):
        return " ".join(
            collect_text(value)
            for value in data
        )

    return str(data)


def append_unique(items: list, value: str):
    """Append a finding only if it is not already present."""

    if value not in items:
        items.append(value)


def find_matches(text: str, keywords: list) -> list:
    """Match complete words and phrases to reduce false positives."""

    text = text.lower()
    matches = []

    for keyword in keywords:
        pattern = (
            r"(?<!\w)"
            + re.escape(keyword.lower())
            + r"(?!\w)"
        )

        if re.search(pattern, text):
            matches.append(keyword)

    return matches


def prepare_project_context(
    project,
    additional_context=None
) -> dict:
    """Collect relevant project information."""

    fields = [
        "project_id",
        "project_name",
        "name",
        "project_type",
        "industry_sector",
        "industry",
        "business_model",
        "budget",
        "target_market",
        "description",
        "technical_readiness",
        "team_experience",
        "resource_availability"
    ]

    context = {}

    for field in fields:

        value = get_value(project, field)

        if value is None or value == "":
            value = get_value(additional_context, field)

        if value is not None and value != "":
            context[field] = value

    return context


# --------------------------------------------------
# RISK INFORMATION HELPERS
# --------------------------------------------------

def get_identified_risks(risk_assessment):
    """Retrieve identified risks from the risk assessment."""

    risks = get_value(
        risk_assessment,
        "identified_risks",
        []
    )

    if not isinstance(risks, (list, tuple)):
        return []

    return risks


def get_risk_severity(risk: Any):
    """
    Calculate the severity of an identified risk.

    Uses the existing risk matrix score when available.
    Otherwise, calculates likelihood multiplied by impact.
    """

    score = get_value(risk, "risk_matrix_score")

    likelihood = get_value(risk, "likelihood")
    impact = get_value(risk, "impact")

    if score is None and likelihood is not None and impact is not None:
        score = likelihood * impact

    try:
        score = float(score)
    except (TypeError, ValueError):
        return None, None

    if score >= 17:
        severity = "Critical"

    elif score >= 10:
        severity = "High"

    elif score >= 5:
        severity = "Medium"

    else:
        severity = "Low"

    return score, severity


# --------------------------------------------------
# INTERNAL SWOT ANALYSIS
# --------------------------------------------------

def analyze_internal_factors(
    project,
    additional_context=None,
    risk_assessment=None
):
    """
    Identify internal strengths and weaknesses.

    Uses:
    - Project information
    - Additional project context
    - Risk assessment ratings
    - Identified project risks

    External market and legal risks are returned separately
    so they can be included under SWOT threats.
    """

    strengths = []
    weaknesses = []
    external_risk_threats = []

    # Retrieve information from project first.
    # If unavailable, check additional_context.

    def get_project_value(key):

        value = get_value(project, key)

        if value is None or value == "":
            value = get_value(additional_context, key)

        return value

    description = str(
        get_project_value("description") or ""
    ).lower()

    business_model = get_project_value("business_model")
    budget = get_project_value("budget")

    technical_readiness = get_project_value(
        "technical_readiness"
    )

    team_experience = get_project_value(
        "team_experience"
    )

    resource_availability = get_project_value(
        "resource_availability"
    )

    # ----------------------------------------------
    # BUSINESS MODEL
    # ----------------------------------------------

    if business_model:

        append_unique(
            strengths,
            f"The project has a specified business model: {business_model}."
        )

    else:

        append_unique(
            weaknesses,
            "The business model has not been specified."
        )

    # ----------------------------------------------
    # BUDGET
    # ----------------------------------------------

    if budget is None:

        append_unique(
            weaknesses,
            "Budget information is missing, limiting financial assessment."
        )

    elif isinstance(budget, (int, float)) and budget <= 0:

        append_unique(
            weaknesses,
            "The supplied budget is invalid and needs to be reviewed."
        )

    # ----------------------------------------------
    # TECHNICAL READINESS
    # ----------------------------------------------

    if technical_readiness is not None:

        if technical_readiness <= 2:

            append_unique(
                weaknesses,
                "The reported technical readiness is low."
            )

        elif technical_readiness >= 4:

            append_unique(
                strengths,
                "The project reports a good level of technical readiness."
            )

    # ----------------------------------------------
    # TEAM EXPERIENCE
    # ----------------------------------------------

    if team_experience is not None:

        if team_experience <= 2:

            append_unique(
                weaknesses,
                "The reported team experience may be insufficient "
                "for project execution."
            )

        elif team_experience >= 4:

            append_unique(
                strengths,
                "The project reports a strong level of team experience."
            )

    # ----------------------------------------------
    # RESOURCE AVAILABILITY
    # ----------------------------------------------

    if resource_availability is not None:

        if resource_availability <= 2:

            append_unique(
                weaknesses,
                "Limited resource availability may affect execution."
            )

        elif resource_availability >= 4:

            append_unique(
                strengths,
                "The project reports good resource availability."
            )

    # ----------------------------------------------
    # RISK ASSESSMENT INPUT RATINGS
    # ----------------------------------------------

    input_data = get_value(
        risk_assessment,
        "input_data",
        {}
    )

    internal_rating_rules = {
        "budget_adequacy":
            "The project reports inadequate budget availability.",

        "market_validation":
            "The project has limited evidence of market validation.",

        "technical_readiness":
            "The project reports low technical readiness.",

        "team_experience":
            "The project reports insufficient team experience.",

        "resource_availability":
            "The project reports limited resource availability."
    }

    for field, message in internal_rating_rules.items():

        rating = get_value(input_data, field)

        if rating is not None and rating <= 2:

            append_unique(
                weaknesses,
                message
            )

    # ----------------------------------------------
    # COMPETITION AND REGULATORY RATINGS
    # ----------------------------------------------

    competition_rating = get_value(
        input_data,
        "competition_intensity"
    )

    regulatory_rating = get_value(
        input_data,
        "regulatory_complexity"
    )

    if competition_rating is not None and competition_rating >= 4:

        append_unique(
            external_risk_threats,
            "The project faces high competition intensity."
        )

    if regulatory_rating is not None and regulatory_rating >= 4:

        append_unique(
            external_risk_threats,
            "The project may face significant regulatory complexity."
        )

    # ----------------------------------------------
    # IDENTIFIED PROJECT RISKS
    # ----------------------------------------------

    identified_risks = get_identified_risks(
        risk_assessment
    )

    for risk in identified_risks:

        category = str(
            get_value(risk, "category", "Other")
        ).strip().lower()

        title = str(
            get_value(risk, "title", "Unspecified risk")
        ).strip()

        risk_description = str(
            get_value(risk, "description", "")
        ).strip()

        score, severity = get_risk_severity(risk)

        # Ignore risks below Medium severity.
        if score is None or score < 5 or not title:
            continue

        # Internal risks become weaknesses.
        if category in {
            "financial",
            "technical",
            "operational"
        }:

            finding = (
                f"Identified internal {category} risk "
                f"({severity}): {title}."
            )

            if risk_description:
                finding += f" {risk_description}"

            append_unique(
                weaknesses,
                finding
            )

        # External risks become threats.
        elif category in {
            "market",
            "legal"
        }:

            finding = (
                f"Identified external {category} risk "
                f"({severity}): {title}."
            )

            if risk_description:
                finding += f" {risk_description}"

            append_unique(
                external_risk_threats,
                finding
            )

    # ----------------------------------------------
    # PROJECT DESCRIPTION
    # ----------------------------------------------

    if not description.strip():

        append_unique(
            weaknesses,
            "The project description is missing or insufficient."
        )

    # ----------------------------------------------
    # DEFAULT FINDINGS
    # ----------------------------------------------

    if not strengths:

        strengths.append(
            "Insufficient information is available to establish "
            "specific internal strengths."
        )

    if not weaknesses:

        weaknesses.append(
            "No major internal weakness was identified from "
            "the supplied information."
        )

    return strengths, weaknesses, external_risk_threats


# --------------------------------------------------
# EXTERNAL SWOT ANALYSIS
# --------------------------------------------------

def analyze_external_factors(
    market_analysis=None,
    additional_threats=None
):

    opportunities = []
    threats = []

    market_text = collect_text(
        market_analysis
    ).lower()

    matched_opportunities = find_matches(
        market_text,
        MARKET_OPPORTUNITY_INDICATORS
    )

    matched_threats = find_matches(
        market_text,
        MARKET_THREAT_INDICATORS
    )

    # Market opportunities
    for indicator in matched_opportunities:

        append_unique(
            opportunities,
            f"Market analysis indicates: {indicator}."
        )

    # Market threats
    for indicator in matched_threats:

        append_unique(
            threats,
            f"Market analysis indicates: {indicator}."
        )

    # Additional external threats from risk assessment
    for threat in additional_threats or []:

        append_unique(
            threats,
            threat
        )

    # Default findings
    if not opportunities:

        opportunities.append(
            "Additional market research is required to identify "
            "specific external opportunities."
        )

    if not threats:

        threats.append(
            "Additional market research is required to identify "
            "specific external threats."
        )

    return opportunities, threats


# --------------------------------------------------
# RULE-BASED SWOT GENERATION
# --------------------------------------------------

def generate_rule_based_swot(
    project,
    market_analysis=None,
    additional_context=None,
    risk_assessment=None
):

    # Analyze internal factors and extract external risks.
    strengths, weaknesses, external_risk_threats = (
        analyze_internal_factors(
            project=project,
            additional_context=additional_context,
            risk_assessment=risk_assessment
        )
    )

    # Analyze market information and external risks.
    opportunities, threats = analyze_external_factors(
        market_analysis=market_analysis,
        additional_threats=external_risk_threats
    )

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats,
        "provider": "rules"
    }


# --------------------------------------------------
# GEMINI REFINEMENT
# --------------------------------------------------

def refine_swot_with_gemini(
    project,
    swot_result,
    market_analysis=None,
    additional_context=None,
    risk_assessment=None
):

    api_key = os.getenv("GEMINI_API_KEY")

    # Use rule-based output when API key is unavailable.
    if not api_key:
        return swot_result

    try:

        from google import genai

        client = genai.Client(
            api_key=api_key
        )

        model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.0-flash"
        )

        context = {
            "project": prepare_project_context(
                project,
                additional_context
            ),
            "market_analysis": market_analysis,
            "additional_context": additional_context,
            "risk_assessment": risk_assessment,
            "initial_swot": swot_result
        }

        prompt = f"""
You are an evidence-aware project evaluation assistant.

Refine the supplied SWOT analysis.

Rules:

1. Use only the supplied project, market and risk information.
2. Do not invent statistics, competitors, laws or market trends.
3. Keep strengths and weaknesses focused on internal factors.
4. Keep opportunities and threats focused on external factors.
5. Financial, technical and operational project risks belong
   under weaknesses when they indicate internal limitations.
6. Market and legal risks belong under threats.
7. Preserve material Medium, High and Critical risk findings
   from the initial SWOT analysis.
8. Do not classify AI usage alone as a proven strength.
9. Do not treat potential findings as verified facts.
10. If evidence is insufficient, clearly mention that more
    information is needed.
11. Avoid repeating the same finding in multiple categories.
12. Use clear, concise and professional language.
13. Return valid JSON only.

Expected JSON structure:

{{
    "strengths": [],
    "weaknesses": [],
    "opportunities": [],
    "threats": []
}}

Input information:

{json.dumps(context, default=str)}
"""

        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        if not response.text:
            return swot_result

        response_text = response.text.strip()

        # Remove Markdown code fences if returned by Gemini.
        response_text = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response_text
        ).strip()

        result = json.loads(response_text)

        required_categories = [
            "strengths",
            "weaknesses",
            "opportunities",
            "threats"
        ]

        # Validate Gemini response.
        for category in required_categories:

            values = result.get(category)

            if (
                not isinstance(values, list)
                or not values
                or not all(
                    isinstance(item, str) and item.strip()
                    for item in values
                )
            ):

                return swot_result

        # Preserve the original rule-based findings.
        # Gemini must not remove important identified risks.
        merged_result = {}

        for category in required_categories:

            merged_values = list(
                result[category]
            )

            for original_finding in swot_result[category]:

                append_unique(
                    merged_values,
                    original_finding
                )

            merged_result[category] = merged_values

        return {
            **merged_result,
            "provider": "gemini"
        }

    except Exception:

        # Preserve rule-based output if Gemini fails.
        return swot_result


# --------------------------------------------------
# MAIN SWOT FUNCTION
# --------------------------------------------------

def generate_swot(
    project,
    market_analysis=None,
    additional_context=None,
    use_gemini=True,
    risk_assessment=None
):

    # First generate rule-based SWOT.
    result = generate_rule_based_swot(
        project=project,
        market_analysis=market_analysis,
        additional_context=additional_context,
        risk_assessment=risk_assessment
    )

    # Optionally refine the result using Gemini.
    if use_gemini:

        result = refine_swot_with_gemini(
            project=project,
            swot_result=result,
            market_analysis=market_analysis,
            additional_context=additional_context,
            risk_assessment=risk_assessment
        )

    return result
