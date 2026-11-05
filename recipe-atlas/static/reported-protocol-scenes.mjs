// Reader-only scenes. No record writes, paper/model reads or source-specific art.
// The caller preserves handmade/per-paper handlers and calls this only at the
// source-bound/generic fallback boundary. A null result retains the old image.
export const REPORTED_SCENE_CAVEAT = 'Schematic: vessel shapes and colors are illustrative.';

const text = value => typeof value === 'string' ? value.trim() : '';
const normalized = value => text(value).toLowerCase().replaceAll('_', ' ').replace(/\s+/g, ' ');
const missing = /^(?:not reported|not specified|unknown|unspecified|n\/?a|none)$/i;
const present = value => Boolean(text(value)) && !missing.test(text(value));
const reportedText = fact => fact?.status === 'reported' && present(fact.value) ? text(fact.value) : '';
const words = value => normalized(value).replace(/[-–—]/g, ' ');
const positive = (value, pattern) => {
  const s = words(value);
  if (!pattern.test(s)) return false;
  // Scope negation to the matching clause, rather than cancelling another
  // positive action elsewhere (e.g. reflux without chemical reduction).
  return s.split(/[.;]/).some(clause => pattern.test(clause)
    && !/\b(?:avoid|prevent|without|no|not|omit|exclude|rather than)\b[^,;]*$/.test(
      clause.slice(0, clause.search(pattern))));
};
const roomTemperature = q => q?.status === 'reported'
  && [q.qualifier, q.raw_text].some(value => /^room[- ]temperature\b/i.test(text(value)));
const quantityReported = q => q?.status === 'reported' && (roomTemperature(q) || present(q.unit)
  && [q.value, q.minimum, q.maximum].some(v => typeof v === 'number' && Number.isFinite(v)));
const conditionKeys = /(?:^|_)(?:temperature|duration|time|pressure|flux|beam_flux)(?:_|$)/i;
const solutionAction = /\b(?:dissolv\w*|add\w*|mix\w*|stir\w*|heat\w*|reflux\w*|inject\w*|degas\w*|purge\w*|cool\w*|quench\w*|react\w*|hold\w*|hydroly[sz]\w*|condens\w*|gel\w*|prepar\w*|combin\w*)\b/;
const depositionAction = /\b(?:grow\w*|deposit\w*|anneal\w*|epitax\w*|sputter\w*|evaporat\w*|supply\w*)\b/;
const chamberSystem = /\bmbe\b|molecular beam epitax|\bmocvd\b|\bmovpe\b|\bcvd\b|chemical vapou?r deposition|sputter|vacuum deposition|thermal evaporation|epitax|(?:growth|deposition|vacuum|evaporation) chamber/;
const closedSystem = /autoclave|hydrothermal|solvothermal|sealed (?:reactor|vessel)|pressure reactor/;

function reactorFacts(o, r, options) {
  // Reuse the existing strict parser supplied by the caller. Never JSON.parse
  // a source note here. Invalid/unavailable structured metadata supplies no facts.
  if (typeof options.readReactorLine !== 'function' || !text(o.environment?.note)) return null;
  const parsed = options.readReactorLine(o.environment.note);
  if (!parsed?.valid || !parsed.line) return null;
  const ids = new Set((r.sources || []).map(source => source.id));
  const categories = ['vessel_type', 'atmosphere', 'schlenk_line', 'glovebox', 'heating_method', 'stirring', 'addition_method', 'cooling_method'];
  const keys = parsed.scoped || parsed.attributes ? ['reactor_line_id', ...categories] : categories;
  if (!keys.every(key => {
    const field = parsed.line[key];
    if (parsed.attributes) return Array.isArray(field?.evidence) && field.evidence.every(e => ids.has(e.source_id));
    return !parsed.scoped && field?.status === 'not_reported' || ids.has(field?.source_id);
  })) return null;
  return parsed.line;
}

