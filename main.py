# Members 2 and 3: FastAPI backend (PostgreSQL on Neon)
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from analysis import analyze

app = FastAPI()

# lets the React app (running on another port) call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_COLS = ["project_id", "project_name", "project_type", "budget", "target_market", "description"]


def connect():
    # Neon connection string from the environment (it already contains sslmode=require).
    # A new connection per request, because Neon pauses idle databases.
    return psycopg2.connect(os.getenv("DATABASE_URL"))


class Project(BaseModel):
    name: str
    email: str
    project_name: str
    project_type: str
    budget: float
    target_market: str
    description: str


@app.get("/")
def read_root():
    try:
        conn = connect()
        conn.close()
    except Exception:
        raise HTTPException(500, "Failed to connect to the database")
    return {"message": "Welcome to the Project Management API"}


# ---------- Member 2: save and fetch projects ----------
@app.post("/projects")
def add_project(p: Project):
    if p.budget <= 0 or "@" not in p.email or len(p.description) < 10:
        raise HTTPException(400, "Check email, budget and description (min 10 characters)")
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) "
            "ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name RETURNING user_id",
            (p.name, p.email))
        user_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO projects (user_id, project_name, project_type, budget, target_market, description) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING project_id",
            (user_id, p.project_name, p.project_type, p.budget, p.target_market, p.description))
        project_id = cur.fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"project_id": project_id}


@app.get("/projects")
def list_projects():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT project_id, project_name, project_type, budget, target_market, description "
                    "FROM projects ORDER BY project_id DESC")
        rows = cur.fetchall()
    finally:
        conn.close()
    return [dict(zip(PROJECT_COLS, r)) for r in rows]


@app.get("/projects/{pid}")
def get_project(pid: int):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT project_id, project_name, project_type, budget, target_market, description "
                    "FROM projects WHERE project_id = %s", (pid,))
        row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Project not found")
    return dict(zip(PROJECT_COLS, row))


# ---------- Member 3: market + competitor analysis ----------
@app.post("/projects/{pid}/market-analysis")
def market_analysis(pid: int):
    project = get_project(pid)          # raises 404 if the project does not exist
    try:
        result = analyze(project)
    except Exception as e:
        raise HTTPException(502, f"Analysis failed: {e}")

    conn = connect()
    try:
        cur = conn.cursor()
        # replace the earlier analysis so re-running does not create duplicates
        cur.execute("DELETE FROM competitor_analysis WHERE project_id = %s", (pid,))
        for c in result["competitors"]:
            cur.execute(
                "INSERT INTO competitor_analysis (project_id, competitor_name, market_position, "
                "market_share, revenue, growth, competitive_risk) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (pid, c["name"], c["type"], c["market_share"], c["revenue"], c["growth"], c["risk"]))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return result