// Capture the same fifteen selected protocol steps before and after a Reader change.
// Importing this module or invoking it without arguments performs no browser I/O.
//
// node tools/ci/protocol-scenes-check.mjs --base <site-root> --out <fresh-dir> \
//   --phase before|after
//
// Uses the existing PLAYWRIGHT_DIR convention. Screenshots and receipts belong in
// the workflow artifact; this module does not upload files or modify site data.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const TARGET_SCHEMA = 'mattersyn-protocol-scenes-targets/1';
export const VIEWPORTS = Object.freeze([{ width: 1440, height: 900 }, { width: 390, height: 844 }]);
export const BENCHMARK_FORMULAS = Object.freeze(['CdSe', 'CdS', 'ZnS', 'InAs', 'PbS', 'InP', 'Au', 'TiO2', 'GaAs', 'SnO2']);
const TARGET_FILE = fileURLToPath(new URL('./protocol-scenes-targets.json', import.meta.url));
const FIELDS = new Set(['id', 'group', 'formula', 'record_id', 'route', 'operation_index', 'operation_id', 'operation_label', 'record_json_bytes', 'record_json_sha256', 'minimum_label_px_after']);
const EXAMPLES = ['gaas-droplet', 'hot-injection', 'hydrothermal', 'sol-gel', 'solid-state'];
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const nonempty = (value) => typeof value === 'string' && value.trim().length > 0 && !/[\r\n\0]/.test(value);

export function validateTargets(value) {
  assert(value && typeof value === 'object' && !Array.isArray(value));
  assert.deepEqual(Object.keys(value).sort(), ['schema', 'targets']);
  assert.equal(value.schema, TARGET_SCHEMA);
  assert(Array.isArray(value.targets) && value.targets.length === 15, 'Exactly fifteen fixed protocol targets are required');
  const ids = new Set();
  const records = new Set();
  const defaults = [];
  const examples = [];
  for (const target of value.targets) {
    assert(target && typeof target === 'object' && !Array.isArray(target));
    assert(Object.keys(target).every((key) => FIELDS.has(key)), 'Unexpected target field');
    assert(nonempty(target.id) && /^[a-z0-9-]+$/.test(target.id));
    assert(nonempty(target.record_id) && /^[a-z0-9._-]+$/.test(target.record_id));
    assert(!ids.has(target.id) && !records.has(target.record_id), 'Duplicate target or record');
    ids.add(target.id); records.add(target.record_id);
    assert(nonempty(target.formula) && target.formula.length <= 128);
    assert(nonempty(target.operation_id) && nonempty(target.operation_label) && target.operation_label.length <= 300);
    assert(Number.isSafeInteger(target.operation_index) && target.operation_index >= 0);
    assert(Number.isSafeInteger(target.record_json_bytes) && target.record_json_bytes > 0);
    assert(typeof target.record_json_sha256 === 'string' && /^[a-f0-9]{64}$/.test(target.record_json_sha256));
    assert(nonempty(target.route) && !/^(?:[a-z]+:|\/|\\)/i.test(target.route), 'Only a site-relative material route is allowed');
    const route = new URL(target.route, 'https://validation.invalid/');
    assert.equal(route.origin, 'https://validation.invalid');
    assert(['/material.html', '/cdse.html'].includes(route.pathname) && !route.hash);
    assert([...route.searchParams.keys()].every((key) => key === 'id' || key === 'method'));
    if (target.group === 'benchmark-default') {
      defaults.push(target.formula);
      assert(!route.searchParams.has('method'), 'A benchmark must visit the actual default record');
      assert(!Object.hasOwn(target, 'minimum_label_px_after'));
    } else {
      assert.equal(target.group, 'route-example');
      examples.push(target.id);
      assert.equal(route.searchParams.get('method'), target.record_id);
      assert.equal(target.minimum_label_px_after, 12);
    }
  }
  assert.deepEqual(defaults, BENCHMARK_FORMULAS);
  assert.deepEqual(examples, EXAMPLES);
  return value.targets;
}

export function targetURL(base, target) {
  const root = new URL(base);
  assert(['http:', 'https:'].includes(root.protocol) && !root.username && !root.password && !root.search && !root.hash);
  if (!root.pathname.endsWith('/')) root.pathname += '/';
  const url = new URL(target.route, root);
  assert.equal(url.origin, root.origin);
  assert(url.pathname.startsWith(root.pathname), 'Target escaped the supplied site root');
  return url.href;
}

