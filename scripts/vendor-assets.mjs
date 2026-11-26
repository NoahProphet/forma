import { copyFile, mkdir } from "node:fs/promises";

const files = {
  "node_modules/htmx.org/dist/htmx.min.js": "static/js/htmx.min.js",
  "node_modules/htmx.org/LICENSE": "static/js/htmx-LICENSE.txt",
  "node_modules/@fontsource-variable/vazirmatn/files/vazirmatn-arabic-wght-normal.woff2": "static/fonts/vazirmatn-arabic.woff2",
  "node_modules/@fontsource-variable/vazirmatn/files/vazirmatn-latin-wght-normal.woff2": "static/fonts/vazirmatn-latin.woff2",
  "node_modules/@fontsource-variable/vazirmatn/LICENSE": "static/fonts/vazirmatn-OFL.txt",
};

await mkdir("static/fonts", { recursive: true });
await Promise.all(Object.entries(files).map(([source, target]) => copyFile(source, target)));
