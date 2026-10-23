import { defineConfig, devices } from "@playwright/test";
import { backendPort, backendUrl, configFile, dataFile, frontendPort, frontendUrl, repoRoot } from "./e2e/env";

// Python interpreter with the backend requirements installed, e.g. PYTHON=../.venv/bin/python
const python = process.env.PYTHON || "python3";

export default defineConfig({
  testDir: "./e2e",
  // All tests share one backend and data file
  workers: 1,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: frontendUrl,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `"${python}" -m uvicorn main:app --host localhost --port ${backendPort} --log-level warning`,
      cwd: repoRoot,
      url: `${backendUrl}/version`,
      reuseExistingServer: false,
      env: {
        ABSA_DATA_PATH: dataFile,
        ABSA_CONFIG_PATH: configFile,
        ABSA_ALLOWED_ORIGINS: frontendUrl,
      },
    },
    {
      command: "npx vite",
      url: frontendUrl,
      reuseExistingServer: false,
      env: {
        VITE_BACKEND_URL: backendUrl,
        ANNOABSA_FRONTEND_PORT: String(frontendPort),
        ANNOABSA_FRONTEND_HOST: "localhost",
        ANNOABSA_NO_OPEN: "1",
      },
    },
  ],
});
