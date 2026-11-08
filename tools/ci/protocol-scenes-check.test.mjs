import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { validateTargets, targetURL, checkAfterLabels, checkReportedDrawing, fontMetrics, VIEWPORTS, argumentsFor, safeDiagnosticURL, safeDiagnosticText, registerFailureDiagnostics, structuralReadinessSummary, collectFailureDiagnostics, visit, LEGACY_TARGET_SCHEMA, TARGET_SCHEMA, K_REGRESSION_TARGETS, beforeTargetsFromBaseSnapshot, checkRecordOperationMetrics, collectRecordOperationMetrics, viewportsForTarget, REPORTED_SCENE_KINDS, VESSEL_VARIANTS, sceneFixtureMatrix, standaloneWidthLimitedFurnace, fixtureRecordCases } from './protocol-scenes-check.mjs';

const original = JSON.parse(fs.readFileSync(new URL('./protocol-scenes-targets.json', import.meta.url), 'utf8'));
const copy = () => structuredClone(original);

test('fixed public target set preserves eighteen views and adds two exact K injection regressions', () => {
  const rows = validateTargets(copy());
  assert.equal(rows.length, 20);
  assert.equal(rows.filter((row) => row.group === 'benchmark-default').length, 10);
  assert.equal(rows.filter((row) => row.group === 'route-example').length, 5);
  assert.equal(rows.filter((row) => row.group === 'reader-e-step1').length, 3);
  assert.deepEqual(VIEWPORTS.map((row) => row.width), [1440, 390]);
  assert.equal(rows.length * VIEWPORTS.length * 2, 80);
});

test('private fields, record duplicates, absent target and invalid operation/hash are rejected', () => {
  const mutations = [
    (x) => { x.targets[0].private_path = 'private'; },
    (x) => { x.targets[0].review_status = 'private'; },
    (x) => { x.targets[1].record_id = x.targets[0].record_id; },
    (x) => { x.targets.pop(); },
    (x) => { x.targets[0].operation_index = -1; },
    (x) => { x.targets[0].record_json_sha256 = 'not-a-sha'; },
  ];
  for (const mutate of mutations) { const value = copy(); mutate(value); assert.throws(() => validateTargets(value)); }
});

test('defaults cannot acquire method parameters, examples must name their exact record', () => {
  const defaultWithMethod = copy(); defaultWithMethod.targets[0].route += '?method=' + defaultWithMethod.targets[0].record_id;
  assert.throws(() => validateTargets(defaultWithMethod));
  const wrongExample = copy(); wrongExample.targets[10].route = wrongExample.targets[10].route.replace(wrongExample.targets[10].record_id, 'other');
  assert.throws(() => validateTargets(wrongExample));
});

test('changed defaults retain exact Wu step1; only an actual Wu default may share its pins', () => {
  const rows=validateTargets(copy()),ordinary=rows.find(r=>r.id==='default-gaas'),extra=rows.find(r=>r.id==='extra-gaas-wu2010-step1');
  assert.equal(new URL(extra.route,'https://validation.invalid/').searchParams.get('method'),extra.record_id);
  const duplicate=copy();for(const key of ['record_id','operation_id','operation_index','operation_label','record_json_sha256','record_json_bytes'])duplicate.targets[8][key]=extra[key];
  assert.equal(validateTargets(duplicate).length,20);
  for(const mutate of [x=>{x.targets[15].record_json_sha256='0'.repeat(64);},x=>{x.targets[15].record_json_bytes++;},x=>{x.targets[15].operation_label+=' altered';},x=>{x.targets[16].record_id=extra.record_id;}]){const value=structuredClone(duplicate);mutate(value);assert.throws(()=>validateTargets(value));}
});

test('all three extra views are the exact first operation on their explicit material/record route', () => {
  const extras = original.targets.slice(15,18);
  assert.deepEqual(extras.map((row) => [row.id, row.operation_index, row.operation_id]), [
    ['extra-gaas-wu2010-step1', 0, 's01-grow'],
    ['extra-au-fan2006-step1', 0, 's01-prepare'],
    ['extra-pbs-reinhart2017-step1', 0, 's01-add'],
  ]);
  for (let i = 15; i < 18; i++) {
    for (const mutate of [
      (x) => { x.targets[i].operation_index = 1; },
      (x) => { x.targets[i].operation_id = 'different-step'; },
      (x) => { x.targets[i].route = x.targets[i].route.replace(/&method=.*/, ''); },
      (x) => { x.targets[i].route = x.targets[i].route.replace('id=', 'id=wrong-'); },
      (x) => { x.targets[i].group = 'unapproved-extra'; },
    ]) { const value = copy(); mutate(value); assert.throws(() => validateTargets(value)); }
  }
});

test('target URLs stay within live or local candidate site roots', () => {
  const row = original.targets[1];
  assert.equal(targetURL('https://cuiyist.github.io/mattersyn-site/', row), 'https://cuiyist.github.io/mattersyn-site/' + row.route);
  assert.equal(targetURL('http://127.0.0.1:8172/candidate', row), 'http://127.0.0.1:8172/candidate/' + row.route);
  for (const route of ['https://other.invalid/material.html', '//other.invalid/material.html', '../material.html']) {
    assert.throws(() => targetURL('http://127.0.0.1:8172/candidate/', { route }));
  }
  const outside = copy(); outside.targets[0].route = 'https://other.invalid/material.html';
  assert.throws(() => validateTargets(outside));
});

