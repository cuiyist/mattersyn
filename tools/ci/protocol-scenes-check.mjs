// Capture the same eighteen selected protocol steps before and after a Reader change.
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
const STEP1_EXAMPLES = Object.freeze({
  'extra-gaas-wu2010-step1': { formula: 'GaAs', record_id: 'wu2010-nl100217k-gaas-quantum-dot-pairs-qdps-in-al0-3ga0-1', operation_id: 's01-grow', material_id: 'gaas-889234' },
  'extra-au-fan2006-step1': { formula: 'Au', record_id: 'fan2006-b600923a-ordered-gold-nanocrystal-silica-particle-1', operation_id: 's01-prepare', material_id: 'au-3325c2' },
  'extra-pbs-reinhart2017-step1': { formula: 'PbS', record_id: 'reinhart2017-jacs-7b00158-3-mercaptopropionic-acid-3-mpa-capped-pb-1', operation_id: 's01-add', material_id: 'pbs-7e1774' },
});
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const nonempty = (value) => typeof value === 'string' && value.trim().length > 0 && !/[\r\n\0]/.test(value);

export function validateTargets(value) {
  assert(value && typeof value === 'object' && !Array.isArray(value));
  assert.deepEqual(Object.keys(value).sort(), ['schema', 'targets']);
  assert.equal(value.schema, TARGET_SCHEMA);
  assert(Array.isArray(value.targets) && value.targets.length === 18, 'Exactly eighteen fixed protocol targets are required');
  const ids = new Set();
  const records = new Map();
  const defaults = [];
  const examples = [];
  const step1Examples = [];
  let namedWuDuplicate = false;
  for (const target of value.targets) {
    assert(target && typeof target === 'object' && !Array.isArray(target));
    assert(Object.keys(target).every((key) => FIELDS.has(key)), 'Unexpected target field');
    assert(nonempty(target.id) && /^[a-z0-9-]+$/.test(target.id));
    assert(nonempty(target.record_id) && /^[a-z0-9._-]+$/.test(target.record_id));
    assert(!ids.has(target.id), 'Duplicate target');
    ids.add(target.id);
    if (records.has(target.record_id)) {
      const previous = records.get(target.record_id);
      assert.equal(previous.id, 'default-gaas', 'Only the named Wu default/explicit pair may share a record');
      assert.equal(target.id, 'extra-gaas-wu2010-step1', 'Only the named Wu default/explicit pair may share a record');
      for (const key of ['record_id', 'operation_index', 'operation_id', 'operation_label', 'record_json_bytes', 'record_json_sha256']) {
        assert.equal(target[key], previous[key], `The Wu duplicate must retain the same ${key}`);
      }
      namedWuDuplicate = true;
    } else records.set(target.record_id, target);
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
    } else if (target.group === 'route-example') {
      examples.push(target.id);
      assert.equal(route.searchParams.get('method'), target.record_id);
      assert.equal(target.minimum_label_px_after, 12);
    } else {
      assert.equal(target.group, 'reader-e-step1');
      const expected = STEP1_EXAMPLES[target.id];
      assert(expected, 'Only the three named extra step1 targets are admitted');
      step1Examples.push(target.id);
      for (const key of ['formula', 'record_id', 'operation_id']) assert.equal(target[key], expected[key]);
      assert.equal(target.operation_index, 0, 'An extra target must open the actual first operation');
      assert.equal(route.pathname, '/material.html');
      assert.equal(route.searchParams.get('id'), expected.material_id);
      assert.equal(route.searchParams.get('method'), target.record_id, 'An extra target must explicitly name its record');
      assert.equal(target.minimum_label_px_after, 12);
    }
  }
  assert.deepEqual(defaults, BENCHMARK_FORMULAS);
  assert.deepEqual(examples, EXAMPLES);
  assert.deepEqual(step1Examples, Object.keys(STEP1_EXAMPLES));
  assert(namedWuDuplicate && records.size === 17, 'The named Wu pair is the only intentional shared record');
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

