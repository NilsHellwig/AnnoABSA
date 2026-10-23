import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Shared by playwright.config.ts and the specs (each worker loads it), so paths must be deterministic.
const here = path.dirname(fileURLToPath(import.meta.url));

export const repoRoot = path.resolve(here, "..", "..");
export const fixturesDir = path.join(here, "fixtures");
export const workDir = path.join(os.tmpdir(), "annoabsa-e2e");
export const dataFile = path.join(workDir, "data.json");
export const configFile = path.join(workDir, "config.json");

export const backendPort = Number(process.env.E2E_BACKEND_PORT) || 8123;
export const frontendPort = Number(process.env.E2E_FRONTEND_PORT) || 3123;
export const backendUrl = `http://localhost:${backendPort}`;
export const frontendUrl = `http://localhost:${frontendPort}`;

fs.mkdirSync(workDir, { recursive: true });
fs.copyFileSync(path.join(fixturesDir, "config.json"), configFile);
if (!fs.existsSync(dataFile)) fs.copyFileSync(path.join(fixturesDir, "data.json"), dataFile);