function operationVessel(o, line) {
  const fromLine = reportedText(line?.vessel_type);
  if (fromLine) return {value: fromLine, scope: 'step'};
  for (const key of ['vessel', 'vessel_type', 'reactor', 'equipment', 'system']) {
    const field = o?.[key] ?? o?.parameters?.[key];
    const value = reportedText(field);
    if (value) return {value, scope: 'step'};
  }
  return null;
}

function vesselKind(vessel) {
  const name = words(vessel?.value);
  if (/\b(?:three|3) neck/.test(name) && /flask/.test(name)) return 'three-neck-flask';
  if (/\bbeaker\b/.test(name)) return 'beaker';
  if (/\b(?:test |centrifuge )?tube\b/.test(name)) return 'tube';
  if (/\bvial\b/.test(name)) return 'vial';
  if (/\bflask\b/.test(name)) return 'flask';
  return 'plain';
}

function ownHotTemperature(o) {
  return Object.entries(o.parameters || {}).some(([key, q]) => {
    if (!/temperature/i.test(key) || !quantityReported(q)) return false;
    const value = Number.isFinite(q.value) ? q.value : q.minimum;
    if (!Number.isFinite(value)) return false; // an upper bound is not an exact hot charge
    const unit = text(q.unit).toLowerCase();
    const celsius = ['degc', '°c', 'c'].includes(unit) ? value : unit === 'k' ? value - 273.15 : null;
    return celsius !== null && celsius >= 100;
  });
}

function recipeVessel(r) {
  // This exact public record note is emitted by the existing to_site converter.
  // Keep its recipe scope; never imply a workup uses the synthesis vessel.
  const values = [...new Set((r.products || []).flatMap(p => p.notes || []).map(note =>
    /^Reactor:\s*(.+?)\s*\(Main PDF p\.[^)]*\)\.$/.exec(text(note))?.[1]).filter(Boolean))];
  if (values.length !== 1) return null;
  const value = values[0];
  if (!present(value) || /^(?:2 ml distilled water|thin films of silicon oxide|25 × 25 mm ito coated)/i.test(words(value))) return null;
  return {value, scope: 'recipe'};
}

function literalStockCharges(o, aliases) {
  // Read only an imperative addition clause in this operation. A destination,
  // prior preparation, conditional charge or carried mixture is not an addition.
  const escape = value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const ownTexts = [text(o.description), text(o.label)];
  const conditional = /\b(?:if|unless|optionally|optional|may|might|could|would|for later|as needed)\b/i;
  const negatedCharge = /\b(?:do not|never|avoid|omit|without)\s+(?:add\w*|inject\w*|introduc\w*|load\w*|supply\w*|feed\w*|pour\w*)\b/i;
  // A short label must not override a conditional/negative own description.
  if (ownTexts.some(own => conditional.test(own) || negatedCharge.test(own))) return [];
  for (const own of ownTexts) {
    const names = [];
    for (const clause of own.split(/\.(?=\s|$)|[;\n]/)) {
      const charge = /^\s*(?:(?:then|slowly|rapidly|carefully|dropwise|immediately)\s+)*(?:add|inject|introduce|load|supply|feed|pour)\s+(.+)$/i.exec(clause);
      if (!charge) continue;
      const object = charge[1].split(/\b(?:to|into|onto|through|over|under|at|with|without|in|while|for|using|after|before|and|except|excluding|rather than)\b/i)[0];
      if (/\b(?:no|not|never|avoid|omit|prevent)\b/i.test(object)) continue;
      for (const alias of aliases) {
        const name = escape(alias).replace(/\s+/g, '\\s+');
        const match = new RegExp('(^|[^A-Za-z0-9])((?:(?:fresh(?:ly prepared)?|aqueous)\\s+)*' + name
          + '(?:\\s+(?:solution|stock|suspension|dispersion|mixture))?)(?=$|[^A-Za-z0-9])', 'i').exec(object);
        if (match && !names.includes(match[2])) names.push(match[2]);
      }
    }
    if (names.length) return names.filter(name => !names.some(other => other !== name
      && other.toLowerCase().includes(name.toLowerCase())));
  }
  return [];
}

