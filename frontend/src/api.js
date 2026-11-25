const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    // network failure or CORS block: the browser gives no status
    throw new Error("Cannot reach the backend. Is uvicorn running on " + API_URL + "?");
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail =
        typeof data.detail === "string"
          ? data.detail
          : (data.detail || [])
              .map((d) => `${(d.loc || []).slice(1).join(".")}: ${d.msg}`)
              .join("; ");
    } catch {}
    const err = new Error(detail || `Request failed (${res.status})`);
    err.status = res.status; // lets callers treat 404 as "nothing saved yet"
    throw err;
  }
  return res.json();
}

const post = (path, body) =>
  request(path, { method: "POST", body: JSON.stringify(body ?? {}) });

// ---------------------------------------------------------------- health
export const checkHealth = () => request("/");
export const getOpenApi = () => request("/openapi.json"); // used to build the evaluation form

// ------------------------------------------------ Milestone 1: projects
export const listProjects = () => request("/projects");
export const getProject = (id) => request(`/projects/${id}`);
export const createProject = (payload) => post("/projects", payload); // { message, project_id }
export const updateProject = (id, payload) =>
  request(`/projects/${id}`, { method: "PUT", body: JSON.stringify(payload) });
export const deleteProject = (id) => request(`/projects/${id}`, { method: "DELETE" });

// ------------------------------- Milestone 1: market + competitor analysis
export const analyzeProject = (id) => post(`/projects/${id}/market-analysis`);
export const getMarketAnalysis = (id) => request(`/projects/${id}/market-analysis`); // saved competitors

// ------------------------------------- Milestone 2: individual assessments
export const runRiskAssessment = (id, payload) => post(`/projects/${id}/risk-assessment`, payload);
export const runSwotAnalysis = (id, payload) => post(`/projects/${id}/swot-analysis`, payload);
export const runFeasibility = (id, payload) => post(`/projects/${id}/feasibility`, payload);

// ------------------------------------------ Milestone 2: combined evaluation
// risk + SWOT + feasibility in one call, saved in one transaction
export const evaluateProject = (id, payload) => post(`/projects/${id}/evaluate`, payload);

// saved results; a 404 error (err.status === 404) means "not evaluated yet"
export const getEvaluationResults = (id) => request(`/projects/${id}/evaluation-results`);