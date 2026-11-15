const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = typeof data.detail === "string"
        ? data.detail
        : (data.detail || []).map((d) => `${(d.loc || []).slice(-1)[0]}: ${d.msg}`).join("; ");
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export const listProjects = () => request("/projects");
export const getProject = (id) => request(`/projects/${id}`);
export const createProject = (payload) =>
  request("/projects", { method: "POST", body: JSON.stringify(payload) }); // returns { project_id }
export const analyzeProject = (id) =>
  request(`/projects/${id}/market-analysis`, { method: "POST" });