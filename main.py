
import os
import json
from typing import Optional, Dict, Any

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from assessment_models import (
    ProjectEvaluationRequest,
    RiskAssessmentRequest,
    FeasibilityInput
)

from engines.project_evaluator import evaluate_project
from engines.risk_calculator import calculate_risk
from engines.swot_analyzer import generate_swot
from engines.feasibility_evaluator import evaluate_feasibility

from analysis import analyze


# ==================================================
# CONFIGURATION
# ==================================================

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(
    title="Failure Prediction AI - Project Risk Analyzer",
    description=(
        "Backend API for project management, market analysis, "
        "risk assessment, SWOT and feasibility evaluation."
    ),
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_COLS = [
    "project_id",
    "project_name",
    "project_type",
    "budget",
    "target_market",
    "description"
]


def connect():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL is not configured."
        )

    return psycopg2.connect(database_url)


# ==================================================
# REQUEST MODELS
# ==================================================

class Project(BaseModel):
    name: str
    email: str
    project_name: str
    project_type: str
    budget: float
    target_market: str
    description: str


class SWOTAnalysisRequest(BaseModel):
    market_analysis: Optional[Dict[str, Any]] = None
    additional_context: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[RiskAssessmentRequest] = None
    use_gemini: bool = False


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def fetch_project(pid: int):

    conn = connect()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT project_id, project_name, project_type,
                   budget, target_market, description
            FROM projects
            WHERE project_id = %s
            """,
            (pid,)
        )

        row = cur.fetchone()

    finally:
        conn.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return dict(zip(PROJECT_COLS, row))


def to_dict(value):

    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    return value


def json_text(value):

    if value is None:
        return None

    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)

    return str(value)


def parse_json(value):

    if value is None:
        return None

    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    return value


def get_score(risk_result, key):

    if not isinstance(risk_result, dict):
        return None

    value = risk_result.get(key)

    if value is not None:
        return value

    scores = risk_result.get("risk_scores", {})

    if isinstance(scores, dict):
        return scores.get(key)

    return None


def generate_project_swot(
    project,
    market_analysis,
    additional_context,
    risk_result,
    use_gemini=False
):
    """
    Shared SWOT generation function.

    Both individual SWOT and combined project evaluation
    use this function to ensure consistent inputs and logic.
    """

    return generate_swot(
        project=project,
        market_analysis=market_analysis,
        additional_context=additional_context,
        use_gemini=use_gemini,
        risk_assessment=risk_result
    )



# ==================================================
# RISK ASSESSMENT DATABASE OPERATIONS
# ==================================================

def get_risk_priority(score):
    """Return the priority for an individual category score (0-100)."""
    if score is None:
        return "Not specified"

    score = float(score)

    if score < 35:
        return "Low"
    elif score < 65:
        return "Medium"
    return "High"


def save_risk_assessment(
    cur,
    pid,
    risk_result,
    identified_risks=None
):
    """
    Save risk category scores and individually identified risks.
    Previous records are deleted by the calling endpoint.
    """

    risk_categories = {
        "Financial Risk": "financial_risk",
        "Market Risk": "market_risk",
        "Technical Risk": "technical_risk",
        "Operational Risk": "operational_risk",
        "Competition and Regulatory Risk": (
            "competition_regulatory_risk"
        )
    }

    # Save the five category-level risk scores.
    for category_name, result_key in risk_categories.items():

        score = get_score(risk_result, result_key)

        if score is None:
            continue

        cur.execute(
            """
            INSERT INTO risk_assessments (
                project_id,
                risk_category,
                risk_score,
                risk_description,
                priority_level,
                score_type
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                pid,
                category_name,
                score,
                (
                    f"{category_name} score calculated "
                    "by the risk assessment engine."
                ),
                get_risk_priority(score),
                "category"
            )
        )

    # Save individually identified risks.
    for item in identified_risks or []:

        item = to_dict(item)

        if not isinstance(item, dict):
            continue

        category = item.get(
            "category",
            "Identified Risk"
        )

        likelihood = item.get("likelihood")
        impact = item.get("impact")

        matrix_score = item.get("risk_matrix_score")

        if (
            matrix_score is None
            and likelihood is not None
            and impact is not None
        ):
            matrix_score = likelihood * impact

        priority = (
            item.get("risk_level")
            or item.get("severity")
            or item.get("priority")
        )

        if priority is None and matrix_score is not None:
            if matrix_score >= 17:
                priority = "Critical"
            elif matrix_score >= 10:
                priority = "High"
            elif matrix_score >= 5:
                priority = "Medium"
            else:
                priority = "Low"

        if priority is None:
            priority = "Not specified"

        description = (
            item.get("description")
            or item.get("risk_description")
            or item.get("title")
            or item.get("name")
            or "Identified project risk"
        )

        cur.execute(
            """
            INSERT INTO risk_assessments (
                project_id,
                risk_category,
                risk_score,
                risk_description,
                priority_level,
                score_type
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                pid,
                category,
                matrix_score,
                description,
                priority,
                "individual"
            )
        )


def save_swot_analysis(cur, pid, swot_result):

    swot_result = to_dict(swot_result)

    cur.execute(
        """
        INSERT INTO swot_analysis (
            project_id,
            strengths,
            weaknesses,
            opportunities,
            threats
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            pid,
            json_text(swot_result.get("strengths")),
            json_text(swot_result.get("weaknesses")),
            json_text(swot_result.get("opportunities")),
            json_text(swot_result.get("threats"))
        )
    )


