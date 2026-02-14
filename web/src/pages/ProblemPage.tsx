import { type FormEvent, useState } from "react";
import { useParams } from "react-router-dom";
import type { Problem, SubmissionSummary } from "../types/api";
import { useFetch } from "../hooks/useFetch";
import styles from "./ProblemPage.module.css";

type SubmitState = "idle" | "submitting" | "success" | "error";

function ProblemPage() {
  const { uuid } = useParams<{ uuid: string }>();

  const { data: problem, loading, error: fetchError } = useFetch<Problem>(
    `/api/v1/problems/${uuid}`,
  );

  const [code, setCode] = useState("def solve():\n    return 42\n");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [statusCode, setStatusCode] = useState<number | null>(null);
  const [submission, setSubmission] = useState<SubmissionSummary | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!uuid) return;

    setSubmitState("submitting");
    setStatusCode(null);
    setSubmission(null);
    setSubmitError(null);

    try {
      const response = await fetch("/api/v1/submissions/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem_uuid: uuid, code }),
      });

      setStatusCode(response.status);

      const contentType = response.headers.get("content-type") ?? "";
      const body = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

      if (!response.ok) {
        setSubmitState("error");
        const detail =
          typeof body === "object" && body !== null && "detail" in body
            ? String(body.detail)
            : `Error ${response.status}`;
        setSubmitError(detail);
        return;
      }

      setSubmitState("success");
      setSubmission(body as SubmissionSummary);
    } catch (err) {
      setSubmitState("error");
      setSubmitError(err instanceof Error ? err.message : "Unexpected error");
    }
  };

  if (loading) return <div className="page"><p>Loading problem...</p></div>;
  if (fetchError) return <div className="page"><p className="error-text">Error: {fetchError}</p></div>;
  if (!problem) return <div className="page"><p>Problem not found.</p></div>;

  return (
    <div className="page">
      <h1>{problem.title}</h1>

      <section className={styles.section}>
        <h2>Statement</h2>
        <p>{problem.statement}</p>
      </section>

      {problem.hints ? (
        <section className={styles.section}>
          <h2>Hints</h2>
          <p>{problem.hints}</p>
        </section>
      ) : null}

      {problem.examples ? (
        <section className={styles.section}>
          <h2>Examples</h2>
          <pre>{problem.examples}</pre>
        </section>
      ) : null}

      <hr />

      <h2>Submit Solution</h2>
      <form onSubmit={submit} className={styles.codeForm}>
        <label>
          Code
          <textarea
            value={code}
            onChange={(event) => setCode(event.target.value)}
            rows={10}
            className={styles.codeArea}
          />
        </label>

        <button type="submit" className="btn-primary" disabled={submitState === "submitting"}>
          {submitState === "submitting" ? "Submitting..." : "Submit"}
        </button>
      </form>

      <div className={styles.statusLine}>
        <p>
          Submission state: <strong>{submitState}</strong>
        </p>
        {statusCode !== null ? <p>HTTP status: {statusCode}</p> : null}
      </div>

      {submission ? (
        <div className={styles.resultBlock}>
          <h3>Submission Created</h3>
          <pre>{JSON.stringify(submission, null, 2)}</pre>
        </div>
      ) : null}

      {submitError ? (
        <div className={styles.resultBlock}>
          <p className="error-text">{submitError}</p>
        </div>
      ) : null}
    </div>
  );
}

export default ProblemPage;
