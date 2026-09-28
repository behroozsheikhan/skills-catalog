import { skills } from "../lib/catalog.mjs";
import type { APIRoute } from "astro";
export const GET: APIRoute = ({ site }) => {
  const base = import.meta.env.BASE_URL.replace(/\/$/, "") + "/";
  const paths = [
    "",
    "about/",
    ...skills.map((s) => s.path),
    ...Array.from(
      { length: Math.ceil(skills.length / 100) },
      (_, i) => `directory/${i + 1}/`,
    ),
  ];
  const escape = (s: string) =>
    s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  return new Response(
    '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
      paths
        .map(
          (p) =>
            `<url><loc>${escape(new URL(base + p, site).href)}</loc></url>`,
        )
        .join("") +
      "</urlset>",
    { headers: { "Content-Type": "application/xml" } },
  );
};
