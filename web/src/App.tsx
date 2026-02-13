import { useEffect, useState } from "react";

function App() {
  const [health, setHealth] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => setHealth(data.status))
      .catch(() => setHealth("error"));
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Codette</h1>
      <p>Mini-LeetCode Platform</p>
      <p>
        API Health: <strong>{health ?? "loading..."}</strong>
      </p>
      <p>
        <a href="/problems">Manage Problems</a>
      </p>
      <p>
        Navigate to <code>/problem/:uuid</code> to view a problem and submit a solution.
      </p>
    </div>
  );
}

export default App;
