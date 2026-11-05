import assert from 'node:assert/strict';
import {test} from 'node:test';
import {reportedProtocolSceneDescriptor as descriptor, createReportedProtocolScene, REPORTED_SCENE_CAVEAT} from '../static/reported-protocol-scenes.mjs';

const q = (value, unit = 'degC', status = 'reported') => ({value, unit, status});
const op = (action, label = action, extra = {}) => ({id: 'step', action, label, inputs: [], parameters: {}, environment: {status: 'not_reported', value: null}, ...extra});
const rec = (extra = {}) => ({method: 'Other', materials: [], stocks: [], material_states: [], products: [], operations: [], ...extra});
const choose = (o, r = rec()) => descriptor(o, r);
const freeze = value => {if (value && typeof value === 'object' && !Object.isFrozen(value)) {Object.values(value).forEach(freeze); Object.freeze(value);} return value;};

for (const action of ['dissolve', 'add', 'mix', 'stir', 'heat', 'react', 'hold', 'hydrolyze', 'condense', 'gel']) {
  test(`${action} selects only a generic solution scene`, () => {
    const d = choose(op(action));
    assert.equal(d.kind, 'solution');
    assert.equal(d.vessel, null);
    assert.equal(d.environment, '');
    assert.deepEqual(d.added, []);
  });
}

test('positive current-step actions select injection, degassing, cooling and reflux', () => {
  for (const [action, kind] of [['inject', 'inject'], ['degas', 'degas'], ['purge', 'degas'], ['cool', 'cool'], ['quench', 'cool'], ['reflux', 'reflux']]) {
    assert.equal(choose(op(action)).kind, kind);
  }
});

test('a later technique mentioned in feed preparation does not choose that apparatus', () => {
  assert.equal(choose(op('dissolve', 'Prepare a feed for later reflux')).kind, 'solution');
  assert.equal(choose(op('heat', 'Heat a feed before transfer to an autoclave')).kind, 'solution');
  assert.equal(choose(op('prepare', 'Prepare the substrate before MBE growth'), rec({method: 'MBE'})).kind, 'solution');
});

test('negated actions do not become a new apparatus selection', () => {
  for (const action of ['do_not_heat', 'avoid_reflux', 'without_centrifugation', 'omit_filtering']) {
    assert.equal(choose(op(action)), null);
  }
  assert.equal(choose(op('reflux', 'Reflux without chemical reduction')).kind, 'reflux');
  assert.equal(choose(op('heat', 'Heat without a condenser')).kind, 'solution');
});

test('workup stays distinct from the recipe synthesis system', () => {
  const r = rec({method: 'Hydrothermal', products: [{notes: ['Reactor: Teflon-lined autoclave (Main PDF p.3).']}]});
  for (const [action, kind] of [['precipitate', 'workup-tube'], ['wash', 'workup-tube'], ['redisperse', 'workup-tube'], ['dry', 'dry-tube'], ['centrifuge', 'centrifuge'], ['filter', 'filter']]) {
    const d = choose(op(action), r);
    assert.equal(d.kind, kind);
    assert.equal(d.vessel, null);
    assert.equal(d.heating, false);
  }
});

test('plain wash does not infer a centrifuge or a filter', () => {
  assert.equal(choose(op('wash')).kind, 'workup-tube');
});

test('deposition uses its own reported system while ordinary solution growth does not', () => {
  assert.equal(choose(op('grow'), rec({method: 'Molecular beam epitaxy'})).kind, 'chamber');
  assert.equal(choose(op('deposit'), rec({method: 'Chemical vapor deposition'})).kind, 'chamber');
  assert.equal(choose(op('sputter'), rec({method: 'Sputtering'})).kind, 'chamber');
  assert.equal(choose(op('evaporate'), rec({method: 'Thermal evaporation'})).kind, 'chamber');
  assert.equal(choose(op('grow', 'Grow crystals in solution')), null);
  assert.equal(choose(op('wash'), rec({method: 'MBE'})).kind, 'workup-tube');
});

