/** Accept only this site's catalog route as a return destination. */
export function catalogReturnURL(currentURL, base) {
  const current = new URL(currentURL);
  const fallback = base + "#catalog";
  const raw = current.searchParams.get("returnTo");
  if (!raw) return fallback;
  try {
    const target = new URL(raw, current.origin);
    if (
      target.origin !== current.origin ||
      target.pathname !== base ||
      target.username ||
      target.password
    )
      return fallback;
    return target.pathname + target.search + "#catalog";
  } catch {
    return fallback;
  }
}