test('after examples require measured inline labels of at least12 actual screen pixels', () => {
  const example = original.targets[10];
  const measured = (px) => ({ inline_svg_count: 1, minimum_measured_screen_font_px: px });
  checkAfterLabels('after', example, measured(12));
  assert.throws(() => checkAfterLabels('after', example, measured(11.99)));
  assert.throws(() => checkAfterLabels('after', example, { inline_svg_count: 0, minimum_measured_screen_font_px: 16 }));
  assert.throws(() => checkAfterLabels('after', example, { inline_svg_count: 1, minimum_measured_screen_font_px: null }));
  checkAfterLabels('before', example, measured(8));
  checkAfterLabels('after', original.targets[0], measured(8));
});

const rect = (left, top, width, height) => ({ left, top, right: left + width, bottom: top + height, width, height });
const label = (left, top, px = 13) => ({ tag: 'span', visible: true, screen_font_px: px, text_bounds: rect(left, top, 40, 16) });
function drawingMetrics() {
  const a = label(15, 15), b = label(215, 15);
  return { renderer: 'reported-fields', reported_drawings: [{ bounds: rect(0, 0, 400, 300), layout: 'leader-lines-v2', apparatus_bounds: rect(8, 80, 384, 210), svg_bounds: rect(8, 80, 384, 210), apparatus_body_bounds: rect(40,90,320,180), apparatus_body_svg_bbox: rect(25,10,250,180), svg_viewbox: {x:0,y:0,width:300,height:200}, appendage_geometry_bounds: [], chamber_heater_fronts: [], chamber_heater_overlay_count:0, leader_line_count: 2, plain_annotations: [{border_width_px: 0, background_transparent: true}], leaf_labels: [a, b], fact_blocks: [
    { class_name: 'reported-scene-inlet', bounds: rect(10, 10, 150, 70), leaf_labels: [a] },
    { class_name: 'reported-scene-atmosphere', bounds: rect(210, 10, 150, 70), leaf_labels: [b] },
  ] }] };
}

test('new after drawings require visible leaf fonts of12 actual pixels, never separate dl labels', () => {
  checkReportedDrawing('after', drawingMetrics());
  for (const value of [11.99, null, NaN]) {
    const metrics = drawingMetrics(); metrics.reported_drawings[0].leaf_labels[0].screen_font_px = value;
    assert.throws(() => checkReportedDrawing('after', metrics));
  }
  const hidden = drawingMetrics(); hidden.reported_drawings[0].leaf_labels[0].visible = false;
  assert.throws(() => checkReportedDrawing('after', hidden));
  const missing = drawingMetrics(); missing.reported_drawings = [];
  assert.throws(() => checkReportedDrawing('after', missing));
});

test('reported facts and rendered text stay inside the drawing and their own fact block', () => {
  for (const mutate of [
    (d) => { d.fact_blocks[0].bounds = rect(-1, 10, 150, 70); },
    (d) => { d.fact_blocks[0].bounds = rect(300, 10, 150, 70); },
    (d) => { d.leaf_labels[0].text_bounds = rect(390, 15, 40, 16); },
    (d) => { d.fact_blocks[0].leaf_labels[0].text_bounds = rect(150, 15, 40, 16); },
    (d) => { d.fact_blocks[0].bounds = rect(10, 10, 0, 0); },
  ]) { const metrics = drawingMetrics(); mutate(metrics.reported_drawings[0]); assert.throws(() => checkReportedDrawing('after', metrics)); }
});

test('separate fact blocks cannot overlap, while touching edges are allowed', () => {
  const metrics = drawingMetrics(); metrics.reported_drawings[0].fact_blocks[1].bounds = rect(159, 10, 150, 70);
  assert.throws(() => checkReportedDrawing('after', metrics), /overlap/);
  metrics.reported_drawings[0].fact_blocks[1].bounds = rect(160, 10, 150, 70);
  checkReportedDrawing('after', metrics);
});

test('before and handmade/per-paper scenes retain old checks without requiring a new drawing', () => {
  checkReportedDrawing('before', { renderer: 'reported-fields', reported_drawings: [] });
  checkReportedDrawing('after', { renderer: null, reported_drawings: [] });
  checkReportedDrawing('after', { renderer: 'per-paper', reported_drawings: [] });
  const noReportedFacts = drawingMetrics(); noReportedFacts.reported_drawings[0].leaf_labels = []; noReportedFacts.reported_drawings[0].fact_blocks = [];
  checkReportedDrawing('after', noReportedFacts);
});