test('solvent evaporation is workup rather than a deposition chamber', () => {
  assert.equal(choose(op('evaporate', 'Evaporate solvent'), rec({method: 'Thermal evaporation'})).kind, 'dry-tube');
});

test('unreported source feeds and substrate names are omitted from a chamber', () => {
  const d = choose(op('grow'), rec({method: 'MBE'}));
  assert.equal(d.sourceFeed, false);
  assert.deepEqual(d.substrates, []);
  assert.deepEqual(d.added, []);
});

test('only current-step reported flux and substrate inputs are represented', () => {
  const d = choose(op('grow', 'Grow under a Ga beam', {inputs: ['sub'], parameters: {Ga_flux: q(1, 'ML/s')}}),
    rec({method: 'MBE', materials: [{id: 'sub', name: 'GaAs(001)', role: 'substrate'}, {id: 'other-sub', name: 'Si(111)', role: 'substrate'}]}));
  assert.equal(d.sourceFeed, true);
  assert.deepEqual(d.substrates, ['GaAs(001)']);
  assert.deepEqual(d.added, []);
  assert.equal(d.conditions[0].key, 'Ga_flux');
});

test('deposited layer compositions are not asserted as chamber reagents or feeds', () => {
  for (const name of ['GaAs', 'Al0.3Ga0.7As', 'Silicon']) {
    const r = rec({method: 'MBE', materials: [{id: 'layer', name, role: 'metal_precursor'}]});
    const d = choose(op('deposit', `Deposit ${name} buffer layer`, {inputs: ['layer']}), r);
    assert.equal(d.kind, 'chamber');
    assert.deepEqual(d.added, []);
    assert.equal(d.sourceFeed, false);
  }
});

test('explicit chamber supply names and reported deposition flux remain visible', () => {
  const r = rec({method: 'MBE', materials: [{id: 'source', name: 'Gallium', role: 'metal_precursor'}]});
  const supplied = choose(op('supply', 'Supply gallium', {inputs: ['source']}), r);
  assert.deepEqual(supplied.added, ['Gallium']);
  assert.equal(supplied.sourceFeed, true);
  const deposited = choose(op('deposit', 'Deposit a layer', {inputs: ['source'], parameters: {Ga_flux: q(1, 'ML/s')}}), r);
  assert.deepEqual(deposited.added, []);
  assert.equal(deposited.sourceFeed, true);
});

test('hydrothermal/solvothermal current reaction steps use a closed reactor', () => {
  for (const method of ['Hydrothermal', 'Solvothermal']) {
    const d = choose(op('heat'), rec({method}));
    assert.equal(d.kind, 'closed-reactor');
    assert.equal(d.vessel, null); // no invented lining, capacity or pressure
  }
});

test('calcination, furnace annealing and ball milling have separate scenes', () => {
  assert.equal(choose(op('calcine')).kind, 'furnace');
  assert.equal(choose(op('anneal', 'Anneal in a furnace')).kind, 'furnace');
  assert.equal(choose(op('anneal')), null);
  assert.equal(choose(op('ball_mill')).kind, 'mill-jar');
  assert.equal(choose(op('grind', 'Grind by hand')), null);
});

test('solid-state and explicitly reported furnace heating choose furnace/crucible geometry', () => {
  assert.equal(choose(op('heat'), rec({method: 'Solid state reaction'})).kind, 'furnace');
  assert.equal(choose(op('heat', 'Heat in a furnace')).kind, 'furnace');
  assert.equal(choose(op('heat'), rec({products: [{notes: ['Reactor: Tube furnace (Main PDF p.2).']}]})).kind, 'furnace');
});

test('an explicit step vessel wins without assigning the recipe vessel to all workup', () => {
  const r = rec({products: [{notes: ['Reactor: Three-neck flask (Main PDF p.2).']}]});
  assert.deepEqual(choose(op('mix', 'Mix', {vessel: {status: 'reported', value: 'Vial'}}), r).vessel, {value: 'Vial', scope: 'step'});
  assert.deepEqual(choose(op('heat'), r).vessel, {value: 'Three-neck flask', scope: 'recipe'});
  assert.equal(choose(op('mix', 'Mix', {vessel: {status: 'not_reported', value: 'Vial'}})).vessel, null);
});