function preparedInputStockNames(id, o, r) {
  // A state may label a freshly added stock only with an unambiguous explicit
  // preparation-output link. Never expand carried states or every stock component.
  if ((r.material_states || []).filter(state => state.id === id).length !== 1
      || (r.materials || []).some(material => material.id === id)) return [];
  const operations = r.operations || [];
  const current = operations.map((step, index) => ({step, index})).filter(({step}) => step === o || step.id && step.id === o.id);
  const producers = operations.map((step, index) => ({step, index})).filter(({step}) => (step.outputs || []).includes(id));
  if (current.length !== 1 || producers.length !== 1) return [];
  const {step: prep, index} = producers[0];
  if (!prep.id || index >= current[0].index || prep.outputs.length !== 1
      || operations.filter(step => step.id === prep.id).length !== 1) return [];
  const stocks = (r.stocks || []).filter(stock => (stock.preparation_operation_ids || []).includes(prep.id));
  if (stocks.length !== 1) return [];
  const aliases = (stocks[0].components || []).flatMap(component => {
    const matches = (r.materials || []).filter(material => material.id === component.material_id);
    if (matches.length !== 1 || !(prep.inputs || []).includes(component.material_id)
        || ['apparatus', 'substrate'].includes(matches[0].role)) return [];
    return [matches[0].name, matches[0].formula].filter(present).map(text);
  });
  return literalStockCharges(o, [...new Set(aliases)]);
}

function addedNames(o, r, sceneKind) {
  const action = words(o.action), label = words(o.label);
  // A deposition input can describe the layer being grown rather than a feed.
  // Only explicit charging/supply actions name chamber reagents. Reported flux
  // conditions still draw their own feed, independently of these input names.
  const chamberCharge = /\b(?:add(?:ed|ing)?|inject(?:ed|ing)?|suppl(?:y|ied|ying)|feed(?:ing)?|fed|load(?:ed|ing)?)\b/;
  if (sceneKind === 'chamber' && !positive(action, chamberCharge) && !positive(label, chamberCharge)) return [];
  const adds = /\b(?:add\w*|dissolv\w*|prepar\w*|mix\w*|stir\w*|inject\w*|supply\w*|deposit\w*|load\w*|combin\w*|precipitat\w*|redisper\w*|resuspend\w*)\b/;
  if (!positive(action, adds) && !positive(label, /\b(?:add(?:ed|ing)?|inject(?:ed|ing)?|suppl(?:y|ied)|deposit(?:ed|ing)?)\b/)) return [];
  const materials = new Map((r.materials || []).filter(m => !['apparatus', 'substrate'].includes(m.role))
    .map(m => [m.id, text(m.name)]));
  const stocks = new Map((r.stocks || []).map(s => [s.id, text(s.name)]));
  const carried = new Set((r.material_states || []).map(s => s.id));
  const index = (r.operations || []).findIndex(step => step === o || step.id && step.id === o.id);
  const usedEarlier = new Set(index > 0 ? r.operations.slice(0, index).flatMap(step => step.inputs || []) : []);
  const names = [];
  for (const id of o.inputs || []) {
    if (carried.has(id)) {
      names.push(...preparedInputStockNames(id, o, r));
      continue;
    }
    const name = materials.get(id) || stocks.get(id);
    if (!present(name)) continue;
    // A repeated input may just describe the mixture already in the vessel.
    // Show a repeated charge only when this step explicitly names that input.
    if (usedEarlier.has(id) && !label.includes(words(name))) continue;
    // A formula-level GaAs input is not a measured Ga source. In droplet/flux
    // steps where the explicit step says Ga/gallium but not GaAs, omit this
    // ambiguous mapped input rather than renaming or inventing a reagent.
    if (sceneKind === 'chamber' && /\bgaas\b|gallium arsenide/i.test(name)
        && !/\bgaas\b|gallium arsenide/.test(label)) continue;
    names.push(name);
  }
  // Preserve a short explicit step spelling rather than relabel a contradictory
  // formula-level input (the Hanke Ga-droplet case).
  const literalGa = /\bGa atoms\b/i.exec(text(o.label));
  if (sceneKind === 'chamber' && literalGa && !names.length) names.push(literalGa[0]);
  return [...new Set(names)];
}