def save_success_prediction(cur, pid, risk_result):

    overall_risk = get_score(
        risk_result,
        "overall_risk_score"
    )

    success_indicator = get_score(
        risk_result,
        "success_potential_indicator"
    )

    if success_indicator is None and overall_risk is not None:
        success_indicator = 100 - float(overall_risk)

    cur.execute(
        """
        INSERT INTO success_predictions (
            project_id,
            success_probability,
            overall_risk_score
        )
        VALUES (%s, %s, %s)
        """,
        (
            pid,
            success_indicator,
            overall_risk
        )
    )



def save_feasibility_assessment(cur, pid, feasibility_result):
    """
    Save the complete TELOS feasibility assessment.

    Stores:
    - Overall feasibility score
    - Feasibility level
    - Assessment completeness
    - Full assessment result in JSONB
    """

    feasibility_result = to_dict(feasibility_result)

    if not isinstance(feasibility_result, dict):
        raise ValueError(
            "Feasibility result must be a dictionary."
        )

    # Extract values using the actual keys returned
    # by feasibility_evaluator.py.

    score = (
        feasibility_result.get("overall_feasibility_score")
        or feasibility_result.get("overall_score")
        or feasibility_result.get("feasibility_score")
        or feasibility_result.get("score")
    )

    level = (
        feasibility_result.get("feasibility_level")
        or feasibility_result.get("overall_feasibility")
        or feasibility_result.get("feasibility_status")
        or feasibility_result.get("status")
    )

    completeness = (
        feasibility_result.get("assessment_completeness")
    )

    if completeness is None:
        completeness = feasibility_result.get("completeness")

    # Preserve the complete assessment, including all TELOS
    # dimensions, ratings, scores and descriptions.

    cur.execute(
        """
        INSERT INTO feasibility_assessments (
            project_id,
            feasibility_score,
            feasibility_level,
            completeness,
            assessment_details
        )
        VALUES (%s, %s, %s, %s, %s::jsonb)
        """,
        (
            pid,
            score,
            level,
            completeness,
            json.dumps(feasibility_result, default=str)
        )
    )



# ==================================================
# SAVE COMBINED EVALUATION
# ==================================================

def save_milestone2_results(
    pid,
    risk_result,
    swot_result,
    feasibility_result,
    identified_risks=None
):
    """
    Replace previous risk records and save the latest
    combined evaluation results in one transaction.
    """

    conn = connect()

    try:
        cur = conn.cursor()

        # IMPORTANT:
        # Delete previous risk records before inserting new ones.
        cur.execute(
            """
            DELETE FROM risk_assessments
            WHERE project_id = %s
            """,
            (pid,)
        )

        # Insert latest risk assessment.
        save_risk_assessment(
            cur,
            pid,
            risk_result,
            identified_risks
        )

        # Save latest SWOT result.
        save_swot_analysis(
            cur,
            pid,
            swot_result
        )

        # Save latest success-potential indicator.
        save_success_prediction(
            cur,
            pid,
            risk_result
        )

        # Save the feasibility result in the same transaction.
        save_feasibility_assessment(
            cur,
            pid,
            feasibility_result
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/")
def read_root():

    try:
        conn = connect()
        conn.close()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to connect to the database"
        )

    return {
        "message": "Welcome to Failure Prediction AI API",
        "database": "Connected",
        "status": "Running"
    }