test('conflicting recipe vessels and three confirmed nonvessel notes are omitted', () => {
  const r = rec({products: [{notes: ['Reactor: Flask (Main PDF p.2).', 'Reactor: Autoclave (Main PDF p.3).']}]});
  assert.equal(choose(op('heat'), r).vessel, null);
  for (const value of ['2 ml distilled water', 'Thin films of silicon oxide (SiOx) on p-type silicon (111) substrates', '25 × 25 mm ITO-coated glass substrate']) {
    assert.equal(choose(op('heat'), rec({products: [{notes: [`Reactor: ${value} (Main PDF p.2).`]}]})).vessel, null);
  }
});

test('only direct current-step material/stock inputs supply addition labels', () => {
  const r = rec({materials: [{id: 'm', name: 'Cadmium acetate', role: 'metal_precursor'}, {id: 'unused', name: 'Unused reagent', role: 'ligand'}],
    stocks: [{id: 'stock', name: 'Selenium stock'}], material_states: [{id: 'mixture', name: 'Carried mixture'}]});
  assert.deepEqual(choose(op('inject', 'Inject', {inputs: ['mixture', 'm', 'stock', 'missing']}), r).added, ['Cadmium acetate', 'Selenium stock']);
  assert.deepEqual(choose(op('heat', 'Heat the mixture', {inputs: ['m', 'stock']}), r).added, []);
});

test('repeated record inputs do not imply a new addition', () => {
  const first = op('add', 'Add ligand', {id: 'first', inputs: ['ligand']});
  const second = op('stir', 'Stir the existing mixture', {id: 'second', inputs: ['ligand']});
  const r = rec({materials: [{id: 'ligand', name: 'Oleylamine', role: 'ligand'}], operations: [first, second]});
  assert.deepEqual(choose(second, r).added, []);
  const third = op('add', 'Add more oleylamine', {id: 'third', inputs: ['ligand']});
  r.operations.push(third);
  assert.deepEqual(choose(third, r).added, ['Oleylamine']);
});

test('an ambiguous GaAs input is not relabelled as gallium in a droplet step', () => {
  const r = rec({method: 'Molecular beam epitaxy', materials: [{id: 'gaas', name: 'GaAs quantum dots', role: 'metal_precursor'}]});
  const d = choose(op('deposit', 'Deposit gallium droplets', {inputs: ['gaas']}), r);
  assert.equal(d.kind, 'chamber');
  assert.deepEqual(d.added, []);
});

test('the explicit own-step Ga atoms spelling can replace an ambiguous mapped GaAs input', () => {
  const r = rec({method: 'MBE', materials: [{id: 'gaas', name: 'GaAs quantum dots', role: 'metal_precursor'}]});
  assert.deepEqual(choose(op('supply', 'Supply Ga atoms to form droplets', {inputs: ['gaas']}), r).added, ['Ga atoms']);
  assert.deepEqual(choose(op('supply', 'Supply the flux', {inputs: ['gaas']}), r).added, []);
});

test('an own-step As4 flux supplies an MBE beam without inventing a flux value', () => {
  const d = choose(op('grow', 'Grow dots', {environment: {status: 'reported', value: 'As4 flux'}}), rec({method: 'MBE'}));
  assert.equal(d.kind, 'chamber');
  assert.equal(d.sourceFeed, true);
  assert.equal(d.beamSystem, true);
  assert.equal(d.conditions.length, 0);
  assert.deepEqual(d.added, []);
});