export function checkReportedDrawing(phase, metrics) {
  if (phase !== 'after') return;
  const drawings = metrics.reported_drawings || [];
  if (metrics.renderer !== 'reported-fields' && drawings.length === 0) return;
  assert.equal(drawings.length, 1, 'A reported scene must contain one new drawing card');
  const epsilon = 0.01;
  const rectangle = (r) => r && ['left', 'top', 'right', 'bottom', 'width', 'height'].every((key) => Number.isFinite(r[key]))
    && r.width > 0 && r.height > 0 && r.right >= r.left && r.bottom >= r.top;
  const inside = (inner, outer) => rectangle(inner) && inner.left >= outer.left - epsilon
    && inner.top >= outer.top - epsilon && inner.right <= outer.right + epsilon && inner.bottom <= outer.bottom + epsilon;
  const drawing = drawings[0];
  assert(rectangle(drawing.bounds), 'The reported drawing must be visible and measurable');
  assert.equal(drawing.layout, 'leader-lines-v2', 'The reported drawing must use the large leader-label layout');
  assert(inside(drawing.apparatus_bounds, drawing.bounds), 'The apparatus panel must stay inside the drawing');
  assert(drawing.apparatus_bounds.width >= drawing.bounds.width * 0.90, 'The apparatus must use the drawing width');
  const center = (r) => (r.left + r.right) / 2;
  assert(Math.abs(center(drawing.apparatus_bounds) - center(drawing.bounds)) <= 8, 'The apparatus panel must be centered');
  assert(inside(drawing.svg_bounds, drawing.apparatus_bounds), 'The apparatus SVG must stay inside its panel');
  assert(drawing.svg_bounds.width >= drawing.apparatus_bounds.width * 0.95, 'The apparatus SVG must fill its panel');
  assert(inside(drawing.apparatus_body_bounds, drawing.svg_bounds), 'The actual apparatus body must not clip its SVG');
  assert(drawing.apparatus_body_bounds.width >= drawing.bounds.width * 0.70, 'The actual apparatus body must occupy most of the drawing width');
  assert(rectangle(drawing.apparatus_body_svg_bbox) && drawing.apparatus_body_svg_bbox.width >= drawing.svg_viewbox.width * 0.70, 'SVG body geometry must fill its viewBox');
  assert(Array.isArray(drawing.appendage_geometry_bounds), 'Visible appendage measurements are required');
  for (const r of drawing.appendage_geometry_bounds) {
    assert(r && ['left','top','right','bottom','width','height'].every((key) => Number.isFinite(r[key]))
      && r.width >= 0 && r.height >= 0 && (r.width > 0 || r.height > 0)
      && r.left >= drawing.svg_bounds.left - epsilon && r.top >= drawing.svg_bounds.top - epsilon
      && r.right <= drawing.svg_bounds.right + epsilon && r.bottom <= drawing.svg_bounds.bottom + epsilon,
    'A visible syringe, cooling arrow, condenser or leader clips its SVG');
  }
  assert(Number.isSafeInteger(drawing.leader_line_count) && drawing.leader_line_count >= 0);
  assert(Array.isArray(drawing.plain_annotations));
  for (const label of drawing.plain_annotations) {
    assert.equal(label.border_width_px, 0, 'Leader annotations must not use label boxes');
    assert(label.background_transparent, 'Leader annotations must have transparent backgrounds');
  }
  if (drawing.plain_annotations.length) assert(drawing.leader_line_count > 0, 'Reported labels need thin leader lines');
  assert(Array.isArray(drawing.chamber_heater_fronts), 'Measured chamber heater fronts are required');
  assert(Number.isSafeInteger(drawing.chamber_heater_overlay_count) && drawing.chamber_heater_overlay_count === drawing.chamber_heater_fronts.length, 'Every chamber heater label needs an opaque inset front');
  for (const front of drawing.chamber_heater_fronts) {
    assert(inside(front.bounds,drawing.svg_bounds), 'The heater front must stay inside the chamber drawing');
    assert(front.fully_opaque, 'The heater face must cover the old SVG rectangle behind its text');
    assert(Array.isArray(front.leaf_labels) && front.leaf_labels.length, 'The heater face needs measured text');
    for (const label of front.leaf_labels) {
      const t=label.text_bounds,b=front.bounds;
      assert(t.left >= b.left+2 && t.right <= b.right-2 && t.top >= b.top+2 && t.bottom <= b.bottom-2,
        'Heater text needs a clear inset from every visible heater-face border');
    }
    for (const other of [front.holder_platform_bounds,...front.beam_bounds].filter(Boolean)) {
      const a=front.bounds;
      assert(!(Math.min(a.right,other.right)-Math.max(a.left,other.left)>epsilon && Math.min(a.bottom,other.bottom)-Math.max(a.top,other.top)>epsilon),
        'The heater front must not obscure the holder platform or source beams');
    }
  }
  assert(Array.isArray(drawing.leaf_labels) && Array.isArray(drawing.fact_blocks));
  for (const label of drawing.leaf_labels) {
    assert(label.visible && Number.isFinite(label.screen_font_px) && label.screen_font_px >= 12,
      'An on-drawing leaf label is hidden, unmeasured or below12 actual screen pixels');
    assert(inside(label.text_bounds, drawing.bounds), 'An on-drawing leaf label overflows its drawing');
  }
  for (const block of drawing.fact_blocks) {
    assert(inside(block.bounds, drawing.bounds), 'A fact block overflows the reported drawing');
    assert(Array.isArray(block.leaf_labels) && block.leaf_labels.length > 0, 'A fact block needs visible measurable leaf labels');
    for (const label of block.leaf_labels) assert(inside(label.text_bounds, block.bounds), 'A fact label overflows its block');
  }
  for (let i = 0; i < drawing.fact_blocks.length; i++) {
    for (let j = i + 1; j < drawing.fact_blocks.length; j++) {
      const a = drawing.fact_blocks[i].bounds, b = drawing.fact_blocks[j].bounds;
      const width = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const height = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      assert(!(width > epsilon && height > epsilon), 'Reported fact blocks overlap');
    }
  }
}

