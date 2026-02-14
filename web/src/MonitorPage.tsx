import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import styles from "./MonitorPage.module.css";

type RunSummary = {
  uuid: string;
  status: string;
  execution_ref: string | null;
  failure_stage: string | null;
  failure_error: string | null;
  runner_output_uri: string | null;
  grader_output_uri: string | null;
  created_at: string;
};

type EvaluationSummary = {
  uuid: string;
  success: boolean;
  created_at: string;
};

type QueueEntry = {
  uuid: string;
  submission_uuid: string;
  problem_uuid: string;
  attempt_count: number;
  last_checked_at: string | null;
  last_error: string | null;
  created_at: string;
  runs: RunSummary[];
  evaluations: EvaluationSummary[];
};

type RunEntry = {
  uuid: string;
  submission_uuid: string;
  status: string;
  execution_ref: string | null;
  failure_stage: string | null;
  failure_error: string | null;
  runner_output_uri: string | null;
  grader_output_uri: string | null;
  created_at: string;
};

function deriveQueueStatus(entry: QueueEntry): string {
  if (entry.evaluations.some((e) => e.success)) return "done";
  if (entry.last_error) return "failed";
  if (entry.last_checked_at) return "processing";
  return "pending";
}

function queueBadgeClass(status: string): string {
  switch (status) {
    case "done":
      return styles.badgeDone;
    case "failed":
      return styles.badgeFailed;
    case "processing":
      return styles.badgeProcessing;
    default:
      return styles.badgePending;
  }
}

function runBadgeClass(status: string): string {
  switch (status) {
    case "done":
      return styles.badgeDone;
    case "failed":
      return styles.badgeFailed;
    case "runner_done":
      return styles.badgeRunnerDone;
    default:
      return styles.badgeQueued;
  }
}

function truncateUuid(uuid: string): string {
  return uuid.slice(0, 8);
}

type ProblemMap = Record<string, string>;