export function reportedProtocolSceneSpec(o, r = {}, options = {}) {
  if (!o || !present(o.action)) return null;
  const action = words(o.action), own = words([o.action, o.label].filter(Boolean).join(' '));
  const ownDetails = words([o.action, o.label, o.description].filter(Boolean).join(' '));
  if (/^(?:do not|never|avoid|omit|without)\b/.test(action)) return null;
  const method = words(options.routeLabel || r.method);
  const line = reactorFacts(o, r, options);
  const stepVessel = operationVessel(o, line);
  const vessel = stepVessel || recipeVessel(r);
  const system = words([stepVessel?.value, vessel?.value, method].filter(Boolean).join(' '));
  const environment = reportedText(line?.atmosphere) || reportedText(o.environment);
  const preparatory = /\b(?:for later|before|prior to|subsequent)\b/.test(own);
  const waferHeating = positive(action, /\b(?:heat\w*|desorb\w*)\b/)
    && positive(ownDetails, /\b(?:wafer|substrate)\b/);
  const liquidContext = positive(ownDetails, /\b(?:aqueous|solution|solvent|slurry|suspension|dispersion|dissolv\w*|water|ethanol|methanol|toluene|hexane|oleylamine|octadecene)\b/)
    && !positive(ownDetails, /\b(?:water|solvent) vapou?r\b/);
  const unsupportedSolidPreparation = positive(ownDetails, /\bmortar\b|\bpestle\b/)
    || positive(ownDetails, /\b(?:powders?|wafer|substrate|dry solids?)\b/) && !liquidContext;
  let kind = null;
  if (positive(action, /\bcentrifug\w*\b/)) kind = 'centrifuge';
  else if (positive(action, /\bfilter\w*\b/)) kind = 'filter';
  else if (positive(action, /\b(?:wash\w*|rins\w*|precipitat\w*|floccul\w*|redisper\w*|resuspend\w*)\b/)) kind = 'workup-tube';
  else if (positive(action, /\bdry\w*\b/)) kind = 'dry-tube';
  else if (positive(action, /\bevaporat\w*\b/) && /\bsolvent\b/.test(own)) kind = 'dry-tube';
  else if (positive(own, /\bball mill\w*\b/) && /\b(?:mill\w*|grind\w*)\b/.test(action)) kind = 'mill-jar';
  else if (!preparatory && (positive(action, depositionAction) || waferHeating)
      && (positive(system, chamberSystem) || positive(own, chamberSystem))) kind = 'chamber';
  else if (!preparatory && positive(action, /\b(?:heat\w*|react\w*|hold\w*|load\w*|hydrothermal|solvothermal)\b/)
      && (positive(system, closedSystem) || positive(own, closedSystem))) kind = 'closed-reactor';
  else if (positive(action, /\bcalcin\w*|\bsinter\w*/)
      || positive(action, /\bheat\w*\b/) && positive([own, system, reportedText(line?.heating_method)].join(' '), /furnace|solid state/)
      || positive(action, /\banneal\w*\b/) && positive([own, system].join(' '), /furnace|solid state/)) kind = 'furnace';
  else if (positive(action, solutionAction)) {
    // Dry preparation is not evidence of a liquid charge. Keep its admitted
    // original image when no supported solid apparatus was selected above.
    if (unsupportedSolidPreparation) return null;
    if (!preparatory && (positive(action, /\breflux\w*\b/)
        || positive(action, /\b(?:heat\w*|react\w*)\b/) && positive(own, /\breflux\w*\b/))
        && !/\bwithout\b.*\bcondenser\b/.test(own)) kind = 'reflux';
    else if (positive(action, /\binject\w*\b/)) kind = 'inject';
    else if (positive(action, /\b(?:cool\w*|quench\w*)\b/)) kind = 'cool';
    else if (positive(action, /\b(?:degas\w*|purge\w*)\b/)) kind = 'degas';
    else kind = 'solution';
  }
  if (!kind) return null;
  const workup = ['centrifuge', 'filter', 'workup-tube', 'dry-tube'].includes(kind);
  const useVessel = stepVessel || (!workup ? vessel : null);
  const heating = ['reflux', 'furnace'].includes(kind)
    || !workup && (positive(action, /\bheat\w*\b/)
      || ['solution', 'inject'].includes(kind) && ownHotTemperature(o));
  const gasLine = /nitrogen|argon|helium|hydrogen|oxygen|\bn2\b|\bar\b|\bo2\b|vacuum|inert|gas|flow|bubbl/i.test(environment)
    || positive(action, /\b(?:evacuat\w*|vacuum)\b/);
  const conditions = Object.entries(o.parameters || {}).filter(([key, q]) => conditionKeys.test(key) && quantityReported(q))
    .map(([key, quantity]) => ({key, quantity}));
  const added = addedNames(o, r, kind);
  const sourceFeed = kind === 'chamber' && (added.length > 0
    || conditions.some(c => /flux|beam|source/i.test(c.key))
    || positive(own, /\b(?:beam|flux|source feed)\b/)
    || /\b(?:as|sb)[24]\b|\b(?:beam|flux)\b/i.test(environment));
  return {
    kind, heating, gasLine, environment, vessel: useVessel,
    // Workup gets the requested generic tube symbol without claiming a reported
    // vessel name, capacity or fittings. A reported shape still takes precedence.
    vesselKind: useVessel ? vesselKind(useVessel) : workup ? 'tube' : 'plain',
    added, conditions, sourceFeed,
    beamSystem: /\bmbe\b|molecular beam epitax/.test(system + ' ' + own),
    // Only explicit current-step substrate inputs are named. No recipe-wide
    // material or substrate list is assigned to every deposition operation.
    substrates: kind === 'chamber' ? [...new Set((r.materials || []).filter(m =>
      m.role === 'substrate' && (o.inputs || []).includes(m.id) && present(m.name)).map(m => text(m.name)))] : [],
  };
}

