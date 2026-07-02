#!/usr/bin/env node
/**
 * docker-fonts-dl.js — CRUSADER F03
 * Télécharge les polices Google Fonts en woff2 pour embarquement dans l'image Docker.
 * Exécuté UNE SEULE FOIS pendant le build Docker. Aucun appel réseau au rendu.
 *
 * Polices : Cinzel, Playfair Display, Lato, Oswald, Roboto Slab, Inter
 * Système : Arial / Arial Black → ttf-mscorefonts-installer (apt)
 *           Helvetica / Nimbus Sans → fonts-urw-base35 (apt)
 */

const https = require("https");
const fs    = require("fs");
const path  = require("path");

const OUT = "/crusader-fonts";
fs.mkdirSync(OUT, { recursive: true });

// User-Agent Chrome → Google Fonts renvoie du woff2 (format moderne)
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

// ─── Polices à télécharger ────────────────────────────────────────────────────
const FONTS = [
  {
    family: "Cinzel",
    variants: [
      { weight: 400, style: "normal", file: "Cinzel-Regular" },
      { weight: 700, style: "normal", file: "Cinzel-Bold" },
    ],
  },
  {
    family: "Playfair Display",
    variants: [
      { weight: 400, style: "normal", file: "PlayfairDisplay-Regular" },
      { weight: 700, style: "normal", file: "PlayfairDisplay-Bold" },
      { weight: 400, style: "italic", file: "PlayfairDisplay-Italic" },
      { weight: 700, style: "italic", file: "PlayfairDisplay-BoldItalic" },
    ],
  },
  {
    family: "Lato",
    variants: [
      { weight: 400, style: "normal", file: "Lato-Regular" },
      { weight: 700, style: "normal", file: "Lato-Bold" },
      { weight: 400, style: "italic", file: "Lato-Italic" },
    ],
  },
  {
    family: "Oswald",
    variants: [
      { weight: 400, style: "normal", file: "Oswald-Regular" },
      { weight: 600, style: "normal", file: "Oswald-SemiBold" },
      { weight: 700, style: "normal", file: "Oswald-Bold" },
    ],
  },
  {
    family: "Roboto Slab",
    variants: [
      { weight: 400, style: "normal", file: "RobotoSlab-Regular" },
      { weight: 700, style: "normal", file: "RobotoSlab-Bold" },
    ],
  },
  {
    family: "Inter",
    variants: [
      { weight: 400, style: "normal", file: "Inter-Regular" },
      { weight: 700, style: "normal", file: "Inter-Bold" },
      { weight: 900, style: "normal", file: "Inter-Black" },
    ],
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function httpsGet(url, extraHeaders = {}) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const options = {
      hostname: parsed.hostname,
      path: parsed.pathname + parsed.search,
      headers: { "User-Agent": UA, ...extraHeaders },
    };
    const req = https.get(options, (res) => {
      // Suivi des redirects
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        resolve(httpsGet(res.headers.location, extraHeaders));
        return;
      }
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve({ status: res.statusCode, body: Buffer.concat(chunks) }));
      res.on("error", reject);
    });
    req.on("error", reject);
    req.setTimeout(15000, () => { req.destroy(); reject(new Error(`Timeout: ${url}`)); });
  });
}

async function downloadFont(family, variant) {
  const slug      = family.replace(/ /g, "+");
  const styleParam = variant.style === "italic"
    ? `ital,wght@1,${variant.weight}`
    : `wght@${variant.weight}`;
  const cssUrl = `https://fonts.googleapis.com/css2?family=${slug}:${styleParam}&display=swap`;

  const { status, body: cssBody } = await httpsGet(cssUrl);
  if (status !== 200) throw new Error(`Google Fonts CSS HTTP ${status} pour ${family}`);

  const css = cssBody.toString("utf8");

  // Extraire TOUTES les URLs woff2 — prendre la première (subset unicode-range latin)
  const matches = [...css.matchAll(/url\((https:\/\/fonts\.gstatic\.com\/[^)]+\.woff2)\)/g)];
  if (!matches.length) {
    throw new Error(
      `Aucune URL woff2 trouvée pour ${family} ${variant.weight} ${variant.style}.\n` +
      `CSS reçu (200 premiers cars) : ${css.slice(0, 200)}`
    );
  }

  // Prendre le dernier bloc (généralement "latin" = le plus complet sans subsets exotiques)
  const woff2Url = matches[matches.length - 1][1];
  const { status: s2, body: woff2Data } = await httpsGet(woff2Url);
  if (s2 !== 200) throw new Error(`Download woff2 HTTP ${s2} : ${woff2Url}`);

  const outPath = path.join(OUT, `${variant.file}.woff2`);
  fs.writeFileSync(outPath, woff2Data);
  process.stdout.write(`  [OK] ${variant.file}.woff2 — ${woff2Data.length} octets\n`);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log(`\n[FONTS] Téléchargement vers ${OUT}...`);
  let ok = 0, errors = 0;

  for (const font of FONTS) {
    console.log(`\n  ${font.family}:`);
    for (const variant of font.variants) {
      try {
        await downloadFont(font.family, variant);
        ok++;
      } catch (e) {
        process.stderr.write(`  [ERROR] ${font.family} ${variant.weight} ${variant.style}: ${e.message}\n`);
        errors++;
      }
    }
  }

  const files = fs.readdirSync(OUT);
  const totalKB = files.reduce((acc, f) => {
    return acc + fs.statSync(path.join(OUT, f)).size;
  }, 0) / 1024;

  console.log(`\n[FONTS] Terminé : ${ok} OK, ${errors} erreur(s). ${files.length} fichiers, ${totalKB.toFixed(0)} KB total.`);

  if (errors > 0) {
    process.exit(1);
  }
}

main().catch((e) => {
  console.error("[FONTS] Erreur fatale :", e.message);
  process.exit(1);
});
