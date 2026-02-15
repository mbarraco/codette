import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Submission, RunSummary, EvaluationDetail } from "../types/api";
import { truncateUuid } from "../utils/format";
import { useFetch } from "../hooks/useFetch";
import StatusBadge from "../components/StatusBadge";
import CopyButton from "../components/CopyButton";
import DataTable from "../components/DataTable";
import styles from "./MonitorPage.module.css";

function deriveSubmissionStatus(s: Submission): string {
  const latestEval = [...s.evaluations].sort((a, b) =>
    b.created_at.localeCompare(a.created_at),
  )[0];
  if (latestEval) {
    return latestEval.success ? "passed" : "failed";
  }

  const latestRun = [...s.runs].sort((a, b) =>
    b.created_at.localeCompare(a.created_at),
  )[0];
  if (latestRun?.status === "failed") return "error";
  if (latestRun?.status === "runner_done") return "grading";

  const qe = s.queue_entries[0];
  if (qe?.last_checked_at) return "running";
  if (qe) return "queued";

  return "submitted";
}

function runEmoji(run: RunSummary, evaluation: EvaluationDetail | undefined): string {
  if (run.status === "failed") return "\u26a0\ufe0f";
  if (evaluation) {
    return evaluation.success ? "\u2705" : "\u274c";
  }
  if (run.status === "runner_done" || run.status === "done") return "\u23f3";
  return "\u25cb";
}

function runEmojiLabel(run: RunSummary, evaluation: EvaluationDetail | undefined): string {
  if (run.status === "failed") return "error";
  if (evaluation) return evaluation.success ? "passed" : "failed";
  if (run.status === "runner_done" || run.status === "done") return "grading";
  return run.status;
}

type ProblemMap = Record<string, string>;

type ProblemListItem = {
  uuid: string;
  title: string;
};

function MonitorPage() {
  const { data: submissions, loading } = useFetch<Submission[]>(
    "/api/v1/submissions/",
    { pollingInterval: 5000 },
  );
  const { data: problemsList } = useFetch<ProblemListItem[]>(
    "/api/v1/problems/",
    { pollingInterval: 5000 },
  );

  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const [problemNames, setProblemNames] = useState<ProblemMap>({});

  useEffect(() => {
    if (!problemsList) return;
    const map: ProblemMap = {};
    for (const prob of problemsList) {
      map[prob.uuid] = prob.title;
    }
    setProblemNames(map);
  }, [problemsList]);

  const toggleRun = (uuid: string) => {
    setExpandedRunId((prev) => (prev === uuid ? null : uuid));
  };

  return (
    <div className="page">
      <h1>Monitor</h1>

      <DataTable
        loading={loading}
        empty={!submissions || submissions.length === 0}
        emptyMessage="No submissions yet."
      >
        <table className={styles.monitorTable}>
          <thead>
            <tr>
              <th>Problem</th>
              <th>Status</th>
              <th>Runs</th>
              <th>Attempts</th>
              <th>Last Error</th>
              <th>Submitted At</th>
            </tr>
          </thead>
          <tbody>
            {(submissions ?? []).map((s) => {
              const status = deriveSubmissionStatus(s);
              const qe = s.queue_entries[0];
              const sortedRuns = [...s.runs].sort((a, b) =>
                a.created_at.localeCompare(b.created_at),
              );
              const sortedEvals = [...s.evaluations].sort((a, b) =>
                a.created_at.localeCompare(b.created_at),
              );
              const evalByRunIndex = new Map<number, EvaluationDetail>();
              sortedEvals.forEach((ev, i) => evalByRunIndex.set(i, ev));
              const expandedRun = sortedRuns.find(
                (r) => r.uuid === expandedRunId,
              );
              const expandedRunIndex = expandedRun
                ? sortedRuns.indexOf(expandedRun)
                : -1;
              const expandedRunEval = expandedRunIndex >= 0
                ? evalByRunIndex.get(expandedRunIndex)
                : undefined;

              return (
                <Fragment key={s.uuid}>
                  <tr>
                    <td>
                      <Link to={`/problem/${s.problem_uuid}`}>
                        {problemNames[s.problem_uuid] ??
                          truncateUuid(s.problem_uuid)}
                      </Link>
                    </td>
                    <td>
                      <StatusBadge status={status} variant="submission" />
                    </td>
                    <td>
                      <div className={styles.runsCell}>
                        {sortedRuns.length > 0
                          ? sortedRuns.map((r, i) => {
                              const ev = evalByRunIndex.get(i);
                              const label = runEmojiLabel(r, ev);
                              return (
                                <button
                                  key={r.uuid}
                                  type="button"
                                  className={styles.runEmoji}
                                  title={`${label} — ${truncateUuid(r.uuid)}`}
                                  aria-label={`Run ${truncateUuid(r.uuid)}: ${label}`}
                                  onClick={() => toggleRun(r.uuid)}
                                >
                                  {runEmoji(r, ev)}
                                </button>
                              );
                            })
                          : "-"}
                      </div>
                    </td>
                    <td>{qe?.attempt_count ?? 0}</td>
                    <td
                      className={styles.truncate}
                      title={qe?.last_error ?? ""}
                    >
                      {qe?.last_error ?? "-"}
                    </td>
                    <td>{new Date(s.created_at).toLocaleString()}</td>
                  </tr>
                  {expandedRun ? (
                    <tr className={styles.detailsRow}>
                      <td className={styles.detailsCell} colSpan={6}>
                        <div className={styles.detailsMeta}>
                          <strong>
                            Run {truncateUuid(expandedRun.uuid)}
                          </strong>
                          <StatusBadge
                            status={expandedRun.status}
                            variant="run"
                          />
                          {expandedRun.execution_ref ? (
                            <span className={styles.mono}>
                              ref: {expandedRun.execution_ref}
                            </span>
                          ) : null}
                          <span>
                            {new Date(
                              expandedRun.created_at,
                            ).toLocaleString()}
                          </span>
                        </div>
                        {expandedRun.failure_stage ? (
                          <div className={styles.detailsMeta}>
                            <strong>Failed at:</strong>{" "}
                            {expandedRun.failure_stage}
                          </div>
                        ) : null}
                        {expandedRun.failure_error ? (
                          <>
                            <div className={styles.detailsMeta}>
                              <strong>Error</strong>
                              <CopyButton text={expandedRun.failure_error} />
                            </div>
                            <div className={styles.errorBox}>
                              {expandedRun.failure_error}
                            </div>
                          </>
                        ) : null}
                        {expandedRunEval ? (
                          <div className={styles.detailsMeta}>
                            <strong>Evaluation:</strong>
                            <StatusBadge
                              status={expandedRunEval.success ? "passed" : "failed"}
                              variant="submission"
                            />
                          </div>
                        ) : null}
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
  );
}

export default MonitorPage;
