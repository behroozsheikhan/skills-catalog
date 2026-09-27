/** Export only source fields, with hashes, for a reviewed translation workflow. */
import fs from "node:fs";
import crypto from "node:crypto";
import { skills } from "../src/lib/catalog.mjs";
const missing = skills.filter((s) => !s.fa);
if (process.argv.includes("--export")) {
  const unique = new Map();
  for (const s of missing) {
    const sourceHash = crypto
      .createHash("sha256")
      .update(s.what + "\n" + s.use_when)
      .digest("hex");
    if (!unique.has(sourceHash))
      unique.set(sourceHash, {
        key: s.key,
        sourceHash,
        what: s.what,
        use_when: s.use_when,
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
        translated: skills.length - missing.length,
        pending: missing.length,
      },
      null,
      2,
    ),
  );
