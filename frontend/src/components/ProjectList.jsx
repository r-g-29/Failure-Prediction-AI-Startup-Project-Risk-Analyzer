export default function ProjectList({ projects, selectedId, onSelect }) {
  return (
    <aside className="sidebar">
      <h3>Saved Projects</h3>
      {projects.length === 0 && <p className="muted">Nothing saved yet.</p>}
      {projects.map((p) => (
        <button key={p.project_id}
                className={`list-item ${p.project_id === selectedId ? "active" : ""}`}
                onClick={() => onSelect(p.project_id)}>
          #{p.project_id} {p.project_name}
        </button>
      ))}
    </aside>
  );
}