class MetricNode {
  constructor(tag, className, bounds, children = [], fontSize = '13px') {
    this.tagName = tag.toUpperCase(); this.className = className; this.bounds = bounds; this.children = children;
    this.style = { fontSize, visibility: 'visible', display: 'block', transform: 'none', scale: 'none', rotate: 'none', zoom: '1' };
    this.dataset = {}; this.textContent = 'reported label'; this.parentElement = null;
    for (const child of children) child.parentElement = this;
  }
  getBoundingClientRect() { return this.bounds; }
  getBBox() { return this.svgBBox || {x:this.bounds.left,y:this.bounds.top,width:this.bounds.width,height:this.bounds.height}; }
  contains(node) { return node === this || this.children.some((child) => child.contains(node)); }
  querySelectorAll(selector) {
    const matches = (node, term) => {
      if (term === '[data-part="leader-line"] path') return node.tagName === 'PATH' && node.parentElement?.dataset.part === 'leader-line';
      const part = /^\[data-part="([^"]+)"\]$/.exec(term); if(part) return node.dataset.part === part[1];
      return term.startsWith('.') ? node.className.split(/\s+/).includes(term.slice(1)) : node.tagName.toLowerCase() === term;
    };
    const terms = selector.split(',').map((term) => term.trim()), out = [];
    for (const child of this.children) { if (terms.some((term) => matches(child, term))) out.push(child); out.push(...child.querySelectorAll(selector)); }
    return out;
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  closest(selector) { for (let node = this; node; node = node.parentElement) if (node.tagName.toLowerCase() === selector) return node; return null; }
}

function withMetricDOM(run) {
  const keys = ['getComputedStyle', 'document', 'DOMMatrixReadOnly']; const old = Object.fromEntries(keys.map((key) => [key, globalThis[key]]));
  globalThis.getComputedStyle = (node) => node.style;
  globalThis.document = { createRange: () => { let selected; return { selectNodeContents: (node) => { selected = node; }, getBoundingClientRect: () => selected.textBounds || selected.bounds }; } };
  globalThis.DOMMatrixReadOnly = class { constructor(value) { const [a, b, c, d] = value.slice(7, -1).split(',').map(Number); Object.assign(this, { a, b, c, d, is2D: true }); } };
  try { run(); } finally { for (const key of keys) if (old[key] === undefined) delete globalThis[key]; else globalThis[key] = old[key]; }
}

function metricFixture() {
  const indicator = new MetricNode('i', 'reported-scene-heating-indicator', rect(95, 20, 8, 8));
  const strong = new MetricNode('strong', '', rect(20, 20, 90, 18), [indicator]);
  const value = new MetricNode('span', '', rect(20, 45, 90, 18));
  const plate = new MetricNode('div', 'reported-scene-heating-plate', rect(10, 10, 120, 70), [strong, value]);
  const line = new MetricNode('path', '', rect(10, 10, 15, 30));
  const leaders = new MetricNode('g', '', rect(10, 10, 15, 30), [line]); leaders.dataset.part = 'leader-line';
  const body = new MetricNode('g','',rect(40,20,320,170));body.dataset.part='apparatus-body';body.svgBBox={x:25,y:10,width:250,height:180};
  const svg = new MetricNode('svg', '', rect(8, 8, 384, 200), [body,leaders]);svg.viewBox={baseVal:{x:0,y:0,width:300,height:200}};
  const equipment = new MetricNode('div', 'reported-scene-apparatus', rect(8, 8, 384, 280), [svg, plate]);
  const drawing = new MetricNode('div', 'reported-scene-drawing', rect(0, 0, 400, 300), [equipment]); drawing.dataset.layout = 'leader-lines-v2';
  const outside = new MetricNode('dl', 'reported-scene-labels', rect(0, 310, 400, 30), [new MetricNode('dd', '', rect(0, 310, 100, 16), [], '8px')]);
  const art = new MetricNode('div', 'protocol-art', rect(0, 0, 400, 350), [drawing, outside]); art.dataset.renderer = 'reported-fields';
  return { art, drawing };
}

test('drawing metrics include HEATING strong with an indicator child and exclude the outside dl', () => {
  withMetricDOM(() => {
    const { art } = metricFixture(), metrics = fontMetrics(art), drawing = metrics.reported_drawings[0];
    assert.deepEqual(drawing.leaf_labels.map((row) => row.tag), ['strong', 'span']);
    assert.equal(drawing.fact_blocks.length, 1); assert.equal(drawing.fact_blocks[0].class_name, 'reported-scene-heating-plate');
    assert.deepEqual(drawing.leaf_labels.map((row) => row.screen_font_px), [13, 13]);
    assert.equal(metrics.minimum_measured_screen_font_px, 8, 'The separate original metric remains unchanged');
    checkReportedDrawing('after', metrics);
  });
});

test('actual HTML screen font metric catches ancestor scale rather than trusting declared13px', () => {
  withMetricDOM(() => {
    const { art, drawing } = metricFixture(); drawing.style.transform = 'matrix(0.5,0,0,0.5,0,0)';
    const metrics = fontMetrics(art); assert.equal(metrics.reported_drawings[0].leaf_labels[0].screen_font_px, 6.5);
    assert.throws(() => checkReportedDrawing('after', metrics), /below12/);
  });
});

test('direct no-argument invocation is inert and does not require Playwright or a browser', () => {
  const script = fileURLToPath(new URL('./protocol-scenes-check.mjs', import.meta.url));
  const result = spawnSync(process.execPath, [script], { encoding: 'utf8', env: { ...process.env, PLAYWRIGHT_DIR: 'Z:/definitely-not-installed' } });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout), { status: 'DEFAULT_INERT', browser_started: false, network_calls: 0, screenshots_created: 0 });
});

