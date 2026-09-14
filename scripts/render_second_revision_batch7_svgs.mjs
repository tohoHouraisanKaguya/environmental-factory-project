#!/usr/bin/env node

import fs from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import process from "node:process";

const require = createRequire(import.meta.url);
const sharp = require("sharp");

const [svgDir, pngDir] = process.argv.slice(2);
if (!svgDir || !pngDir) {
  console.error("usage: render_second_revision_batch7_svgs.mjs <svg-dir> <png-dir>");
  process.exit(2);
}

await fs.mkdir(pngDir, { recursive: true });
const names = (await fs.readdir(svgDir)).filter((name) => name.endsWith(".svg")).sort();
if (names.length !== 12) {
  throw new Error(`expected 12 SVG files, found ${names.length}`);
}

for (const name of names) {
  const source = path.join(svgDir, name);
  const target = path.join(pngDir, name.replace(/\.svg$/u, ".png"));
  await sharp(source, { density: 96 })
    .flatten({ background: "#ffffff" })
    .resize(1600, 800, { fit: "fill" })
    .png({ compressionLevel: 9, adaptiveFiltering: false })
    .toFile(target);
  process.stdout.write(`${target}\n`);
}