test('reported high-temperature injection/addition gets heat only from its own operation', () => {
  assert.equal(choose(op('inject', 'Inject', {parameters: {temperature: q(300)}})).heating, true);
  assert.equal(choose(op('add', 'Add', {parameters: {temperature: q(450, 'K')}})).heating, true);
  assert.equal(choose(op('inject', 'Inject', {parameters: {temperature: q(25)}})).heating, false);
  assert.equal(choose(op('inject', 'Inject', {parameters: {temperature: q(300, 'degC', 'not_reported')}})).heating, false);
  const other = op('heat', 'Heat', {id: 'other', parameters: {temperature: q(300)}}), current = op('inject', 'Inject');
  assert.equal(choose(current, rec({operations: [other, current]})).heating, false);
});

test('validated reactor metadata is consumed through the existing parser hook only', () => {
  const line = Object.fromEntries(['vessel_type', 'atmosphere', 'schlenk_line', 'glovebox', 'heating_method', 'stirring', 'addition_method', 'cooling_method']
    .map(key => [key, {status: 'not_reported', value: null}]));
  line.vessel_type = {status: 'reported', value: 'Beaker', source_id: 'main', locator: 'p.2'};
  line.atmosphere = {status: 'reported', value: 'Argon', source_id: 'main', locator: 'p.2'};
  let calls = 0;
  const operation = op('heat', 'Heat', {environment: {status: 'not_reported', value: null, note: 'strict-parser-marker'}});
  const r = rec({sources: [{id: 'main'}]});
  const options = {readReactorLine: note => {calls++;assert.equal(note, 'strict-parser-marker');return {valid: true, line};}};
  const d = descriptor(operation, r, options);
  assert.equal(calls, 1);
  assert.deepEqual(d.vessel, {value: 'Beaker', scope: 'step'});
  assert.equal(d.vesselKind, 'beaker');
  assert.equal(d.environment, 'Argon');
  assert.equal(descriptor(operation, r, {readReactorLine: () => ({valid: false, line})}).vessel, null);
  assert.equal(descriptor(operation, rec({sources: [{id: 'different'}]}), options).vessel, null);
  assert.equal(descriptor(operation, r).vessel, null);
});

test('only reported own-step conditions and atmosphere become labels', () => {
  const d = choose(op('heat', 'Heat', {parameters: {temperature: q(180), duration: q(30, 'min'), pressure: q(2, 'bar', 'not_reported'), invented: q(99)},
    environment: {status: 'reported', value: 'Nitrogen'}}));
  assert.deepEqual(d.conditions.map(c => c.key), ['temperature', 'duration']);
  assert.equal(d.environment, 'Nitrogen');
  assert.equal(d.gasLine, true);
  assert.equal(choose(op('stir', 'Stir', {environment: {status: 'not_reported', value: 'Argon'}})).environment, '');
  assert.equal(choose(op('stir', 'Stir', {environment: {status: 'reported', value: 'Ambient air'}})).gasLine, false);
});

test('unknown actions return null so an existing admitted image can remain', () => {
  for (const action of ['characterize', 'record_context', 'measure_absorption', 'store', 'unknown_step']) assert.equal(choose(op(action)), null);
  assert.equal(createReportedProtocolScene(op('unknown')), null);
});

class Element {
  constructor(tag) {this.tagName = tag; this.children = []; this.style = {}; this.dataset = {}; this.attributes = {}; this.textContent = ''; this.innerHTML = '';}
  append(...children) {this.children.push(...children);}
  setAttribute(key, value) {this.attributes[key] = value;}
}
const all = node => [node, ...node.children.flatMap(all)];
const withDocument = run => {const previous = globalThis.document;globalThis.document = {createElement: t => new Element(t), createElementNS: (_, t) => new Element(t)};try {run();} finally {globalThis.document = previous;}};

