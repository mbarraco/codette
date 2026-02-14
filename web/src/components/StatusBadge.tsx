import styles from "./StatusBadge.module.css";

type StatusBadgeProps = {
  status: string;
  variant?: "queue" | "run";
};

function badgeClass(status: string, variant: "queue" | "run"): string {
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
