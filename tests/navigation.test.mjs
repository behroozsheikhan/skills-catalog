import test from "node:test";
import assert from "node:assert/strict";
import { catalogReturnURL } from "../src/lib/navigation.mjs";
const origin = "https://example.com";
function detail(value) {
  return (
    origin +
    "/skills-catalog/skills/author/name/?returnTo=" +
    encodeURIComponent(value)
  );
}
test("return preserves the complete search state", () => {
  const state =
    "/skills-catalog/?q=react&topic=code&author=vercel&task=code&fa=1&sort=name&size=48&page=2";
  assert.equal(
    catalogReturnURL(detail(state), "/skills-catalog/"),
    state + "#catalog",
  );
});
test("direct visits return to catalog and support root hosting", () => {
  assert.equal(catalogReturnURL(origin + "/skills/test/", "/"), "/#catalog");
  assert.equal(
    catalogReturnURL(detail("/?q=pdf&size=24"), "/"),
    "/?q=pdf&size=24#catalog",
  );
});
test("external, script, unrelated and malformed return URLs are rejected", () => {
  for (const value of [
    "https://evil.example/skills-catalog/",
    "//evil.example/skills-catalog/",
    "javascript:alert(1)",
    "/other/",
    "http://[invalid",
  ])
    assert.equal(
      catalogReturnURL(detail(value), "/skills-catalog/"),
      "/skills-catalog/#catalog",
    );
});
