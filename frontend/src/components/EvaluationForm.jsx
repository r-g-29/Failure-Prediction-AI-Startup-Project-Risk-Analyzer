import { useEffect, useState } from "react";
import { getOpenApi } from "../api";
import { templateFromOpenApi } from "../utils/schemaTemplate";

const SCHEMA_NAME = "ProjectEvaluationRequest";

 
export default function EvaluationForm({ project, busy, onRun }) {
  const [spec, setSpec] = useState(null);
  const [data, setData] = useState(null);

  const load = async () => {
    try {
      const s = await getOpenApi();
      const start = templateFromOpenApi(s, SCHEMA_NAME);
      if (!start) throw new Error($`{SCHEMA_NAME} was not found in the API schema.`);
      setSpec(s);
      setData(start);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => { load(); }, []);  

  const rootSchema = spec?.components?.schemas?.[SCHEMA_NAME];
 
  const withoutBlankRows = (payload) => {
    const out = { ...payload };
    for (const [key, value] of Object.entries(out)) {
      if (!Array.isArray(value)) continue;
      out[key] = value.filter((item) => {
        if (!item || typeof item !== "object") return true;
        const texts = Object.values(item).filter((v) => typeof v === "string");
        return !(texts.length > 0 && texts.every((t) => t.trim() === ""));
      });
    }
    return out;
  };

  const submit = (e) => {
    e.preventDefault();
    onRun(withoutBlankRows(data));
  };

  return (
    <form className="card" onSubmit={submit}>
      <h2>Evaluation Input</h2>
      <p className="muted small">
        Rate <strong>{project.project_name}</strong>, add any risks you already know about, then run. Risk,
        SWOT and feasibility are calculated and saved together.
      </p>

      

      {rootSchema && data && (
        <>
          
       

          <div className="btn-row">
            <button className="primary" type="submit" disabled={busy}>
              {busy ? "Evaluating..." : "Run evaluation"}
            </button>
          </div>
        </>
      )}
    </form>
  );
}