import { useState } from "react";

const TYPES = ["Startup", "Business Plan", "College Project", "Hackathon Idea", "Innovation Concept"];

const empty = {
  name: "", email: "", project_name: "", project_type: TYPES[0],
  target_market: "", budget: "", description: "",
};

export default function ProjectForm({ onSubmit, busy }) {
  const [form, setForm] = useState(empty);
  const [formError, setFormError] = useState("");

  const set = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.email.includes("@")) {
      return setFormError("Enter your name and a valid email.");
    }
    if (form.project_name.trim().length < 2 || !form.target_market.trim()) {
      return setFormError("Project name and target market are required.");
    }
    if (!(Number(form.budget) > 0)) {
      return setFormError("Budget must be greater than 0.");
    }
    if (form.description.trim().length < 10) {
      return setFormError("Description must be at least 10 characters.");
    }
    setFormError("");
    onSubmit({
      name: form.name.trim(),
      email: form.email.trim(),
      project_name: form.project_name.trim(),
      project_type: form.project_type,
      target_market: form.target_market.trim(),
      budget: Number(form.budget),
      description: form.description.trim(),
    });
  };

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <h2>Project Submission</h2>

      <div className="row">
        <label>Your Name
          <input name="name" value={form.name} onChange={set} placeholder="e.g., Sumeeth" />
        </label>
        <label>Email
          <input name="email" type="email" value={form.email} onChange={set} placeholder="you@example.com" />
        </label>
      </div>

      <label>Startup / Project Name
        <input name="project_name" value={form.project_name} onChange={set} placeholder="e.g., TechVenture AI" />
      </label>

      <label>Project Type
        <select name="project_type" value={form.project_type} onChange={set}>
          {TYPES.map((t) => <option key={t}>{t}</option>)}
        </select>
      </label>

      <div className="row">
        <label>Target Market
          <input name="target_market" value={form.target_market} onChange={set} placeholder="e.g., SMBs" />
        </label>
        <label>Budget (USD)
          <input name="budget" type="number" min="1" value={form.budget} onChange={set} placeholder="e.g., 100000" />
        </label>
      </div>

      <label>Project Description
        <textarea name="description" rows="4" value={form.description} onChange={set}
                  placeholder="At least 10 characters..." />
      </label>

      {formError && <p className="error">{formError}</p>}

      <button className="primary" type="submit" disabled={busy}>
        {busy ? "Analyzing..." : "Submit & Analyze"}
      </button>
    </form>
  );
}