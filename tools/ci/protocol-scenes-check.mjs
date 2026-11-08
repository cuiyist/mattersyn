// Capture the same twenty selected protocol steps before and after a Reader change.
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

export const LEGACY_TARGET_SCHEMA = 'mattersyn-protocol-scenes-targets/1';
export const TARGET_SCHEMA = 'mattersyn-protocol-scenes-targets/2';
export const VIEWPORTS = Object.freeze([{ width: 1440, height: 900 }, { width: 390, height: 844 }]);
export const TALAPIN_VIEWPORT = Object.freeze({width:1024,height:768});
export const viewportsForTarget = target => target.id === 'extra-inas-talapin2002-injection' ? [...VIEWPORTS,TALAPIN_VIEWPORT] : VIEWPORTS;
export const BENCHMARK_FORMULAS = Object.freeze(['CdSe', 'CdS', 'ZnS', 'InAs', 'PbS', 'InP', 'Au', 'TiO2', 'GaAs', 'SnO2']);
const TARGET_FILE = fileURLToPath(new URL('./protocol-scenes-targets.json', import.meta.url));
const FIELDS = new Set(['id', 'group', 'formula', 'record_id', 'route', 'operation_index', 'operation_id', 'operation_label', 'record_json_bytes', 'record_json_sha256', 'minimum_label_px_after']);
const EXAMPLES = ['gaas-droplet', 'hot-injection', 'hydrothermal', 'sol-gel', 'solid-state'];
const STEP1_EXAMPLES = Object.freeze({
  'extra-gaas-wu2010-step1': { formula: 'GaAs', record_id: 'wu2010-nl100217k-gaas-quantum-dot-pairs-qdps-in-al0-3ga0-1', operation_id: 's01-grow', material_id: 'gaas-889234' },
  'extra-au-fan2006-step1': { formula: 'Au', record_id: 'fan2006-b600923a-ordered-gold-nanocrystal-silica-particle-1', operation_id: 's01-prepare', material_id: 'au-3325c2' },
  'extra-pbs-reinhart2017-step1': { formula: 'PbS', record_id: 'reinhart2017-jacs-7b00158-3-mercaptopropionic-acid-3-mpa-capped-pb-1', operation_id: 's01-add', material_id: 'pbs-7e1774' },
});
export const K_REGRESSION_TARGETS = Object.freeze([
  {
    "id": "extra-inas-talapin2002-injection",
    "group": "reader-k-size",
    "formula": "InAs",
    "record_id": "talapin2002-ja0123599-inas-nanocrystals-3",
    "route": "material.html?id=inas-a2e691&method=talapin2002-ja0123599-inas-nanocrystals-3",
    "operation_index": 3,
    "operation_id": "s04-inject",
    "operation_label": "Inject InCl3-TMS3As solution into TOP",
    "record_json_bytes": 15856,
    "record_json_sha256": "4c60778816907eab34c4d990d72275ba6454e37ea2bc56e9c3dfea28eab21d0f",
    "minimum_label_px_after": 12
  },
  {
    "id": "extra-cdse-zhu2011-injection",
    "group": "reader-k-size",
    "formula": "CdSe",
    "record_id": "zhu-ja210312s-cdse-core",
    "route": "material.html?id=cdse-d923c5&method=zhu-ja210312s-cdse-core",
    "operation_index": 6,
    "operation_id": "inject",
    "operation_label": "Swiftly inject selenium stock",
    "record_json_bytes": 30936,
    "record_json_sha256": "a7eb84e375ea1c0825709c4649e6482a3b279fcf80a4c67ab953aa4bc656b24e",
    "minimum_label_px_after": 12
  }
].map(Object.freeze));
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const nonempty = (value) => typeof value === 'string' && value.trim().length > 0 && !/[\r\n\0]/.test(value);

export function validateTargets(value) {
  assert(value && typeof value === 'object' && !Array.isArray(value));
  assert.deepEqual(Object.keys(value).sort(), ['schema', 'targets']);
  const count = value.schema === LEGACY_TARGET_SCHEMA ? 18 : value.schema === TARGET_SCHEMA ? 20 : null;
  assert(count !== null, 'Exact protocol target schema required');
  assert(Array.isArray(value.targets) && value.targets.length === count, 'Exact eighteen legacy or twenty K protocol targets are required');
  const ids = new Set();
  const records = new Map();
  const defaults = [];
  const examples = [];
  const step1Examples = [];
  const sizeExamples = [];
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
    } else if (target.group === 'reader-k-size') {
      const expected = K_REGRESSION_TARGETS.find(row => row.id === target.id);
      assert(expected, 'Only the two exact K regression targets are admitted');
      assert.deepEqual(target, expected, 'K regression record, operation, route and raw record pins are fixed');
      sizeExamples.push(target.id);
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
  assert.deepEqual(sizeExamples, count === 20 ? K_REGRESSION_TARGETS.map(row => row.id) : []);
  assert.equal(records.size,count-Number(namedWuDuplicate),'Only the named Wu pair may share a record when that phase default is Wu');
  return value.targets;
}

