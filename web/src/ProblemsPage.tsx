import { type FormEvent, useEffect, useState } from "react";

type TestCase = {
  input: unknown[];
  output: unknown;
};

type ProblemData = {
  uuid: string;
  title: string;
  statement: string;
  hints: string | null;
  examples: string | null;
  test_cases: TestCase[] | null;
  created_at: string;
};

type FormData = {
  title: string;
  statement: string;
  hints: string;
  examples: string;
  test_cases_json: string;
};

const emptyForm: FormData = {
  title: "",
  statement: "",
  hints: "",
  examples: "",
  test_cases_json: "",
};

function ProblemsPage() {
  const [problems, setProblems] = useState<ProblemData[]>([]);
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [editingUuid, setEditingUuid] = useState<string | null>(null);
  const [form, setForm] = useState<FormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const fetchProblems = () => {
    setLoading(true);
    fetch("/api/v1/problems/")
      .then((res) => res.json())
      .then((data) => setProblems(data))
      .catch(() => setProblems([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchProblems();
  }, []);

  const openCreate = () => {
    setEditingUuid(null);
    setForm(emptyForm);
    setJsonError(null);
    setShowModal(true);
  };

  const openEdit = (p: ProblemData) => {
    setEditingUuid(p.uuid);
    setForm({
      title: p.title,
      statement: p.statement,
      hints: p.hints ?? "",
      examples: p.examples ?? "",
      test_cases_json: p.test_cases ? JSON.stringify(p.test_cases, null, 2) : "",
    });
    setJsonError(null);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingUuid(null);
    setForm(emptyForm);
    setJsonError(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setJsonError(null);

    let testCases: TestCase[] | null = null;
    if (form.test_cases_json.trim()) {
      try {
        testCases = JSON.parse(form.test_cases_json);
      } catch {
        setJsonError("Invalid JSON for test cases.");
        return;
      }
    }

    setSaving(true);

    const payload = {
      title: form.title,
      statement: form.statement,
      hints: form.hints || null,
      examples: form.examples || null,
      test_cases: testCases,
    };

    if (editingUuid) {
      await fetch(`/api/v1/problems/${editingUuid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } else {
      await fetch("/api/v1/problems/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }

    setSaving(false);
    closeModal();
    fetchProblems();
  };

  const handleDelete = async (p: ProblemData) => {
    if (!confirm(`Delete problem "${p.title}"?`)) return;
    await fetch(`/api/v1/problems/${p.uuid}`, { method: "DELETE" });
    fetchProblems();
  };

  const truncate = (s: string, max: number) =>
    s.length > max ? s.slice(0, max) + "..." : s;

  return (
    <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Problems</h1>
      <button onClick={openCreate} style={{ marginBottom: "1rem" }}>
        Create Problem
      </button>

      {loading ? (
        <p>Loading...</p>
      ) : problems.length === 0 ? (
        <p>No problems yet.</p>
      ) : (
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            textAlign: "left",
          }}
        >
          <thead>
            <tr>
              <th style={thStyle}>Title</th>
              <th style={thStyle}>Statement</th>
              <th style={thStyle}>Tests</th>
              <th style={thStyle}>Created</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {problems.map((p) => (
              <tr key={p.uuid}>
                <td style={tdStyle}>{p.title}</td>
                <td style={tdStyle}>{truncate(p.statement, 80)}</td>
                <td style={tdStyle}>
                  {p.test_cases ? p.test_cases.length : 0}
                </td>
                <td style={tdStyle}>
                  {new Date(p.created_at).toLocaleDateString()}
                </td>
                <td style={tdStyle}>
                  <button onClick={() => openEdit(p)} style={{ marginRight: "0.5rem" }}>
                    Edit
                  </button>
                  <button onClick={() => handleDelete(p)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showModal ? (
        <div style={overlayStyle}>
          <div style={modalStyle}>
            <h2>{editingUuid ? "Edit Problem" : "Create Problem"}</h2>
            <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.75rem" }}>
              <label>
                Title *
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  required
                  style={{ width: "100%", display: "block" }}
                />
              </label>
              <label>
                Statement *
                <textarea
                  value={form.statement}
                  onChange={(e) => setForm({ ...form, statement: e.target.value })}
                  rows={3}
                  required
                  style={{ width: "100%", display: "block" }}
                />
              </label>
              <label>
                Hints
                <textarea
                  value={form.hints}
                  onChange={(e) => setForm({ ...form, hints: e.target.value })}
                  rows={2}
                  style={{ width: "100%", display: "block" }}
                />
              </label>
              <label>
                Examples
                <textarea
                  value={form.examples}
                  onChange={(e) => setForm({ ...form, examples: e.target.value })}
                  rows={2}
                  style={{ width: "100%", display: "block" }}
                />
              </label>
              <label>
                Test Cases (JSON)
                <textarea
                  value={form.test_cases_json}
                  onChange={(e) => setForm({ ...form, test_cases_json: e.target.value })}
                  rows={6}
                  placeholder={'[\n  {"input": [1, 2], "output": 3},\n  {"input": [0, 5], "output": 0}\n]'}
                  style={{ width: "100%", display: "block", fontFamily: "monospace" }}
                />
              </label>
              {jsonError ? (
                <p style={{ color: "red", margin: 0 }}>{jsonError}</p>
              ) : null}
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button type="submit" disabled={saving}>
                  {saving ? "Saving..." : "Save"}
                </button>
                <button type="button" onClick={closeModal}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
}

const thStyle: React.CSSProperties = {
  borderBottom: "2px solid #ccc",
  padding: "0.5rem",
};

const tdStyle: React.CSSProperties = {
  borderBottom: "1px solid #eee",
  padding: "0.5rem",
};

const overlayStyle: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.4)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const modalStyle: React.CSSProperties = {
  background: "white",
  padding: "2rem",
  borderRadius: "8px",
  minWidth: "400px",
  maxWidth: "600px",
};

export default ProblemsPage;