export function fontMetrics(art) {
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
  // Self-contained: Playwright serializes this whole function into the page.
  // These HTML labels belong to the drawing card, not the separate full <dl>.
  const bounds = (node) => {
    const r = node.getBoundingClientRect();
    return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
  };
  const screenFont = (node) => {
    const size = parseFloat(getComputedStyle(node).fontSize);
    let a = 1, b = 0, c = 0, d = 1;
    const multiply = (aa, bb, cc, dd) => {
      [a, b, c, d] = [aa * a + cc * b, bb * a + dd * b, aa * c + cc * d, bb * c + dd * d];
    };
    const scalar = (s) => s.endsWith('%') ? parseFloat(s) / 100 : Number(s);
    for (let parent = node; parent; parent = parent.parentElement) {
      const style = getComputedStyle(parent);
      if (style.transform && style.transform !== 'none') {
        const matrix = new DOMMatrixReadOnly(style.transform);
        if (!matrix.is2D) return null;
        multiply(matrix.a, matrix.b, matrix.c, matrix.d);
      }
      if (style.scale && style.scale !== 'none') {
        const axes = style.scale.trim().split(/\s+/).map(scalar);
        if (axes.length > 2 || axes.some((x) => !Number.isFinite(x))) return null;
        multiply(axes[0], 0, 0, axes[1] ?? axes[0]);
      }
      if (style.rotate && style.rotate !== 'none') {
        const rotation = /^(-?[\d.]+)(deg|rad|turn)$/.exec(style.rotate);
        if (!rotation) return null;
        const angle = Number(rotation[1]) * (rotation[2] === 'deg' ? Math.PI / 180 : rotation[2] === 'turn' ? 2 * Math.PI : 1);
        multiply(Math.cos(angle), Math.sin(angle), -Math.sin(angle), Math.cos(angle));
      }
      if (style.zoom && style.zoom !== 'normal') {
        const zoom = scalar(style.zoom);
        if (!Number.isFinite(zoom) || zoom <= 0) return null;
        multiply(zoom, 0, 0, zoom);
      }
    }
    return size * Math.hypot(c, d);
  };
  const reportedDrawings = [...art.querySelectorAll('.reported-scene-drawing')].map((drawing) => {
    const leafNodes = [...drawing.querySelectorAll('strong,span')].filter((node) => !node.querySelector('strong,span'));
    const leaf = (node) => {
      const style = getComputedStyle(node), r = bounds(node), range = document.createRange();
      range.selectNodeContents(node);
      const text = range.getBoundingClientRect();
      return { tag: node.tagName.toLowerCase(), visible: r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none',
        screen_font_px: screenFont(node), text_bounds: { left: text.left, top: text.top, right: text.right, bottom: text.bottom, width: text.width, height: text.height } };
    };
    const factSelector = '.reported-scene-inlet,.reported-scene-atmosphere,.reported-scene-duration,.reported-scene-temperature,.reported-scene-heating-plate';
    // Nested heater temperature text is part of the heater block; independent
    // blocks still must not overlap. Count every leaf once in its outer block.
    const blocks = [...drawing.querySelectorAll(factSelector)];
    const apparatus = drawing.querySelector('.reported-scene-apparatus');
    const svg = apparatus?.querySelector('svg');
    // SVG getBBox ignores clipPaths: shared liquid/highlight paths may extend
    // beyond their visible vessel. Measure the fixed visible vessel outline,
    // then verify every visible external appendage/leader independently.
    const body = svg?.querySelector('[data-part="apparatus-outline"]') || svg?.querySelector('[data-part="apparatus-body"]');
    const appendages = svg ? [...svg.querySelectorAll('[data-part="syringe"],[data-part="cooling-arrow"],[data-part="reflux-condenser"],[data-part="reflux-lines"],[data-part="addition-arrow"],[data-part="gas-line"],[data-part="gas-label-leader"],[data-part="addition-label-leader"]')] : [];
    const geometry = body?.getBBox();
    const viewbox = svg?.viewBox.baseVal;
    const plainSelector = '.reported-scene-inlet,.reported-scene-source,.reported-scene-atmosphere,.reported-scene-duration,.reported-scene-temperature,.reported-scene-substrate';
    const transparent = (color) => !color || color === 'transparent' || /^rgba\([^)]*,\s*0(?:\.0+)?\)$/.test(color);
    return { bounds: bounds(drawing), layout: drawing.dataset.layout || null,
      apparatus_bounds: apparatus ? bounds(apparatus) : null, svg_bounds: svg ? bounds(svg) : null,
      apparatus_body_bounds: body ? bounds(body) : null,
      apparatus_body_svg_bbox: geometry ? {left:geometry.x,top:geometry.y,right:geometry.x+geometry.width,bottom:geometry.y+geometry.height,width:geometry.width,height:geometry.height} : null,
      svg_viewbox: viewbox ? {x:viewbox.x,y:viewbox.y,width:viewbox.width,height:viewbox.height} : null,
      appendage_geometry_bounds: appendages.map(bounds),
      leader_line_count: drawing.querySelectorAll('[data-part="leader-line"] path').length,
      plain_annotations: [...drawing.querySelectorAll(plainSelector)].filter((node) => !blocks.some((block) => block.className === 'reported-scene-heating-plate' && block.contains(node))).map((node) => {
        const style = getComputedStyle(node);
        return { border_width_px: Math.max(...['borderTopWidth', 'borderRightWidth', 'borderBottomWidth', 'borderLeftWidth'].map((key) => parseFloat(style[key]) || 0)),
          background_transparent: transparent(style.backgroundColor) && (!style.backgroundImage || style.backgroundImage === 'none') };
      }),
      chamber_heater_overlay_count: [...drawing.querySelectorAll('.reported-scene-heating-plate')].filter((node)=>node.parentElement?.className==='reported-scene-geometry').length,
      chamber_heater_fronts: [...drawing.querySelectorAll('[data-heater-front="true"]')].map((front)=>{
        const style=getComputedStyle(front),color=style.backgroundColor||'';
        return {bounds:bounds(front),fully_opaque:(/^rgb\(/.test(color)||/^rgba\([^)]*,\s*1(?:\.0+)?\)$/.test(color)) && Number(style.opacity||1)===1 && (!style.backgroundImage||style.backgroundImage==='none'),
          leaf_labels:leafNodes.filter((node)=>front.contains(node)).map(leaf),
          holder_platform_bounds:svg?.querySelector('[data-part="substrate-holder"]')?bounds(svg.querySelector('[data-part="substrate-holder"]')):null,
          beam_bounds:svg?[...svg.querySelectorAll('[data-part="source-beam"],[data-part="source-feed"]')].map(bounds):[]};
      }),
      leaf_labels: leafNodes.map(leaf),
      fact_blocks: blocks.filter((block) => !blocks.some((parent) => parent !== block && parent.contains(block))).map((block) => ({ class_name: block.className, bounds: bounds(block), leaf_labels: leafNodes.filter((node) => block.contains(node)).map(leaf) })) };
  });
  return { scene: art.dataset.scene || null, classes: art.className, external_image_count: art.querySelectorAll('img').length,
    inline_svg_count: art.querySelectorAll('svg').length, labels, minimum_measured_screen_font_px: sizes.length ? Math.min(...sizes) : null,
    renderer: art.dataset.renderer || null, reported_drawings: reportedDrawings };
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
    row.horizontal_page_overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
    assert.equal(row.horizontal_page_overflow, false, 'Horizontal page overflow');
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
    checkReportedDrawing(phase, row.scene_metrics);
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
  assert(receipt.pages.length === 36 && failures.length === 0, receipt.summary);
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  main().catch((error) => { console.error(error.message || error); process.exitCode = 1; });
}
