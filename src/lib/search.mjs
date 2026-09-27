export const tasks = [
  {
    id: "code",
    label: "توسعه و رفع باگ",
    terms: [
      "code",
      "coding",
      "debug",
      "refactor",
      "programming",
      "کدنویسی",
      "توسعه",
      "باگ",
    ],
  },
  {
    id: "design",
    label: "طراحی رابط کاربری",
    terms: ["design", "frontend", "ui", "ux", "figma", "طراحی", "رابط"],
  },
  {
    id: "content",
    label: "نوشتن و تولید محتوا",
    terms: [
      "writing",
      "copywriting",
      "content",
      "email",
      "seo",
      "نوشتن",
      "محتوا",
      "ایمیل",
      "سئو",
    ],
  },
  {
    id: "data",
    label: "تحلیل داده",
    terms: [
      "data",
      "database",
      "sql",
      "analytics",
      "spreadsheet",
      "داده",
      "تحلیل",
    ],
  },
  {
    id: "test",
    label: "تست و امنیت",
    terms: [
      "test",
      "testing",
      "security",
      "audit",
      "vulnerability",
      "تست",
      "امنیت",
    ],
  },
  {
    id: "automate",
    label: "اتوماسیون کارها",
    terms: [
      "automation",
      "automate",
      "workflow",
      "browser",
      "اتوماسیون",
      "مرورگر",
    ],
  },
  {
    id: "document",
    label: "کار با اسناد",
    terms: [
      "pdf",
      "docx",
      "document",
      "presentation",
      "pptx",
      "اسناد",
      "سند",
      "ارائه",
    ],
  },
];
const synonyms = [
  ["ایمیل سرد", "cold email"],
  ["هوش مصنوعی", "artificial intelligence", "ai", "llm"],
  ["پی دی اف", "pdf"],
  ["ری اکت", "react"],
  ["ری‌اکت", "react"],
  ["نکست", "next.js", "nextjs"],
  ["گیت هاب", "github"],
  ["گیتهاب", "github"],
  ["ورد", "docx", "word"],
  ["اکسل", "xlsx", "spreadsheet"],
  ["تصویر", "image"],
  ["ویدیو", "video"],
  ["صوت", "audio"],
  ["گفتار", "speech"],
  ["ترجمه", "translate", "translation"],
  ["قیمت گذاری", "pricing"],
  ["بازاریابی", "marketing"],
  ["فروش", "sales"],
  ["استقرار", "deploy", "deployment"],
  ["پایتون", "python"],
  ["مرورگر", "browser"],
  ["تست", "test", "testing"],
  ["امنیت", "security"],
  ["سئو", "seo"],
  ["ایمیل", "email"],
  ["دیتابیس", "database"],
  ["رفع باگ", "debug", "debugging"],
  ...tasks.map((t) => t.terms),
];
export function normalize(s = "") {
  return s
    .toLowerCase()
    .replace(/[يى]/g, "ی")
    .replace(/ك/g, "ک")
    .replace(/[\u064B-\u065F\u0670]/g, "")
    .replace(/\u200c/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
export function groups(query) {
  let q = normalize(query);
  const result = [];
  for (const group of [...synonyms].sort(
    (a, b) =>
      Math.max(...b.map((x) => x.length)) - Math.max(...a.map((x) => x.length)),
  )) {
    const match = group
      .map(normalize)
      .find((x) => x.includes(" ") && q.includes(x));
    if (match) {
      result.push(group.map(normalize));
      q = q.replace(match, " ");
    }
  }
  for (const word of q.split(/\s+/).filter(Boolean)) {
    const group = synonyms.find((g) => g.some((x) => normalize(x) === word));
    result.push(group ? group.map(normalize) : [word]);
  }
  return result;
}
export function searchRows(
  rows,
  {
    q = "",
    topic = "",
    author = "",
    task = "",
    translated = false,
    sort = "relevant",
  } = {},
) {
  const terms = groups(q);
  const filtered = rows.filter(
    (r) =>
      (!topic || r.topic === topic) &&
      (!author || r.author === author) &&
      (!task || r.tasks.includes(task)) &&
      (!translated || r.fa) &&
      terms.every((g) => g.some((t) => r.search.includes(t))),
  );
  if (sort === "name") filtered.sort((a, b) => a.name.localeCompare(b.name));
  else if (sort === "updated")
    filtered.sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));
  else if (q)
    filtered.sort(
      (a, b) =>
        Number(normalize(b.name).includes(normalize(q))) -
          Number(normalize(a.name).includes(normalize(q))) ||
        Number(b.fa) - Number(a.fa),
    );
  return filtered;
}
