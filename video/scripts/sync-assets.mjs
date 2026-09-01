// Kopiert die Figma-Exporte der gewuenschten Woche und die Inter-Webfonts
// nach public/ und schreibt src/assets.generated.ts mit der Bildliste.
//
//   node scripts/sync-assets.mjs            -> neueste KW im images/-Ordner
//   WEEK=KW-35 node scripts/sync-assets.mjs -> bestimmte Woche
import {copyFileSync, mkdirSync, readdirSync, rmSync, writeFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const videoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const repoRoot = path.resolve(videoRoot, '..');
const imagesRoot = path.join(repoRoot, 'images');

const weeks = readdirSync(imagesRoot)
  .filter((d) => /^KW-\d+/.test(d))
  .sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]));
if (weeks.length === 0) {
  throw new Error(`Keine KW-Ordner unter ${imagesRoot} gefunden.`);
}
const week = process.env.WEEK ?? weeks.at(-1);
const weekDir = path.join(imagesRoot, week);

const pub = path.join(videoRoot, 'public');
rmSync(path.join(pub, 'cuts'), {recursive: true, force: true});
mkdirSync(path.join(pub, 'cuts'), {recursive: true});

const files = readdirSync(weekDir)
  .filter((f) => /\.(jpe?g|png)$/i.test(f))
  .sort();
for (const f of files) {
  copyFileSync(path.join(weekDir, f), path.join(pub, 'cuts', f));
}

mkdirSync(path.join(pub, 'fonts'), {recursive: true});
const interDir = path.join(videoRoot, 'node_modules', '@fontsource', 'inter', 'files');
for (const weight of ['500', '700', '900']) {
  const name = `inter-latin-${weight}-normal.woff2`;
  copyFileSync(path.join(interDir, name), path.join(pub, 'fonts', name));
}

const banner = '// Automatisch erzeugt von scripts/sync-assets.mjs - nicht von Hand bearbeiten.';
writeFileSync(
  path.join(videoRoot, 'src', 'assets.generated.ts'),
  `${banner}\nexport const WEEK = ${JSON.stringify(week)};\nexport const CUT_IMAGES = ${JSON.stringify(
    files.map((f) => `cuts/${f}`),
    null,
    2,
  )};\n`,
);

console.log(`${week}: ${files.length} Bilder nach public/cuts kopiert.`);
