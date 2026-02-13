import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import styles from "./MonitorPage.module.css";

type RunSummary = {
  uuid: string;
  status: string;
  execution_ref: string | null;
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
  const [loading, setLoading] = useState(true);

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
              <table>
                <thead>
                  <tr>
                    <th>Submission</th>
                    <th>Problem</th>
                    <th>Status</th>
                    <th>Attempts</th>
                    <th>Last Error</th>
                    <th>Queued At</th>
                  </tr>
                </thead>
                <tbody>
                  {queueEntries.map((e) => {
                    const status = deriveQueueStatus(e);
                    return (
                      <tr key={e.uuid}>
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
                      </tr>
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
              <table>
                <thead>
                  <tr>
                    <th>Run</th>
                    <th>Submission</th>
                    <th>Status</th>
                    <th>Execution Ref</th>
                    <th>Created At</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((r) => (
                    <tr key={r.uuid}>
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
                      <td>{new Date(r.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
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
