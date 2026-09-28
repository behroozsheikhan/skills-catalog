import crypto from "node:crypto";
/** Hash exactly the displayed source fields, including the description fallback. */
export function translationSourceHash(row) {
  const what = row.what || "";
  let payload = what + "\n" + (row.use_when || "");
  if (!what) payload += "\n" + (row.description || "");
  return crypto.createHash("sha256").update(payload).digest("hex");
}
