import { type FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

type ProblemData = {
  uuid: string;
  title: string;
  statement: string;
  hints: string | null;
  examples: string | null;
  created_at: string;
};

type SubmissionResponse = {
  uuid: string;
  artifact_uri: string;
  problem_uuid: string;
  created_at: string;
};

type SubmitState = "idle" | "submitting" | "success" | "error";

function ProblemPage() {
  const { uuid } = useParams<{ uuid: string }>();

  const [problem, setProblem] = useState<ProblemData | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [code, setCode] = useState("def solve():\n    return 42\n");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [statusCode, setStatusCode] = useState<number | null>(null);
  const [submission, setSubmission] = useState<SubmissionResponse | null>(null);
  const [submitError, setSubmitError] = useState<unknown>(null);

  useEffect(() => {
    if (!uuid) return;
    setLoading(true);
    setFetchError(null);

    fetch(`/api/v1/problems/${uuid}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Problem not found (${res.status})`);
        return res.json();
      })
      .then((data) => setProblem(data))
      .catch((err) => setFetchError(err.message))
      .finally(() => setLoading(false));
  }, [uuid]);

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

      const contentType = response.headers.get("content-type") ?? "";
      const body = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

      setStatusCode(response.status);

      if (!response.ok) {
        setSubmitState("error");
        setSubmitError(body);
        return;
      }

      setSubmitState("success");
      setSubmission(body as SubmissionResponse);
    } catch (error) {
      setSubmitState("error");
      setSubmitError({
        message: error instanceof Error ? error.message : "Unexpected error",
      });
    }
  };

  if (loading) return <p>Loading problem...</p>;
  if (fetchError) return <p>Error: {fetchError}</p>;
  if (!problem) return <p>Problem not found.</p>;

  return (
    <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>{problem.title}</h1>

      <section>
        <h2>Statement</h2>
        <p>{problem.statement}</p>
      </section>

      {problem.hints ? (
        <section>
          <h2>Hints</h2>
          <p>{problem.hints}</p>
        </section>
      ) : null}

      {problem.examples ? (
        <section>
          <h2>Examples</h2>
          <pre>{problem.examples}</pre>
        </section>
      ) : null}

      <hr />

      <h2>Submit Solution</h2>
      <form onSubmit={submit} style={{ display: "grid", gap: "0.75rem", maxWidth: "720px" }}>
        <label>
          Code
          <textarea
            value={code}
            onChange={(event) => setCode(event.target.value)}
            rows={10}
            style={{ width: "100%", fontFamily: "monospace" }}
          />
        </label>

        <button type="submit" disabled={submitState === "submitting"}>
          {submitState === "submitting" ? "Submitting..." : "Submit"}
        </button>
      </form>

      <p>
        Submission state: <strong>{submitState}</strong>
      </p>
      {statusCode !== null ? <p>HTTP status: {statusCode}</p> : null}

      {submission ? (
        <>
          <h3>Success JSON</h3>
          <pre>{JSON.stringify(submission, null, 2)}</pre>
        </>
      ) : null}

      {submitError ? (
        <>
          <h3>Error JSON</h3>
          <pre>{JSON.stringify(submitError, null, 2)}</pre>
        </>
      ) : null}
    </div>
  );
}

export default ProblemPage;