# ==================================================
# PROJECT MANAGEMENT ENDPOINTS
# ==================================================

@app.post("/projects", status_code=201)
def add_project(p: Project):

    if (
        p.budget <= 0
        or "@" not in p.email
        or len(p.description) < 10
    ):
        raise HTTPException(
            status_code=400,
            detail="Check email, budget and description."
        )

    conn = connect()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users (name, email)
            VALUES (%s, %s)
            ON CONFLICT (email)
            DO UPDATE SET name = EXCLUDED.name
            RETURNING user_id
            """,
            (p.name, p.email)
        )

        user_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO projects (
                user_id,
                project_name,
                project_type,
                budget,
                target_market,
                description
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING project_id
            """,
            (
                user_id,
                p.project_name,
                p.project_type,
                p.budget,
                p.target_market,
                p.description
            )
        )

        project_id = cur.fetchone()[0]
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return {
        "message": "Project created successfully",
        "project_id": project_id
    }


@app.get("/projects")
def list_projects():

    conn = connect()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT project_id, project_name, project_type,
                   budget, target_market, description
            FROM projects
            ORDER BY project_id DESC
            """
        )

        rows = cur.fetchall()

    finally:
        conn.close()

    return [
        dict(zip(PROJECT_COLS, row))
        for row in rows
    ]


@app.get("/projects/{pid}")
def get_project(pid: int):
    return fetch_project(pid)


@app.put("/projects/{pid}")
def update_project(pid: int, p: Project):

    if (
        p.budget <= 0
        or "@" not in p.email
        or len(p.description) < 10
    ):
        raise HTTPException(
            status_code=400,
            detail="Check email, budget and description."
        )

    conn = connect()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT user_id
            FROM projects
            WHERE project_id = %s
            """,
            (pid,)
        )

        row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        user_id = row[0]

        cur.execute(
            """
            UPDATE users
            SET name = %s, email = %s
            WHERE user_id = %s
            """,
            (p.name, p.email, user_id)
        )

        cur.execute(
            """
            UPDATE projects
            SET project_name = %s,
                project_type = %s,
                budget = %s,
                target_market = %s,
                description = %s
            WHERE project_id = %s
            """,
            (
                p.project_name,
                p.project_type,
                p.budget,
                p.target_market,
                p.description,
                pid
            )
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return {
        "message": "Project updated successfully",
        "project_id": pid
    }


@app.delete("/projects/{pid}")
def delete_project(pid: int):

    conn = connect()

    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT project_id FROM projects WHERE project_id = %s",
            (pid,)
        )

        if not cur.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        cur.execute(
            "DELETE FROM competitor_analysis WHERE project_id = %s",
            (pid,)
        )

        # Milestone 2 records are removed by ON DELETE CASCADE.
        cur.execute(
            "DELETE FROM projects WHERE project_id = %s",
            (pid,)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return {
        "message": "Project deleted successfully",
        "project_id": pid
    }


# ==================================================
# MARKET AND COMPETITOR ANALYSIS
# ==================================================

@app.post("/projects/{pid}/market-analysis")
def market_analysis(pid: int):

    project = fetch_project(pid)

    try:
        result = analyze(project)

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Analysis failed: {str(e)}"
        )

    conn = connect()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM competitor_analysis
            WHERE project_id = %s
            """,
            (pid,)
        )

        for competitor in result["competitors"]:

            cur.execute(
                """
                INSERT INTO competitor_analysis (
                    project_id,
                    competitor_name,
                    market_position,
                    market_share,
                    revenue,
                    growth,
                    competitive_risk
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    pid,
                    competitor["name"],
                    competitor["type"],
                    competitor["market_share"],
                    competitor["revenue"],
                    competitor["growth"],
                    competitor["risk"]
                )
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return result


