import { defineConfig } from "astro/config";
export default defineConfig({
  site: process.env.SITE_URL || "https://skillcatalog.ir",
  base: process.env.BASE_PATH ?? "/",
  output: "static",
  devToolbar: { enabled: false },
  server: { host: "0.0.0.0", allowedHosts: [".e2b.app"] },
  build: { inlineStylesheets: "never" },
});
