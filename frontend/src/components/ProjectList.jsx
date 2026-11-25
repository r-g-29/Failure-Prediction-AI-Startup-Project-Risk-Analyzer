import { useState } from "react";

export default function ProjectList({ projects, selectedId, onSelect, onEdit, onDelete }) {
  const [q, setQ] = useState("");
  const shown = projects.filter((p) =>
    `${p.project_id} ${p.project_name}`.toLowerCase().includes(q.trim().toLowerCase())
  );

  return (
    <aside className="sidebar">
      <h3>Saved Projects</h3>
      <input className="search" placeholder="Search projects..." value={q} onChange={(e) => setQ(e.target.value)} />
      {projects.length === 0 && <p className="muted">Nothing saved yet.</p>}
      {projects.length > 0 && shown.length === 0 && <p className="muted">No match.</p>}
      {shown.map((p) => (
        <div className="list-row" key={p.project_id}>
          <button
            className={`list-item ${p.project_id === selectedId ? "active" : ""}`}
            onClick={() => onSelect(p.project_id)}
          >
            #{p.project_id} {p.project_name}
          </button>
          <div className="row-actions">
            <button className="mini" onClick={() => onEdit(p.project_id)}>Edit</button>
            <button className="mini danger" onClick={() => onDelete(p.project_id)}>Delete</button>
          </div>
        </div>
      ))}
    </aside>
  );
}