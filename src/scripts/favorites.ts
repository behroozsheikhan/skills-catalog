import {
  browserFavorites,
  toggleFavorite,
  FAVORITES_KEY,
} from "../lib/favorites.mjs";
export function syncFavoriteButtons() {
  const saved = browserFavorites();
  document
    .querySelectorAll<HTMLButtonElement>("[data-favorite-key]")
    .forEach((button) => {
      button.hidden = false;
      const active = saved.has(button.dataset.favoriteKey!);
      button.setAttribute("aria-pressed", String(active));
      const label = active ? "حذف از علاقه‌مندی‌ها" : "افزودن به علاقه‌مندی‌ها";
      button.setAttribute(
        "aria-label",
        label + ": " + button.dataset.favoriteKey,
      );
      button.title = label;
      button.textContent = button.classList.contains("favorite-detail")
        ? active
          ? "♥ در علاقه‌مندی‌ها"
          : "♡ افزودن به علاقه‌مندی‌ها"
        : active
          ? "♥"
          : "♡";
    });
  document
    .querySelectorAll("[data-favorites-count]")
    .forEach((el) => (el.textContent = saved.size.toLocaleString("fa-IR")));
}
const status = document.createElement("p");
status.className = "favorites-message";
status.hidden = true;
status.setAttribute("role", "status");
document.body.append(status);
let timer: ReturnType<typeof setTimeout>;
document.addEventListener("click", (event) => {
  const button = (event.target as HTMLElement).closest<HTMLButtonElement>(
    "[data-favorite-key]",
  );
  if (!button) return;
  try {
    const saved = toggleFavorite(localStorage, button.dataset.favoriteKey!);
    status.textContent = saved.has(button.dataset.favoriteKey!)
      ? "به علاقه‌مندی‌های این مرورگر اضافه شد."
      : "از علاقه‌مندی‌ها حذف شد.";
    syncFavoriteButtons();
    document.dispatchEvent(new Event("favorites-changed"));
  } catch {
    status.textContent =
      "ذخیره انجام نشد. فضای ذخیره‌سازی مرورگر در دسترس نیست یا پر شده است.";
  }
  status.hidden = false;
  clearTimeout(timer);
  timer = setTimeout(() => (status.hidden = true), 5000);
});
window.addEventListener("storage", (event) => {
  if (event.key === FAVORITES_KEY || event.key === null) {
    syncFavoriteButtons();
    document.dispatchEvent(new Event("favorites-changed"));
  }
});
window.addEventListener("pageshow", () => {
  syncFavoriteButtons();
  document.dispatchEvent(new Event("favorites-changed"));
});
syncFavoriteButtons();
