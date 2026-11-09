import assert from 'node:assert/strict';
import {test} from 'node:test';
import {reportedProtocolSceneDescriptor as descriptor, createReportedProtocolScene, REPORTED_SCENE_CAVEAT, shortReportedSceneName, compactReportedSceneQuantity} from '../static/reported-protocol-scenes.mjs';

import {quantityValue} from '../static/quantity-value.mjs';

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
  assert.equal(choose(op('prepare', 'Prepare the substrate before MBE growth'), rec({method: 'MBE'})), null);
});

test('wafer desorption uses its reported epitaxy system without a liquid vessel', () => {
  const d = choose(op('heat', 'Wafer temperature raised to 620 C for desorption', {parameters: {temperature: q(620)}}), rec({method: 'Molecular beam epitaxy'}));
  assert.equal(d.kind, 'chamber');
  assert.equal(d.sourceFeed, false);
  assert.deepEqual(d.added, []);
  assert.equal(choose(op('heat', 'Heat the wafer')), null);
});

test('dry preparation uses only its explicit supported apparatus or keeps its image', () => {
  assert.equal(choose(op('mix', 'Resulting powder was well mixed using an agate mortar and pestle'),
    rec({products: [{notes: ['Reactor: closed aluminum crucible (Main PDF p.2).']}]})).kind, 'mortar-pestle');
  assert.equal(choose(op('mix', 'Mix Mg and B powders in the stoichiometric ratio of MgB2'),
    rec({method: 'Powder-in-tube', products: [{notes: ['Reactor: planetary ball mill (Main PDF p.2).']}]})), null);
});

test('explicit liquid powder processing remains supported without borrowing neighboring context', () => {
  assert.equal(choose(op('dissolve', 'Dissolve powder in water')).kind, 'solution');
  assert.equal(choose(op('mix', 'Mix the powder into an aqueous suspension')).kind, 'solution');
  assert.equal(choose(op('mix', 'Mix powder without water')), null);
  assert.equal(choose(op('mix', 'Mix dry powder under water vapor')), null);
  assert.equal(choose(op('mix', 'Mix powder'), rec({method: 'Aqueous synthesis'})), null);
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
  const d = choose(op('wash'));
  assert.equal(d.kind, 'workup-tube');
  assert.equal(d.vesselKind, 'tube');
  assert.equal(d.vessel, null);
});

test('workup uses a generic tube symbol unless its own vessel is reported', () => {
  for (const action of ['precipitate', 'wash', 'redisperse', 'dry']) {
    assert.equal(choose(op(action)).vesselKind, 'tube');
    assert.equal(choose(op(action, action, {vessel: {status: 'reported', value: 'Beaker'}})).vesselKind, 'beaker');
  }
});

test('deposition uses its reported system while explicit solution growth uses a plain vessel', () => {
  assert.equal(choose(op('grow'), rec({method: 'Molecular beam epitaxy'})).kind, 'chamber');
  assert.equal(choose(op('deposit'), rec({method: 'Chemical vapor deposition'})).kind, 'chamber');
  assert.equal(choose(op('sputter'), rec({method: 'Sputtering'})).kind, 'chamber');
  assert.equal(choose(op('evaporate'), rec({method: 'Thermal evaporation'})).kind, 'chamber');
  assert.equal(choose(op('grow', 'Grow crystals in solution')).kind, 'solution');
  assert.equal(choose(op('grow', 'Grow crystals')), null);
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
  const labels = all(scene).filter(n => ['span', 'strong', 'dt', 'dd'].includes(n.tagName) && n.textContent);
  assert.ok(labels.length >= 4);
  assert.ok(labels.every(n => parseFloat(n.style.fontSize) >= 12 && n.style.overflowWrap === 'anywhere'));
  assert.match(labels.map(n => n.textContent).join(' '), /retained qualifier/);
  const svg = all(scene).find(n => n.tagName === 'svg');
  assert.doesNotMatch(svg.innerHTML, /<text\b|retained qualifier|Argon|precursor name/);
}));