test('K retains full-width labels and centered height-fitted apparatus with plain connected labels', () => {
  for (const [mutate, message] of [
    [(d) => { d.layout = 'corner-boxes'; }, /leader-label/],
    [(d) => { d.apparatus_bounds = rect(60, 80, 280, 210); }, /drawing width/],
    [(d) => { d.apparatus_bounds = rect(0, 80, 370, 210); }, /centered/],
    [(d) => { d.svg_bounds = rect(120, 80, 200, 210); }, /centered/],
    [(d) => { d.plain_annotations[0].border_width_px = 1; }, /label boxes/],
    [(d) => { d.plain_annotations[0].background_transparent = false; }, /transparent/],
    [(d) => { d.leader_line_count = 0; }, /leader lines/],
  ]) { const metrics = drawingMetrics(); mutate(metrics.reported_drawings[0]); assert.throws(() => checkReportedDrawing('after', metrics), message); }
});

test('nested temperature is measured once inside its heater, without hiding independent overlap', () => {
  withMetricDOM(() => {
    const { art, drawing } = metricFixture();
    const plate = drawing.querySelector('.reported-scene-heating-plate');
    const value = plate.children[1];
    const temperature = new MetricNode('div', 'reported-scene-temperature', rect(15, 40, 105, 30), [value]);
    plate.children[1] = temperature; temperature.parentElement = plate;
    const metrics = fontMetrics(art);
    assert.equal(metrics.reported_drawings[0].fact_blocks.length, 1);
    assert.equal(metrics.reported_drawings[0].leaf_labels.length, 2);
    assert.equal(metrics.reported_drawings[0].leader_line_count, 1);
    checkReportedDrawing('after', metrics);
  });
});

test('height-limited geometry may be narrow without weakening intrinsic body/viewBox or clipping checks',()=>{const m=drawingMetrics();m.reported_drawings[0].apparatus_body_bounds=rect(140,90,114,180);checkReportedDrawing('after',m);const b=drawingMetrics();b.reported_drawings[0].apparatus_body_svg_bbox=rect(95,10,114,180);assert.throws(()=>checkReportedDrawing('after',b),/SVG body geometry/);});
test('visible body and zero-width or zero-height leader appendages stay inside SVG',()=>{const m=drawingMetrics();m.reported_drawings[0].appendage_geometry_bounds=[rect(20,90,0,50),rect(30,100,50,0)];checkReportedDrawing('after',m);m.reported_drawings[0].appendage_geometry_bounds.push(rect(-1,90,20,40));assert.throws(()=>checkReportedDrawing('after',m),/visible syringe/);const b=drawingMetrics();b.reported_drawings[0].apparatus_body_bounds=rect(0,90,320,180);assert.throws(()=>checkReportedDrawing('after',b),/must not clip/);});
test('font metrics measure actual SVG body bbox and viewBox rather than its wrapper',()=>withMetricDOM(()=>{const{art}=metricFixture(),d=fontMetrics(art).reported_drawings[0];assert.equal(d.apparatus_body_bounds.width,320);assert.equal(d.apparatus_body_svg_bbox.width,250);assert.equal(d.svg_viewbox.width,300);assert.deepEqual(d.appendage_geometry_bounds,[]);}));

test('before named-Wu default duplicate and after snapshot each keep20 IDs with changed defaults',()=>{
 const before=copy();
 const beforeDefault=before.targets.find(t=>t.id==='default-gaas');
 const namedWu=before.targets.find(t=>t.id==='extra-gaas-wu2010-step1');
 for(const key of ['record_id','operation_id','operation_index','operation_label','record_json_sha256','record_json_bytes'])beforeDefault[key]=namedWu[key];
 assert.equal(validateTargets(before).length,20);assert.equal(new Set(before.targets.map(t=>t.record_id)).size,19);
 const actual=copy(),actualDefault=actual.targets.find(t=>t.id==='default-gaas');
 assert.equal(validateTargets(actual).length,20);
 assert.equal(new Set(actual.targets.map(t=>t.record_id)).size,20-Number(actualDefault.record_id===namedWu.record_id));
 const alternative=copy();alternative.targets.find(t=>t.id==='default-gaas').record_id='another-gaas-default';
 assert.equal(validateTargets(alternative).length,20);assert.equal(new Set(alternative.targets.map(t=>t.record_id)).size,20);
 assert.notEqual(beforeDefault.record_id,alternative.targets.find(t=>t.id==='default-gaas').record_id);
});
test('explicit target snapshot CLI option preserves required phase/base/out',()=>{
 assert.equal(argumentsFor(['--base','https://example.invalid/','--out','out','--phase','before','--targets','prior.json']).targets,'prior.json');
 for(const args of [['--targets','prior.json'],['--base','x','--out','out','--phase','after','--targets','a','--targets','b'],['--base','x','--out','out','--phase','after','--unknown','yes']])assert.throws(()=>argumentsFor(args));
});

test('heater-face text must be inset on an opaque face clear of platform and beams',()=>{const m=drawingMetrics(),d=m.reported_drawings[0];d.chamber_heater_overlay_count=1;d.chamber_heater_fronts=[{bounds:rect(160,220,80,25),fully_opaque:true,leaf_labels:[label(177,224)],holder_platform_bounds:rect(150,190,100,10),beam_bounds:[rect(190,120,0,60)]}];checkReportedDrawing('after',m);for(const change of ['border','transparent','platform','beam']){const x=structuredClone(m),f=x.reported_drawings[0].chamber_heater_fronts[0];if(change==='border')f.leaf_labels[0].text_bounds=rect(177,221,40,16);if(change==='transparent')f.fully_opaque=false;if(change==='platform')f.holder_platform_bounds=rect(150,220,100,10);if(change==='beam')f.beam_bounds=[rect(195,210,2,30)];assert.throws(()=>checkReportedDrawing('after',x),/heater|Heater/);}checkReportedDrawing('before',{renderer:'reported-fields'});});

