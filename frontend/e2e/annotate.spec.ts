import { expect, test } from "@playwright/test";
import {
  addButton,
  addTuple,
  annotationItems,
  annotationText,
  backendError,
  categorySelect,
  completedCount,
  fixtureTexts,
  goToItem,
  openApp,
  polaritySelect,
  readData,
  recordDialogs,
  resetData,
  saveButton,
  saveEmptyButton,
  writeData,
} from "./helpers";

const texts = fixtureTexts();

test.beforeEach(() => resetData());

test("shows the first item, session and version", async ({ page }) => {
  await openApp(page, texts[0]);
  await expect(page.getByTestId("session-id")).toHaveText("Session: e2e");
  await expect(page.getByTestId("app-version")).toHaveText(/^v\d+\.\d+\.\d+$/);
  await expect(backendError(page)).toHaveCount(0);
});

test("saves complete tuples and moves to the next item", async ({ page }) => {
  const dialogs = recordDialogs(page);
  await openApp(page, texts[0]);
  await addTuple(page, "food quality", "positive");
  await addTuple(page, "service general", "negative");
  await expect(annotationItems(page)).toHaveCount(2);
  await saveButton(page).click();

  await expect(annotationText(page)).toHaveText(texts[1]);
  expect(readData()[0].label).toEqual([
    { aspect_category: "food quality", sentiment_polarity: "positive" },
    { aspect_category: "service general", sentiment_polarity: "negative" },
  ]);
  expect(readData()[1].label).toBeUndefined();
  await expect(completedCount(page)).toHaveText("1 annotations completed");
  expect(dialogs).toEqual([]);
});

test("Add aspect stays disabled until the tuple is complete", async ({ page }) => {
  await openApp(page, texts[0]);
  await expect(addButton(page)).toBeDisabled();
  await categorySelect(page).selectOption("food quality");
  await expect(addButton(page)).toBeDisabled();
  await polaritySelect(page).selectOption("positive");
  await expect(addButton(page)).toBeEnabled();
});

test.describe("half-filled tuple", () => {
  test("cancelling the warning keeps the item and the partial tuple", async ({ page }) => {
    await openApp(page, texts[0]);
    await addTuple(page, "food quality", "positive");
    await categorySelect(page).selectOption("service general"); // polarity left empty

    const dialog = page.waitForEvent("dialog");
    const click = saveButton(page).click();
    const d = await dialog;
    expect(d.type()).toBe("confirm");
    expect(d.message()).toContain("has not been added");
    await d.dismiss();
    await click;

    await expect(annotationText(page)).toHaveText(texts[0]);
    await expect(categorySelect(page)).toHaveValue("service general");
    expect(readData()[0].label).toBeUndefined();
  });

  test("confirming the warning saves only the complete tuples", async ({ page }) => {
    await openApp(page, texts[0]);
    await addTuple(page, "food quality", "positive");
    await polaritySelect(page).selectOption("negative"); // category left empty

    page.once("dialog", (d) => d.accept());
    await saveButton(page).click();

    await expect(annotationText(page)).toHaveText(texts[1]);
    expect(readData()[0].label).toEqual([{ aspect_category: "food quality", sentiment_polarity: "positive" }]);
  });

  test("a fully filled but not added tuple also triggers the warning", async ({ page }) => {
    await openApp(page, texts[0]);
    await addTuple(page, "food quality", "positive");
    await categorySelect(page).selectOption("ambience general");
    await polaritySelect(page).selectOption("neutral");

    const dialogs = recordDialogs(page);
    await saveButton(page).click();
    await expect.poll(() => dialogs.length).toBe(1);
    await expect(annotationText(page)).toHaveText(texts[0]);
  });

  test("the warning also guards 'Save empty list'", async ({ page }) => {
    await openApp(page, texts[0]);
    await polaritySelect(page).selectOption("positive");

    const dialogs = recordDialogs(page); // dismisses
    await saveEmptyButton(page).click();
    await expect.poll(() => dialogs.length).toBe(1);
    expect(readData()[0].label).toBeUndefined();
  });
});

test("saving an empty list without started tuple needs no confirmation", async ({ page }) => {
  const dialogs = recordDialogs(page);
  await openApp(page, texts[0]);
  await saveEmptyButton(page).click();
  await expect(annotationText(page)).toHaveText(texts[1]);
  expect(readData()[0].label).toEqual([]);
  expect(dialogs).toEqual([]);
});

test("annotations are shown again when navigating back", async ({ page }) => {
  await openApp(page, texts[0]);
  await addTuple(page, "drinks style_options", "positive");
  await saveButton(page).click();
  await expect(annotationText(page)).toHaveText(texts[1]);
  await expect(annotationItems(page)).toHaveCount(0);

  await page.getByTestId("previous-button").click();
  await expect(annotationText(page)).toHaveText(texts[0]);
  await expect(annotationItems(page)).toHaveCount(1);
  await expect(page.getByTestId("annotation-item-category")).toHaveValue("drinks style_options");
});

test("resumes at the first unannotated item", async ({ page }) => {
  const data = readData();
  data[0].label = [];
  data[1].label = [{ aspect_category: "drinks style_options", sentiment_polarity: "positive" }];
  writeData(data);
  await openApp(page, texts[2]);
  await expect(completedCount(page)).toHaveText("2 annotations completed");
});

test("the last item shows 'Save & finish'", async ({ page }) => {
  await openApp(page, texts[0]);
  await goToItem(page, texts.length, texts[texts.length - 1]);
  await expect(saveEmptyButton(page)).toHaveText("Save empty list & finish");
  await addTuple(page, "service general", "positive");
  await expect(saveButton(page)).toHaveText("Save & finish");
  await saveButton(page).click();
  await expect
    .poll(() => readData()[texts.length - 1].label)
    .toEqual([{ aspect_category: "service general", sentiment_polarity: "positive" }]);
});

test("two annotators can save at the same time", async ({ browser }) => {
  const [a, b] = await Promise.all([browser.newPage(), browser.newPage()]);
  await Promise.all([openApp(a, texts[0]), openApp(b, texts[0])]);
  await goToItem(b, 3, texts[2]);
  await addTuple(a, "food quality", "positive");
  await addTuple(b, "ambience general", "negative");

  await Promise.all([saveButton(a).click(), saveButton(b).click()]);
  await expect(annotationText(a)).toHaveText(texts[1]);
  await expect(annotationText(b)).toHaveText(texts[3]);

  const data = readData();
  expect(data[0].label).toEqual([{ aspect_category: "food quality", sentiment_polarity: "positive" }]);
  expect(data[2].label).toEqual([{ aspect_category: "ambience general", sentiment_polarity: "negative" }]);
  await Promise.all([a.close(), b.close()]);
});

test.describe("malformed data file", () => {
  test("invalid JSON is reported in the UI", async ({ page }) => {
    writeData('[{"text": "a"},\n {"text": "b",}]');
    await page.goto("/");
    await expect(backendError(page)).toContainText("not valid JSON (line 2");
  });

  test("wrong structure is reported in the UI", async ({ page }) => {
    writeData('{"text": "not a list"}');
    await page.goto("/");
    await expect(backendError(page)).toContainText("must contain a JSON list");
  });

  test("a save failing because the file broke is reported", async ({ page }) => {
    await openApp(page, texts[0]);
    await addTuple(page, "food quality", "positive");
    writeData("[");
    await saveButton(page).click();
    await expect(backendError(page)).toContainText("Saving failed: Invalid data file");
    await expect(annotationText(page)).toHaveText(texts[0]);
  });
});