@app.get("/projects/{pid}/market-analysis")
def get_market_analysis(pid: int):

    fetch_project(pid)

    conn = connect()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT competitor_name,
                   market_position,
                   market_share,
                   revenue,
                   growth,
                   competitive_risk
            FROM competitor_analysis
            WHERE project_id = %s
            """,
            (pid,)
        )

        rows = cur.fetchall()

    finally:
        conn.close()

    return {
        "project_id": pid,
        "competitors": [
            {
                "name": row[0],
                "type": row[1],
                "market_share": row[2],
                "revenue": row[3],
                "growth": row[4],
                "risk": row[5]
            }
            for row in rows
        ]
    }


# ==================================================
# MILESTONE 2: INDIVIDUAL ASSESSMENTS
# ==================================================

@app.post("/projects/{pid}/risk-assessment")
def run_risk_assessment(
    pid: int,
    request: RiskAssessmentRequest
):

    project = fetch_project(pid)

    try:
        result = calculate_risk(request)

        conn = connect()

        try:
            cur = conn.cursor()

            # Delete old risk records before saving new ones.
            cur.execute(
                """
                DELETE FROM risk_assessments
                WHERE project_id = %s
                """,
                (pid,)
            )

            save_risk_assessment(
                cur,
                pid,
                result,
                request.identified_risks
            )

            save_success_prediction(
                cur,
                pid,
                result
            )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

        return {
            "project_id": pid,
            "project_name": project["project_name"],
            "risk_assessment": result
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Risk assessment failed: {str(e)}"
        )



@app.post("/projects/{pid}/swot-analysis")
def run_swot_analysis(
    pid: int,
    request: SWOTAnalysisRequest
):
    project = fetch_project(pid)

    try:
        # Calculate risk assessment using the supplied inputs.
        risk_result = None

        if request.risk_assessment:
            risk_result = calculate_risk(
                request.risk_assessment
            )

        # Generate SWOT using the shared function.
        result = generate_project_swot(
            project=project,
            market_analysis=request.market_analysis,
            additional_context=request.additional_context,
            risk_result=risk_result,
            use_gemini=request.use_gemini
        )

        # Save SWOT result.
        conn = connect()

        try:
            cur = conn.cursor()

            save_swot_analysis(
                cur,
                pid,
                result
            )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

        return {
            "project_id": pid,
            "project_name": project["project_name"],
            "swot_analysis": result
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SWOT analysis failed: {str(e)}"
        )


@app.post("/projects/{pid}/feasibility")
def run_feasibility_assessment(
    pid: int,
    request: FeasibilityInput
):

    project = fetch_project(pid)

    try:
        result = evaluate_feasibility(request)

        conn = connect()

        try:
            cur = conn.cursor()
            save_feasibility_assessment(cur, pid, result)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return {
            "project_id": pid,
            "project_name": project["project_name"],
            "feasibility_assessment": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feasibility assessment failed: {str(e)}"
        )


# ==================================================
# MILESTONE 2: COMBINED PROJECT EVALUATION
# ==================================================


@app.post("/projects/{pid}/evaluate")
def run_project_evaluation(
    pid: int,
    request: ProjectEvaluationRequest
):
    project = fetch_project(pid)

    try:
        # --------------------------------
        # 1. RISK ASSESSMENT
        # --------------------------------

        risk_request = RiskAssessmentRequest(
            ratings=request.ratings,
            identified_risks=request.identified_risks
        )

        risk_result = calculate_risk(risk_request)

        risk_result = to_dict(risk_result)

        # --------------------------------
        # 2. SWOT ANALYSIS
        # --------------------------------

        swot_result = generate_project_swot(
            project=project,
            market_analysis=request.market_analysis,
            additional_context=request.additional_context,
            risk_result=risk_result,
            use_gemini=request.use_gemini
        )

        swot_result = to_dict(swot_result)

        # --------------------------------
        # 3. FEASIBILITY ASSESSMENT
        # --------------------------------

        feasibility_result = evaluate_feasibility(
            request.feasibility
        )

        feasibility_result = to_dict(feasibility_result)

        # --------------------------------
        # 4. SAVE RESULTS
        # --------------------------------

        save_milestone2_results(
            pid=pid,
            risk_result=risk_result,
            swot_result=swot_result,
            identified_risks=request.identified_risks,
            feasibility_result=feasibility_result
        )

        # --------------------------------
        # 5. RETURN COMPLETE EVALUATION
        # --------------------------------

        return {
            "project_id": pid,
            "project_name": project["project_name"],
            "risk_assessment": risk_result,
            "swot_analysis": swot_result,
            "feasibility_assessment": feasibility_result,
            "evaluation_status": "Completed"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Project evaluation failed: {str(e)}"
        )


# ==================================================
# RETRIEVE SAVED PROJECT EVALUATION RESULTS
# ==================================================

@app.get(
    "/projects/{pid}/evaluation-results",
    summary="Get Project Evaluation Results",
    description=(
        "Retrieve saved risk assessment, SWOT analysis "
        "and success-potential indicator for a project."
    )
)
def get_evaluation_results(pid: int):

    project = fetch_project(pid)

    conn = connect()

    try:
        cur = conn.cursor()

        # Retrieve latest risk assessment records.
        cur.execute(
            """
            SELECT risk_category,
                   risk_score,
                   risk_description,
                   priority_level,
                   score_type
            FROM risk_assessments
            WHERE project_id = %s
            ORDER BY risk_id DESC
            """,
            (pid,)
        )

        risk_rows = cur.fetchall()

        # Retrieve latest SWOT analysis.
        cur.execute(
            """
            SELECT strengths,
                   weaknesses,
                   opportunities,
                   threats,
                   generated_at
            FROM swot_analysis
            WHERE project_id = %s
            ORDER BY generated_at DESC, swot_id DESC
            LIMIT 1
            """,
            (pid,)
        )

        swot_row = cur.fetchone()

        # Retrieve latest success prediction.
        cur.execute(
            """
            SELECT success_probability,
                   overall_risk_score,
                   prediction_date
            FROM success_predictions
            WHERE project_id = %s
            ORDER BY prediction_date DESC, prediction_id DESC
            LIMIT 1
            """,
            (pid,)
        )

        prediction_row = cur.fetchone()

        # Retrieve the latest feasibility assessment.
        cur.execute(
            """
            SELECT feasibility_score,
                   feasibility_level,
                   completeness,
                   assessment_details,
                   assessed_at
            FROM feasibility_assessments
            WHERE project_id = %s
            ORDER BY assessed_at DESC, feasibility_id DESC
            LIMIT 1
            """,
            (pid,)
        )

        feasibility_row = cur.fetchone()

    finally:
        conn.close()

    if (
        not risk_rows
        and not swot_row
        and not prediction_row
        and not feasibility_row
    ):
        raise HTTPException(
            status_code=404,
            detail="No evaluation results found for this project."
        )

    risk_results = [
        {
            "risk_category": row[0],
            "risk_score": (
                float(row[1])
                if row[1] is not None
                else None
            ),
            "risk_description": row[2],
            "priority_level": row[3],
            "score_type": row[4]
        }
        for row in risk_rows
    ]

    swot_results = None

    if swot_row:
        swot_results = {
            "strengths": parse_json(swot_row[0]),
            "weaknesses": parse_json(swot_row[1]),
            "opportunities": parse_json(swot_row[2]),
            "threats": parse_json(swot_row[3]),
            "generated_at": swot_row[4]
        }

    success_prediction = None

    if prediction_row:
        success_prediction = {
            "success_potential_indicator": (
                float(prediction_row[0])
                if prediction_row[0] is not None
                else None
            ),
            "overall_risk_score": (
                float(prediction_row[1])
                if prediction_row[1] is not None
                else None
            ),
            "prediction_date": prediction_row[2],
            "note": (
                "The success-potential indicator is calculated "
                "from the risk score. It is not a trained ML probability."
            )
        }

    feasibility_assessment = None

    if feasibility_row:
        feasibility_assessment = {
            "feasibility_score": (
                float(feasibility_row[0])
                if feasibility_row[0] is not None
                else None
            ),
            "feasibility_level": feasibility_row[1],
            "completeness": (
                float(feasibility_row[2])
                if feasibility_row[2] is not None
                else None
            ),
            "assessment_details": parse_json(feasibility_row[3]),
            "assessed_at": feasibility_row[4]
        }

    return {
        "project_id": pid,
        "project_name": project["project_name"],
        "risk_assessment": risk_results,
        "swot_analysis": swot_results,
        "success_prediction": success_prediction,
        "feasibility_assessment": feasibility_assessment
    }
