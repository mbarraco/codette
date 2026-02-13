import { type FormEvent, useEffect, useState } from "react";
import styles from "./ProblemsPage.module.css";

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

type TestCaseRow = {
  input: string;
  output: string;
};

type FormData = {
  title: string;
  statement: string;
  hints: string;
  examples: string;
  testCases: TestCaseRow[];
};

const emptyRow: TestCaseRow = { input: "", output: "" };

const emptyForm: FormData = {
  title: "",
  statement: "",
  hints: "",
  examples: "",
  testCases: [],
};

function ProblemsPage() {
  const [problems, setProblems] = useState<ProblemData[]>([]);
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [editingUuid, setEditingUuid] = useState<string | null>(null);
  const [form, setForm] = useState<FormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

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
    setParseError(null);
    setShowModal(true);
  };

  const openEdit = (p: ProblemData) => {
    setEditingUuid(p.uuid);
    setForm({
      title: p.title,
      statement: p.statement,
      hints: p.hints ?? "",
      examples: p.examples ?? "",
      testCases: p.test_cases
        ? p.test_cases.map((tc) => ({
            input: JSON.stringify(tc.input),
            output: JSON.stringify(tc.output),
          }))
        : [],
    });
    setParseError(null);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingUuid(null);
    setForm(emptyForm);
    setParseError(null);
  };

  const addTestCase = () => {
    setForm({ ...form, testCases: [...form.testCases, { ...emptyRow }] });
  };

  const removeTestCase = (index: number) => {
    setForm({
      ...form,
      testCases: form.testCases.filter((_, i) => i !== index),
    });
  };

  const updateTestCase = (
    index: number,
    field: keyof TestCaseRow,
    value: string,
  ) => {
    const updated = form.testCases.map((tc, i) =>
      i === index ? { ...tc, [field]: value } : tc,
    );
    setForm({ ...form, testCases: updated });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setParseError(null);

    let testCases: TestCase[] | null = null;
    if (form.testCases.length > 0) {
      try {
        testCases = form.testCases.map((row, i) => {
          const input = JSON.parse(row.input);
          if (!Array.isArray(input)) {
            throw new Error(
              `Test case ${i + 1}: Input must be a JSON array, e.g. [1, 2]`,
            );
          }
          const output = JSON.parse(row.output);
          return { input, output };
        });
      } catch (err) {
        setParseError(
          err instanceof SyntaxError
            ? "Invalid JSON in test case fields."
            : String((err as Error).message),
        );
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
    <div className="page">
      <div className={styles.header}>
        <h1>Problems</h1>
        <button className="btn-primary" onClick={openCreate}>
          Create Problem
        </button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : problems.length === 0 ? (
        <p>No problems yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Statement</th>
              <th>Tests</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {problems.map((p) => (
              <tr key={p.uuid}>
                <td>{p.title}</td>
                <td>{truncate(p.statement, 80)}</td>
                <td>{p.test_cases ? p.test_cases.length : 0}</td>
                <td>{new Date(p.created_at).toLocaleDateString()}</td>
                <td>
                  <div className={styles.cellActions}>
                    <button onClick={() => openEdit(p)}>Edit</button>
                    <button className="btn-danger" onClick={() => handleDelete(p)}>
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showModal ? (
        <div className="overlay">
          <div className="modal">
            <h2>{editingUuid ? "Edit Problem" : "Create Problem"}</h2>
            <form onSubmit={handleSubmit} className={styles.form}>
              <label>
                Title *
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  required
                />
              </label>
              <label>
                Statement *
                <textarea
                  value={form.statement}
                  onChange={(e) =>
                    setForm({ ...form, statement: e.target.value })
                  }
                  rows={3}
                  required
                />
              </label>
              <label>
                Hints
                <textarea
                  value={form.hints}
                  onChange={(e) => setForm({ ...form, hints: e.target.value })}
                  rows={2}
                />
              </label>
              <label>
                Examples
                <textarea
                  value={form.examples}
                  onChange={(e) =>
                    setForm({ ...form, examples: e.target.value })
                  }
                  rows={2}
                />
              </label>
              <fieldset>
                <legend>Test Cases</legend>
                {form.testCases.map((tc, i) => (
                  <div key={i} className={styles.testCaseRow}>
                    <label>
                      Input
                      <input
                        type="text"
                        value={tc.input}
                        onChange={(e) =>
                          updateTestCase(i, "input", e.target.value)
                        }
                        placeholder="[1, 2]"
                      />
                    </label>
                    <label>
                      Output
                      <input
                        type="text"
                        value={tc.output}
                        onChange={(e) =>
                          updateTestCase(i, "output", e.target.value)
                        }
                        placeholder="3"
                      />
                    </label>
                    <button
                      type="button"
                      onClick={() => removeTestCase(i)}
                      aria-label={`Remove test case ${i + 1}`}
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button type="button" onClick={addTestCase}>
                  Add Test Case
                </button>
              </fieldset>
              {parseError ? <p className="error-text">{parseError}</p> : null}
              <div className={styles.formButtons}>
                <button type="submit" className="btn-primary" disabled={saving}>
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

export default ProblemsPage;
