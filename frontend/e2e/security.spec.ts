import { expect, test, type Page } from "@playwright/test";
import { backendUrl, frontendUrl } from "./env";
import { readData, resetData } from "./helpers";

// A page on another origin that the annotator happens to have open. It is served by
// Playwright's router, so no server is needed. It is on localhost (another port), so
// the browser's local-network protections do not block it and the backend must.
const ATTACKER = "http://localhost:3999";

async function openAttackerPage(page: Page, body = ""): Promise<void> {
  await page.route(`${ATTACKER}/**`, (route) =>
    route.fulfill({ contentType: "text/html", body: `<!doctype html><html><body>${body}</body></html>` }),
  );
  await page.goto(`${ATTACKER}/`);
}

test.beforeEach(() => resetData());

test("a foreign page cannot modify annotations", async ({ page }) => {
  await openAttackerPage(page);
  const before = readData();

  const results = await page.evaluate(async (backend) => {
    const payload = JSON.stringify({ name: "annotations", value: [{ aspect_category: "pwned" }] });
    const out: Record<string, string> = {};
    // 1. "Simple" request: sent without CORS preflight, response is opaque
    try {
      const r = await fetch(`${backend}/annotations/0`, {
        method: "POST",
        mode: "no-cors",
        headers: { "Content-Type": "text/plain" },
        body: payload,
      });
      out.noCors = r.type;
    } catch (e) {
      out.noCors = String(e);
    }
    // 2. Regular JSON request: needs a CORS preflight
    try {
      const r = await fetch(`${backend}/annotations/1`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      out.cors = String(r.status);
    } catch (e) {
      out.cors = "blocked";
    }
    // 3. Classic HTML form post
    await new Promise<void>((resolve) => {
      const frame = document.createElement("iframe");
      frame.name = "sink";
      frame.onload = () => resolve();
      document.body.appendChild(frame);
      const form = document.createElement("form");
      form.method = "POST";
      form.action = `${backend}/auto-add-positions`;
      form.target = "sink";
      document.body.appendChild(form);
      form.submit();
    });
    return out;
  }, backendUrl);

  expect(results.cors).toBe("blocked");
  expect(readData()).toEqual(before);
});

test("a foreign page cannot read annotations", async ({ page }) => {
  await openAttackerPage(page);
  const result = await page.evaluate(async (backend) => {
    try {
      const r = await fetch(`${backend}/data/0`);
      return `read ${r.status}`;
    } catch (e) {
      return "blocked";
    }
  }, backendUrl);
  expect(result).toBe("blocked");
});

test("the requests above are rejected by the backend itself, not only by the browser", async ({ request }) => {
  const r = await request.post(`${backendUrl}/annotations/0`, {
    headers: { Origin: ATTACKER, "Content-Type": "text/plain" },
    data: JSON.stringify({ name: "annotations", value: [] }),
  });
  expect(r.status()).toBe(403);
  expect(readData()[0].label).toBeUndefined();
});

test("the app cannot be embedded in a foreign page", async ({ page }) => {
  await openAttackerPage(
    page,
    `<iframe id="app" src="${frontendUrl}/" onload="window.appFrameLoaded = true"></iframe>`,
  );
  await page.waitForFunction(() => (window as any).appFrameLoaded === true);
  await expect(page.frameLocator("#app").getByTestId("app-title")).toHaveCount(0);
});

test("frontend and backend send anti-framing and nosniff headers", async ({ request }) => {
  for (const url of [`${frontendUrl}/`, `${backendUrl}/settings`]) {
    const r = await request.get(url);
    expect(r.ok()).toBeTruthy();
    const headers = r.headers();
    expect(headers["x-frame-options"]).toBe("DENY");
    expect(headers["x-content-type-options"]).toBe("nosniff");
    expect(headers["content-security-policy"]).toContain("frame-ancestors 'none'");
  }
});
