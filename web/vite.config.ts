import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://api:8000",
        changeOrigin: true,
        // Keep versioned API routes intact, but map legacy /api/health to /health.
        rewrite: (path) =>
          path === "/api/health" ? "/health" : path,
      },
    },
  },
});