export function checkAfterLabels(phase, target, metrics) {
  if (phase !== 'after' || !target.minimum_label_px_after) return;
  assert(metrics.inline_svg_count > 0, 'The shared operation drawing has no measurable inline SVG');
  assert(typeof metrics.minimum_measured_screen_font_px === 'number' && Number.isFinite(metrics.minimum_measured_screen_font_px));
  assert(metrics.minimum_measured_screen_font_px >= target.minimum_label_px_after,
    `Shared drawing label is below ${target.minimum_label_px_after}px on screen`);
}

function fontMetrics(art) {
  const labels = [];
  for (const text of art.querySelectorAll('svg text')) {
    const rect = text.getBoundingClientRect();
    const style = getComputedStyle(text);
    const matrix = text.getScreenCTM();
    if (!rect.width || !rect.height || style.visibility === 'hidden' || style.display === 'none') continue;
    const scale = matrix ? Math.hypot(matrix.c, matrix.d) : null;
    labels.push({ kind: 'inline-svg-text', text: text.textContent.trim(), css_font_px: parseFloat(style.fontSize),
      screen_font_px: scale === null ? null : parseFloat(style.fontSize) * scale });
  }
  for (const text of art.querySelectorAll('span,strong,p,h3,small,dt,dd')) {
    if (text.closest('svg')) continue;
    const rect = text.getBoundingClientRect();
    const style = getComputedStyle(text);
    if (!rect.width || !rect.height || style.visibility === 'hidden' || style.display === 'none' || !text.textContent.trim()) continue;
    labels.push({ kind: 'html-label', text: text.textContent.trim(), css_font_px: parseFloat(style.fontSize), screen_font_px: parseFloat(style.fontSize) });
  }
  const sizes = labels.map((label) => label.screen_font_px).filter((size) => typeof size === 'number' && Number.isFinite(size));
  return { scene: art.dataset.scene || null, classes: art.className, external_image_count: art.querySelectorAll('img').length,
    inline_svg_count: art.querySelectorAll('svg').length, labels, minimum_measured_screen_font_px: sizes.length ? Math.min(...sizes) : null };
}

function fileReceipt(out, name) {
  const bytes = fs.readFileSync(path.join(out, name));
  return { file: name, bytes: bytes.length, sha256: sha256(bytes) };
}

async function visit(browser, base, out, phase, target, viewport) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1, serviceWorkers: 'block', reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(String(error.message || error)));
  const row = { id: target.id, formula: target.formula, record_id: target.record_id, operation_id: target.operation_id,
    operation_index: target.operation_index, viewport, requested_route: target.route };
  try {
    const response = await page.goto(targetURL(base, target), { waitUntil: 'domcontentloaded', timeout: 90000 });
    row.status = response ? response.status() : null;
    assert.equal(row.status, 200, 'Material route did not return 200');
    await page.waitForSelector('main[data-reader-ready]', { state: 'attached', timeout: 60000 });
    row.observed_initial_record = await page.locator('main[data-reader-ready]').getAttribute('data-reader-ready');
    assert.equal(row.observed_initial_record, target.record_id, 'Actual default or explicit record differs from the fixed target');
    await page.waitForSelector('#protocol .protocol-step-list button', { state: 'attached', timeout: 60000 });
    const buttons = page.locator('#protocol .protocol-step-list button');
    assert(await buttons.count() > target.operation_index, 'Recorded operation index is missing');
    const button = buttons.nth(target.operation_index);
    row.selected_button_text = await button.innerText();
    await button.click();
    await page.waitForFunction((label) => document.querySelector('#protocol .protocol-copy h3')?.textContent === label,
      target.operation_label, { timeout: 30000 });
    assert.equal(await button.getAttribute('aria-pressed'), 'true');
    assert.equal(await page.locator('#protocol .protocol-copy h3').innerText(), target.operation_label);
    const art = page.locator('#protocol .protocol-art');
    await art.waitFor({ state: 'visible', timeout: 30000 });
    const stage = page.locator('#protocol .protocol-stage');
    await stage.scrollIntoViewIfNeeded();
    await stage.evaluate((node) => node.scrollIntoView({ block: 'start', behavior: 'instant' }));
    await page.waitForTimeout(750);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2), false, 'Horizontal page overflow');
    row.scene_metrics = await art.evaluate(fontMetrics);
    row.below_image_note_count = await page.locator('#protocol .protocol-stage .protocol-visual > .protocol-visual-note').count();
    assert.equal(row.below_image_note_count, 1, 'Expected one note below the operation image');
    const href = await page.locator('.reader-switch a').filter({ hasText: 'Download JSON' }).getAttribute('href');
    assert(href, 'Download JSON link is missing');
    const download = await context.request.get(new URL(href, page.url()).href);
    assert.equal(download.status(), 200, 'Download JSON is unavailable');
    const bytes = await download.body();
    assert.equal(bytes.length, target.record_json_bytes, 'Record JSON byte length changed');
    row.download_json_sha256 = sha256(bytes);
    assert.equal(row.download_json_sha256, target.record_json_sha256, 'Record JSON bytes changed');
    assert.deepEqual(errors, [], 'Uncaught page script errors');
    const stem = `${target.id}-${viewport.width}`;
    await page.screenshot({ path: path.join(out, `${stem}-viewport.png`) });
    await stage.screenshot({ path: path.join(out, `${stem}-protocol.png`) });
    row.screenshots = [fileReceipt(out, `${stem}-viewport.png`), fileReceipt(out, `${stem}-protocol.png`)];
    row.actual_final_url = page.url();
    checkAfterLabels(phase, target, row.scene_metrics);
    row.automated_checks_passed = true;
    row.human_visual_review = 'pending';
  } catch (error) {
    row.automated_checks_passed = false;
    row.error = String(error.message || error);
  } finally {
    row.page_errors = errors;
    await context.close();
  }
  return row;
}