export const reportedProtocolSceneDescriptor = reportedProtocolSceneSpec;

const glass = '#edf4f7', ink = '#668594';
const paths = {
  vessel: `<path d="M174 54h72v68c48 17 65 51 49 84-12 27-39 40-85 40s-73-13-85-40c-16-33 1-67 49-84Z" fill="${glass}" stroke="${ink}" stroke-width="3"/><path d="M131 194q79 18 158 0" fill="none" stroke="#adc4ce" stroke-width="3"/>`,
  heater: `<rect x="137" y="252" width="146" height="20" rx="5" fill="#dce6eb" stroke="${ink}" stroke-width="3"/><path d="M168 261h84" stroke="#a67d5b" stroke-width="3"/>`,
  syringe: `<g transform="translate(271 28) rotate(25)"><path d="M0 0v22m-13-22h26m-9 22v55h-18V22Zm-9 55v49" fill="${glass}" stroke="${ink}" stroke-width="3"/></g>`,
  gas: `<path d="M72 47h72v34h30m-42-34v-18" fill="none" stroke="${ink}" stroke-width="3"/>`,
  tube: `<path d="M165 64h90v145c0 46-90 46-90 0Z" fill="${glass}" stroke="${ink}" stroke-width="3"/><path d="M168 177q42 12 84 0" fill="none" stroke="#adc4ce" stroke-width="3"/>`,
};

