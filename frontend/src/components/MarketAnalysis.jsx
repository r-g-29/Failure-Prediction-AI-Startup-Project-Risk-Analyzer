import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
} from "recharts";

export default function MarketAnalysis({ project, onReanalyze, busy }) {
  if (!project) {
    return (
      <div className="card">
        <h2>Market Analysis</h2>
        <p className="muted">Submit a project or pick one from the list.</p>
      </div>
    );
  }

  // the market data may sit at the top level of the result or under "market"
  const a = project.analysis;
  const m = a?.market ?? a;
  const hasMarket = m && (m.tam || m.sam || m.som || m.summary || m.trends);
  const trends = Array.isArray(m?.trends) ? m.trends : [];
  const xKey = trends[0] && "year" in trends[0] ? "year" : Object.keys(trends[0] || {})[0];
  const yKey = trends[0] && Object.keys(trends[0]).find((k) => k !== xKey);

  return (
    <div className="card">
      <h2>Market Analysis</h2>
      <p className="muted">
        <strong>{project.project_name}</strong> · {project.project_type} · {project.target_market}
      </p>
      <p>{project.description}</p>

      {!a ? (
        <button className="primary" onClick={onReanalyze} disabled={busy}>
          {busy ? "Analyzing..." : "Generate analysis"}
        </button>
      ) : (
        <>
          {hasMarket && (
            <div className="metrics">
              <div className="metric"><span>TAM</span><b>{m.tam ?? "-"}</b>
                <small className="up">{m.growth_rate}</small></div>
              <div className="metric"><span>SAM</span><b>{m.sam ?? "-"}</b></div>
              <div className="metric"><span>SOM</span><b>{m.som ?? "-"}</b></div>
            </div>
          )}

          {trends.length > 0 && yKey && (
            <div className="chart">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey={xKey} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey={yKey} stroke="#dc2626" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {m?.summary && <p>{m.summary}</p>}

          <button onClick={onReanalyze} disabled={busy}>
            {busy ? "Analyzing..." : "Re-run analysis"}
          </button>
        </>
      )}
    </div>
  );
}