import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import crypto from "node:crypto";
import { skills, searchIndex, related } from "../src/lib/catalog.mjs";
import { normalize, searchRows } from "../src/lib/search.mjs";
test("all source skills have unique routes and valid links", () => {
  assert.equal(skills.length, 7764);
  assert.equal(new Set(skills.map((s) => s.path)).size, skills.length);
  for (const s of skills) {
    assert.ok(s.path.startsWith("skills/"));
    assert.ok(new URL(s.url).protocol === "https:");
    if (s.github) assert.equal(new URL(s.github).hostname, "github.com");
  }
});
test("Persian variants and half spaces normalize", () => {
  assert.equal(normalize("كاربرد يک اسكيل"), "کاربرد یک اسکیل");
  assert.equal(normalize("قیمت‌گذاری"), "قیمت گذاری");
});
test("English and Persian synonym searches", () => {
  for (const q of ["react", "ری‌اکت", "پی دی اف", "ایمیل سرد"])
    assert.ok(searchRows(searchIndex, { q }).length > 0, q);
  assert.ok(
    searchRows(searchIndex, { q: "پی دی اف" }).some((s) => s.name === "pdf"),
  );
  assert.ok(
    searchRows(searchIndex, { q: "ایمیل سرد" }).every(
      (s) => s.search.includes("cold email") || s.search.includes("ایمیل سرد"),
    ),
  );
});
test("query tokens are ANDed; punctuation cannot crash search", () => {
  assert.ok(
    searchRows(searchIndex, { q: "react performance" }).some(
      (s) => s.name === "react-best-practices",
    ),
  );
  assert.equal(searchRows(searchIndex, { q: "zzzznotexisting" }).length, 0);
  assert.doesNotThrow(() => searchRows(searchIndex, { q: '" <script> [+++]' }));
});
test("filters compose and translated-only has no untranslated rows", () => {
  const r = searchRows(searchIndex, {
    q: "react",
    author: "vercel",
    task: "code",
    translated: true,
  });
  assert.ok(r.length > 0);
  assert.ok(
    r.every((s) => s.author === "vercel" && s.tasks.includes("code") && s.fa),
  );
  const topic = skills[0].topic;
  assert.ok(searchRows(searchIndex, { topic }).every((s) => s.topic === topic));
});
test("source text and incompleteness are preserved", () => {
  const s = skills.find((s) => s.key === "deepgram/1password");
  assert.ok(s.use_when.endsWith("…"));
  assert.ok(s.fa.use_when.endsWith("…"));
  assert.ok(s.fa.what.includes("CLI"));
  assert.equal(
    skills.find((s) => s.key === "anthropic/frontend-design").use_when,
    "",
  );
});
test("translation hashes match original fields", () => {
  const entries = JSON.parse(fs.readFileSync("data/fa.json", "utf8"));
  for (const [key, t] of Object.entries(entries)) {
    const s = skills.find((s) => s.key === key);
    assert.ok(s, key);
    assert.equal(
      t.sourceHash,
      crypto
        .createHash("sha256")
        .update(s.what + "\n" + s.use_when)
        .digest("hex"),
    );
    assert.equal(t.status, "draft");
  }
});
test("related skills exclude current item and same-name mirrors", () => {
  const s = skills[0],
    r = related(s);
  assert.equal(r.length, 3);
  assert.ok(r.every((x) => x.key !== s.key && x.name !== s.name));
});
test("name and date sorting are deterministic", () => {
  const r = searchRows(searchIndex, { sort: "updated" });
  assert.ok(r[0].updated >= r.at(-1).updated);
  const a = searchRows(searchIndex, { sort: "name" });
  assert.ok(a[0].name.localeCompare(a.at(-1).name) <= 0);
});