test('legacy transparent chamber heater overlay cannot pass after but remains capturable before',()=>{const m=drawingMetrics();m.reported_drawings[0].chamber_heater_overlay_count=1;assert.throws(()=>checkReportedDrawing('after',m),/opaque inset front/);checkReportedDrawing('before',m);});


const fakeDiagnosticPage = () => {
  const handlers = new Map();
  return { handlers, on(name, callback) { handlers.set(name, callback); } };
};
test('failure diagnostic URLs remove credentials queries hashes and non-HTTP payloads', () => {
  assert.equal(safeDiagnosticURL('https://user:password@example.test/a.js?token=secret#fragment'), 'https://example.test/a.js');
  assert.equal(safeDiagnosticURL('http://127.0.0.1:8173/a.js?v=123'), 'http://127.0.0.1:8173/a.js');
  assert.equal(safeDiagnosticURL('data:text/html,secret'), '[non-http-url]');
  assert.equal(safeDiagnosticURL('not a URL'), '[invalid-url]');
  assert.equal(safeDiagnosticURL('https://example.test/' + 'a'.repeat(500)).length, 240);
  const text = safeDiagnosticText('failed https://u:password@example.test/a.js?token=secret#fragment /b.js?token=secret#fragment');
  assert(!/password|token|secret|fragment|\?/.test(text));
  assert.equal(safeDiagnosticText('x'.repeat(500)).length, 240);
});
test('passive failure evidence caps each event class and records omitted entries', () => {
  const page = fakeDiagnosticPage(), evidence = registerFailureDiagnostics(page);
  for (let i = 0; i < 25; i++) {
    page.handlers.get('requestfailed')({ url: () => 'https://u:p@example.test/a.js?secret=1#x', resourceType: () => 'script', failure: () => ({ errorText: 'net::ERR_FAILED' }) });
    page.handlers.get('response')({ url: () => 'https://example.test/a.js?secret=1', status: () => 503, request: () => ({ resourceType: () => 'script' }) });
    page.handlers.get('console')({ type: () => 'error', text: () => 'Error loading https://u:p@example.test/a.js?secret=1' });
  }
  page.handlers.get('response')({ status: () => 200 });
  page.handlers.get('console')({ type: () => 'info' });
  for (const key of ['request_failures', 'non_2xx_responses', 'console_errors']) {
    assert.equal(evidence[key].length, 20); assert.equal(evidence.omitted[key], 5);
  }
  assert(!JSON.stringify(evidence).includes('secret'));
  page.handlers.get('requestfailed')({ url: () => { throw new TypeError('secret'); } });
  assert.deepEqual(evidence.collection_errors, [{ stage: 'requestfailed', error_class: 'TypeError' }]);
});
test('structural readiness contains markers and counts without body or script text', () => {
  const oldDocument = globalThis.document, oldPerformance = globalThis.performance;
  const marker = { getAttribute: () => 'record-id', get innerText() { throw Error('No text reads'); } };
  try {
    globalThis.document = { readyState: 'interactive', scripts: [{ src: '/a.js', type: 'module' }, { src: '', type: '' }],
      querySelector: (s) => s === 'main[data-reader-ready]' ? marker : s === 'main' ? {} : null,
      querySelectorAll: () => ({ length: 3 }), get body() { throw Error('No body reads'); } };
    globalThis.performance = { getEntriesByType: () => [{ initiatorType: 'script' }, { initiatorType: 'fetch' }] };
    const result = structuralReadinessSummary();
    assert.equal(result.reader_marker_value, 'record-id'); assert.equal(result.script_count, 2);
    assert.equal(result.external_script_count, 1); assert.equal(result.module_script_count, 1);
    assert.equal(result.protocol_button_count, 3); assert.equal(result.resource_counts.fetch, 1);
    assert(!Object.hasOwn(result, 'text') && !Object.hasOwn(result, 'body'));
  } finally { globalThis.document = oldDocument; globalThis.performance = oldPerformance; }
});
test('diagnostic collection errors are separate and never replace original failure evidence', async () => {
  const page = fakeDiagnosticPage(), evidence = registerFailureDiagnostics(page);
  page.evaluate = async () => { throw new TypeError('evaluation failed'); };
  page.screenshot = async () => { throw new Error('screenshot failed'); };
  const result = await collectFailureDiagnostics(page, evidence, '/unused', 'target-1440');
  assert.deepEqual(result.collection_errors, [{ stage: 'structural-readiness', error_class: 'TypeError' }, { stage: 'failure-screenshot', error_class: 'Error' }]);
});
test('best-effort failure screenshot has its own exact receipt without replacing normal screenshots', async () => {
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'protocol-failure-test-'));
  try {
    const page = fakeDiagnosticPage(), evidence = registerFailureDiagnostics(page);
    page.evaluate = async () => ({ document_ready_state: 'complete', reader_marker_present: false });
    page.screenshot = async ({ path: destination, timeout }) => { assert.equal(timeout, 5000); fs.writeFileSync(destination, 'synthetic image fixture'); };
    const result = await collectFailureDiagnostics(page, evidence, out, 'target-1440');
    assert.equal(result.screenshot.file, 'target-1440-failure-viewport.png');
    assert.equal(result.screenshot.bytes, Buffer.byteLength('synthetic image fixture'));
    assert.equal(result.screenshot.sha256.length, 64); assert.deepEqual(result.collection_errors, []);
  } finally { assert.equal(path.dirname(out), path.resolve(os.tmpdir())); fs.rmSync(out, { recursive: true }); }
});
test('unsafe diagnostic screenshot names cannot write outside capture output', async () => {
  const page = fakeDiagnosticPage(), evidence = registerFailureDiagnostics(page);
  page.evaluate = async () => ({}); page.screenshot = async () => { throw new Error('must not run'); };
  const result = await collectFailureDiagnostics(page, evidence, '/unused', '../escape');
  assert.equal(result.screenshot, undefined); assert.equal(result.collection_errors[0].stage, 'failure-screenshot');
});
test('actual visit retains HTTP200 readiness timeout and failure despite diagnostic failures', async () => {
  const page = fakeDiagnosticPage(), seen = [], originalError = new Error('Original readiness timeout'); let closed = false;
  page.goto = async (url, options) => { seen.push(['goto', options.timeout]); return { status: () => 200 }; };
  page.waitForSelector = async (selector, options) => { seen.push([selector, options.timeout]); throw originalError; };
  page.evaluate = async () => { throw new Error('diagnostic evaluation'); };
  page.screenshot = async () => { throw new Error('diagnostic screenshot'); };
  const context = { newPage: async () => page, close: async () => { closed = true; } };
  const browser = { newContext: async () => context };
  const row = await visit(browser, 'https://cuiyist.github.io/mattersyn-site/', '/unused', 'before', original.targets[0], VIEWPORTS[0]);
  assert.equal(row.status, 200); assert.equal(row.automated_checks_passed, false);
  assert.equal(row.error, originalError.message); assert.deepEqual(row.page_errors, []); assert.equal(closed, true);
  assert.deepEqual(seen, [['goto', 90000], ['main[data-reader-ready]', 60000]]);
  assert.equal(row.failure_diagnostics.collection_errors.length, 2);
});


