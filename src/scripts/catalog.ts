import { browserFavorites } from "../lib/favorites.mjs";
import { syncFavoriteButtons } from "./favorites";
import { searchRows } from "../lib/search.mjs";
type Row = {
  key: string;
  sourceLanguage: "en" | "zh";
  path: string;
  name: string;
  author: string;
  topic: string;
  summary: string;
  title: string;
  fa: boolean;
  known: boolean;
  updated: string;
  tasks: string[];
  search: string;
};
const $ = <T extends HTMLElement>(s: string) => document.querySelector<T>(s)!;
const base = $("#catalog").dataset.base!;
const input = $<HTMLInputElement>("#search"),
  author = $<HTMLSelectElement>("#author-filter"),
  task = $<HTMLSelectElement>("#task-filter"),
  translated = $<HTMLInputElement>("#translated-filter"),
  favoritesOnly = $<HTMLInputElement>("#favorites-filter"),
  sort = $<HTMLSelectElement>("#sort"),
  pageSizeSelect = $<HTMLSelectElement>("#page-size");
let topic = "",
  page = 1,
  pageSize = 12,
  rows: Row[] | null = null,
  loading: Promise<void> | null = null;
const fmt = (n: number) => n.toLocaleString("fa-IR");
const el = (tag: string, cls: string, text = "") => {
  const e = document.createElement(tag);
  e.className = cls;
  e.textContent = text;
  return e;
};
function stateFromURL() {
  const p = new URLSearchParams(location.search);
  input.value = (p.get("q") || "").slice(0, 160);
  author.value = p.get("author") || "";
  task.value = p.get("task") || "";
  topic = p.get("topic") || "";
  if (
    ![...document.querySelectorAll<HTMLElement>("[data-topic]")].some(
      (e) => e.dataset.topic === topic,
    )
  )
    topic = "";
  translated.checked = p.get("fa") === "1";
  favoritesOnly.checked = p.get("favorites") === "1";
  sort.value = p.get("sort") || "relevant";
  if (!sort.value) sort.value = "relevant";
  const requestedSize = Number(p.get("size"));
  pageSize = [12, 24, 48, 96].includes(requestedSize) ? requestedSize : 12;
  pageSizeSelect.value = String(pageSize);
  page = Math.max(1, parseInt(p.get("page") || "1", 10) || 1);
}
function updateURL() {
  const p = new URLSearchParams();
  if (input.value.trim()) p.set("q", input.value.trim());
  if (topic) p.set("topic", topic);
  if (author.value) p.set("author", author.value);
  if (task.value) p.set("task", task.value);
  if (translated.checked) p.set("fa", "1");
  if (favoritesOnly.checked) p.set("favorites", "1");
  if (sort.value !== "relevant") p.set("sort", sort.value);
  if (pageSize !== 12) p.set("size", String(pageSize));
  if (page > 1) p.set("page", String(page));
  history.replaceState(
    null,
    "",
    location.pathname + (p.size ? "?" + p.toString() : ""),
  );
}
function createCard(r: Row) {
  const a = el("a", "skill-card") as HTMLAnchorElement;
  const destination = new URL(base + r.path, location.origin);
  destination.searchParams.set(
    "returnTo",
    location.pathname + location.search + "#catalog",
  );
  a.href = destination.href;
  const top = el("div", "card-top"),
    icon = el(
      "span",
      "skill-icon " + ["mint", "blue", "violet", "amber"][r.author.length % 4],
      r.tasks.includes("design")
        ? "✧"
        : r.tasks.includes("document")
          ? "▤"
          : "‹/›",
    );
  const source = el("span", "author", r.author);
  source.dir = "ltr";
  if (r.known) {
    const check = el("span", "", "✓");
    check.title = "منبع شناخته‌شده؛ تضمین امنیت نیست";
    source.append(check);
  }
  top.append(icon, source, el("span", "card-arrow", "←"));
  const name = el("h3", "", r.name);
  name.dir = "ltr";
  name.lang = "en";
  a.append(top, name);
  if (r.title) a.append(el("p", "card-title", r.title));
  const description = el(
    "p",
    "card-description" + (!r.fa ? " english" : ""),
    r.summary,
  );
  description.dir = r.fa ? "rtl" : "ltr";
  description.lang = r.fa ? "fa" : r.sourceLanguage;
  const bottom = el("div", "card-bottom");
  bottom.append(
    el("span", "topic-tag", r.topic.replace(/^\S+\s/, "")),
    el(
      "span",
      "language-tag",
      r.fa
        ? "FA / " + r.sourceLanguage.toUpperCase()
        : r.sourceLanguage.toUpperCase(),
    ),
  );
  a.append(description, bottom);
  const shell = el("div", "skill-card-shell");
  const favorite = el("button", "favorite-button", "♡") as HTMLButtonElement;
  favorite.type = "button";
  favorite.dataset.favoriteKey = r.key;
  shell.append(favorite, a);
  return shell;
}
function render(writeURL = true) {
  if (!rows) return;
  const saved = browserFavorites();
  const result = searchRows(
    favoritesOnly.checked ? rows.filter((r) => saved.has(r.key)) : rows,
    {
      q: input.value,
      topic,
      author: author.value,
      task: task.value,
      translated: translated.checked,
      sort: sort.value,
    },
  ) as Row[];
  const pages = Math.max(1, Math.ceil(result.length / pageSize));
  page = Math.min(page, pages);
  if (writeURL) updateURL();
  $("#results").replaceChildren(
    ...result.slice((page - 1) * pageSize, page * pageSize).map(createCard),
  );
  syncFavoriteButtons();
  $("#empty-state h3").textContent = favoritesOnly.checked
    ? "علاقه‌مندی‌ای با این شرایط پیدا نشد"
    : "هنوز اسکیل مناسب پیدا نشد";
  $("#empty-state p").textContent = favoritesOnly.checked
    ? "با دکمهٔ قلب، اسکیل‌ها را ذخیره کن؛ یا فیلترهای دیگر را بردار."
    : "عبارت کوتاه‌تری بنویس یا بعضی فیلترها را بردار.";
  $("#result-count").textContent = `${fmt(result.length)} اسکیل برای کشف کردن`;
  $("#empty-state").hidden = result.length > 0;
  $(".pagination").hidden = result.length === 0;
  $("#page-info").textContent = `صفحهٔ ${fmt(page)} از ${fmt(pages)}`;
  $<HTMLButtonElement>("#prev-page").disabled = page <= 1;
  $<HTMLButtonElement>("#next-page").disabled = page >= pages;
  document.querySelectorAll<HTMLElement>("[data-topic]").forEach((b) => {
    const active = b.dataset.topic === topic;
    b.classList.toggle("selected", active);
    b.setAttribute("aria-pressed", String(active));
  });
  const active = $("#active-filters");
  active.replaceChildren();
  const chip = (label: string, clear: () => void) => {
    const b = el("button", "active-chip", label + " ×");
    b.setAttribute("aria-label", "حذف فیلتر " + label);
    b.onclick = () => {
      clear();
      page = 1;
      render();
    };
    active.append(b);
  };
  if (favoritesOnly.checked)
    chip("علاقه‌مندی‌ها", () => (favoritesOnly.checked = false));
  if (topic) chip(topic, () => (topic = ""));
  if (author.value) chip(author.value, () => (author.value = ""));
  if (task.value) chip(task.selectedOptions[0].text, () => (task.value = ""));
  if (translated.checked)
    chip("دارای ترجمهٔ فارسی", () => (translated.checked = false));
}
async function load() {
  if (rows) return;
  if (loading) return loading;
  $("#load-error").hidden = true;
  $("#results").setAttribute("aria-busy", "true");
  loading = (async () => {
    try {
      const response = await fetch(base + "data/search.json");
      if (!response.ok) throw Error("index");
      rows = await response.json();
      render();
    } catch {
      $("#load-error").hidden = false;
      $(".pagination").hidden = true;
    } finally {
      loading = null;
      $("#results").setAttribute("aria-busy", "false");
    }
  })();
  return loading;
}
function apply() {
  page = 1;
  updateURL();
  if (rows) render();
  else void load();
}
pageSizeSelect.addEventListener("change", () => {
  const requestedSize = Number(pageSizeSelect.value);
  pageSize = [12, 24, 48, 96].includes(requestedSize) ? requestedSize : 12;
  apply();
});
let timer: ReturnType<typeof setTimeout>;
input.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(apply, 180);
});
$("#search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  clearTimeout(timer);
  apply();
  $("#catalog").scrollIntoView({
    behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "instant"
      : "smooth",
  });
});
[author, task, translated, sort, favoritesOnly].forEach((e) =>
  e.addEventListener("change", apply),
);
document.querySelectorAll<HTMLElement>("[data-topic]").forEach((b) =>
  b.addEventListener("click", () => {
    topic = b.dataset.topic || "";
    apply();
  }),
);
document.querySelectorAll<HTMLElement>("[data-query]").forEach((b) =>
  b.addEventListener("click", () => {
    input.value = b.dataset.query || "";
    apply();
    $("#catalog").scrollIntoView({ behavior: "smooth" });
  }),
);
function clear(all = false) {
  topic = "";
  author.value = "";
  task.value = "";
  translated.checked = false;
  favoritesOnly.checked = false;
  if (all) {
    input.value = "";
    sort.value = "relevant";
  }
  apply();
}
document
  .querySelectorAll(".clear-filters")
  .forEach((b) => b.addEventListener("click", () => clear()));
