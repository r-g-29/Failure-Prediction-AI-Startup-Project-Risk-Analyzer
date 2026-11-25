
from engines.risk_calculator import calculate_risk
from engines.swot_analyzer import generate_swot
from engines.feasibility_evaluator import evaluate_feasibility


def evaluate_project(
    project,
    risk_request,
    feasibility_inputs,
    market_analysis=None,
    additional_context=None,
    use_gemini=True
):
    """
    Perform complete Milestone 2 project evaluation.

    Modules:
    1. Risk assessment
    2. SWOT analysis
    3. TELOS feasibility assessment

    The risk assessment is also supplied to SWOT analysis
    to improve consistency between evaluation results.
    """

    # --------------------------------------------------
    # 1. RISK ASSESSMENT
    # --------------------------------------------------

    risk_result = calculate_risk(
        risk_request
    )

    # --------------------------------------------------
    # 2. SWOT ANALYSIS
    # --------------------------------------------------

    swot_result = generate_swot(
        project=project,
        market_analysis=market_analysis,
        additional_context=additional_context,
        use_gemini=use_gemini,
        risk_assessment=risk_result
    )

    # --------------------------------------------------
    # 3. FEASIBILITY ASSESSMENT
    # --------------------------------------------------

    feasibility_result = evaluate_feasibility(
        feasibility_inputs
    )

    # --------------------------------------------------
    # 4. PROJECT NAME
    # --------------------------------------------------

    if isinstance(project, dict):

        project_name = project.get(
            "project_name",
            "Unnamed Project"
        )

    else:

        project_name = getattr(
            project,
            "project_name",
            "Unnamed Project"
        )

    # --------------------------------------------------
    # 5. COMBINED EVALUATION RESPONSE
    # --------------------------------------------------

    return {
        "project_name": project_name,
        "risk_assessment": risk_result,
        "swot_analysis": swot_result,
        "feasibility_assessment": feasibility_result,
        "evaluation_status": "Completed"
    }