function solutionVessel(spec) {
  if (spec.vesselKind === 'three-neck-flask') return paths.vessel
    + `<path d="M151 130V78h20v40M249 130V78h20v40" fill="${glass}" stroke="${ink}" stroke-width="3"/>`;
  if (spec.vesselKind === 'flask') return paths.vessel;
  if (spec.vesselKind === 'tube') return paths.tube;
  if (spec.vesselKind === 'vial') return `<path d="M163 78h94v145q-47 27-94 0Z" fill="${glass}" stroke="${ink}" stroke-width="3"/><path d="M159 78h102" stroke="${ink}" stroke-width="5"/>`;
  if (spec.vesselKind === 'beaker') return `<path d="M147 84h112l16-10v150q-64 29-128 0Z" fill="${glass}" stroke="${ink}" stroke-width="3"/>`;
  // No narrow neck, side arms, graduation, capacity or fitted lid when absent.
  return `<path d="M148 98h124v126q-62 28-124 0Z" fill="${glass}" stroke="${ink}" stroke-width="3"/><path d="M151 180q59 12 118 0" fill="none" stroke="#adc4ce" stroke-width="3"/>`;
}

function diagram(spec) {
  const {kind} = spec;
  if (kind === 'chamber') return `<rect x="60" y="48" width="300" height="180" rx="22" fill="${glass}" stroke="${ink}" stroke-width="3"/><path d="M180 180h100v13H180z" fill="none" stroke="${ink}" stroke-width="3"/>`
    + (spec.sourceFeed ? spec.beamSystem
      ? `<path d="M95 85l70 60m-48-9 48 9-9-47" fill="none" stroke="${ink}" stroke-width="3"/>`
      : `<path d="M109 25v50h34v57" fill="none" stroke="${ink}" stroke-width="3"/>` : '')
    + (spec.gasLine ? paths.gas : '');
  if (kind === 'closed-reactor') return `<rect x="142" y="61" width="136" height="179" rx="25" fill="${glass}" stroke="${ink}" stroke-width="4"/><path d="M127 62h166v-16H127zM160 26h100v20M177 9v18m66-18v18" fill="${glass}" stroke="${ink}" stroke-width="3"/>`;
  if (kind === 'furnace') return `<rect x="65" y="45" width="290" height="194" rx="14" fill="#eef1f3" stroke="${ink}" stroke-width="4"/><rect x="94" y="77" width="232" height="126" rx="8" fill="#f6f6f3" stroke="${ink}" stroke-width="2"/><path d="M170 158h80l-12 28h-56Z" fill="${glass}" stroke="${ink}" stroke-width="3"/>`;
  if (kind === 'mill-jar') return `<rect x="119" y="71" width="182" height="139" rx="36" fill="${glass}" stroke="${ink}" stroke-width="4"/><path d="M125 100h170M130 180h160M94 139H59m12-11-12 11 12 11m255-11h35m-12-11 12 11-12 11" fill="none" stroke="${ink}" stroke-width="3"/><g fill="#cedde5" stroke="${ink}" stroke-width="2"><circle cx="172" cy="136" r="13"/><circle cx="221" cy="163" r="13"/><circle cx="248" cy="126" r="13"/></g>`;
  if (kind === 'filter') return `<path d="M115 46h190l-80 110v36l-30 10v-46Z" fill="${glass}" stroke="${ink}" stroke-width="3"/><path d="M164 219v43h92v-43M210 196v31" fill="none" stroke="${ink}" stroke-width="3"/>`;
  if (kind === 'centrifuge') return `<ellipse cx="170" cy="147" rx="99" ry="69" fill="${glass}" stroke="${ink}" stroke-width="4"/><circle cx="170" cy="147" r="24" fill="#dbe6ec" stroke="${ink}" stroke-width="3"/><path d="m125 111 90 72m0-72-90 72" stroke="${ink}" stroke-width="8"/><g transform="translate(132 0) scale(.8)">${paths.tube}</g>`;
  if (kind === 'workup-tube' || kind === 'dry-tube') return solutionVessel(spec) + (spec.gasLine ? paths.gas : '');
  if (kind === 'reflux') return `<path d="M190 12h40v105h-40zM210 117v20M190 36h-22m62 56h22" fill="${glass}" stroke="${ink}" stroke-width="3"/>` + solutionVessel(spec) + paths.heater + (spec.gasLine ? paths.gas : '');
  return solutionVessel(spec) + (spec.heating ? paths.heater : '') + (kind === 'inject' ? paths.syringe : '')
    + (spec.gasLine ? paths.gas : '') + (kind === 'cool' ? `<path d="M330 93v92m-13-16 13 16 13-16" fill="none" stroke="${ink}" stroke-width="3"/>` : '');
}

