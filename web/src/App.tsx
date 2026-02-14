import { useFetch } from "./hooks/useFetch";
import styles from "./App.module.css";

type HealthResponse = {
  status: string;
};

function App() {
  const { data, error } = useFetch<HealthResponse>("/api/health");

  const healthText = error ? "error" : (data?.status ?? "loading...");

  return (
    <div className={`page ${styles.hero}`}>
      <h1>Codette</h1>
      <p className={styles.subtitle}>Mini-LeetCode Platform</p>
      <p className={styles.status}>
        API Health: <strong>{healthText}</strong>
      </p>
    </div>
  );
}

export default App;
