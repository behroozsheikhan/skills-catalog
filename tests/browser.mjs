import fs from "node:fs";
import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
const artifacts = process.env.ARTIFACT_DIR || "test-results";
fs.mkdirSync(artifacts, { recursive: true });
const base = process.env.TEST_URL || "http://localhost:4321/";
const browser = await chromium.launch({
  headless: true,
  ...(process.env.CHROMIUM_PATH
    ? {
        executablePath: process.env.CHROMIUM_PATH,
        args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
      }
    : {}),
});
try {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(base);
  await page.waitForFunction(() =>
    document.querySelector("#page-info")?.textContent.includes("از"),
  );
  assert.equal(await page.locator("#results .skill-card").count(), 12);
  assert.ok((await page.title()).includes("اسکیل کاتالوگ"));
  assert.equal(await page.locator(".site-header a[href*=github]").count(), 0);
  for (const size of [24, 48, 96]) {
    await page.locator("#page-size").selectOption(String(size));
    assert.equal(await page.locator("#results .skill-card").count(), size);
    assert.equal(new URL(page.url()).searchParams.get("size"), String(size));
  }
  await page.locator("#next-page").click();
  await page.locator("#page-size").selectOption("24");
  assert.equal(new URL(page.url()).searchParams.get("page"), null);
  await page.reload();
  await page.waitForFunction(
    () => document.querySelectorAll("#results .skill-card").length === 24,
  );
  assert.equal(await page.locator("#page-size").inputValue(), "24");
  await page.goto(base + "?size=999");
  await page.waitForFunction(() =>
    document.querySelector("#page-info")?.textContent.includes("از"),
  );
  assert.equal(await page.locator("#page-size").inputValue(), "12");
  assert.equal(await page.locator("#results .skill-card").count(), 12);
  const firstFavorite = page.locator("#results [data-favorite-key]").first();
  const favoriteKey = await firstFavorite.getAttribute("data-favorite-key");
  await firstFavorite.click();
  assert.equal(await firstFavorite.getAttribute("aria-pressed"), "true");
  assert.equal(new URL(page.url()).pathname, new URL(base).pathname);
  await page.reload();
  await page.waitForFunction(() =>
    document.querySelector("#page-info")?.textContent.includes("از"),
  );
  await page.locator("#favorites-filter").check();
  assert.equal(await page.locator("#results .skill-card").count(), 1);
  await page.locator("#results .skill-card").first().click();
  await page.locator(".favorite-detail").waitFor({ state: "visible" });
  assert.equal(
    await page.locator(".favorite-detail").getAttribute("aria-pressed"),
    "true",
  );
  await page.locator(".favorite-detail").click();
  await page.locator("#back-to-results").click();
  await page.waitForSelector("#empty-state:not([hidden])");
  assert.equal(await page.locator("#favorites-filter").isChecked(), true);
  await page.locator("#reset-all").click();
  assert.equal(await page.locator("#results .skill-card").count(), 12);
  // Changes made in another tab refresh existing buttons.
  const secondTab = await page.context().newPage();
  await secondTab.goto(base + "skills/" + favoriteKey + "/");
  await secondTab.locator(".favorite-detail").click();
  await page.waitForFunction(
    () =>
      document
        .querySelector("#results [data-favorite-key]")
        ?.getAttribute("aria-pressed") === "true",
  );
  await secondTab.locator(".favorite-detail").click();
  await page.waitForFunction(
    () =>
      document
        .querySelector("#results [data-favorite-key]")
        ?.getAttribute("aria-pressed") === "false",
  );
  await secondTab.close();
  await page.locator("#search").fill("ایمیل سرد");
  await page.waitForTimeout(350);
  await page.waitForFunction(() => location.search.includes("q="));
  assert.ok((await page.locator("#results .skill-card").count()) > 0);
  await page.locator("#search").fill("react");
  await page.locator("#author-filter").selectOption("vercel");
  await page.waitForTimeout(350);
  assert.ok((await page.locator("#results .skill-card").count()) > 0);
  assert.ok(
    (await page.locator("#results .author").allTextContents()).every((t) =>
      t.includes("vercel"),
    ),
  );
  await page.reload();
  await page.waitForFunction(() =>
    document.querySelector("#page-info")?.textContent.includes("از"),
  );
  assert.equal(await page.locator("#search").inputValue(), "react");
  assert.equal(await page.locator("#author-filter").inputValue(), "vercel");
  await page.locator("#search").fill("therearenosuchskills99999");
  await page.waitForTimeout(400);
  assert.ok(await page.locator("#empty-state").isVisible());
  await page.locator("#reset-all").click();
  assert.equal(await page.locator("#results .skill-card").count(), 12);
  await page.locator("#next-page").click();
  assert.ok((await page.locator("#page-info").textContent()).includes("۲"));
  await page.locator("#prev-page").click();
  await page.locator("#theme-toggle").click();
  const theme = await page.locator("html").getAttribute("data-theme");
  await page.reload();
  assert.equal(await page.locator("html").getAttribute("data-theme"), theme);
  await page.goto(base + "skills/deepgram/1password/");
  assert.ok(
    (await page.locator(".persian-copy").allTextContents()).some((t) =>
      t.endsWith("…"),
    ),
  );
  assert.equal(await page.locator(".original-copy [lang=en]").count(), 2);
  assert.equal(await page.locator("link[rel=canonical]").count(), 1);
  assert.ok(
    !(await page.locator(".metadata-panel").textContent()).includes(
      "وضعیت ترجمه",
    ),
  );
  assert.ok(
    (
      await page.locator(".metadata-panel a.secondary-button").textContent()
    ).includes("صفحه در mcpservers"),
  );

  await page.screenshot({
    path: artifacts + "/detail-dark.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(base);
  await page.waitForSelector("#results .skill-card");
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
    false,
  );
  await page.locator("#theme-toggle").click();
  await page.screenshot({ path: artifacts + "/mobile.png", fullPage: true });
  await page.locator("#open-filters").click();
  assert.equal(
    await page.locator("#filters-panel").getAttribute("aria-modal"),
    "true",
  );
  await page.locator("#author-filter").selectOption("anthropic");
  await page.locator("#close-filters").click();
  await page.waitForTimeout(300);
  assert.ok(
    (await page.locator("#results .author").allTextContents()).every((t) =>
      t.includes("anthropic"),
    ),
  );
  assert.equal(
    await page.locator("#open-filters").getAttribute("aria-expanded"),
    "false",
  );
  await page.locator("#open-filters").click();
  await page.keyboard.press("Escape");
  assert.ok(!(await page.locator("#filters-panel").isVisible()));
  await page.goto(base + "skills/deepgram/1password/");
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
    false,
  );
  await page.setViewportSize({ width: 320, height: 720 });
  await page.goto(base);
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
    false,
  );
  assert.deepEqual(errors, []);
  console.log(
    "PASS: search, combined filters, URL persistence, empty state, pagination, theme persistence, bilingual detail, mobile filters, Escape, 320/390px overflow, no JS errors",
  );
  const nojs = await browser.newContext({ javaScriptEnabled: false });
  const doc = await nojs.newPage();
  await doc.goto(base + "skills/anthropic/frontend-design/");
  assert.ok(
    (await doc.locator("h1").textContent()).includes("frontend-design"),
  );
  await doc.goto(base + "directory/1/");
  assert.equal(await doc.locator(".directory-page li").count(), 100);
  await nojs.close();
  console.log("PASS: no-JavaScript detail and directory");
  const offline = await browser.newPage();
  await offline.route("**/data/search.json", (route) => route.abort());
  await offline.goto(base);
  await offline.waitForSelector("#load-error:not([hidden])");
  await offline.unroute("**/data/search.json");
  await offline.locator("#retry-load").click();
  await offline.waitForFunction(() =>
    document.querySelector("#page-info")?.textContent.includes("از"),
  );
  assert.ok(await offline.locator("#load-error").isHidden());
  console.log("PASS: search index failure and retry");
} finally {
  await browser.close();
}