function htmlNode(tag, value) {
  const n = document.createElement(tag);
  if (value !== undefined) n.textContent = value;
  n.style.fontSize = '13px';
  n.style.lineHeight = '1.45';
  n.style.overflowWrap = 'anywhere';
  n.style.minWidth = '0';
  return n;
}

export function createReportedProtocolScene(o, r, options = {}) {
  const spec = reportedProtocolSceneSpec(o, r, options);
  if (!spec) return null;
  const host = document.createElement('div');
  host.className = 'protocol-art protocol-art-reported';
  host.dataset.scene = spec.kind;
  host.dataset.renderer = 'reported-fields';
  host.dataset.reportedScene = 'true';
  Object.assign(host.style, {display: 'grid', gridTemplateColumns: 'minmax(0,1fr)',
    height: 'auto', minHeight: '260px', minWidth: '0', width: '100%', gap: '12px'});
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 420 280');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', (['workup-tube', 'dry-tube'].includes(spec.kind)
    ? spec.kind.replace('-tube', '') : spec.kind).replaceAll('-', ' ') + ' operation diagram');
  svg.style.width = '100%';
  svg.style.height = 'auto';
  svg.style.maxHeight = '280px';
  svg.innerHTML = diagram(spec); // Fixed geometry only: never record-provided markup.
  const labels = htmlNode('dl');
  labels.className = 'reported-scene-labels';
  Object.assign(labels.style, {margin: '0', display: 'grid', gap: '7px'});
  const row = (title, value) => {
    if (!present(value)) return;
    const group = htmlNode('div'), dt = htmlNode('dt', title), dd = htmlNode('dd', value);
    dd.style.margin = '2px 0 0';
    group.append(dt, dd); labels.append(group);
  };
  if (spec.added.length) row('Added this step', spec.added.join('; '));
  if (spec.substrates.length) row('Reported substrate', spec.substrates.join('; '));
  if (spec.vessel) row(spec.vessel.scope === 'recipe' ? 'Reported recipe vessel' : 'Reported vessel', spec.vessel.value);
  for (const {key, quantity} of spec.conditions) {
    // The existing Reader amount() formatter retains qualifiers and bases.
    // Do not invent a replacement when no formatter was supplied.
    let formatted = typeof options.formatQuantity === 'function' ? options.formatQuantity(quantity) : '';
    if ((!present(formatted) || /not reported|unavailable/i.test(formatted)) && roomTemperature(quantity))
      formatted = text(quantity.raw_text) || text(quantity.qualifier);
    if (present(formatted) && !/not reported|unavailable/i.test(formatted)) row(key.replaceAll('_', ' '), formatted);
  }
  if (spec.environment) row('Reported atmosphere', spec.environment);
  host.append(svg, labels);
  return host;
}