// Preserve every exact comparison-base target. The only additions to a legacy
// eighteen-target snapshot are these two literal regressions, verified against
// comparison-base canonical record bytes before a browser is started.
export function beforeTargetsFromBaseSnapshot(snapshot, baseRecordBytes) {
  const prior = validateTargets(snapshot);
  const records = baseRecordBytes || {};
  assert.deepEqual(Object.keys(records).sort(), K_REGRESSION_TARGETS.map(t => t.record_id).sort(), 'Two exact comparison-base record byte inputs required');
  for (const target of K_REGRESSION_TARGETS) {
    const raw = records[target.record_id];
    assert(Buffer.isBuffer(raw) || raw instanceof Uint8Array, 'Raw comparison-base record bytes required');
    assert.equal(raw.length, target.record_json_bytes);
    assert.equal(sha256(raw), target.record_json_sha256, 'K regression record differs from comparison-base raw pin');
    const record = JSON.parse(Buffer.from(raw).toString('utf8'));
    assert.equal(record.record_id, target.record_id);
    assert.equal(record.operations?.[target.operation_index]?.id, target.operation_id);
    assert.equal(record.operations?.[target.operation_index]?.label, target.operation_label);
  }
  const value = {schema: TARGET_SCHEMA, targets: structuredClone(prior)};
  if (snapshot.schema === LEGACY_TARGET_SCHEMA) value.targets.push(...structuredClone(K_REGRESSION_TARGETS));
  validateTargets(value);
  assert.deepEqual(value.targets.slice(0,18), snapshot.targets.slice(0,18), 'All original eighteen target objects must be preserved');
  return value;
}

export const REPORTED_SCENE_KINDS = Object.freeze(['solution','inject','cool','degas','reflux','chamber','closed-reactor','furnace','centrifuge','filter','workup-tube','dry-tube','mill-jar','mortar-pestle']);
export const VESSEL_VARIANTS = Object.freeze(['plain','flask','three-neck-flask','tube','vial','beaker']);
export function sceneFixtureMatrix() {
  const conditions=[{key:'temperature',value:'270 °C',shortValue:'270 °C'},{key:'duration',value:'30 min'}];
  const common={vesselKind:'three-neck-flask',added:['Cadmium acetate dihydrate','Tris(trimethylsilyl)arsine','Trioctylphosphine oxide'],environment:'Nitrogen',gasLine:true,heating:true,stirring:true};
  const rows=REPORTED_SCENE_KINDS.map(kind=>({id:'kind-'+kind,spec:{...common,kind},conditions:structuredClone(conditions)}));
  for(const row of rows){
    if(['mortar-pestle','mill-jar'].includes(row.spec.kind)){Object.assign(row.spec,{added:['Reported dry powder A','Reported dry powder B'],gasLine:false,environment:'',heating:false,stirring:false});row.conditions=[{key:'duration',value:'30 min'}];}
    else if(row.spec.kind==='furnace'){Object.assign(row.spec,{added:[],gasLine:false,environment:'',stirring:false});}
    else if(row.spec.kind==='centrifuge'){Object.assign(row.spec,{added:[],gasLine:false,environment:'',heating:false,stirring:false});row.conditions=[{key:'duration',value:'10 min'}];}
    else if(row.spec.kind==='filter'){Object.assign(row.spec,{added:['Reported suspension'],gasLine:false,environment:'',heating:false,stirring:false});row.conditions=[{key:'duration',value:'10 min'}];}
    else if(row.spec.kind==='cool')row.spec.heating=false;
  }
  const chamber=rows.find(r=>r.spec.kind==='chamber');Object.assign(chamber.spec,{added:['Ga','As2','As4'],environment:'Ar',beamSystem:true,substrates:['GaAs wafer']});
  chamber.conditions.push({key:'Ga flux',value:'1 unit'},{key:'As2 flux',value:'2 units'},{key:'As4 flux',value:'3 units'});
  for(const vesselKind of VESSEL_VARIANTS)rows.push({id:'vessel-'+vesselKind,spec:{...common,kind:'inject',vesselKind},conditions:structuredClone(conditions)});
  rows.push({id:'chamber-feed',spec:{...structuredClone(chamber.spec),beamSystem:false},conditions:structuredClone(chamber.conditions)});
  rows.push({id:'unheated-no-gas-no-stir',spec:{...common,kind:'solution',gasLine:false,environment:'',heating:false,stirring:false},conditions:[]});
  return rows;
}

