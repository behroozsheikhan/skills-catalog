/** Export only source fields, with hashes, for a reviewed translation workflow. */
import fs from "node:fs";
import { translationSourceHash } from "../src/lib/translations.mjs";
import { skills } from "../src/lib/catalog.mjs";
const editorial = skills.filter((s) => s.fa?.method === "editorial");
const missing = skills.filter((s) =>
  process.argv.includes("--editorial-pending")
    ? s.fa?.method !== "editorial"
    : !s.fa,
);
if (process.argv.includes("--export")) {
  const unique = new Map();
  for (const s of missing) {
    const sourceHash = translationSourceHash(s);
    if (!unique.has(sourceHash))
      unique.set(sourceHash, {
        key: s.key,
        sourceHash,
        what: s.what,
        use_when: s.use_when,
        ...(!s.what ? { description: s.description } : {}),
      });
  }
  const path = process.argv[process.argv.indexOf("--export") + 1];
  if (!path || path.startsWith("--"))
    throw Error(
      "Usage: npm run translations -- --export /path/to/missing.jsonl",
    );
  fs.writeFileSync(
    path,
    [...unique.values()].map((x) => JSON.stringify(x)).join("\n") + "\n",
  );
  console.log(`${unique.size} distinct source pairs exported to ${path}`);
} else
  console.log(
    JSON.stringify(
      {
        total: skills.length,
        translated: skills.filter((s) => s.fa).length,
        pending: skills.filter((s) => !s.fa).length,
        editorialSkills: editorial.length,
        editorialSourcePairs: new Set(editorial.map((s) => s.fa.sourceHash))
          .size,
        editorialPending: skills.length - editorial.length,
      },
      null,
      2,
    ),
  );
