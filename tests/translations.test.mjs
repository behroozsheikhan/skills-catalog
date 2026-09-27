import test from "node:test";
import assert from "node:assert/strict";
import { translationSourceHash } from "../src/lib/translations.mjs";
import { skills, searchIndex } from "../src/lib/catalog.mjs";

test("description fallback participates in translation invalidation", () => {
  const row = {
    what: "",
    use_when: "For testing",
    description: "First description",
  };
  assert.notEqual(
    translationSourceHash(row),
    translationSourceHash({ ...row, description: "Changed" }),
  );
  assert.equal(
    translationSourceHash({ ...row, what: "Short text" }),
    translationSourceHash({
      ...row,
      what: "Short text",
      description: "Changed",
    }),
  );
});
test("translations preserve empty fields and do not leak placeholders", () => {
  for (const s of skills.filter((s) => s.fa)) {
    for (const field of ["what", "use_when"]) {
      assert.equal(
        !s.fa[field],
        !s[field],
        `${s.key}: ${field} empty field mismatch`,
      );
      assert.ok(
        !/\[\[(?:T\d+|\d{5})\]\]/.test(s.fa[field]),
        `${s.key}: unresolved token`,
      );
      for (const marker of ['…','...']) {
        assert.equal(s.fa[field].split(marker).length, (s[field]||'').split(marker).length, `${s.key}: truncation marker mismatch`);
      }
    }
    if (!s.what && s.description)
      assert.ok(s.fa.description, `${s.key}: fallback not translated`);
  }
});
test("Persian descriptions are used in search summaries", () => {
  for (const s of skills.filter((s) => s.fa)) {
    const item = searchIndex.find((x) => x.key === s.key);
    assert.equal(
      item.summary,
      s.fa.what || s.fa.description || s.what || s.description || "",
    );
  }
});
