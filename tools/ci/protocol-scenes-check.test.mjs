import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { validateTargets, targetURL, checkAfterLabels, checkReportedDrawing, fontMetrics, VIEWPORTS, argumentsFor } from './protocol-scenes-check.mjs';

const original = JSON.parse(fs.readFileSync(new URL('./protocol-scenes-targets.json', import.meta.url), 'utf8'));
const copy = () => structuredClone(original);

test('fixed public target set has ten actual defaults, five named examples and three explicit step1 views', () => {
  const rows = validateTargets(copy());
  assert.equal(rows.length, 18);
  assert.equal(rows.filter((row) => row.group === 'benchmark-default').length, 10);
  assert.equal(rows.filter((row) => row.group === 'route-example').length, 5);
  assert.equal(rows.filter((row) => row.group === 'reader-e-step1').length, 3);
  assert.deepEqual(VIEWPORTS.map((row) => row.width), [1440, 390]);
  assert.equal(rows.length * VIEWPORTS.length * 2, 72);
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
  assert.equal(validateTargets(duplicate).length,18);
  for(const mutate of [x=>{x.targets[15].record_json_sha256='0'.repeat(64);},x=>{x.targets[15].record_json_bytes++;},x=>{x.targets[15].operation_label+=' altered';},x=>{x.targets[16].record_id=extra.record_id;}]){const value=structuredClone(duplicate);mutate(value);assert.throws(()=>validateTargets(value));}
});

test('all three extra views are the exact first operation on their explicit material/record route', () => {
  const extras = original.targets.slice(15);
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

test('G drawings keep a full-width centered apparatus with plain connected labels', () => {
  for (const [mutate, message] of [
    [(d) => { d.layout = 'corner-boxes'; }, /leader-label/],
    [(d) => { d.apparatus_bounds = rect(60, 80, 280, 210); }, /drawing width/],
    [(d) => { d.apparatus_bounds = rect(0, 80, 370, 210); }, /centered/],
    [(d) => { d.svg_bounds = rect(100, 80, 200, 210); }, /fill its panel/],
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

test('actual vessel geometry must fill the drawing even when wrapper and SVG are full width',()=>{const m=drawingMetrics();m.reported_drawings[0].apparatus_body_bounds=rect(140,90,114,180);assert.throws(()=>checkReportedDrawing('after',m),/actual apparatus body must occupy/);const b=drawingMetrics();b.reported_drawings[0].apparatus_body_svg_bbox=rect(95,10,114,180);assert.throws(()=>checkReportedDrawing('after',b),/SVG body geometry/);});
test('visible body and zero-width or zero-height leader appendages stay inside SVG',()=>{const m=drawingMetrics();m.reported_drawings[0].appendage_geometry_bounds=[rect(20,90,0,50),rect(30,100,50,0)];checkReportedDrawing('after',m);m.reported_drawings[0].appendage_geometry_bounds.push(rect(-1,90,20,40));assert.throws(()=>checkReportedDrawing('after',m),/visible syringe/);const b=drawingMetrics();b.reported_drawings[0].apparatus_body_bounds=rect(0,90,320,180);assert.throws(()=>checkReportedDrawing('after',b),/must not clip/);});
test('font metrics measure actual SVG body bbox and viewBox rather than its wrapper',()=>withMetricDOM(()=>{const{art}=metricFixture(),d=fontMetrics(art).reported_drawings[0];assert.equal(d.apparatus_body_bounds.width,320);assert.equal(d.apparatus_body_svg_bbox.width,250);assert.equal(d.svg_viewbox.width,300);assert.deepEqual(d.appendage_geometry_bounds,[]);}));

test('before named-Wu default duplicate and after snapshot each keep18 IDs with changed defaults',()=>{
 const before=copy();
 const beforeDefault=before.targets.find(t=>t.id==='default-gaas');
 const namedWu=before.targets.find(t=>t.id==='extra-gaas-wu2010-step1');
 for(const key of ['record_id','operation_id','operation_index','operation_label','record_json_sha256','record_json_bytes'])beforeDefault[key]=namedWu[key];
 assert.equal(validateTargets(before).length,18);assert.equal(new Set(before.targets.map(t=>t.record_id)).size,17);
 assert.equal(validateTargets(copy()).length,18);assert.equal(new Set(original.targets.map(t=>t.record_id)).size,18);
 assert.notEqual(beforeDefault.record_id,original.targets.find(t=>t.id==='default-gaas').record_id);
});
test('explicit target snapshot CLI option preserves required phase/base/out',()=>{
 assert.equal(argumentsFor(['--base','https://example.invalid/','--out','out','--phase','before','--targets','prior.json']).targets,'prior.json');
 for(const args of [['--targets','prior.json'],['--base','x','--out','out','--phase','after','--targets','a','--targets','b'],['--base','x','--out','out','--phase','after','--unknown','yes']])assert.throws(()=>argumentsFor(args));
});

test('heater-face text must be inset on an opaque face clear of platform and beams',()=>{const m=drawingMetrics(),d=m.reported_drawings[0];d.chamber_heater_overlay_count=1;d.chamber_heater_fronts=[{bounds:rect(160,220,80,25),fully_opaque:true,leaf_labels:[label(177,224)],holder_platform_bounds:rect(150,190,100,10),beam_bounds:[rect(190,120,0,60)]}];checkReportedDrawing('after',m);for(const change of ['border','transparent','platform','beam']){const x=structuredClone(m),f=x.reported_drawings[0].chamber_heater_fronts[0];if(change==='border')f.leaf_labels[0].text_bounds=rect(177,221,40,16);if(change==='transparent')f.fully_opaque=false;if(change==='platform')f.holder_platform_bounds=rect(150,220,100,10);if(change==='beam')f.beam_bounds=[rect(195,210,2,30)];assert.throws(()=>checkReportedDrawing('after',x),/heater|Heater/);}checkReportedDrawing('before',{renderer:'reported-fields'});});

test('legacy transparent chamber heater overlay cannot pass after but remains capturable before',()=>{const m=drawingMetrics();m.reported_drawings[0].chamber_heater_overlay_count=1;assert.throws(()=>checkReportedDrawing('after',m),/opaque inset front/);checkReportedDrawing('before',m);});
