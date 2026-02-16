import { type FormEvent, useState } from "react";
import type { TestCase, Problem } from "../types/api";
import { useFetch } from "../hooks/useFetch";
import { apiFetch } from "../utils/apiFetch";
import PageHeader from "../components/PageHeader";
import DataTable from "../components/DataTable";
import styles from "./ProblemsPage.module.css";

type TestCaseRow = {
  input: string;
  output: string;
};

type FormData = {
  title: string;
  functionSignature: string;
  statement: string;
  hints: string;
  examples: string;
  testCases: TestCaseRow[];
};

const emptyRow: TestCaseRow = { input: "", output: "" };

const emptyForm: FormData = {
  title: "",
  functionSignature: "",
  statement: "",
  hints: "",
  examples: "",
  testCases: [],
};

function ProblemsPage() {
  const { data: problems, loading, refetch } = useFetch<Problem[]>(
    "/api/v1/problems/",
  );

  const [showModal, setShowModal] = useState(false);
  const [editingUuid, setEditingUuid] = useState<string | null>(null);
  const [form, setForm] = useState<FormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

  const openCreate = () => {
    setEditingUuid(null);
    setForm(emptyForm);
    setParseError(null);
    setShowModal(true);
  };

  const openEdit = (p: Problem) => {
    setEditingUuid(p.uuid);
    setForm({
      title: p.title,
      functionSignature: p.function_signature ?? "",
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
      function_signature: form.functionSignature || null,
    };

    try {
      const res = editingUuid
        ? await apiFetch(`/api/v1/problems/${editingUuid}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          })
        : await apiFetch("/api/v1/problems/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Error ${res.status}`);
      }

      closeModal();
      refetch();
    } catch (err) {
      setParseError(err instanceof Error ? err.message : "Failed to save problem");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (p: Problem) => {
    if (!confirm(`Delete problem "${p.title}"?`)) return;
    await apiFetch(`/api/v1/problems/${p.uuid}`, { method: "DELETE" });
    refetch();
  };

  const truncate = (s: string, max: number) =>
    s.length > max ? s.slice(0, max) + "..." : s;

  return (
    <div className="page">
      <PageHeader
        title="Problems"
        action={
          <button type="button" className="btn-primary" onClick={openCreate}>
            Create Problem
          </button>
        }
      />

      <DataTable
        loading={loading}
        empty={!problems || problems.length === 0}
        emptyMessage="No problems yet."
      >
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
            {(problems ?? []).map((p) => (
              <tr key={p.uuid}>
                <td>{p.title}</td>
                <td>{truncate(p.statement, 80)}</td>
                <td>{p.test_cases ? p.test_cases.length : 0}</td>
                <td>{new Date(p.created_at).toLocaleDateString()}</td>
                <td>
                  <div className="cellActions">
                    <button type="button" onClick={() => openEdit(p)}>Edit</button>
                    <button type="button" className="btn-danger" onClick={() => handleDelete(p)}>
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </DataTable>

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
                Function Signature *
                <input
                  type="text"
                  value={form.functionSignature}
                  onChange={(e) =>
                    setForm({ ...form, functionSignature: e.target.value })
                  }
                  placeholder="def solve(a, b):"
                  style={{ fontFamily: "monospace" }}
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
