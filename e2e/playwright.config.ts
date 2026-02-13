import { defineConfig } from "@playwright/test";

const resultsDir = "./results";

export default defineConfig({
  testDir: "./tests",
  outputDir: `${resultsDir}/artifacts`,
  timeout: 30_000,
  retries: 1,
  use: {
    baseURL: process.env.BASE_URL ?? "http://web:5173",
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: `${resultsDir}/report` }],
  ],
});
