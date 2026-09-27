export const FAVORITES_KEY = "skill-catalog:favorites:v1";
export function readFavorites(storage) {
  try {
    const data = JSON.parse(storage.getItem(FAVORITES_KEY) || "[]");
    return new Set(
      Array.isArray(data)
        ? data.filter(
            (x) => typeof x === "string" && x.length <= 500 && x.includes("/"),
          )
        : [],
    );
  } catch {
    return new Set();
  }
}
export function toggleFavorite(storage, key) {
  const favorites = readFavorites(storage);
  if (favorites.has(key)) favorites.delete(key);
  else favorites.add(key);
  storage.setItem(FAVORITES_KEY, JSON.stringify([...favorites]));
  return favorites;
}
export function browserFavorites() {
  try {
    return readFavorites(localStorage);
  } catch {
    return new Set();
  }
}