// A separate one-operation record must exercise width fit: the22-scene record
// is height-limited and cannot reveal a missing inner-panel horizontal inset.
export function standaloneWidthLimitedFurnace() {
  return {id:'single-furnace-width-limited',spec:{kind:'furnace',vesselKind:'plain',added:[],environment:'',gasLine:false,heating:true,stirring:false},
    conditions:[{key:'temperature',value:'800 °C',shortValue:'800 °C'}]};
}
export function fixtureRecordCases(viewport) {
  const cases=[{container_width:Math.min(560,viewport.width-48),standalone:false},{container_width:280,standalone:false}];
  if(viewport.width===390)cases.push({container_width:310,standalone:true});
  return cases;
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
  // K1 fits geometry to the first exhausted width or height; the SVG may
  // therefore be narrower than its full-width centered label panel.
  assert(Math.abs(center(drawing.svg_bounds) - center(drawing.apparatus_bounds)) <= 8, 'The fitted apparatus SVG must be centered');
  assert(inside(drawing.apparatus_body_bounds, drawing.svg_bounds), 'The actual apparatus body must not clip its SVG');
  // Apparatus-to-card width is intentionally not fixed: a tall record uses
  // the same height-limited geometry scale for every step (K1).
  assert(rectangle(drawing.apparatus_body_svg_bbox) && drawing.apparatus_body_svg_bbox.width >= drawing.svg_viewbox.width * 0.70, 'SVG body geometry must fill its viewBox');
  assert(Array.isArray(drawing.appendage_geometry_bounds), 'Visible appendage measurements are required');
  for (const r of drawing.appendage_geometry_bounds) {
    assert(r && ['left','top','right','bottom','width','height'].every((key) => Number.isFinite(r[key]))
      && r.width >= 0 && r.height >= 0 && (r.width > 0 || r.height > 0)
      && r.left >= drawing.svg_bounds.left - epsilon && r.top >= drawing.svg_bounds.top - epsilon
      && r.right <= drawing.svg_bounds.right + epsilon && r.bottom <= drawing.svg_bounds.bottom + epsilon,
    'A visible syringe, cooling arrow, condenser or leader clips its SVG');
  }
  for (const leader of drawing.annotation_overlay_geometry || []) {
    const r=leader.bounds,outer=leader.svg_bounds;
    assert(r && ['left','top','right','bottom','width','height'].every(k=>Number.isFinite(r[k])) && r.width>=0 && r.height>=0 && (r.width>0||r.height>0), 'Overlay leader geometry must be measurable');
    assert(rectangle(outer) && r.left>=outer.left-epsilon && r.top>=outer.top-epsilon && r.right<=outer.right+epsilon && r.bottom<=outer.bottom+epsilon,'A visible leader clips its own annotation overlay');
    assert(inside(outer,drawing.bounds),'Annotation overlay must stay inside the drawing');
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
  const heaterDiagnostic = front => {
    const number=value=>Number.isFinite(value)?Math.round(value*1000)/1000:null;
    const rect=value=>value?Object.fromEntries(['left','top','right','bottom','width','height'].map(key=>[key,number(value[key])])):null;
    return JSON.stringify({front:rect(front.bounds),svg:rect(drawing.svg_bounds),holder:rect(front.holder_platform_bounds),drawing:rect(drawing.bounds),actual_scale:drawing.actual_body_scale?{x:number(drawing.actual_body_scale.x),y:number(drawing.actual_body_scale.y)}:null,declared_record_scale:number(drawing.declared_record_geometry_scale),declared_svg_scale:number(drawing.declared_svg_geometry_scale)}).slice(0,1600);
  };
  for (const front of drawing.chamber_heater_fronts) {
    assert(inside(front.bounds,drawing.svg_bounds), 'The heater front must stay inside the chamber drawing; geometry=' + heaterDiagnostic(front));
    assert(front.fully_opaque, 'The heater face must cover the old SVG rectangle behind its text');
    assert(Array.isArray(front.leaf_labels) && front.leaf_labels.length, 'The heater face needs measured text');
    for (const label of front.leaf_labels) {
      const t=label.text_bounds,b=front.bounds;
      assert(t.left >= b.left+2 && t.right <= b.right-2 && t.top >= b.top+2 && t.bottom <= b.bottom-2,
        'Heater text needs a clear inset from every visible heater-face border; geometry=' + heaterDiagnostic(front));
    }
    for (const other of [front.holder_platform_bounds,...front.beam_bounds].filter(Boolean)) {
      const a=front.bounds;
      assert(!(Math.min(a.right,other.right)-Math.max(a.left,other.left)>epsilon && Math.min(a.bottom,other.bottom)-Math.max(a.top,other.top)>epsilon),
        'The heater front must not obscure the holder platform or source beams; geometry=' + heaterDiagnostic(front));
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
    const svg = apparatus?.querySelector('svg[data-geometry-scale]') || apparatus?.querySelector('svg');
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
      declared_record_geometry_scale: drawing.dataset.recordGeometryScale ? Number(drawing.dataset.recordGeometryScale) : null,
      declared_svg_geometry_scale: svg?.dataset.geometryScale ? Number(svg.dataset.geometryScale) : null,
      actual_body_scale: (() => { const m = body?.getScreenCTM?.(); return m ? {x:Math.hypot(m.a,m.b),y:Math.hypot(m.c,m.d)} : null; })(),
      apparatus_body_svg_bbox: geometry ? {left:geometry.x,top:geometry.y,right:geometry.x+geometry.width,bottom:geometry.y+geometry.height,width:geometry.width,height:geometry.height} : null,
      svg_viewbox: viewbox ? {x:viewbox.x,y:viewbox.y,width:viewbox.width,height:viewbox.height} : null,
      appendage_geometry_bounds: appendages.map(bounds).filter(r=>r.width>0||r.height>0),
      annotation_overlay_geometry: [...drawing.querySelectorAll('svg[data-part="annotation-leaders"]')].flatMap(overlay=>[...overlay.querySelectorAll('path,line,polyline')].map(node=>({bounds:bounds(node),svg_bounds:bounds(overlay)}))),
      leader_line_count: [...drawing.querySelectorAll('[data-part="leader-line"] path,path[data-part="leader-line"]')].filter(node=>{const r=bounds(node);return r.width>0||r.height>0;}).length,
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
  const frame = art.closest?.('[data-protocol-art-frame]') || art.querySelector('[data-protocol-art-frame]');
  const nativeHost = frame?.querySelector('[data-protocol-native-art]');
  const frameMetrics = frame ? {bounds:bounds(frame),scroll_width:frame.scrollWidth,client_width:frame.clientWidth,scroll_height:frame.scrollHeight,client_height:frame.clientHeight,overflow_x:getComputedStyle(frame).overflowX,overflow_y:getComputedStyle(frame).overflowY,declared_record_geometry_scale:frame.dataset.recordGeometryScale?Number(frame.dataset.recordGeometryScale):null,native_width:frame.dataset.nativeArtWidth?Number(frame.dataset.nativeArtWidth):null,native_height:frame.dataset.nativeArtHeight?Number(frame.dataset.nativeArtHeight):null,native_bounds:nativeHost?bounds(nativeHost):null} : null;
  return { protocol_frame:frameMetrics, scene: art.dataset.scene || null, classes: art.className, external_image_count: art.querySelectorAll('img').length,
    inline_svg_count: art.querySelectorAll('svg').length, labels, minimum_measured_screen_font_px: sizes.length ? Math.min(...sizes) : null,
    renderer: art.dataset.renderer || null, reported_drawings: reportedDrawings };
}

// Every selected operation is measured at the real viewport, not inferred from
// a declared data attribute or a single screenshot. Native/per-paper artwork
// retains its existing font exemptions; reported G drawings keep all leaf-font,
// overlap, leader, clipping and heater checks above.
export function checkRecordOperationMetrics(phase, operations, viewport) {
  if (phase !== 'after') return;
  assert(Array.isArray(operations) && operations.length, 'All actual record operations require numeric metrics');
  const cap = viewport.width <= 700 ? 320 : 400;
  const scales = [];
  for (const [index,row] of operations.entries()) {
    assert.equal(row.operation_index,index,'All operations must be measured once in record order');
    assert.equal(row.below_image_note_count,1,'Every operation needs one common caption line');
    assert.equal(row.enlarge_count,1,'Every operation needs one Enlarge control');
    const metrics=row.metrics, frame=metrics?.protocol_frame;
    assert(frame && frame.bounds && Number.isFinite(frame.bounds.height) && frame.bounds.height>0, 'Every normal drawing requires a visible common art frame');
    assert(frame.bounds.height <= cap+0.5, `Drawing exceeds ${cap}px viewport height cap`);
    assert(frame.bounds.width>0 && frame.bounds.width<=viewport.width+0.5,'Drawing frame exceeds viewport width');
    for (const axis of ['width','height']) {
      assert(Number.isFinite(frame['scroll_'+axis]) && Number.isFinite(frame['client_'+axis]),'Drawing scroll dimensions are required');
      const overflow=frame['overflow_'+(axis==='width'?'x':'y')];
      assert(!['auto','scroll'].includes(overflow),'Drawing frame must have no user-scroll mechanism');
      if(frame['scroll_'+axis] > frame['client_'+axis]+1) {
        // CSS transforms retain untransformed scroll extents on protected native
        // artwork. The actual transformed host is independently bounded below.
        assert(!(metrics.reported_drawings || []).length && frame.native_bounds && ['hidden','clip'].includes(overflow),'Whole drawing must fit without internal scrolling or clipped excess');
      }
    }
    const insideFrame = bounds => bounds && ['left','right','top','bottom','width','height'].every(k=>Number.isFinite(bounds[k])) && bounds.width>0 && bounds.height>0 && bounds.left>=frame.bounds.left-0.5 && bounds.right<=frame.bounds.right+0.5 && bounds.top>=frame.bounds.top-0.5 && bounds.bottom<=frame.bounds.bottom+0.5;
    if (!(metrics.reported_drawings || []).length && (metrics.inline_svg_count>0 || metrics.external_image_count>0)) {
      assert(insideFrame(frame.native_bounds),'Protected native artwork must be fully visible inside its frame');
      assert(Number.isFinite(frame.native_width)&&frame.native_width>0 && Number.isFinite(frame.native_height)&&frame.native_height>0,'Native dimensions must be measured before fit');
      const x=frame.native_bounds.width/frame.native_width,y=frame.native_bounds.height/frame.native_height,declared=frame.declared_record_geometry_scale,tolerance=Math.max(0.001,x*0.005);
      assert(Number.isFinite(declared)&&declared>0 && Math.abs(x-y)<=tolerance && Math.abs(x-declared)<=tolerance,'Native artwork displayed/intrinsic scale must match actual uniform record fit');
      scales.push(x);
    }
    checkReportedDrawing(phase,metrics);
    for (const drawing of metrics.reported_drawings || []) {
      assert(insideFrame(drawing.bounds),'The complete reported drawing must stay inside its common frame');
      const actual=drawing.actual_body_scale, declared=drawing.declared_record_geometry_scale, svg=drawing.declared_svg_geometry_scale;
      assert(actual && ['x','y'].every(k=>Number.isFinite(actual[k])&&actual[k]>0),'Actual apparatus getScreenCTM scale is required');
      assert(Number.isFinite(declared)&&declared>0 && Number.isFinite(svg)&&svg>0,'Record and SVG scale metadata are required');
      const tolerance=Math.max(0.001,actual.x*0.005);
      assert(Math.abs(actual.x-actual.y)<=tolerance,'Apparatus geometry must scale uniformly');
      assert(Math.abs(actual.x-declared)<=tolerance && Math.abs(actual.x-svg)<=tolerance,'Declared geometry scale must match actual screen geometry');
      scales.push(actual.x);
    }
  }
  if (scales.length) {
    const tolerance=Math.max(0.001,scales[0]*0.005);
    assert(scales.every(s=>Math.abs(s-scales[0])<=tolerance),'Every shared operation of one record must have the same actual geometry scale');
  }
}
export async function collectRecordOperationMetrics(page, record) {
  assert(Array.isArray(record?.operations) && record.operations.length, 'Raw record operations required');
  const buttons=page.locator('#protocol .protocol-step-list button');
  assert.equal(await buttons.count(),record.operations.length,'Rendered operation list differs from raw record');
  const rows=[];
  for (const [index,operation] of record.operations.entries()) {
    await buttons.nth(index).click();
    await page.waitForFunction(label=>document.querySelector('#protocol .protocol-copy h3')?.textContent===label,operation.label,{timeout:30000});
    await page.waitForFunction(()=>[...document.querySelectorAll('#protocol .protocol-art img')].every(img=>img.complete&&img.naturalWidth>0),null,{timeout:30000});
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    rows.push({operation_index:index,operation_id:operation.id,
      below_image_note_count:await page.locator('#protocol .protocol-stage .protocol-visual > .protocol-visual-note').count(),
      enlarge_count:await page.locator('#protocol .protocol-stage .protocol-visual button').filter({hasText:'Enlarge operation diagram'}).count(),
      metrics:await page.locator('#protocol .protocol-art').evaluate(fontMetrics)});
  }
  return rows;
}

// Candidate-only synthetic layout probes use the exact runtime controller and
// drawing factory. They do not add site assets, records or scientific claims.
export async function probeSceneFixtureMatrix(browser, base) {
  const matrix=sceneFixtureMatrix(),results=[],standaloneResults=[];
  for(const viewport of VIEWPORTS){
    const context=await browser.newContext({viewport,deviceScaleFactor:1,serviceWorkers:'block',reducedMotion:'reduce'}),page=await context.newPage(),errors=[];
    page.on('pageerror',error=>errors.push(String(error.message||error)));
    try{
      const root=new URL(base.endsWith('/')?base:base+'/');
      const response=await page.goto(new URL('index.html',root).href,{waitUntil:'domcontentloaded',timeout:90000});assert.equal(response?.status(),200);
      await page.addStyleTag({url:new URL('reader.css',root).href});
      for(const recordCase of fixtureRecordCases(viewport)){
        const containerWidth=recordCase.container_width,recordFixtures=recordCase.standalone?[standaloneWidthLimitedFurnace()]:matrix;
        await page.evaluate(async({root,matrix,width})=>{
          window.__KFixture?.controller?.disconnect();
          const drawingModule=await import(new URL('reported-scene-drawing.mjs',root).href);
          const fit=await import(new URL('protocol-record-fit.mjs',root).href);
          if(document.fonts?.ready)await document.fonts.ready;
          const host=document.createElement('div');host.className='k-fixture-host protocol-visual';
          Object.assign(host.style,{width:width+'px',maxWidth:'none',padding:'0',margin:'0',boxSizing:'border-box'});
          document.body.replaceChildren(host);document.body.className='reader-main';Object.assign(document.body.style,{margin:'0',padding:'0',maxWidth:'none'});
          const createArt=(row,options)=>{
            const art=document.createElement('div');art.className='protocol-art protocol-art-reported';art.dataset.renderer='reported-fields';art.dataset.scene=row.spec.kind;
            Object.assign(art.style,{display:'grid',gridTemplateColumns:'minmax(0,1fr)',height:'auto',minHeight:'0px',minWidth:'0',width:'100%',gap:'12px'});
            const drawing=drawingModule.createReportedDrawing(row.spec,row.conditions,options);art.append(drawing);
            art.recordGeometry={...drawing.reportedViewport,extraOverhead:row.spec.kind==='chamber'?32:0};
            art.updateDrawingLayout=()=>drawing.updateAnnotationLayout?.();return art;
          };
          let current=matrix[0],controller;
          const render=row=>{
            current=row;const options=controller.options(row.id),art=createArt(row,options),frame=fit.createProtocolArtFrame(art,options);
            const policy=fit.protocolPresentationPolicy({},{}),note=document.createElement('p'),enlarge=document.createElement('button');
            note.className='protocol-visual-note';note.textContent=policy.caption;enlarge.textContent='Enlarge operation diagram ↗';enlarge.type='button';
            host.replaceChildren(frame,note,enlarge);
            if(controller.refresh(frame)){render(row);return;}
            art.updateDrawingLayout?.();
          };
          controller=fit.createRecordFitController({host,operations:matrix,createArt,onChange:()=>render(current)});
          window.__KFixture={controller,render,matrix};render(current);
        },{root:root.href,matrix:recordFixtures,width:containerWidth});
        const rows=[];
        for(const [index,fixture]of recordFixtures.entries()){
          await page.evaluate(id=>{const f=window.__KFixture;f.render(f.matrix.find(row=>row.id===id));},fixture.id);
          await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
          const metrics=await page.locator('.k-fixture-host .protocol-art').evaluate(fontMetrics);
          const row={operation_index:index,operation_id:fixture.id,below_image_note_count:await page.locator('.k-fixture-host > .protocol-visual-note').count(),enlarge_count:await page.locator('.k-fixture-host > button').count(),metrics};
          try{checkRecordOperationMetrics('after',[{...row,operation_index:0}],viewport);}catch(error){throw new Error(`Synthetic ${fixture.id} at ${viewport.width}px / ${containerWidth}px container: ${error.message}`);}
          rows.push(row);
        }
        checkRecordOperationMetrics('after',rows,viewport);
        assert.deepEqual(errors,[],'Synthetic scene matrix page errors');
        (recordCase.standalone?standaloneResults:results).push({viewport,container_width:containerWidth,record_kind:recordCase.standalone?'single-width-limited-furnace':'shared22-scene-record',fixtures:rows.map(({operation_id,metrics})=>({id:operation_id,scene:metrics.scene,frame_height:metrics.protocol_frame.bounds.height,frame_width:metrics.protocol_frame.bounds.width,actual_body_scales:metrics.reported_drawings.map(d=>d.actual_body_scale),minimum_leaf_font_px:Math.min(...metrics.reported_drawings.flatMap(d=>d.leaf_labels.map(l=>l.screen_font_px))),passed:true})),same_record_scale_passed:true});
      }
    }finally{await context.close();}
  }
  return{synthetic_only:true,source_records_changed:0,fixture_count:matrix.length,configurations:results,standalone_width_limited_records:standaloneResults,tested_fixture_views:matrix.length*results.length+standaloneResults.reduce((n,r)=>n+r.fixtures.length,0),passed:true};
}

function fileReceipt(out, name) {
  const bytes = fs.readFileSync(path.join(out, name));
  return { file: name, bytes: bytes.length, sha256: sha256(bytes) };
}

const DIAGNOSTIC_LIMIT = 20;
export function safeDiagnosticURL(value) {
  try {
    const url = new URL(String(value));
    return ['http:', 'https:'].includes(url.protocol) ? `${url.origin}${url.pathname}`.slice(0, 240) : '[non-http-url]';
  } catch { return '[invalid-url]'; }
}
export function safeDiagnosticText(value) {
  return String(value || '').replace(/https?:\/\/[^\s"'<>]+/gi, safeDiagnosticURL)
    .replace(/(^|[\s(])((?:\/|\.\/)[^\s"'<>?#]*)(?:\?[^\s"'<>#]*)?(?:#[^\s"'<>]*)?/g, '$1$2').slice(0, 240);
}
export function registerFailureDiagnostics(page) {
  const evidence = { request_failures: [], non_2xx_responses: [], console_errors: [], collection_errors: [], omitted: {} };
  const append = (key, value) => {
    if (evidence[key].length < DIAGNOSTIC_LIMIT) evidence[key].push(value);
    else evidence.omitted[key] = (evidence.omitted[key] || 0) + 1;
  };
  const handler = (stage, action) => (...args) => {
    try { action(...args); }
    catch (error) { append('collection_errors', { stage, error_class: safeDiagnosticText(error.name || 'Error') }); }
  };
  page.on('requestfailed', handler('requestfailed', (request) => append('request_failures', {
    url: safeDiagnosticURL(request.url()), resource_type: safeDiagnosticText(request.resourceType()).slice(0, 32),
    error: safeDiagnosticText(request.failure()?.errorText || 'request failed') })));
  page.on('response', handler('response', (response) => {
    const status = response.status();
    if (status < 200 || status >= 300) append('non_2xx_responses', { url: safeDiagnosticURL(response.url()), status,
      resource_type: safeDiagnosticText(response.request().resourceType()).slice(0, 32) });
  }));
  page.on('console', handler('console', (message) => {
    if (message.type() === 'error') append('console_errors', { text: safeDiagnosticText(message.text()) });
  }));
  return evidence;
}
export function structuralReadinessSummary() {
  const marker = document.querySelector('main[data-reader-ready]');
  const scripts = [...document.scripts];
  const resources = performance.getEntriesByType('resource');
  const kinds = ['script', 'link', 'fetch', 'xmlhttprequest', 'css', 'img'];
  const resource_counts = Object.fromEntries(kinds.map((kind) => [kind, resources.filter((r) => r.initiatorType === kind).length]));
  return { document_ready_state: document.readyState, main_present: Boolean(document.querySelector('main')),
    reader_marker_present: Boolean(marker), reader_marker_value: marker ? String(marker.getAttribute('data-reader-ready') || '').slice(0, 160) : null,
    protocol_present: Boolean(document.querySelector('#protocol')), protocol_button_count: document.querySelectorAll('#protocol .protocol-step-list button').length,
    script_count: scripts.length, external_script_count: scripts.filter((s) => Boolean(s.src)).length,
    module_script_count: scripts.filter((s) => s.type === 'module').length,
    resource_count: resources.length, resource_counts };
}
export async function collectFailureDiagnostics(page, evidence, out, stem) {
  const collectionError = (stage, error) => {
    if (evidence.collection_errors.length < DIAGNOSTIC_LIMIT) evidence.collection_errors.push({ stage, error_class: safeDiagnosticText(error.name || 'Error') });
    else evidence.omitted.collection_errors = (evidence.omitted.collection_errors || 0) + 1;
  };
  let timer;
  try {
    evidence.readiness = await Promise.race([page.evaluate(structuralReadinessSummary), new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error('Diagnostic timeout')), 5000);
    })]);
  } catch (error) { collectionError('structural-readiness', error); }
  finally { clearTimeout(timer); }
  try {
    assert(/^[a-z0-9-]+$/.test(stem), 'Safe diagnostic filename required');
    const name = `${stem}-failure-viewport.png`;
    await page.screenshot({ path: path.join(out, name), timeout: 5000 });
    evidence.screenshot = fileReceipt(out, name);
  } catch (error) { collectionError('failure-screenshot', error); }
  return evidence;
}

export async function visit(browser, base, out, phase, target, viewport) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1, serviceWorkers: 'block', reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(String(error.message || error)));
  const failureEvidence = registerFailureDiagnostics(page);
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
    if (phase === 'after') {
      const allOperationMetrics = await collectRecordOperationMetrics(page, JSON.parse(bytes.toString('utf8')));
      checkRecordOperationMetrics(phase, allOperationMetrics, viewport);
      // Keep complete numeric evidence without repeating every label/block in
      // the artifact for every operation. Full checks ran above on each step.
      row.record_operation_metrics = allOperationMetrics.map(({operation_index,operation_id,below_image_note_count,enlarge_count,metrics})=>({
        operation_index,operation_id,below_image_note_count,enlarge_count,frame:metrics.protocol_frame,scene:metrics.scene,renderer:metrics.renderer,
        inline_svg_count:metrics.inline_svg_count,external_image_count:metrics.external_image_count,
        minimum_measured_screen_font_px:metrics.minimum_measured_screen_font_px,full_drawing_checks_passed:true,
        shared_geometry:metrics.reported_drawings.map(d=>({actual_body_scale:d.actual_body_scale,declared_record_geometry_scale:d.declared_record_geometry_scale,declared_svg_geometry_scale:d.declared_svg_geometry_scale,drawing_height:d.bounds.height,leaf_label_count:d.leaf_labels.length,fact_block_count:d.fact_blocks.length}))
      }));
      // Leave the selected screenshot operation/URL stable after numeric checks.
      await buttons.nth(target.operation_index).click();
      await page.waitForFunction(label=>document.querySelector('#protocol .protocol-copy h3')?.textContent===label,target.operation_label,{timeout:30000});
      assert.deepEqual(errors, [], 'Uncaught page script errors during all-operation measurement');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2),false,'All-operation measurement introduced horizontal page overflow');
    }
    row.automated_checks_passed = true;
    row.human_visual_review = 'pending';
  } catch (error) {
    row.automated_checks_passed = false;
    row.error = String(error.message || error);
    try { row.failure_diagnostics = await collectFailureDiagnostics(page, failureEvidence, out, `${target.id}-${viewport.width}`); }
    catch (diagnosticError) { row.failure_diagnostics = { collection_errors: [{ stage: 'collector', error_class: safeDiagnosticText(diagnosticError.name || 'Error') }] }; }
  } finally {
    row.page_errors = errors;
    await context.close();
  }
  return row;
}

export function argumentsFor(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 2) {
    assert(['--base', '--out', '--phase', '--targets'].includes(argv[i]) && typeof argv[i + 1] === 'string', 'Use --base, --out and --phase');
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
  const raw = fs.readFileSync(args.targets || TARGET_FILE);
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
    browser = await chromium.launch({args: ['--disable-gpu']});
    receipt.browser_started = true;
    for (const target of targets) {
      for (const viewport of viewportsForTarget(target)) {
        const row = await visit(browser, args.base, out, args.phase, target, viewport);
        receipt.pages.push(row); save();
        console.log(`${args.phase} ${target.id} ${viewport.width}: ${row.automated_checks_passed ? 'pass' : row.error}`);
      }
    }
    if(args.phase==='after'){receipt.scene_fixture_matrix=await probeSceneFixtureMatrix(browser,args.base);save();}
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
  assert(receipt.pages.length === targets.reduce((count,target)=>count+viewportsForTarget(target).length,0) && failures.length === 0, receipt.summary);
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  main().catch((error) => { console.error(error.message || error); process.exitCode = 1; });
}
