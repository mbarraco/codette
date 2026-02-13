import { useEffect, useState } from "react";
import styles from "./App.module.css";

function App() {
  const [health, setHealth] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => setHealth(data.status))
      .catch(() => setHealth("error"));
  }, []);

  return (
    <div className={`page ${styles.hero}`}>
      <h1>Codette</h1>
      <p className={styles.subtitle}>Mini-LeetCode Platform</p>
      <p className={styles.status}>
        API Health: <strong>{health ?? "loading..."}</strong>
      </p>
      <p className={styles.hint}>
        Navigate to <code>/problem/:uuid</code> to view a problem and submit a
        solution.
      </p>
    </div>
  );
}

export default App;
