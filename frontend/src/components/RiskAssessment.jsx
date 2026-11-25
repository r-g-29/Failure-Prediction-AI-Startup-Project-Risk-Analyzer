const riskTone = (s) => (s >= 70 ? "high" : s >= 40 ? "medium" : "low");
const goodTone = (v) => (v >= 60 ? "low" : v >= 40 ? "medium" : "high"); 

function Bar({ value, tone }) {
  return (
    <div className="bar">
      <div className={`bar-fill ${tone}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}

const SWOT_BOXES = [
  { key: "strengths", title: "Strengths", cls: "strengths" },
  { key: "weaknesses", title: "Weaknesses", cls: "weaknesses" },
  { key: "opportunities", title: "Opportunities", cls: "opportunities" },
  { key: "threats", title: "Threats", cls: "threats" },
];

export default function RiskAssessment({ project, risk, busy, onRun }) {
  if (!project) {
    return (
      <div className="card">
        <h2>Risk Assessment & SWOT Analysis</h2>
        <p className="muted">Pick a project in the Project Input tab first.</p>
      </div>
    );
  }

  if (!risk) {
    return (
      <div className="card">
        <h2>Risk Assessment & SWOT Analysis</h2>
        <p className="muted">
          <strong>{project.project_name}</strong> has no risk assessment yet. For better results, run the
          market analysis first so the competitors are included.
        </p>
        <button className="primary run-btn" onClick={onRun} disabled={busy}>
          {busy ? "Assessing..." : "Run risk assessment"}
        </button>
      </div>
    );
  }

  const tone = riskTone(risk.overall_risk_score);
  const { feasibility } = risk;

  return (
    <>
      <p className="muted risk-title">
        <strong>{project.project_name}</strong> · {project.project_type}
      </p>
      <div className="risk-layout">
        {/* ---------- Risk score ---------- */}
        <div className="card">
          <h2>Risk Score</h2>
          <div className="score-box">
            <span className="muted">Overall Risk Score</span>
            <div className={`big-score ${tone}`}>{risk.overall_risk_score}</div>
            <b className={`level ${tone}`}>{risk.risk_level}</b>
          </div>

          <div className="success-box">
            <div className="between">
              <span>Success Probability</span>
              <b>{risk.success_probability}%</b>
            </div>
            <Bar value={risk.success_probability} tone={goodTone(risk.success_probability)} />
          </div>

          <h3>Key Risk Factors</h3>
          {risk.risks.map((r) => (
            <div className="factor" key={r.category}>
              <div className="between">
                <b>{r.category}</b>
                <span className={`badge ${riskTone(r.score)}`}>{r.priority} · {r.score}</span>
              </div>
              <Bar value={r.score} tone={riskTone(r.score)} />
              <small className="muted">{r.description}</small>
            </div>
          ))}
        </div>

        {/* ---------- SWOT ---------- */}
        <div className="card">
          <h2>SWOT Analysis</h2>
          <div className="swot-grid">
            {SWOT_BOXES.map((b) => (
              <div className={`swot ${b.cls}`} key={b.key}>
                <h4>{b.title}</h4>
                <ul>
                  {(risk.swot[b.key] || []).map((p, i) => <li key={i}>{p}</li>)}
                </ul>
              </div>
            ))}
          </div>
          <button className="rerun" onClick={onRun} disabled={busy}>
            {busy ? "Assessing..." : "Re-run assessment"}
          </button>
        </div>

        {/* ---------- Feasibility ---------- */}
        <div className="card">
          <h2>Project Feasibility</h2>
          <div className="score-box">
            <span className="muted">Feasibility Score</span>
            <div className={`big-score ${goodTone(feasibility.score)}`}>{feasibility.score}%</div>
            <small className="muted">{feasibility.label}</small>
          </div>

          <h3>Assessment Metrics</h3>
          {feasibility.metrics.map((m) => (
            <div className="factor" key={m.name}>
              <div className="between">
                <span>{m.name}</span>
                <b>{m.score}%</b>
              </div>
              <Bar value={m.score} tone={goodTone(m.score)} />
            </div>
          ))}
        </div>
      </div>
    </>
  );
}