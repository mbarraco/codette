import { existsSync } from "node:fs";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const defaultProxyTarget = existsSync("/.dockerenv")
  ? "http://api:8000"
  : "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: ["web"],
    proxy: {
      "/api": {
        target: process.env.VITE_PROXY_TARGET ?? defaultProxyTarget,
        changeOrigin: true,
        // Keep versioned API routes intact, but map legacy /api/health to /health.
        rewrite: (path) =>
          path === "/api/health" ? "/health" : path,
      },
    },
  },
});
