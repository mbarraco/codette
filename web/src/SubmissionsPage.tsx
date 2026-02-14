import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { basicSetup } from "codemirror";
import { python } from "@codemirror/lang-python";
import { Compartment, EditorState } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { linter, type Diagnostic } from "@codemirror/lint";
import styles from "./SubmissionsPage.module.css";

type SubmissionData = {
  uuid: string;
  artifact_uri: string;
  problem_uuid: string;
  created_at: string;
  runs: { uuid: string; status: string }[];
  queue_entries: unknown[];
  evaluations: unknown[];
};

type ProblemOption = {
  uuid: string;
  title: string;
  function_signature: string | null;
};

function CodeEditor({
  value,
  onChange,
  functionSignature,
}: {
  value: string;
  onChange: (val: string) => void;
  functionSignature: string | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const lintCompartment = useRef(new Compartment());

  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;
  const suppressSync = useRef(false);

  useEffect(() => {
    if (!containerRef.current) return;

    const state = EditorState.create({
      doc: value,
      extensions: [
        basicSetup,
        python(),
        lintCompartment.current.of([]),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            suppressSync.current = true;
            onChangeRef.current(update.state.doc.toString());
          }
        }),
      ],
    });

    const view = new EditorView({ state, parent: containerRef.current });
    viewRef.current = view;

    return () => view.destroy();
    // Only create editor once when mounted
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const view = viewRef.current;
    if (!view) return;
    if (suppressSync.current) {
      suppressSync.current = false;
      return;
    }
    const current = view.state.doc.toString();
    if (current !== value) {
      view.dispatch({
        changes: { from: 0, to: current.length, insert: value },
      });
    }
  }, [value]);

  useEffect(() => {
    const view = viewRef.current;
    if (!view) return;

    if (!functionSignature) {
      view.dispatch({
        effects: lintCompartment.current.reconfigure([]),
      });
      return;
    }

    const match = functionSignature.match(/def\s+(\w+)\s*\(/);
    const expectedName = match ? match[1] : null;

    if (!expectedName) {
      view.dispatch({
        effects: lintCompartment.current.reconfigure([]),
      });
      return;
    }

    const sigLinter = linter((view) => {
      const doc = view.state.doc.toString();
      const pattern = new RegExp(`def\\s+${expectedName}\\s*\\(`);
      if (pattern.test(doc)) return [];
      const diagnostic: Diagnostic = {
        from: 0,
        to: Math.min(doc.length, 1),
        severity: "warning",
        message: `Expected function definition: ${functionSignature}`,
      };
      return [diagnostic];
    });

    view.dispatch({
      effects: lintCompartment.current.reconfigure(sigLinter),
    });
  }, [functionSignature]);

  return <div ref={containerRef} className={styles.editor} />;
}

function SubmissionsPage() {
  const [submissions, setSubmissions] = useState<SubmissionData[]>([]);
  const [problems, setProblems] = useState<ProblemOption[]>([]);
  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);
  const [selectedProblem, setSelectedProblem] = useState("");
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const problemNames: Record<string, string> = {};
  for (const p of problems) {
    problemNames[p.uuid] = p.title;
  }

  const fetchData = async () => {
    setLoading(true);
    try {
      const [subsRes, probsRes] = await Promise.all([
        fetch("/api/v1/submissions/"),
        fetch("/api/v1/problems/"),
      ]);
      const subs = await subsRes.json();
      const probs = await probsRes.json();
      setProblems(probs);
      setSubmissions(subs);
    } catch {
      setSubmissions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const selectedFunctionSignature = useMemo(() => {
    if (!selectedProblem) return null;
    const p = problems.find((prob) => prob.uuid === selectedProblem);
    return p?.function_signature ?? null;
  }, [selectedProblem, problems]);

  const handleProblemChange = useCallback(
    (uuid: string) => {
      setSelectedProblem(uuid);
      if (!uuid) {
        setCode("");
        return;
      }
      const p = problems.find((prob) => prob.uuid === uuid);
      const sig = p?.function_signature;
      if (sig) {
        setCode(`${sig}\n    # Write your solution here\n`);
      } else {
        setCode("");
      }
    },
    [problems],
  );

  const handleCodeChange = useCallback((val: string) => {
    setCode(val);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/submissions/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem_uuid: selectedProblem, code }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Error ${res.status}`);
      }
      setCode("");
      setSelectedProblem("");
      setShowForm(false);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (s: SubmissionData) => {
    if (!confirm("Delete this submission?")) return;
    await fetch(`/api/v1/submissions/${s.uuid}`, { method: "DELETE" });
    fetchData();
  };

  return (
    <div className="page">
      <div className={styles.header}>
        <h1>Submissions</h1>
        <button
          type="button"
          className="btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Cancel" : "New Submission"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className={styles.form}>
          <label>
            Problem
            <select
              value={selectedProblem}
              onChange={(e) => handleProblemChange(e.target.value)}
              required
            >
              <option value="">Select a problem...</option>
              {problems.map((p) => (
                <option key={p.uuid} value={p.uuid}>
                  {p.title}
                </option>
              ))}
            </select>
          </label>

          <div>
            <label>Code</label>
            <CodeEditor
              value={code}
              onChange={handleCodeChange}
              functionSignature={selectedFunctionSignature}
            />
          </div>

          {error && <p className={styles.error}>{error}</p>}

          <button type="submit" disabled={submitting || !code.trim()}>
            {submitting ? "Submitting..." : "Submit"}
          </button>
        </form>
      )}

      {loading ? (
        <p>Loading...</p>
      ) : submissions.length === 0 ? (
        <p>No submissions yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Problem</th>
              <th>Artifact URI</th>
              <th>Runs</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {submissions.map((s) => (
              <tr key={s.uuid}>
                <td>{problemNames[s.problem_uuid] ?? s.problem_uuid}</td>
                <td>{s.artifact_uri}</td>
                <td>{s.runs.length}</td>
                <td>{new Date(s.created_at).toLocaleDateString()}</td>
                <td>
                  <div className={styles.cellActions}>
                    <button
                      className="btn-danger"
                      onClick={() => handleDelete(s)}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default SubmissionsPage;
