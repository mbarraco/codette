import styles from "./StatusBadge.module.css";

type StatusBadgeProps = {
  status: string;
  variant?: "queue" | "run" | "submission";
};

function badgeClass(status: string, variant: "queue" | "run" | "submission"): string {
  if (variant === "submission") {
    switch (status) {
      case "passed":
        return styles.badgeDone;
      case "failed":
      case "error":
        return styles.badgeFailed;
      case "grading":
      case "running":
        return styles.badgeProcessing;
      case "queued":
        return styles.badgePending;
      case "submitted":
        return styles.badgeSubmitted;
      default:
        return styles.badgePending;
    }
  }
  if (variant === "run") {
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

function StatusBadge({ status, variant = "queue" }: StatusBadgeProps) {
  return (
    <span className={`${styles.badge} ${badgeClass(status, variant)}`}>
      {status}
    </span>
  );
}

export default StatusBadge;
