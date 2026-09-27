import fs from "node:fs";
import { translationSourceHash } from "./translations.mjs";
import { normalize, tasks } from "./search.mjs";
const read = (p) =>
  fs.readFileSync(new URL(p, `file://${process.cwd()}/`), "utf8");
const translations = JSON.parse(read("data/fa.json"));
const translationsByHash = new Map(
  Object.values(translations).map((t) => [t.sourceHash, t]),
);
const topicMap = new Map();
Object.entries(JSON.parse(read("skills-catalog/topics.json"))).forEach(
  ([topic, keys]) => keys.forEach((k) => topicMap.set(k, topic)),
);
const dates = new Map(
  read("skills-catalog/lastmod.tsv")
    .trim()
    .split("\n")
    .map((line) => {
      const [key, date] = line.split("\t");
      return [key.replace(/^agent-skills\//, ""), date?.slice(0, 10)];
    }),
);
const removed = new Set(
  read("skills-catalog/removed.jsonl")
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((l) => JSON.parse(l).key),
);
const known = new Set([
  "anthropic",
  "openai",
  "github",
  "microsoft",
  "nvidia",
  "vercel",
  "google",
  "cloudflare",
  "figma",
  "notion",
  "stripe",
  "sentry",
  "huggingface",
  "prisma",
  "firecrawl",
  "posthog",
]);
const seen = new Set();
/** @type {import('./types').Skill[]} */
export const skills = read("skills-catalog/skills-index-flat.jsonl")
  .trim()
  .split("\n")
  .map(JSON.parse)
  .filter((s) => {
    const key = `${s.author}/${s.name}`;
    if (seen.has(key) || removed.has(key)) return false;
    seen.add(key);
    return true;
  })
  .map((s) => {
    const key = `${s.author}/${s.name}`;
    const hash = translationSourceHash(s);
    const own = translations[key];
    // Exact source match only; hash lookup is O(1), even for a fully translated catalog.
    const fa = own?.sourceHash === hash ? own : translationsByHash.get(hash);
    const topic = topicMap.get(key) || "📦 سایر / عمومی";
    const haystack = normalize(`${s.name} ${s.what} ${s.use_when}`);
    const labels = tasks
      .filter((t) =>
        t.terms.some((term) =>
          new RegExp(`(^|[^a-z])${term}([^a-z]|$)`, "i").test(haystack),
        ),
      )
      .map((t) => t.id);
    return {
      ...s,
      key,
      topic,
      fa,
      known: known.has(s.author),
      tasks: labels,
      updated: s.updated || dates.get(key) || "",
      path: `skills/${encodeURIComponent(s.author)}/${encodeURIComponent(s.name)}/`,
    };
  });
const featured = [
  "anthropic/frontend-design",
  "vercel/react-best-practices",
  "anthropic/pdf",
  "openai/figma",
  "anthropic/mcp-builder",
  "anthropic/webapp-testing",
  "openai/imagegen",
  "openai/playwright",
  "anthropic/skill-creator",
  "openai/security-best-practices",
  "openai/transcribe",
  "deepgram/1password",
];
skills.sort((a, b) => {
  const ai = featured.indexOf(a.key),
    bi = featured.indexOf(b.key);
  return (
    (ai < 0 ? 999 : ai) - (bi < 0 ? 999 : bi) ||
    Number(!!b.fa) - Number(!!a.fa) ||
    a.name.localeCompare(b.name)
  );
});
export const topics = [...new Set(skills.map((s) => s.topic))].sort(
  (a, b) =>
    skills.filter((s) => s.topic === b).length -
    skills.filter((s) => s.topic === a).length,
);
export const authors = [...new Set(skills.map((s) => s.author))].sort();
export const number = (n) => Number(n).toLocaleString("fa-IR");
export const shortTopic = (t) => t.replace(/^\S+\s/, "");
export const searchIndex = skills.map((s) => ({
  key: s.key,
  name: s.name,
  author: s.author,
  path: s.path,
  topic: s.topic,
  tasks: s.tasks,
  updated: s.updated,
  known: s.known,
  fa: !!s.fa,
  title: s.fa?.title || "",
  summary: s.fa?.what || s.fa?.description || s.what || s.description || "",
  search: normalize(
    [
      s.name,
      s.author,
      s.what || s.description,
      s.use_when,
      s.topic,
      s.fa?.title || "",
      s.fa?.what || s.fa?.description || "",
      s.fa?.use_when || "",
    ].join(" "),
  ),
}));
/** @param {import('./types').Skill} skill @returns {import('./types').Skill[]} */
export function related(skill) {
  return skills
    .filter((s) => s.key !== skill.key && s.name !== skill.name)
    .map((s) => ({
      s,
      score:
        (s.topic === skill.topic ? 3 : 0) +
        s.tasks.filter((t) => skill.tasks.includes(t)).length * 2 +
        (s.author === skill.author ? 1 : 0),
    }))
    .filter((x) => x.score > 1)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map((x) => x.s);
}
