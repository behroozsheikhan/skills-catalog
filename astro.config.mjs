import { defineConfig } from "astro/config";
export default defineConfig({
  site: process.env.SITE_URL || "https://behroozsheikhan.github.io",
  base: process.env.BASE_PATH ?? "/skills-catalog",
  output: "static",
  devToolbar: { enabled: false },
  server: { host: "0.0.0.0", allowedHosts: [".e2b.app"] },
  build: { inlineStylesheets: "never" },
});
