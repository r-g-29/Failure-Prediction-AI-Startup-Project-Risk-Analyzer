 
const riskTone = (s) => (s >= 65 ? "high" : s >= 35 ? "medium" : "low");
const goodTone = (v) => (v >= 60 ? "low" : v >= 40 ? "medium" : "high"); // high value = good

const prioClass = (p) => {
  const v = String(p || "").toLowerCase();
  if (v === "critical" || v === "high") return "high";
  if (v === "medium") return "medium";
  if (v === "low") return "low";
  return "";
};

const pretty = (k) => String(k).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
const num = (v) => (v === null || v === undefined || v === "" || Number.isNaN(Number(v)) ? null : Number(v));
const round = (v) => (v === null ? "-" : Number.isInteger(v) ? v : v.toFixed(1));

function Bar({ value, tone }) {
  return (
    <div className="bar">
      <div className={`bar-fill ${tone}`} style={{ width: `${Math.max(0, Math.min(100, value ?? 0))}%` }} />
    </div>
  );
}
 
function asItems(value) {
  if (value == null) return [];
  const list = Array.isArray(value) ? value : [value];
  return list
    .map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object") {
        return item.description || item.title || item.point || item.text || item.name || JSON.stringify(item);
      }
      return String(item);
    })
    .filter(Boolean);
}

 
function collectRows(details) {
  const rows = [];
  const scoreOf = (o) => [o.score, o.weighted_score, o.overall_score, o.rating_score].map(num).find((v) => v !== null) ?? null;

  const addRow = (name, o) => {
    if (!o || typeof o !== "object" || Array.isArray(o)) return;
    const score = scoreOf(o);
    const rating = o.rating ?? o.level ?? o.status ?? null;
    if (score === null && rating === null) return;
    rows.push({
      name: pretty(name),
      score,
      rating: rating !== null && typeof rating !== "object" ? String(rating) : null,
      description: o.description || o.summary || o.reason || null,
    });
  };

  const walk = (obj, depth) => {
    if (!obj || typeof obj !== "object" || depth > 2) return;
    for (const [key, value] of Object.entries(obj)) {
      if (Array.isArray(value)) {
        value.forEach((item, i) => addRow(item?.dimension || item?.name || item?.title || `${key} ${i + 1}`, item));
      } else if (value && typeof value === "object") {
        const before = rows.length;
        addRow(key, value);
        if (rows.length === before) walk(value, depth + 1);
      }
    }
  };
  walk(details, 0);
  return rows;
}

const SWOT_BOXES = [
  { key: "strengths", title: "Strengths", cls: "strengths" },
  { key: "weaknesses", title: "Weaknesses", cls: "weaknesses" },
  { key: "opportunities", title: "Opportunities", cls: "opportunities" },
  { key: "threats", title: "Threats", cls: "threats" },
];

export default function EvaluationResults({ project, results, loading }) {
  if (loading) {
    return <div className="card"><p className="muted">Loading saved results...</p></div>;
  }
  if (!results) {
    return (
      <div className="card">
        <h2>Evaluation Results</h2>
        <p className="muted">
          <strong>{project.project_name}</strong> has not been evaluated yet. 
        </p>
      </div>
    );
  }

  const prediction = results.success_prediction;
  const swot = results.swot_analysis;
  const feas = results.feasibility_assessment;

  const risks = results.risk_assessment || [];
  const byScore = (a, b) => (b.risk_score ?? -1) - (a.risk_score ?? -1);
  const categories = risks.filter((r) => r.score_type === "category").sort(byScore);
  const individual = risks.filter((r) => r.score_type !== "category").sort(byScore);

  const overall = num(prediction?.overall_risk_score);
  const success = num(prediction?.success_potential_indicator);
  const tone = overall !== null ? riskTone(overall) : "";
  const feasScore = num(feas?.feasibility_score);
  const rows = feas ? collectRows(feas.assessment_details) : [];

  return (
    <div className="risk-layout">
      {/* ---------- Risk score ---------- */}
      <div className="card">
        <h2>Risk Score</h2>
        {overall !== null ? (
          <div className="score-box">
            <span className="muted">Overall Risk Score</span>
            <div className={`big-score ${tone}`}>{round(overall)}</div>
            <b className={`level ${tone}`}>{tone.toUpperCase()} RISK</b>
          </div>
        ) : (
          <p className="muted">No overall score saved.</p>
        )}

        {success !== null && (
          <div className="success-box">
            <div className="between">
              <span>Success Potential</span>
              <b>{round(success)}%</b>
            </div>
            <Bar value={success} tone={goodTone(success)} />
            <small className="muted">{prediction.note}</small>
          </div>
        )}

        {categories.length > 0 && <h3>Risk Categories</h3>}
        {categories.map((r, i) => (
          <div className="factor" key={`c${i}`}>
            <div className="between">
              <b>{r.risk_category}</b>
              <span className={`badge ${prioClass(r.priority_level)}`}>{r.priority_level} · {round(r.risk_score)}</span>
            </div>
            <Bar value={r.risk_score} tone={riskTone(r.risk_score ?? 0)} />
          </div>
        ))}

        {individual.length > 0 && <h3>Identified Risks</h3>}
        {individual.map((r, i) => (
          <div className="factor" key={`i${i}`}>
            <div className="between">
              <b>{r.risk_category}</b>
              <span className={`badge ${prioClass(r.priority_level)}`}>
                {r.priority_level}{r.risk_score != null ? ` · ${round(r.risk_score)}` : ""}
              </span>
            </div>
            <small className="muted">{r.risk_description}</small>
          </div>
        ))}
      </div>

      {/* ---------- SWOT ---------- */}
      <div className="card">
        <h2>SWOT Analysis</h2>
        {swot ? (
          <div className="swot-grid">
            {SWOT_BOXES.map((b) => (
              <div className={`swot ${b.cls}`} key={b.key}>
                <h4>{b.title}</h4>
                <ul>
                  {asItems(swot[b.key]).map((p, i) => <li key={i}>{p}</li>)}
                </ul>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">No SWOT analysis saved.</p>
        )}
      </div>

      {/* ---------- Feasibility ---------- */}
      <div className="card">
        <h2>Project Feasibility</h2>
        {feas ? (
          <>
            <div className="score-box">
              <span className="muted">Feasibility Score</span>
              <div className={`big-score ${feasScore !== null ? goodTone(feasScore) : ""}`}>
                {feasScore !== null ? `${round(feasScore)}%` : "-"}
              </div>
              {feas.feasibility_level && <b>{feas.feasibility_level}</b>}
              {num(feas.completeness) !== null && (
                <small className="muted">Assessment completeness: {round(num(feas.completeness))}%</small>
              )}
            </div>

            {rows.length > 0 && <h3>Assessment Details</h3>}
            {rows.map((r, i) => (
              <div className="factor" key={i}>
                <div className="between">
                  <b>{r.name}</b>
                  <span>
                    {r.score !== null ? round(r.score) : ""}
                    {r.rating ? <span className={`badge ${prioClass(r.rating)}`}> {r.rating}</span> : null}
                  </span>
                </div>
                {r.description && <small className="muted">{r.description}</small>}
              </div>
            ))}

            <details className="raw">
              <summary>View raw assessment data</summary>
              <pre>{JSON.stringify(feas.assessment_details, null, 2)}</pre>
            </details>
          </>
        ) : (
          <p className="muted">No feasibility assessment saved.</p>
        )}
      </div>
    </div>
  );
}