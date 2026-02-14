import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { QueueEntry, RunEntry } from "../types/api";
import { truncateUuid } from "../utils/format";
import { useFetch } from "../hooks/useFetch";
import StatusBadge from "../components/StatusBadge";
import CopyButton from "../components/CopyButton";
import DataTable from "../components/DataTable";
import styles from "./MonitorPage.module.css";

function deriveQueueStatus(entry: QueueEntry): string {
  if (entry.evaluations.some((e) => e.success)) return "done";
  if (entry.last_error) return "failed";
  if (entry.last_checked_at) return "processing";
  return "pending";
}

type ProblemMap = Record<string, string>;

type ProblemListItem = {
  uuid: string;
  title: string;
};

function MonitorPage() {
  const { data: queueEntries, loading: queueLoading } = useFetch<QueueEntry[]>(
    "/api/v1/queue/",
    { pollingInterval: 5000 },
  );
  const { data: runs, loading: runsLoading } = useFetch<RunEntry[]>(
    "/api/v1/runs/",
    { pollingInterval: 5000 },
  );
  const { data: problemsList } = useFetch<ProblemListItem[]>(
    "/api/v1/problems/",
    { pollingInterval: 5000 },
  );

  const [expandedQueueIds, setExpandedQueueIds] = useState<Set<string>>(new Set());
  const [expandedRunIds, setExpandedRunIds] = useState<Set<string>>(new Set());

  const [problemNames, setProblemNames] = useState<ProblemMap>({});

  useEffect(() => {
    if (!problemsList) return;
    const map: ProblemMap = {};
    for (const prob of problemsList) {
      map[prob.uuid] = prob.title;
    }
    setProblemNames(map);
  }, [problemsList]);

  const loading = queueLoading || runsLoading;

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

  return (
    <div className="page">
      <h1>Monitor</h1>

      <DataTable loading={loading} empty={false}>
        <>
          <div className={styles.section}>
            <h2>Queue</h2>
            <DataTable
              loading={false}
              empty={!queueEntries || queueEntries.length === 0}
              emptyMessage="No queue entries."
            >
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
                  {(queueEntries ?? []).map((e) => {
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
                            <StatusBadge status={status} variant="queue" />
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
                                  <CopyButton text={e.last_error} />
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
            </DataTable>
          </div>

          <div className={styles.section}>
            <h2>Runs</h2>
            <DataTable
              loading={false}
              empty={!runs || runs.length === 0}
              emptyMessage="No runs yet."
            >
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
                  {(runs ?? []).map((r) => {
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
                            <StatusBadge status={r.status} variant="run" />
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
                                  <CopyButton text={r.failure_error} />
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
            </DataTable>
          </div>
        </>
      </DataTable>
    </div>
  );
}

export default MonitorPage;