$("#reset-all").addEventListener("click", () => clear(true));
$("#prev-page").addEventListener("click", () => {
  page--;
  render();
  $("#catalog").scrollIntoView();
});
$("#next-page").addEventListener("click", async () => {
  await load();
  if (!rows) return;
  page++;
  render();
  $("#catalog").scrollIntoView();
});
$("#retry-load").addEventListener("click", () => void load());
// Mobile filter panel: modal semantics, Escape, focus trap, focus restoration.
const panel = $("#filters-panel"),
  open = $<HTMLButtonElement>("#open-filters"),
  close = $("#close-filters");
const backdrop = el("div", "filter-backdrop");
backdrop.hidden = true;
document.body.append(backdrop);
function closePanel() {
  panel.classList.remove("is-open");
  panel.removeAttribute("role");
  panel.removeAttribute("aria-modal");
  backdrop.hidden = true;
  document.body.classList.remove("filters-open");
  open.setAttribute("aria-expanded", "false");
  open.focus();
}
open.setAttribute("aria-controls", "filters-panel");
open.setAttribute("aria-expanded", "false");
open.addEventListener("click", () => {
  panel.classList.add("is-open");
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-modal", "true");
  backdrop.hidden = false;
  document.body.classList.add("filters-open");
  open.setAttribute("aria-expanded", "true");
  close.focus();
});
close.addEventListener("click", closePanel);
backdrop.addEventListener("click", closePanel);
document.addEventListener("keydown", (e) => {
  if (panel.classList.contains("is-open")) {
    if (e.key === "Escape") closePanel();
    if (e.key === "Tab") {
      const focusable = [
        ...panel.querySelectorAll<HTMLElement>("button,input,select,a[href]"),
      ].filter((e) => e.offsetParent !== null);
      const first = focusable[0],
        last = focusable.at(-1);
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last?.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first?.focus();
      }
    }
  } else if (
    e.key === "/" &&
    !["INPUT", "TEXTAREA", "SELECT"].includes((e.target as HTMLElement).tagName)
  ) {
    e.preventDefault();
    input.focus();
  }
});
matchMedia("(min-width: 901px)").addEventListener("change", (e) => {
  if (e.matches && panel.classList.contains("is-open")) closePanel();
});
window.addEventListener("popstate", () => {
  stateFromURL();
  if (rows) render(false);
  else void load();
});
stateFromURL();
// Defer the full index until the visitor approaches results or interacts.
if (location.search) void load();
else {
  const observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        void load();
        observer.disconnect();
      }
    },
    { rootMargin: "120px" },
  );
  observer.observe($("#catalog"));
}

document.addEventListener("favorites-changed", () => {
  if (favoritesOnly.checked && rows) {
    const focusedKey = (document.activeElement as HTMLElement)?.dataset
      .favoriteKey;
    render();
    if (focusedKey) {
      const buttons = [
        ...document.querySelectorAll<HTMLButtonElement>(
          "#results [data-favorite-key]",
        ),
      ];
      (
        buttons.find((b) => b.dataset.favoriteKey === focusedKey) ||
        buttons[0] ||
        favoritesOnly
      ).focus();
    }
  }
});
