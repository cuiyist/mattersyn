// Load MatterSyn pages in Chromium, record what each page transfers and how long
// it takes to show its first record, and save desktop and phone screenshots.
//
//   node tools/ci/site-pages-check.mjs --base http://127.0.0.1:8172/nanoxtalsyn-site/ \
//     --index <dist>/data/materials-index.json --out <dir> [--routes routes.json] [--strict]
//
// The ten benchmark material pages (CdSe, CdS, ZnS, InAs, PbS, InP, Au, TiO2, GaAs,
// SnO2) are resolved from the built materials index and get screenshots; extra
// routes (a JSON array of site-relative routes) are only loaded and checked.
// With --strict the exit code is 1 when a page fails to load or throws an
// uncaught script error. Uses Playwright from PLAYWRIGHT_DIR or the default
// module path. Reads only the site's own pages and data.
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'package.json'));
const { chromium, devices } = require('playwright');

export const BENCHMARK_FORMULAS = ['CdSe', 'CdS', 'ZnS', 'InAs', 'PbS', 'InP', 'Au', 'TiO2', 'GaAs', 'SnO2'];
const FIRST_RECORD = 'main[data-reader-ready]'; // set by reader-app.mjs once the selected record is shown

function args(argv) {
  const out = { strict: false };
  for (let i = 2; i < argv.length; i += 1) {
    const key = argv[i].replace(/^--/, '');
    if (key === 'strict') out.strict = true;
    else out[key] = argv[++i];
  }
  return out;
}

export function benchmarkRoutes(index) {
  const rows = Array.isArray(index) ? index : index.materials || [];
  return BENCHMARK_FORMULAS.map((formula) => {
    const matches = rows.filter((row) => row.formula === formula && !row.component_only);
    matches.sort((a, b) => (b.route_records || 0) - (a.route_records || 0));
    return matches[0] ? { formula, id: matches[0].id, route: matches[0].url } : { formula, id: null, route: null };
  });
}

async function visit(browser, base, route, device, shot) {
  const context = await browser.newContext(device);
  const page = await context.newPage();
  const errors = [];
  const failed = [];
  let bytes = 0;
  let requests = 0;
  page.on('pageerror', (error) => errors.push(String(error.message || error).slice(0, 300)));
  page.on('requestfailed', (request) => failed.push(request.url().replace(base, '')));
  page.on('requestfinished', async (request) => {
    requests += 1;
    try {
      const sizes = await request.sizes();
      bytes += sizes.responseBodySize + sizes.responseHeadersSize;
    } catch { /* request closed */ }
  });
  const started = Date.now();
  let status = null;
  let firstRecordMs = null;
  try {
    const response = await page.goto(new URL(route, base).href, { waitUntil: 'domcontentloaded', timeout: 90000 });
    status = response ? response.status() : null;
    try {
      await page.waitForSelector(FIRST_RECORD, { state: 'attached', timeout: 30000 });
      firstRecordMs = Date.now() - started;
    } catch { /* page without record cards */ }
    await page.waitForLoadState('networkidle', { timeout: 90000 }).catch(() => {});
  } catch (error) {
    errors.push(`navigation: ${String(error.message || error).slice(0, 200)}`);
  }
  const loadMs = Date.now() - started;
  if (shot) {
    const height = await page.evaluate(() => document.documentElement.scrollHeight).catch(() => 0);
    const width = page.viewportSize().width;
    await page.screenshot({ path: shot, fullPage: true, clip: { x: 0, y: 0, width, height: Math.max(1, Math.min(height, 8000)) } })
      .catch((error) => errors.push(`screenshot: ${String(error.message || error).slice(0, 200)}`));
  }
  await context.close();
  return { status, page_errors: errors, failed_requests: failed.slice(0, 50), failed_request_count: failed.length,
    transferred_bytes: bytes, requests, first_record_ms: firstRecordMs, load_ms: loadMs };
}

async function main() {
  const a = args(process.argv);
  if (!a.base || !a.index || !a.out) throw new Error('--base, --index and --out are required');
  fs.mkdirSync(a.out, { recursive: true });
  const index = JSON.parse(fs.readFileSync(a.index, 'utf8'));
  const benchmarks = benchmarkRoutes(index);
  const extra = a.routes ? JSON.parse(fs.readFileSync(a.routes, 'utf8')) : [];
  const browser = await chromium.launch();
  const desktop = { viewport: { width: 1440, height: 900 } };
  const phone = devices['iPhone 13'];
  const rows = [];
  for (const bench of benchmarks) {
    if (!bench.route) { rows.push({ ...bench, missing: true }); continue; }
    const name = bench.formula.toLowerCase();
    rows.push({ ...bench, desktop: await visit(browser, a.base, bench.route, desktop, path.join(a.out, `${name}-desktop.png`)),
      phone: await visit(browser, a.base, bench.route, phone, path.join(a.out, `${name}-phone.png`)) });
  }
  const seen = new Set(benchmarks.map((b) => b.route));
  for (const route of extra) {
    if (seen.has(route)) continue;
    seen.add(route);
    rows.push({ route, desktop: await visit(browser, a.base, route, desktop, null) });
  }
  await browser.close();
  const broken = rows.filter((row) => row.missing || [row.desktop, row.phone].some((v) => v && ((v.status || 0) >= 400 || v.status === null || v.page_errors.length)));
  const summary = `${rows.length} routes loaded, ${broken.length} with load or script errors`;
  fs.writeFileSync(path.join(a.out, 'receipt.json'), `${JSON.stringify({ base: a.base, summary, routes: rows }, null, 2)}\n`);
  console.log(summary);
  for (const row of rows.slice(0, benchmarks.length)) {
    const d = row.desktop || {};
    console.log(`${row.formula} ${row.route}: ${((d.transferred_bytes || 0) / 1e6).toFixed(2)} MB, ${d.requests} requests, first record ${d.first_record_ms} ms, load ${d.load_ms} ms`);
  }
  for (const row of broken) console.log(`::warning::${row.route || row.formula}: ${JSON.stringify((row.desktop || {}).page_errors || 'missing')}`);
  if (a.strict && broken.length) process.exitCode = 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  main().catch((error) => { console.error(error); process.exitCode = 1; });
}
