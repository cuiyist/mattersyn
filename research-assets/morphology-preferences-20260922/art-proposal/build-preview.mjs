import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { PARTICLE_SHAPES, particleShapeSVG, particleShapeInfo } from './particle-shape-art.mjs';

const require = createRequire(import.meta.url);
const sharp = require('[local path redacted]');
const here = fileURLToPath(new URL('.', import.meta.url));
await mkdir(`${here}svg`, { recursive: true });
const samples = PARTICLE_SHAPES.map(shape => ({ shape, svg: particleShapeSVG(shape), info: particleShapeInfo(shape) }));
const allIds = samples.flatMap(({svg}) => [...svg.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]));
if (new Set(allIds).size !== allIds.length) throw new Error('Duplicate SVG IDs');
for (const {shape, svg} of samples) {
  for (const match of svg.matchAll(/url\(#([^\)]+)\)/g)) {
    if (!svg.includes(`id="${match[1]}"`)) throw new Error(`Missing local reference: ${shape}`);
  }
  await writeFile(`${here}svg/${shape}.svg`, svg);
}
if (particleShapeSVG('<script>').includes('<script>')) throw new Error('Unexpected shape interpolation');
if (particleShapeSVG('sphere', '"><script>').includes('<script>')) throw new Error('Unexpected label interpolation');

const cols = 4, width = 1280, cellWidth = 320, cellHeight = 294;
const tiles = samples.map(({ shape, svg }, index) => {
  const x = index % cols * cellWidth;
  const y = Math.floor(index / cols) * cellHeight;
  return `<g transform="translate(${x},${y})"><rect x="10" y="10" width="300" height="274" rx="15" fill="#fcfdf9" stroke="#dae4d9"/>${svg.replace('<svg ', '<svg x="18" y="13" width="284" height="220" ')}<text x="160" y="255" text-anchor="middle" fill="#244f51" font-family="Segoe UI,Arial,sans-serif" font-size="16">${shape}</text></g>`;
}).join('');
const sheet = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${Math.ceil(samples.length / cols) * cellHeight}" viewBox="0 0 ${width} ${Math.ceil(samples.length / cols) * cellHeight}"><rect width="100%" height="100%" fill="#f1f5ee"/>${tiles}</svg>`;
await writeFile(`${here}contact-sheet.svg`, sheet);
await sharp(Buffer.from(sheet)).png().toFile(`${here}contact-sheet.png`);
await writeFile(`${here}preview.html`, `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MatterSyn morphology art proposal</title><style>*{box-sizing:border-box}body{font:16px/1.5 system-ui,sans-serif;background:#f1f5ee;color:#254f51;margin:32px}h1{font-size:28px;margin:0 0 8px}p{max-width:800px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(280px,100%),1fr));gap:18px}figure{margin:0;background:#fcfdf9;border:1px solid #dae4d9;border-radius:16px;overflow:hidden}svg{display:block;width:100%;height:auto}figcaption{padding:0 22px 22px}strong{font-size:18px}small{display:block;color:#647c74;margin-top:6px}.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}.legend{display:flex;gap:14px;margin-top:7px;flex-wrap:wrap}</style><h1>Morphology illustrations</h1><p>Qualitative diagrams for source-bound morphology descriptions. Geometry, arrangement, thickness, and region colors are illustrative; these are not measured particle coordinates.</p><div class="grid">${samples.map(({shape,svg,info}) => `<figure>${svg}<figcaption><strong>${shape}</strong>${info.legend.length ? `<div class="legend">${info.legend.map(item => `<span><i class="dot" style="background:${item.color}"></i>${item.label}</span>`).join('')}</div><small>${info.legend.find(item => item.note)?.note || ''}</small>` : ''}</figcaption></figure>`).join('')}</div></html>`);
console.log(JSON.stringify({ shapes: samples.length, uniqueIds: allIds.length, contactSheet: `${here}contact-sheet.png`, preview: `${here}preview.html` }, null, 2));