function MonitorPage() {
  const [queueEntries, setQueueEntries] = useState<QueueEntry[]>([]);
  const [runs, setRuns] = useState<RunEntry[]>([]);
  const [problemNames, setProblemNames] = useState<ProblemMap>({});
  const [expandedQueueIds, setExpandedQueueIds] = useState<Set<string>>(new Set());
  const [expandedRunIds, setExpandedRunIds] = useState<Set<string>>(new Set());
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const toggleQueueDetail = (uuid: string) => {
    setExpandedQueueIds((prev) => {
      const next = new Set(prev);
      if (next.has(uuid)) {
        next.delete(uuid);
      } else {
        next.add(uuid);
      }
      return next;
    });
  };

  const toggleRunDetail = (uuid: string) => {
    setExpandedRunIds((prev) => {
      const next = new Set(prev);
      if (next.has(uuid)) {
        next.delete(uuid);
      } else {
        next.add(uuid);
      }
      return next;
    });
  };

  const fetchData = async () => {
    try {
      const [qRes, rRes, pRes] = await Promise.all([
        fetch("/api/v1/queue/"),
        fetch("/api/v1/runs/"),
        fetch("/api/v1/problems/"),
      ]);
      const q = await qRes.json();
      const r = await rRes.json();
      const p = await pRes.json();
      const map: ProblemMap = {};
      for (const prob of p) {
        map[prob.uuid] = prob.title;
      }
      setQueueEntries(q);
      setRuns(r);
      setProblemNames(map);
    } catch {
      setQueueEntries([]);
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  const copyText = async (value: string | null, key: string) => {
    if (value == null) return;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(value);
      } else {
        const el = document.createElement("textarea");
        el.value = value;
        el.style.position = "fixed";
        el.style.left = "-9999px";
        document.body.appendChild(el);
        el.focus();
        el.select();
        document.execCommand("copy");
        document.body.removeChild(el);
      }
      setCopiedKey(key);
      window.setTimeout(() => {
        setCopiedKey((prev) => (prev === key ? null : prev));
      }, 1200);
    } catch {
      setCopiedKey(null);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="page">
      <h1>Monitor</h1>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          <div className={styles.section}>
            <h2>Queue</h2>
            {queueEntries.length === 0 ? (
              <p>No queue entries.</p>
            ) : (
              <table className={styles.monitorTable}>
                <thead>
                  <tr>
                    <th>Submission</th>
                    <th>Problem</th>
                    <th>Status</th>
                    <th>Attempts</th>
                    <th>Last Error</th>
                    <th>Queued At</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {queueEntries.map((e) => {
                    const status = deriveQueueStatus(e);
                    const expanded = expandedQueueIds.has(e.uuid);
                    return (
                      <Fragment key={e.uuid}>
                        <tr>
                          <td className={styles.mono}>
                            <Link to={`/submissions`}>
                              {truncateUuid(e.submission_uuid)}
                            </Link>
                          </td>
                          <td>
                            <Link to={`/problem/${e.problem_uuid}`}>
                              {problemNames[e.problem_uuid] ?? truncateUuid(e.problem_uuid)}
                            </Link>
                          </td>
                          <td>
                            <span
                              className={`${styles.badge} ${queueBadgeClass(status)}`}
                            >
                              {status}
                            </span>
                          </td>
                          <td>{e.attempt_count}</td>
                          <td
                            className={styles.truncate}
                            title={e.last_error ?? ""}
                          >
                            {e.last_error ?? "-"}
                          </td>
                          <td>
                            {new Date(e.created_at).toLocaleString()}
                          </td>
                          <td>
                            <button
                              type="button"
                              className={styles.detailsButton}
                              onClick={() => toggleQueueDetail(e.uuid)}
                            >
                              {expanded ? "Hide" : "View"}
                            </button>
                          </td>
                        </tr>
                        {expanded ? (
                          <tr className={styles.detailsRow}>
                            <td className={styles.detailsCell} colSpan={7}>
                              <div className={styles.detailsMeta}>
                                <strong>Error</strong>
                                {e.last_error ? (
                                  <>
                                    <button
                                      type="button"
                                      className={styles.copyButton}
                                      onClick={() =>
                                        copyText(
                                          e.last_error,
                                          `queue:${e.uuid}`,
                                        )
                                      }
                                    >
                                      Copy
                                    </button>
                                    {copiedKey === `queue:${e.uuid}` ? (
                                      <span className={styles.copiedTag}>Copied</span>
                                    ) : null}
                                  </>
                                ) : null}
                              </div>
                              <div className={styles.errorBox}>
                                {e.last_error ?? "-"}
                              </div>
                              <pre className={styles.detailsPre}>
                                {JSON.stringify(e, null, 2)}
                              </pre>
                            </td>
                          </tr>
                        ) : null}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          <div className={styles.section}>
            <h2>Runs</h2>
            {runs.length === 0 ? (
              <p>No runs yet.</p>
            ) : (
              <table className={styles.monitorTable}>
                <thead>
                  <tr>
                    <th>Run</th>
                    <th>Submission</th>
                    <th>Status</th>
                    <th>Execution Ref</th>
                    <th>Failed At</th>
                    <th>Last Error</th>
                    <th>Created At</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((r) => {
                    const expanded = expandedRunIds.has(r.uuid);
                    return (
                      <Fragment key={r.uuid}>
                        <tr>
                          <td className={styles.mono}>{truncateUuid(r.uuid)}</td>
                          <td className={styles.mono}>
                            <Link to={`/submissions`}>
                              {truncateUuid(r.submission_uuid)}
                            </Link>
                          </td>
                          <td>
                            <span
                              className={`${styles.badge} ${runBadgeClass(r.status)}`}
                            >
                              {r.status}
                            </span>
                          </td>
                          <td className={styles.mono}>{r.execution_ref ?? "-"}</td>
                          <td>{r.failure_stage ?? "-"}</td>
                          <td className={styles.truncate} title={r.failure_error ?? ""}>
                            {r.failure_error ?? "-"}
                          </td>
                          <td>{new Date(r.created_at).toLocaleString()}</td>
                          <td>
                            <button
                              type="button"
                              className={styles.detailsButton}
                              onClick={() => toggleRunDetail(r.uuid)}
                            >
                              {expanded ? "Hide" : "View"}
                            </button>
                          </td>
                        </tr>
                        {expanded ? (
                          <tr className={styles.detailsRow}>
                            <td className={styles.detailsCell} colSpan={8}>
                              <div className={styles.detailsMeta}>
                                <strong>Error</strong>
                                {r.failure_error ? (
                                  <>
                                    <button
                                      type="button"
                                      className={styles.copyButton}
                                      onClick={() =>
                                        copyText(
                                          r.failure_error,
                                          `run:${r.uuid}`,
                                        )
                                      }
                                    >
                                      Copy
                                    </button>
                                    {copiedKey === `run:${r.uuid}` ? (
                                      <span className={styles.copiedTag}>Copied</span>
                                    ) : null}
                                  </>
                                ) : null}
                              </div>
                              <div className={styles.errorBox}>
                                {r.failure_error ?? "-"}
                              </div>
                              <pre className={styles.detailsPre}>
                                {JSON.stringify(r, null, 2)}
                              </pre>
                            </td>
                          </tr>
                        ) : null}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default MonitorPage;