test('legacy schema requires exactly18; K requires exactly20 and preserves all original18 objects',()=>{
 const legacy={schema:LEGACY_TARGET_SCHEMA,targets:structuredClone(original.targets.slice(0,18))};
 assert.equal(validateTargets(legacy).length,18);assert.equal(validateTargets(copy()).length,20);
 assert.deepEqual(original.targets.slice(0,18),legacy.targets);
 for(const [schema,count]of [[LEGACY_TARGET_SCHEMA,20],[TARGET_SCHEMA,18],['unknown',20]]){const x=copy();x.schema=schema;x.targets=x.targets.slice(0,count);assert.throws(()=>validateTargets(x));}
});
test('both K regressions retain exact material method operation and raw record pins',()=>{
 assert.deepEqual(original.targets.slice(18),K_REGRESSION_TARGETS);
 assert.deepEqual(K_REGRESSION_TARGETS.map(x=>[x.record_id,x.operation_index,x.operation_id]),[
 ['talapin2002-ja0123599-inas-nanocrystals-3',3,'s04-inject'],['zhu-ja210312s-cdse-core',6,'inject']]);
 for(const field of ['record_id','operation_id','operation_index','operation_label','record_json_bytes','record_json_sha256','route']){const x=copy();x.targets[18][field]=typeof x.targets[18][field]==='number'?x.targets[18][field]+1:x.targets[18][field]+'x';assert.throws(()=>validateTargets(x));}
});
test('before conversion refuses absent or changed base raw records before any browser can run',()=>{
 const legacy={schema:LEGACY_TARGET_SCHEMA,targets:structuredClone(original.targets.slice(0,18))};
 assert.throws(()=>beforeTargetsFromBaseSnapshot(legacy,{}));
 const rows=Object.fromEntries(K_REGRESSION_TARGETS.map(x=>[x.record_id,Buffer.from('{}')]));
 assert.throws(()=>beforeTargetsFromBaseSnapshot(legacy,rows));
});
function recordMetricRows(scales=[0.8,0.8],height=300){
 return scales.map((scale,index)=>{const metrics=drawingMetrics();Object.assign(metrics.reported_drawings[0],{bounds:rect(0,0,390,300),apparatus_bounds:rect(8,80,374,210),svg_bounds:rect(8,80,374,210)});metrics.protocol_frame={bounds:rect(0,0,390,height),scroll_width:390,client_width:390,scroll_height:height,client_height:height};Object.assign(metrics.reported_drawings[0],{actual_body_scale:{x:scale,y:scale},declared_record_geometry_scale:scale,declared_svg_geometry_scale:scale});return{operation_index:index,operation_id:'step-'+index,below_image_note_count:1,enlarge_count:1,metrics};});
}
test('all-operation drawing frame enforces400desktop/320phone and no scroll-clipping excess',()=>{
 checkRecordOperationMetrics('after',recordMetricRows([0.8,0.8],400),{width:1440});
 checkRecordOperationMetrics('after',recordMetricRows([0.8,0.8],320),{width:390});
 assert.throws(()=>checkRecordOperationMetrics('after',recordMetricRows([0.8],400.51),{width:1440}),/400px/);
 assert.throws(()=>checkRecordOperationMetrics('after',recordMetricRows([0.8],320.51),{width:390}),/320px/);
 for(const field of ['scroll_height','scroll_width']){const rows=recordMetricRows();rows[0].metrics.protocol_frame[field]+=2;assert.throws(()=>checkRecordOperationMetrics('after',rows,{width:390}),/scrolling|clipped/);}
 const missing=recordMetricRows();delete missing[0].metrics.protocol_frame;assert.throws(()=>checkRecordOperationMetrics('after',missing,{width:390}),/frame/);
 const wrongOrder=recordMetricRows();wrongOrder[1].operation_index=0;assert.throws(()=>checkRecordOperationMetrics('after',wrongOrder,{width:390}),/record order/);
 checkRecordOperationMetrics('before',[],{width:390});
});
test('same-scale checks actual CTM at every operation rather than trusting declared scale metadata',()=>{
 checkRecordOperationMetrics('after',recordMetricRows(),{width:390});
 assert.throws(()=>checkRecordOperationMetrics('after',recordMetricRows([0.8,0.7]),{width:390}),/same actual geometry scale/);
 for(const field of ['declared_record_geometry_scale','declared_svg_geometry_scale']){const rows=recordMetricRows();rows[0].metrics.reported_drawings[0][field]=1;assert.throws(()=>checkRecordOperationMetrics('after',rows,{width:390}),/actual screen/);}
 const skewed=recordMetricRows();skewed[0].metrics.reported_drawings[0].actual_body_scale.y=0.7;assert.throws(()=>checkRecordOperationMetrics('after',skewed,{width:390}),/uniformly/);
 const noActual=recordMetricRows();delete noActual[0].metrics.reported_drawings[0].actual_body_scale;assert.throws(()=>checkRecordOperationMetrics('after',noActual,{width:390}),/getScreenCTM/);
 const lateTiny=recordMetricRows();lateTiny[1].metrics.reported_drawings[0].leaf_labels[0].screen_font_px=11.9;assert.throws(()=>checkRecordOperationMetrics('after',lateTiny,{width:390}),/below12/);
});


