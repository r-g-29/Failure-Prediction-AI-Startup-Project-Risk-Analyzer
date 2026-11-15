import { useEffect, useState } from "react";
import { listProjects, getProject, createProject, analyzeProject } from "./api";
import ProjectForm from "./components/ProjectForm";
import MarketAnalysis from "./components/MarketAnalysis";
import CompetitorList from "./components/CompetitorList";
import ProjectList from "./components/ProjectList";

const TABS = ["Project Input"];
export default function App() {
  const [tab, setTab] = useState(TABS[0]);
  const [projects, setProjects] = useState([]);
  const [project, setProject] = useState(null);   // project fields + analysis
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const refreshList = async () => {
    try { setProjects(await listProjects()); }
    catch (e) { setError(`Could not load projects: ${e.message}`); }
  };

  useEffect(() => { refreshList(); }, []);

  const handleSubmit = async (payload) => {
    setBusy(true); setError("");
    try {
      const { project_id } = await createProject(payload);
      const saved = await getProject(project_id);
      setProject({ ...saved, analysis: null });
      refreshList();
      const analysis = await analyzeProject(project_id);
      setProject({ ...saved, analysis });
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
    setError("");
    try { setProject({ ...(await getProject(id)), analysis: null }); setTab(TABS[0]); }
    catch (e) { setError(e.message); }
  };

  return (
    <div className="app">
      <header>
        <h1>Failure Prediction AI</h1>
        <p className="muted">Startup & Project Risk Analyzer · </p>
      </header>

      {error && <div className="alert">{error}</div>}

      <nav className="tabs">
        {TABS.map((t) => (
          <button key={t} className={t === tab ? "tab active" : "tab"} onClick={() => setTab(t)}>{t}</button>
        ))}
      </nav>

      {tab === "Project Input" ? (
        <div className="layout">
          <ProjectList projects={projects} selectedId={project?.project_id} onSelect={handleSelect} />
          <ProjectForm onSubmit={handleSubmit} busy={busy} />
          <MarketAnalysis project={project} onReanalyze={handleReanalyze} busy={busy} />
          <CompetitorList project={project} />
        </div>
      ) : (
        <div className="card"><p className="muted">{LATER[tab]}</p></div>
      )}
    </div>
  );
}