import { useCallback, useEffect, useRef, useState } from "react";
import { basicSetup } from "codemirror";
import { python } from "@codemirror/lang-python";
import { EditorState } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
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
};

function CodeEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (val: string) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);

  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    if (!containerRef.current) return;

    const state = EditorState.create({
      doc: value,
      extensions: [
        basicSetup,
        python(),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
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
        <button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "New Submission"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className={styles.form}>
          <label>
            Problem
            <select
              value={selectedProblem}
              onChange={(e) => setSelectedProblem(e.target.value)}
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
            <CodeEditor value={code} onChange={handleCodeChange} />
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