test('Talapin adds1024x768 without losing any of the40 standard K views',()=>{
 const rows=validateTargets(copy());assert.equal(rows.reduce((n,t)=>n+viewportsForTarget(t).length,0),41);
 assert.deepEqual(viewportsForTarget(rows.find(t=>t.id==='extra-inas-talapin2002-injection')).map(v=>[v.width,v.height]),[[1440,900],[390,844],[1024,768]]);
 for(const row of rows.filter(t=>t.id!=='extra-inas-talapin2002-injection'))assert.deepEqual(viewportsForTarget(row),VIEWPORTS);
});


test('every measured operation retains one common caption and Enlarge control',()=>{
 for(const field of ['below_image_note_count','enlarge_count'])for(const value of [0,2]){const rows=recordMetricRows();rows[1][field]=value;assert.throws(()=>checkRecordOperationMetrics('after',rows,{width:390}),/caption|Enlarge/);}
});


test('annotation leaders remain clipped to their own full-width overlay and complete drawing',()=>{
 const m=drawingMetrics(),d=m.reported_drawings[0];d.annotation_overlay_geometry=[{bounds:rect(5,10,0,40),svg_bounds:rect(0,0,400,300)}];checkReportedDrawing('after',m);
 d.annotation_overlay_geometry[0].bounds=rect(-1,10,20,40);assert.throws(()=>checkReportedDrawing('after',m),/own annotation overlay/);
 d.annotation_overlay_geometry[0]={bounds:rect(5,10,0,40),svg_bounds:rect(-1,0,400,300)};assert.throws(()=>checkReportedDrawing('after',m),/inside the drawing/);
});
test('protected artwork fit uses actual displayed/native ratio and every step stays within the common frame',()=>{
 const native=recordMetricRows();for(const row of native){row.metrics.reported_drawings=[];row.metrics.renderer='per-paper';row.metrics.inline_svg_count=1;Object.assign(row.metrics.protocol_frame,{declared_record_geometry_scale:0.8,native_width:300,native_height:250,native_bounds:rect(20,20,240,200)});}
 checkRecordOperationMetrics('after',native,{width:390});
 const clipped=structuredClone(native);clipped[1].metrics.protocol_frame.native_bounds.left=-1;assert.throws(()=>checkRecordOperationMetrics('after',clipped,{width:390}),/fully visible/);
 const drift=structuredClone(native);Object.assign(drift[1].metrics.protocol_frame,{native_bounds:rect(20,20,210,175),declared_record_geometry_scale:0.7});assert.throws(()=>checkRecordOperationMetrics('after',drift,{width:390}),/same actual geometry scale/);
 const missing=structuredClone(native);delete missing[0].metrics.protocol_frame.native_width;assert.throws(()=>checkRecordOperationMetrics('after',missing,{width:390}),/Native dimensions/);
 const large=recordMetricRows();large[0].metrics.reported_drawings[0].bounds=rect(0,-1,400,300);assert.throws(()=>checkRecordOperationMetrics('after',large,{width:390}),/complete reported drawing/);
});