test('reported vessel names select different fixed shapes and an absent vessel stays plain', () => withDocument(() => {
  const rendered = new Map();
  for (const [name, kind] of [['Beaker', 'beaker'], ['Vial', 'vial'], ['Test tube', 'tube'], ['Round-bottom flask', 'flask'], ['Three-neck flask', 'three-neck-flask']]) {
    const operation = op('mix', 'Mix', {vessel: {status: 'reported', value: name}});
    assert.equal(choose(operation).vesselKind, kind);
    rendered.set(kind, all(createReportedProtocolScene(operation, rec())).find(n => n.tagName === 'svg').innerHTML.replaceAll(/reported-art-\d+/g, 'art'));
  }
  assert.equal(new Set(rendered.values()).size, 5);
  const plain = createReportedProtocolScene(op('mix'), rec());
  assert.equal(choose(op('mix')).vesselKind, 'plain');
  assert.ok(![...rendered.values()].includes(all(plain).find(n => n.tagName === 'svg').innerHTML.replaceAll(/reported-art-\d+/g, 'art')));
  assert.doesNotMatch(all(plain).find(n => n.tagName === 'svg').innerHTML.replaceAll(/reported-art-\d+/g, 'art'), /M174 54h72v68/); // the old flask neck
}));

test('reported room-temperature qualifier or raw spelling is kept without a numeric temperature', () => withDocument(() => {
  for (const field of ['qualifier', 'raw_text']) {
    const quantity = {status: 'reported', value: null, unit: 'degC', [field]: 'Room temperature'};
    const operation = op('stir', 'Stir', {parameters: {temperature: quantity}});
    assert.equal(choose(operation).conditions.length, 1);
    const scene = createReportedProtocolScene(operation, rec(), {formatQuantity: () => 'Not reported'});
    assert.ok(all(scene).some(n => n.textContent === 'temperature: Room temperature'));
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
  assert.ok(!all(scene).find(n => n.tagName === 'svg').innerHTML.includes(name));
  assert.ok(!all(scene).some(n => n.textContent === REPORTED_SCENE_CAVEAT));
  assert.doesNotMatch(all(scene).find(n => n.tagName === 'svg').innerHTML, /schematic|illustrative|not measured|not reported/i);
}));

test('all matched families produce diagram geometry without fetching or mutating records', () => withDocument(() => {
  const cases = [op('heat'), op('inject'), op('reflux'), op('cool'), op('degas'), op('centrifuge'), op('filter'), op('wash'), op('dry'), op('calcine'), op('ball_mill')];
  for (const operation of cases) {
    const r = freeze(rec({operations: [operation]})), before = JSON.stringify(r);
    const scene = createReportedProtocolScene(operation, r, {formatQuantity: quantity => String(quantity.value)});
    assert.ok(scene && all(scene).find(n => n.tagName === 'svg').innerHTML.length > 30);
    assert.equal(JSON.stringify(r), before);
  }
}));

function fixture(description = 'Slowly add fresh aqueous NaBH4 solution under vigorous stirring.') {
  const prep = {id: 'reductant-solution', action: 'dissolve', inputs: ['nabh4', 'water'], outputs: ['reductant-state']};
  const current = {id: 'reduce', action: 'add', label: 'Reduce under stirring', description,
    inputs: ['ligand-state', 'reductant-state'], outputs: ['reduced-state'], parameters: {}};
  const record = {method: 'Other', materials: [
    {id: 'nabh4', name: 'Sodium borohydride', formula: 'NaBH4', role: 'reducing_agent'},
    {id: 'water', name: 'Water', formula: 'H2O', role: 'solvent'},
    {id: 'ligand', name: 'Oleylamine', role: 'ligand'}],
    stocks: [{id: 'reductant-stock', name: 'Prepare fresh aqueous reductant', preparation_operation_ids: ['reductant-solution'],
      components: [{material_id: 'nabh4'}, {material_id: 'water'}]}],
    material_states: [{id: 'ligand-state'}, {id: 'reductant-state'}, {id: 'reduced-state'}],
    operations: [prep, current]};
  return {record, current, prep};
}
const added = ({record, current}) => descriptor(current, record).added;

test('unique preparation-output stock link names only this step literal solution charge', () => {
  const f = fixture();
  assert.deepEqual(added(f), ['fresh aqueous NaBH4 solution']);
  assert.equal(added(f).some(name => /water|0\.78|40|mmol|mol\/l/i.test(name)), false);
});

test('decimal quantities do not split a charge clause or become an inferred dose label', () => {
  assert.deepEqual(added(fixture('Add 0.5 mL fresh aqueous NaBH4 solution under stirring.')),
    ['fresh aqueous NaBH4 solution']);
});

test('material name is matched literally without deriving a synonym', () => {
  assert.deepEqual(added(fixture('Add sodium borohydride solution into the stirred mixture.')), ['sodium borohydride solution']);
  assert.deepEqual(added(fixture('Add borohydride solution.')), []);
});

test('a carried mixture with no current addition clause supplies no new label', () => {
  for (const description of ['Stir the fresh aqueous NaBH4 solution.', 'Heat the NaBH4 solution.',
    'After adding NaBH4 solution, stir the mixture.', 'Prepare NaBH4 solution for later addition.',
    'Add the ligand to the NaBH4 solution.', 'Add the prepared solution.']) {
    assert.deepEqual(added(fixture(description)), [], description);
  }
});

test('negated conditional and future additions do not label the stock', () => {
  for (const description of ['Do not add NaBH4 solution.', 'Without adding NaBH4 solution, stir.',
    'Add no NaBH4 solution.', 'Add solution without NaBH4.', 'Optionally add NaBH4 solution.',
    'Add NaBH4 solution if necessary.', 'The NaBH4 solution will be added later.']) {
    assert.deepEqual(added(fixture(description)), [], description);
  }
});

test('a positive short label cannot override a negative or conditional description', () => {
  for (const description of ['Do not add NaBH4 solution.', 'Add NaBH4 solution if necessary.',
    'Without adding NaBH4 solution, stir.']) {
    const f = fixture(description); f.current.label = 'Add NaBH4 solution';
    assert.deepEqual(added(f), [], description);
  }
});

test('only literal component mentions are returned, not all stock constituents', () => {
  assert.deepEqual(added(fixture('Add fresh aqueous NaBH4 solution in water.')), ['fresh aqueous NaBH4 solution']);
  assert.deepEqual(added(fixture('Inject H2O into the mixture.')), ['H2O']);
  assert.deepEqual(added(fixture('Add NaBH4X solution.')), []);
});

test('unlinked or ambiguous stock preparation is omitted', () => {
  for (const alter of [
    f => {f.record.stocks[0].preparation_operation_ids = ['unrelated'];},
    f => {f.record.stocks.push({...f.record.stocks[0], id: 'second-stock'});},
    f => {f.record.operations.unshift({...f.prep, id: 'other-producer'});},
    f => {f.prep.outputs.push('other-state');},
    f => {f.record.operations.reverse();},
    f => {f.record.material_states.push({id: 'reductant-state'});},
    f => {f.prep.inputs = ['water'];},
    f => {f.record.stocks[0].components = [{material_id: 'unknown'}];},
    f => {f.record.operations.push({...f.current});},
  ]) {
    const f = fixture(); alter(f); assert.deepEqual(added(f), []);
  }
});

test('a stock-linked state is never borrowed from a non-input or another step description', () => {
  const f = fixture('Stir the mixture.'); f.prep.description = 'Add fresh aqueous NaBH4 solution.';
  assert.deepEqual(added(f), []);
  f.current.description = 'Add fresh aqueous NaBH4 solution.'; f.current.inputs = ['ligand-state'];
  assert.deepEqual(added(f), []);
});

test('direct material/stock behavior and chamber composition exclusion remain intact', () => {
  const f = fixture(); f.current.inputs.push('ligand');
  assert.deepEqual(added(f), ['fresh aqueous NaBH4 solution', 'Oleylamine']);
  f.current.action = 'deposit'; f.current.label = 'Deposit NaBH4 layer'; f.current.description = 'Deposit NaBH4 layer.';
  f.record.method = 'MBE';
  assert.deepEqual(added(f), []);
});

test('the current label may supply a literal addition when its description does not', () => {
  const f = fixture('Stir continuously.'); f.current.label = 'Add fresh aqueous NaBH4 solution';
  assert.deepEqual(added(f), ['fresh aqueous NaBH4 solution']);
});

test('stock mapping and literal labels do not mutate frozen records', () => {
  const f = fixture(); const raw = JSON.stringify(f.record);
  const freeze = value => {if (value && typeof value === 'object') {Object.values(value).forEach(freeze); Object.freeze(value);}};
  freeze(f.record); assert.deepEqual(added(f), ['fresh aqueous NaBH4 solution']);
  assert.equal(JSON.stringify(f.record), raw);
});


test('on-drawing facts sit by ports, duration and heated plate without duplicate rows', () => withDocument(() => {
  const materials = ['one', 'two', 'three', 'four'].map(id => ({id, name: id + ' precursor', role: 'metal_precursor'}));
  const scene = createReportedProtocolScene(op('heat', 'Heat and add', {inputs: materials.map(m => m.id),
    parameters: {temperature: q(180), duration: q(30, 'min')}, environment: {status: 'reported', value: 'Nitrogen'}}), rec({materials}),
    {formatQuantity: q => `${q.value} ${q.unit}`});
  const elements = all(scene), byClass = c => elements.find(n => n.className === c);
  assert.ok(byClass('reported-scene-inlet'));
  assert.equal(all(byClass('reported-scene-inlet')).filter(n => /precursor$/.test(n.textContent)).length, 3);
  assert.ok(!byClass('reported-scene-labels')); // the fourth full name is in its adjacent material chip
  assert.ok(all(byClass('reported-scene-heating-plate')).some(n => n.textContent === 'temperature: 180 degC'));
  assert.ok(all(byClass('reported-scene-atmosphere')).some(n => n.textContent === 'Nitrogen'));
  assert.ok(all(byClass('reported-scene-duration')).some(n => n.textContent === '30 min'));
  assert.ok(elements.filter(n => ['span', 'strong', 'dt', 'dd'].includes(n.tagName)).every(n => parseFloat(n.style.fontSize) >= 12));
}));

test('short labels use only an explicit name abbreviation and retain full record identity', () => {
  assert.equal(shortReportedSceneName('Trioctylphosphine (TOP)'), 'TOP');
  assert.equal(shortReportedSceneName('1-Dodecanethiol (DT)'), 'DT');
  for (const name of ['bis(trimethylsilyl) sulfide', 'copper(II) acetate', 'Unspecified material (II)',
    'octadecene', 'Long unnamed precursor', 'TOP solution (0.1 M)']) assert.equal(shortReportedSceneName(name), name);
  const record = freeze(rec({materials: [{id: 'top', name: 'Trioctylphosphine (TOP)', role: 'ligand'}]}));
  const chosen = choose(op('add', 'Add', {inputs: ['top']}), record);
  assert.deepEqual(chosen.added, ['Trioctylphosphine (TOP)']);
  assert.deepEqual(chosen.addedLabels, ['TOP']);
  assert.equal(record.materials[0].name, 'Trioctylphosphine (TOP)');
});

test('only facts absent from the drawing and adjacent cards retain detail rows', () => withDocument(() => {
  const materials = ['one', 'two', 'three', 'four'].map(id => ({id, name: id + ' precursor', role: 'metal_precursor'}));
  const stocks = [{id: 'stock', name: 'Separately prepared fifth stock', components: []}];
  const scene = createReportedProtocolScene(op('add', 'Add', {inputs: [...materials.map(m => m.id), 'stock'],
    vessel: {status: 'reported', value: 'Three-neck flask'},
    parameters: {temperature: q(180), duration: q(30, 'min'), pressure: q(2, 'bar'), exit_pressure: q(1, 'bar'), light_flux: q(5, 'a.u.')},
    environment: {status: 'reported', value: 'Nitrogen'}}), rec({materials, stocks}), {formatQuantity: q => `${q.value} ${q.unit}`});
  const rows = all(scene).filter(n => n.tagName === 'dd').map(n => n.textContent);
  assert.deepEqual(rows, ['Separately prepared fifth stock', 'Three-neck flask', '1 bar', '5 a.u.']);
  assert.ok(!rows.includes('four precursor') && !rows.includes('2 bar') && !rows.includes('Nitrogen'));
}));

test('glass shading is neutral and a stir bar and lit heater require own-step reports', () => withDocument(() => {
  for (const [operation, stirred, heated] of [
    [op('mix', 'Mix'), false, false], [op('stir', 'Stir'), true, false],
    [op('heat', 'Heat while stirring'), true, true],
    [op('mix', 'Mix', {description: 'Mix without stirring.'}), false, false],
  ]) {
    const scene = createReportedProtocolScene(operation, rec()), elements = all(scene);
    const svg = elements.find(n => n.tagName === 'svg');
    assert.match(svg.innerHTML, /linearGradient/);
    assert.equal(svg.innerHTML.includes('data-part="stir-bar"'), stirred);
    assert.equal(elements.some(n => n.className === 'reported-scene-heating-indicator'), heated);
  }
}));

test('three-neck gas ends above the open right neck and never crosses a side wall', () => withDocument(() => {
  const scene = createReportedProtocolScene(op('add', 'Add', {vessel: {status: 'reported', value: 'Three-neck flask'},
    environment: {status: 'reported', value: 'N2'}}), rec());
  const svg = all(scene).find(n => n.tagName === 'svg');
  const gas = /data-part="gas-line" d="M([0-9.]+) 17H195V57"/.exec(svg.innerHTML);
  assert.ok(gas);
  const [left, , width] = svg.attributes.viewBox.split(' ').map(Number);
  assert.ok(Number(gas[1]) >= left + width * .8 && Number(gas[1]) <= left + width);
  assert.doesNotMatch(svg.innerHTML, /M72 47h72v34h30/);
  assert.ok(!all(scene).some(n => n.className === 'reported-scene-heating-plate'));
}));

test('ambient air labels do not create a gas connection, absent facts create no callouts', () => withDocument(() => {
  const scene = createReportedProtocolScene(op('mix', 'Mix', {environment: {status: 'reported', value: 'Ambient air'}}), rec());
  const elements = all(scene);
  assert.ok(elements.some(n => n.textContent === 'Ambient air'));
  assert.doesNotMatch(elements.find(n => n.tagName === 'svg').innerHTML, /data-part="gas-line"/);
  assert.ok(!elements.some(n => ['reported-scene-inlet', 'reported-scene-duration', 'reported-scene-temperature'].includes(n.className)));
}));

test('separate rendered and enlarged scenes have unique gradient and clipping IDs', () => withDocument(() => {
  const a = all(createReportedProtocolScene(op('mix'), rec())).find(n => n.tagName === 'svg').innerHTML;
  const b = all(createReportedProtocolScene(op('mix'), rec())).find(n => n.tagName === 'svg').innerHTML;
  const ids = s => [...s.matchAll(/id="([^"]+)"/g)].map(m => m[1]);
  assert.ok(ids(a).every(id => !ids(b).includes(id)));
}));


test('explicit removal of heating leaves a plain temperature label without a plate', () => withDocument(() => {
  const operation = op('inject', 'Inject after heat was removed', {parameters: {temperature: q(200)}});
  assert.equal(choose(operation).heating, false);
  const scene = createReportedProtocolScene(operation, rec(), {formatQuantity: q => `${q.value} ${q.unit}`});
  assert.ok(!all(scene).some(n => n.className === 'reported-scene-heating-indicator'));
  assert.ok(!all(scene).some(n => n.className === 'reported-scene-heating-plate'));
  assert.ok(all(scene).some(n => n.textContent === 'temperature: 200 degC'));
}));

test('own As4 flux is labelled beside chamber beams without inferring a numeric flux', () => withDocument(() => {
  const scene = createReportedProtocolScene(op('grow', 'Grow GaAs', {environment: {status: 'reported', value: 'As4 flux'}}), rec({method: 'MBE'}));
  const feed = all(scene).find(n => n.className === 'reported-scene-inlet');
  assert.ok(feed && all(feed).some(n => n.textContent === 'As4 flux'));
}));


test('injection tips and gas lines meet every reported vessel opening without clipping', () => withDocument(() => {
  for (const [name, x, y, gx] of [['Three-neck flask',105,61,195],['Round-bottom flask',142,28,158],['Test tube',136,67,168],['Vial',129,69,176],['Beaker',122,75,190],['',124,83,185]]) {
    const operation=op('inject','Inject',{vessel:name?{status:'reported',value:name}:undefined,environment:{status:'reported',value:'N2'}});
    const svg=all(createReportedProtocolScene(operation,rec())).find(n=>n.tagName==='svg');
    assert.ok(svg.innerHTML.includes(`data-part="syringe" transform="translate(${x} ${y-118})"`));
    const gas = new RegExp(`data-part="gas-line" d="M([0-9.]+) 17H${gx}V${y-4}"`).exec(svg.innerHTML);
    assert.ok(gas);
    const [left, , width] = svg.attributes.viewBox.split(' ').map(Number);
    assert.ok(Number(gas[1]) >= left + width * .8 && Number(gas[1]) <= left + width);
    assert.ok(x - 10 >= left && x + 10 <= left + width);
    assert.ok(Number(svg.attributes.viewBox.split(' ')[1])<=y-124);
    assert.doesNotMatch(svg.innerHTML,/rotate\(-22\)/);
  }
}));


test('compact heater values retain typed bounds/ranges and never discard an unknown qualifier', () => {
  const format = x => (x.approximate ? '≈' : '') + quantityValue(x) + ' ' + x.unit
    + (x.qualifier ? ' · ' + x.qualifier : '') + (x.basis ? ' · ' + x.basis : '');
  for (const [quantity, expected] of [
    [{value: 580, unit: 'degC', basis: 'Reported substrate temperature'}, '580 degC'],
    [{value: null, maximum: 200, unit: 'degC', qualifier: 'reported upper bound'}, '≤200 degC'],
    [{value: null, minimum: 100, minimum_exclusive: true, unit: 'degC', qualifier: 'lower bound'}, '>100 degC'],
    [{value: null, minimum: 100, maximum: 200, unit: 'degC'}, '100–200 degC'],
    [{value: 180, unit: 'degC', approximate: true}, '≈180 degC'],
    [{value: 200, unit: 'degC', qualifier: 'Reported upper bound'}, null],
    [{value: 180, unit: 'degC', qualifier: 'At most, depending on the variant'}, null],
    [{value: null, unit: 'degC', qualifier: 'Room temperature'}, null],
  ]) {
    const original = structuredClone(quantity); freeze(quantity);
    assert.equal(compactReportedSceneQuantity(quantity, format), expected);
    assert.deepEqual(quantity, original);
  }
  assert.equal(compactReportedSceneQuantity(q(180), null), null);
  assert.equal(compactReportedSceneQuantity(q(180), () => 'Not reported'), null);
});

test('swiftly injected own stock resolves through its unique explicit preparation state only',()=>{
 const build=()=>{
  const prepare=op('dissolve','Prepare selenium stock',{id:'prepare-feed',inputs:['selenium'],outputs:['feed-output']}),batch=op('heat','Reheat the reaction batch',{id:'reheat',inputs:[],outputs:['reaction-output']}),inject=op('inject','Swiftly inject selenium stock',{id:'inject-feed',description:'Swiftly inject the selenium stock at270 degrees; no rate is stated.',inputs:['reaction-output','feed-output']});
  return rec({materials:[{id:'selenium',name:'Selenium',formula:'Se',role:'precursor'}],stocks:[{id:'own-feed',name:'Selenium in own reported carrier',preparation_operation_ids:['prepare-feed'],components:[{material_id:'selenium'}]}],material_states:[{id:'feed-output',name:'Prepare selenium stock output',kind:'stock',parent_ids:[]},{id:'reaction-output',name:'Reheated reaction batch',kind:'reaction_batch',parent_ids:[]}],operations:[prepare,batch,inject]});
 };
 const r=build(),o=r.operations[2],before=JSON.stringify(r);assert.deepEqual(choose(o,r).added,['selenium stock']);assert.equal(JSON.stringify(r),before);
 const reactionOnly=build();reactionOnly.operations[2].inputs=['reaction-output'];assert.deepEqual(choose(reactionOnly.operations[2],reactionOnly).added,[]);
 const absentStock=build();absentStock.stocks=[];assert.deepEqual(choose(absentStock.operations[2],absentStock).added,[]);
});

const repeatedAliasRecord=()=>{
 const materials=[{id:'metal',name:'InCl3',role:'metal_precursor'},{id:'feed',name:'tris(trimethylsilyl)arsine (TMS3As)',role:'chalcogen_precursor'},{id:'receiver',name:'trioctylphosphine (TOP)',role:'solvent'}];
 const prepare=op('mix','Prepare precursor solution',{id:'prepare',inputs:['metal','feed','receiver']}),inject=op('inject','Inject InCl3-TMS3As solution into TOP',{id:'inject',description:'Inject InCl3-TMS3As solution into TOP',inputs:['metal','feed','receiver']});
 return rec({materials,operations:[prepare,inject]});
};
test('repeated feed may use its own unique explicit terminal abbreviation before the destination',()=>{
 const r=repeatedAliasRecord(),before=JSON.stringify(r),spec=choose(r.operations[1],r);
 assert.deepEqual(spec.added,['InCl3','tris(trimethylsilyl)arsine (TMS3As)']);
 assert.deepEqual(spec.addedLabels,['InCl3','TMS3As']);assert.equal(JSON.stringify(r),before);
});
test('terminal abbreviations in receiving or later clauses do not create repeated inlet feeds',()=>{
 for(const label of ['Inject InCl3 into TMS3As','Inject InCl3 using TMS3As','Inject InCl3 before TMS3As','Inject InCl3 without TMS3As']){
  const r=repeatedAliasRecord();r.operations[1].label=label;r.operations[1].description=label;
  assert.deepEqual(choose(r.operations[1],r).added,['InCl3']);
 }
});
test('conditional or negative descriptions do not authorize an abbreviated repeat charge',()=>{
 for(const description of ['Optionally inject TMS3As','Do not inject TMS3As','If needed, inject TMS3As']){
  const r=repeatedAliasRecord();r.operations[1].description=description;
  assert.ok(!choose(r.operations[1],r).added.includes(r.materials[1].name));
 }
});
test('ambiguous own abbreviations and non-input names cannot authorize repeat feeds',()=>{
 const r=repeatedAliasRecord();r.materials.push({id:'ambiguous',name:'Another reported species (TMS3As)',role:'precursor'});
 assert.deepEqual(choose(r.operations[1],r).added,['InCl3']);
 const absent=repeatedAliasRecord();absent.operations[1].inputs=['metal','receiver'];assert.deepEqual(choose(absent.operations[1],absent).added,['InCl3']);
});
test('no short feed name is invented when the own material does not give an abbreviation',()=>{
 const r=repeatedAliasRecord();r.materials[1].name='tris(trimethylsilyl)arsine';assert.deepEqual(choose(r.operations[1],r).added,['InCl3']);
});
