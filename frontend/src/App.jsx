import { useEffect, useState } from "react";
import {
  checkHealth, listProjects, getProject, createProject, updateProject, deleteProject,
  analyzeProject, getMarketAnalysis, evaluateProject, getEvaluationResults,
} from "./api";
import ProjectForm from "./components/ProjectForm";
import MarketAnalysis from "./components/MarketAnalysis";
import CompetitorList from "./components/CompetitorList";
import ProjectList from "./components/ProjectList";
import EvaluationForm from "./components/EvaluationForm";
import EvaluationResults from "./components/EvaluationResults";

const TABS = ["Project Input", "Risk Assessment"];


export default function App() {
  const [tab, setTab] = useState(TABS[0]);
  const [projects, setProjects] = useState([]);
  const [project, setProject] = useState(null);     
  const [editing, setEditing] = useState(false);
  const [results, setResults] = useState(null);     
  const [resultsLoading, setResultsLoading] = useState(false);
  const [busy, setBusy] = useState(false);          
  const [evalBusy, setEvalBusy] = useState(false);
  const [online, setOnline] = useState(null);       
  const [error, setError] = useState("");

  const refreshList = async () => {
    try { setProjects(await listProjects()); }
    catch (e) { setError(e.message); }
  };

  
  useEffect(() => {
    const ping = () => checkHealth().then(() => setOnline(true)).catch(() => setOnline(false));
    ping();
    const timer = setInterval(ping, 30000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => { refreshList(); }, []);

  
  useEffect(() => {
    setResults(null);
    if (!project?.project_id) return;
    let cancelled = false;
    setResultsLoading(true);
    getEvaluationResults(project.project_id)
      .then((r) => { if (!cancelled) setResults(r); })
      .catch((e) => { if (!cancelled && e.status !== 404) setError(e.message); }) 
      .finally(() => { if (!cancelled) setResultsLoading(false); });
    return () => { cancelled = true; };
  }, [project?.project_id]);

  
  const loadProject = async (id) => {
    const [saved, market] = await Promise.all([
      getProject(id),
      getMarketAnalysis(id).catch(() => null),
    ]);
    const hasCompetitors = market && Array.isArray(market.competitors) && market.competitors.length > 0;
    return { ...saved, analysis: hasCompetitors ? market : null };
  };

  const handleSubmit = async (payload) => {
    setBusy(true); setError("");
    try {
      if (editing) {
        await updateProject(project.project_id, payload);
        setProject({ ...(await getProject(project.project_id)), analysis: project.analysis });
        setEditing(false);
        refreshList();
      } else {
        const { project_id } = await createProject(payload);
        const saved = await getProject(project_id);
        setProject({ ...saved, analysis: null });
        refreshList();
        const analysis = await analyzeProject(project_id);
        setProject({ ...saved, analysis });
      }
    } catch (e) {
      setError(`Something went wrong: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleReanalyze = async () => {
    setBusy(true); setError("");
    try {
      const analysis = await analyzeProject(project.project_id);
      setProject({ ...project, analysis });
    } catch (e) {
      setError(`Analysis failed: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleSelect = async (id) => {
    setError(""); setEditing(false);
    try { setProject(await loadProject(id)); }
    catch (e) { setError(e.message); }
  };

  const handleEdit = async (id) => {
    setError("");
    try {
      if (project?.project_id !== id) setProject(await loadProject(id));
      setEditing(true);
      setTab("Project Input");
    } catch (e) { setError(e.message); }
  };

  const handleDelete = async (id) => {
    const target = projects.find((p) => p.project_id === id);
    if (!window.confirm(`Delete "${target?.project_name ?? `project #${id}`}" and all its saved analysis? This cannot be undone.`)) return;
    setError("");
    try {
      await deleteProject(id);
      if (project?.project_id === id) { setProject(null); setEditing(false); }
      refreshList();
    } catch (e) { setError(`Delete failed: ${e.message}`); }
  };

  const handleEvaluate = async (payload) => {
    setEvalBusy(true); setError("");
    try {
      await evaluateProject(project.project_id, payload);
      setResults(await getEvaluationResults(project.project_id));   
    } catch (e) {
      setError(`Evaluation failed: ${e.message}`);
    } finally {
      setEvalBusy(false);
    }
  };

  const listProps = {
    projects, selectedId: project?.project_id,
    onSelect: handleSelect, onEdit: handleEdit, onDelete: handleDelete,
  };

  return (
    <div className="app">
      <header className="top">
        <div>
          <h1>Failure Prediction AI</h1>
          <p className="muted">Startup & Project Risk Analyzer </p>
        </div>
        <span className="health" title={online === false ? "Backend not reachable" : "Backend status"}>
          <i className={`dot ${online === null ? "" : online ? "up" : "down"}`} />
          {online === null ? "Checking..." : online ? "API online" : "API offline"}
        </span>
      </header>

      {error && (
        <div className="alert">
          <span>{error}</span>
          <button className="mini" onClick={() => setError("")}>Dismiss</button>
        </div>
      )}

      <nav className="tabs">
        {TABS.map((t) => (
          <button key={t} className={t === tab ? "tab active" : "tab"} onClick={() => setTab(t)}>{t}</button>
        ))}
      </nav>

      {tab === "Project Input" && (
        <div className="layout">
          <ProjectList {...listProps} />
          <ProjectForm
            key={editing ? `edit-${project?.project_id}` : "new"}
            initial={editing ? project : null}
            onSubmit={handleSubmit}
            onCancel={() => setEditing(false)}
            busy={busy}
          />
          <MarketAnalysis project={project} onReanalyze={handleReanalyze} busy={busy} />
          <CompetitorList project={project} />
        </div>
      )}

      {tab === "Risk Assessment" && (
        <div className="layout-risk">
          <ProjectList {...listProps} />
          <div className="stack">
            {!project ? (
              <div className="card">
                <h2>Risk Assessment & SWOT Analysis</h2>
                <p className="muted">Pick a project from the list first.</p>
              </div>
            ) : (
              <>
                <EvaluationForm key={project.project_id} project={project} busy={evalBusy} onRun={handleEvaluate} />
                <EvaluationResults project={project} results={results} loading={resultsLoading} />
              </>
            )}
          </div>
        </div>
      )}

      
    </div>
  );
}