export default function CompetitorList({ project }) {
  const list = project?.analysis?.competitors ?? [];

  return (
    <div className="card">
      <h2>Competitor Landscape</h2>
      {!project && <p className="muted">No project selected.</p>}
      {project && list.length === 0 && <p className="muted">Run the analysis to see competitors.</p>}
      {list.map((c, i) => {
        const risk = String(c.risk ?? "").toLowerCase();
        return (
          <div className="competitor" key={i}>
            <div className="competitor-head">
              <b>{c.name}</b>
              <span className={`badge ${risk}`}>{c.risk ?? "n/a"}</span>
            </div>
            <small className="muted">
              {c.type ?? "-"} · Share: {c.market_share ?? "-"} · Revenue: {c.revenue ?? "-"} · Growth: {c.growth ?? "-"}
            </small>
          </div>
        );
      })}
    </div>
  );
}