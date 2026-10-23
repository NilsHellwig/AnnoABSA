import fs from "node:fs";
import path from "node:path";
import { expect, type Page } from "@playwright/test";
import { dataFile, fixturesDir } from "./env";

export type Item = { text: string; label?: Record<string, unknown>[]; [key: string]: unknown };

export const readData = (): Item[] => JSON.parse(fs.readFileSync(dataFile, "utf-8"));

export const writeData = (content: string | Item[]): void =>
  fs.writeFileSync(dataFile, typeof content === "string" ? content : JSON.stringify(content, null, 2));

export const resetData = (): void => fs.copyFileSync(path.join(fixturesDir, "data.json"), dataFile);

export const fixtureTexts = (): string[] =>
  JSON.parse(fs.readFileSync(path.join(fixturesDir, "data.json"), "utf-8")).map((i: Item) => i.text);

// Elements are addressed via data-testid attributes in App.tsx, not via their texts
export const annotationText = (page: Page) => page.getByTestId("annotation-text");
export const categorySelect = (page: Page) => page.getByTestId("new-aspect-category");
export const polaritySelect = (page: Page) => page.getByTestId("new-sentiment-polarity");
export const addButton = (page: Page) => page.getByTestId("add-aspect-button");
export const saveButton = (page: Page) => page.getByTestId("save-button");
export const saveEmptyButton = (page: Page) => page.getByTestId("save-empty-button");
export const backendError = (page: Page) => page.getByTestId("backend-error");
export const completedCount = (page: Page) => page.getByTestId("completed-count");
export const annotationItems = (page: Page) => page.getByTestId("annotation-item");

export async function openApp(page: Page, expectedText: string): Promise<void> {
  await page.goto("/");
  await expect(annotationText(page)).toHaveText(expectedText);
}

export async function addTuple(page: Page, category: string, polarity: string): Promise<void> {
  await categorySelect(page).selectOption(category);
  await polaritySelect(page).selectOption(polarity);
  await addButton(page).click();
}

export async function goToItem(page: Page, oneBasedIndex: number, expectedText: string): Promise<void> {
  await page.getByTestId("goto-index-input").fill(String(oneBasedIndex));
  await page.getByTestId("goto-index-button").click();
  await expect(annotationText(page)).toHaveText(expectedText);
}

/** Record (and dismiss) every dialog, so a test can assert that none appeared. */
export function recordDialogs(page: Page): string[] {
  const messages: string[] = [];
  page.on("dialog", async (dialog) => {
    messages.push(dialog.message());
    await dialog.dismiss();
  });
  return messages;
}
