import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Prevent AnnoABSA from being framed by other sites and disable MIME sniffing.
const securityHeaders = {
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Content-Security-Policy": "frame-ancestors 'none'",
  "Referrer-Policy": "no-referrer",
};

// Port and host are passed in by the annoabsa CLI.
const port = Number(process.env.ANNOABSA_FRONTEND_PORT) || 3000;
const host = process.env.ANNOABSA_FRONTEND_HOST || "localhost";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port,
    host,
    strictPort: true,
    open: process.env.ANNOABSA_NO_OPEN !== "1",
    headers: securityHeaders,
  },
  preview: {
    port,
    host,
    headers: securityHeaders,
  },
  build: {
    outDir: "build",
  },
});