test('legacy transform phantom scroll extents require hidden non-scrolling frame and actual containment',()=>{
 const rows=recordMetricRows([0.8]);rows[0].metrics.reported_drawings=[];rows[0].metrics.renderer='per-paper';rows[0].metrics.inline_svg_count=1;Object.assign(rows[0].metrics.protocol_frame,{declared_record_geometry_scale:0.8,native_width:300,native_height:250,native_bounds:rect(20,20,240,200),scroll_width:500,scroll_height:500,overflow_x:'hidden',overflow_y:'hidden'});
 checkRecordOperationMetrics('after',rows,{width:390});
 for(const value of ['auto','scroll','visible']){const x=structuredClone(rows);x[0].metrics.protocol_frame.overflow_y=value;assert.throws(()=>checkRecordOperationMetrics('after',x,{width:390}),/scroll|clipped/);}
 const clipped=structuredClone(rows);clipped[0].metrics.protocol_frame.native_bounds=rect(20,20,500,200);assert.throws(()=>checkRecordOperationMetrics('after',clipped,{width:390}),/fully visible/);
 const shared=recordMetricRows([0.8]);Object.assign(shared[0].metrics.protocol_frame,{scroll_height:500,overflow_y:'hidden'});assert.throws(()=>checkRecordOperationMetrics('after',shared,{width:390}),/clipped excess/);
});


test('actual-browser fixture matrix covers every reported kind six injection openings and condition toggles',()=>{
 const rows=sceneFixtureMatrix();assert.equal(rows.length,22);assert.equal(new Set(rows.map(r=>r.id)).size,22);
 assert.deepEqual(rows.filter(r=>r.id.startsWith('kind-')).map(r=>r.spec.kind),REPORTED_SCENE_KINDS);
 assert.deepEqual(rows.filter(r=>r.id.startsWith('vessel-')).map(r=>r.spec.vesselKind),VESSEL_VARIANTS);
 assert(rows.filter(r=>r.spec.kind==='inject').every(r=>r.spec.added.length===3));
 assert.equal(rows.find(r=>r.id==='kind-chamber').spec.beamSystem,true);assert.equal(rows.find(r=>r.id==='chamber-feed').spec.beamSystem,false);
 const off=rows.find(r=>r.id==='unheated-no-gas-no-stir');assert.deepEqual([off.spec.heating,off.spec.gasLine,off.spec.stirring],[false,false,false]);assert.deepEqual(off.conditions,[]);
});


test('heater guard keeps bounded numeric-only failure geometry without weakening containment',()=>{
 const m=drawingMetrics(),d=m.reported_drawings[0];Object.assign(d,{chamber_heater_overlay_count:1,actual_body_scale:{x:0.7,y:0.7},declared_record_geometry_scale:0.7,declared_svg_geometry_scale:0.7});d.chamber_heater_fronts=[{bounds:rect(-1,220,80,25),fully_opaque:true,leaf_labels:[label(10,224)],holder_platform_bounds:rect(150,190,100,10),beam_bounds:[]}];
 assert.throws(()=>checkReportedDrawing('after',m),error=>{assert.match(error.message,/heater front must stay inside/);const detail=error.message.split('geometry=')[1];assert(detail.length<=1600);const value=JSON.parse(detail);assert.equal(value.front.left,-1);assert.equal(value.svg.left,8);assert.equal(value.holder.top,190);assert.deepEqual(value.actual_scale,{x:0.7,y:0.7});assert(!/text|quote|source/.test(detail));return true;});
});


test('all-operation probe waits for loaded native images and preserves timeout without retry',async()=>{
 const calls=[];let imageFailure=false;
 const page={locator(selector){if(selector.includes('step-list'))return{count:async()=>1,nth:()=>({click:async()=>calls.push('click')})};return{count:async()=>1,filter(){return this;},evaluate:async()=>({renderer:'per-paper'})};},
 async waitForFunction(fn,arg,options){assert.equal(options.timeout,30000);if(fn.toString().includes('naturalWidth')){calls.push('images');if(imageFailure)throw Error('Image readiness timeout');}else calls.push('heading');},async evaluate(){calls.push('frames');}};
 const record={operations:[{id:'one',label:'One'}]};const rows=await collectRecordOperationMetrics(page,record);assert.equal(rows.length,1);assert.deepEqual(calls,['click','heading','images','frames']);
 calls.length=0;imageFailure=true;await assert.rejects(collectRecordOperationMetrics(page,record),/Image readiness timeout/);assert.deepEqual(calls,['click','heading','images']);
});


test('standalone furnace is a separate width-limited310px phone record while all22x4 fixtures remain',()=>{
 const cases=VIEWPORTS.flatMap(viewport=>fixtureRecordCases(viewport).map(record=>({viewport,...record})));
 assert.deepEqual(cases.filter(c=>!c.standalone).map(c=>[c.viewport.width,c.container_width]),[[1440,560],[1440,280],[390,342],[390,280]]);
 assert.deepEqual(cases.filter(c=>c.standalone).map(c=>[c.viewport.width,c.viewport.height,c.container_width]),[[390,844,310]]);
 const furnace=standaloneWidthLimitedFurnace();assert.equal(furnace.spec.kind,'furnace');assert.equal(furnace.spec.heating,true);assert.deepEqual(furnace.spec.added,[]);assert.equal(furnace.conditions.length,1);assert.equal(furnace.conditions[0].key,'temperature');
 assert.equal(sceneFixtureMatrix().length*cases.filter(c=>!c.standalone).length+cases.filter(c=>c.standalone).length,89);
});