function argumentsFor(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 2) {
    assert(['--base', '--out', '--phase'].includes(argv[i]) && typeof argv[i + 1] === 'string', 'Use --base, --out and --phase');
    const key = argv[i].slice(2);
    assert(!Object.hasOwn(args, key), 'Duplicate command-line option');
    args[key] = argv[i + 1];
  }
  assert(args.base && args.out && ['before', 'after'].includes(args.phase), 'Use --base, --out and --phase before|after');
  return args;
}

export async function main(argv = process.argv.slice(2)) {
  if (!argv.length) {
    console.log(JSON.stringify({ status: 'DEFAULT_INERT', browser_started: false, network_calls: 0, screenshots_created: 0 }));
    return;
  }
  const args = argumentsFor(argv);
  const raw = fs.readFileSync(TARGET_FILE);
  const targets = validateTargets(JSON.parse(raw));
  for (const target of targets) targetURL(args.base, target);
  const out = path.resolve(args.out);
  assert(!fs.existsSync(out), 'Keep previous capture results; select a fresh output directory');
  const require = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'package.json'));
  const { chromium } = require('playwright');
  fs.mkdirSync(out);
  const receipt = { schema: 'mattersyn-protocol-scenes-capture/1', at_utc: new Date().toISOString(), phase: args.phase, base: args.base,
    target_set_sha256: sha256(raw), workflow_commit: process.env.GITHUB_SHA || null, anonymous: true, browser_started: false,
    publication_checks_replaced: false, records_changed: 0, figures_changed: 0, uploads: 0, pages: [] };
  const save = () => fs.writeFileSync(path.join(out, 'receipt.json'), `${JSON.stringify(receipt, null, 2)}\n`);
  save();
  let browser;
  try {
    browser = await chromium.launch();
    receipt.browser_started = true;
    for (const target of targets) {
      for (const viewport of VIEWPORTS) {
        const row = await visit(browser, args.base, out, args.phase, target, viewport);
        receipt.pages.push(row); save();
        console.log(`${args.phase} ${target.id} ${viewport.width}: ${row.automated_checks_passed ? 'pass' : row.error}`);
      }
    }
  } catch (error) {
    receipt.capture_error = String(error.message || error);
    throw error;
  } finally {
    if (browser) await browser.close();
    save();
  }
  const failures = receipt.pages.filter((row) => !row.automated_checks_passed);
  receipt.summary = `${receipt.pages.length} target/viewports, ${failures.length} failed`;
  save();
  assert(receipt.pages.length === 30 && failures.length === 0, receipt.summary);
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  main().catch((error) => { console.error(error.message || error); process.exitCode = 1; });
}