test('scientific labels are unscaled HTML with >=12px type and wrapping', () => withDocument(() => {
  const r = rec({materials: [{id: 'm', name: 'A long reported precursor name', role: 'metal_precursor'}]});
  const scene = createReportedProtocolScene(op('add', 'Add', {inputs: ['m'], parameters: {temperature: q(70), duration: q(2, 'h')}, environment: {status: 'reported', value: 'Argon'}}), r,
    {formatQuantity: quantity => `${quantity.value} ${quantity.unit} · retained qualifier`});
  assert.equal(scene.dataset.renderer, 'reported-fields');
  assert.equal(scene.style.height, 'auto');
  const labels = all(scene).filter(n => n.tagName === 'dt' || n.tagName === 'dd');
  assert.ok(labels.length >= 6);
  assert.ok(labels.every(n => parseFloat(n.style.fontSize) >= 12 && n.style.overflowWrap === 'anywhere'));
  assert.match(labels.map(n => n.textContent).join(' '), /retained qualifier/);
  const svg = scene.children[0];
  assert.doesNotMatch(svg.innerHTML, /<text\b|retained qualifier|Argon|precursor name/);
}));

test('reported vessel names select different fixed shapes and an absent vessel stays plain', () => withDocument(() => {
  const rendered = new Map();
  for (const [name, kind] of [['Beaker', 'beaker'], ['Vial', 'vial'], ['Test tube', 'tube'], ['Round-bottom flask', 'flask'], ['Three-neck flask', 'three-neck-flask']]) {
    const operation = op('mix', 'Mix', {vessel: {status: 'reported', value: name}});
    assert.equal(choose(operation).vesselKind, kind);
    rendered.set(kind, createReportedProtocolScene(operation, rec()).children[0].innerHTML);
  }
  assert.equal(new Set(rendered.values()).size, 5);
  const plain = createReportedProtocolScene(op('mix'), rec());
  assert.equal(choose(op('mix')).vesselKind, 'plain');
  assert.ok(![...rendered.values()].includes(plain.children[0].innerHTML));
  assert.doesNotMatch(plain.children[0].innerHTML, /M174 54h72v68/); // the old flask neck
}));

test('reported room-temperature qualifier or raw spelling is kept without a numeric temperature', () => withDocument(() => {
  for (const field of ['qualifier', 'raw_text']) {
    const quantity = {status: 'reported', value: null, unit: 'degC', [field]: 'Room temperature'};
    const operation = op('stir', 'Stir', {parameters: {temperature: quantity}});
    assert.equal(choose(operation).conditions.length, 1);
    const scene = createReportedProtocolScene(operation, rec(), {formatQuantity: () => 'Not reported'});
    assert.ok(all(scene).some(n => n.textContent === 'Room temperature'));
    assert.ok(!all(scene).some(n => /\b25\b/.test(n.textContent)));
    assert.equal(choose(operation).heating, false);
  }
}));

test('unavailable quantity formatting is omitted, not replaced with invented numbers', () => withDocument(() => {
  const scene = createReportedProtocolScene(op('heat', 'Heat', {parameters: {temperature: q(70)}}), rec(), {formatQuantity: () => 'Reactor quantity unavailable'});
  assert.ok(!all(scene).some(n => n.textContent.includes('70')));
}));

test('record values never enter SVG markup and no repeated caveat is inside the image', () => withDocument(() => {
  const name = '<img src=x onerror=alert(1)>';
  const scene = createReportedProtocolScene(op('add', 'Add', {inputs: ['m']}), rec({materials: [{id: 'm', name, role: 'ligand'}]}));
  assert.ok(all(scene).some(n => n.textContent === name));
  assert.ok(!scene.children[0].innerHTML.includes(name));
  assert.ok(!all(scene).some(n => n.textContent === REPORTED_SCENE_CAVEAT));
  assert.doesNotMatch(scene.children[0].innerHTML, /schematic|illustrative|not measured|not reported/i);
}));

test('all matched families produce diagram geometry without fetching or mutating records', () => withDocument(() => {
  const cases = [op('heat'), op('inject'), op('reflux'), op('cool'), op('degas'), op('centrifuge'), op('filter'), op('wash'), op('dry'), op('calcine'), op('ball_mill')];
  for (const operation of cases) {
    const r = freeze(rec({operations: [operation]})), before = JSON.stringify(r);
    const scene = createReportedProtocolScene(operation, r, {formatQuantity: quantity => String(quantity.value)});
    assert.ok(scene && scene.children[0].innerHTML.length > 30);
    assert.equal(JSON.stringify(r), before);
  }
}));
