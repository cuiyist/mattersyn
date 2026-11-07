// Shared Reader illustration primitives. Scientific strings enter textContent
// only. The glass/highlight palette follows the handmade neutral reaction vessel;
// its source-specific module and behavior are deliberately unchanged.
const ink = '#7899ad';
let sequence = 0;
// Ports are openings, not vessel walls. The injection tip and gas line share
// these anchors; narrow-neck vessels have separate left and right connections.
const portsFor = spec => ({
  'three-neck-flask': {inlet: [105, 61], gas: [195, 61]},
  flask: {inlet: [142, 28], gas: [158, 28]},
  tube: {inlet: [136, 67], gas: [168, 67]},
  vial: {inlet: [129, 69], gas: [176, 69]},
  beaker: {inlet: [122, 75], gas: [190, 75]},
  plain: {inlet: [124, 83], gas: [185, 83]},
}[spec.vesselKind] || {inlet: [124, 83], gas: [185, 83]});
const node = (tag, value) => {
  const n = document.createElement(tag);
  if (value !== undefined) n.textContent = value;
  Object.assign(n.style, {fontSize: '13px', lineHeight: '1.45', overflowWrap: 'anywhere', minWidth: '0'});
  return n;
};

function glassVessel(spec, id) {
  const round = 'M130 28H170V109C219 125 238 171 217 207C195 246 105 246 83 207C62 171 81 125 130 109Z';
  const three = 'M130 28H170V105L186 114V61H204V127C234 151 237 184 217 212C191 248 108 248 82 212C62 184 66 151 96 127V61H114V114L130 105Z';
  const shapes = {
    flask: round, 'three-neck-flask': three,
    tube: 'M118 67H182V204C182 248 118 248 118 204Z',
    vial: 'M109 69H191V223Q150 241 109 223Z',
    beaker: 'M91 75H195L210 67V221Q150 247 91 221Z',
    plain: 'M93 83H207V221Q150 245 93 221Z',
  };
  const shape = shapes[spec.vesselKind] || shapes.plain;
  const liquid = spec.kind !== 'dry-tube';
  // Liquid color and level are illustrative, never derived from product color,
  // yield, concentration or volume. No graduations, capacity or missing fittings.
  return `<defs><clipPath id="${id}-vessel"><path d="${shape}"/></clipPath></defs>
    <path d="${shape}" fill="url(#${id}-glass)" stroke="${ink}" stroke-width="2.5"/>
    <g clip-path="url(#${id}-vessel)">
      ${liquid ? `<path d="M63 175Q150 188 237 175V254H63Z" fill="url(#${id}-liquid)"/><ellipse cx="150" cy="177" rx="87" ry="10" fill="#d7dfdf" fill-opacity=".5"/>` : ''}
      <path d="M102 93V150Q83 194 110 218M137 38V113" fill="none" stroke="white" stroke-opacity=".85" stroke-width="6" stroke-linecap="round"/>
      ${spec.stirring ? '<path data-part="stir-bar" d="M134 219H166" stroke="#748f9e" stroke-width="7" stroke-linecap="round"/>' : ''}
    </g>
    ${['flask', 'three-neck-flask'].includes(spec.vesselKind) ? `<ellipse cx="150" cy="28" rx="22" ry="5" fill="#f8fcff" stroke="${ink}" stroke-width="2"/>` : ''}
    ${spec.vesselKind === 'three-neck-flask' ? `<path d="M94 61H116M184 61H206" stroke="${ink}" stroke-width="3"/>` : ''}`;
}

function geometry(spec, id) {
  const metal = `fill="url(#${id}-metal)" stroke="${ink}" stroke-width="2.5"`;
  const glass = `fill="url(#${id}-glass)" stroke="${ink}" stroke-width="2.5"`;
  const ports = portsFor(spec);
  let body;
  if (spec.kind === 'chamber') {
    body = `<rect x="27" y="54" width="246" height="175" rx="24" ${metal}/><rect x="45" y="73" width="210" height="135" rx="14" fill="#f7fbfd" stroke="#c4d5df" stroke-width="2"/>
      <path d="M124 176H213V187H124Z" fill="#b5c9d5" stroke="${ink}" stroke-width="2"/>
      ${spec.sourceFeed ? spec.beamSystem
        ? `<path data-part="source-beam" d="M63 75L159 169M90 88L178 167" stroke="#a2b8c5" stroke-width="3" stroke-dasharray="7 6"/><path d="M51 54L76 78M70 43L96 69" stroke="${ink}" stroke-width="9"/>`
        : `<path data-part="source-feed" d="M66 19V96H102V127" fill="none" stroke="${ink}" stroke-width="4"/>` : ''}`;
  } else if (spec.kind === 'closed-reactor') {
    body = `<rect x="91" y="64" width="118" height="173" rx="25" ${metal}/><path d="M79 64H221V46H79ZM103 28H197V46M115 16V28M185 16V28" ${metal}/><path d="M107 84V206" stroke="white" stroke-width="8" stroke-opacity=".65"/>`;
  } else if (spec.kind === 'furnace') {
    body = `<rect x="27" y="51" width="246" height="185" rx="18" ${metal}/><rect x="49" y="77" width="202" height="128" rx="8" fill="#f5f1e9" stroke="${ink}" stroke-width="2"/><path d="M113 155H187L175 186H125Z" fill="#dce5e9" stroke="${ink}" stroke-width="3"/><path d="M61 84V196" stroke="white" stroke-width="5"/>`;
  } else if (spec.kind === 'mortar-pestle') {
    body = `<path d="M65 135H235Q219 228 150 232Q81 228 65 135Z" ${metal}/><ellipse cx="150" cy="135" rx="85" ry="17" fill="#c3d1d9" stroke="${ink}" stroke-width="2.5"/><path d="M177 163L234 50Q241 34 228 29Q216 24 209 40L157 155Q151 168 162 173Q172 177 177 163Z" ${metal}/><path d="M82 157Q96 205 126 214" fill="none" stroke="white" stroke-width="6"/>`;
  } else if (spec.kind === 'mill-jar') {
    body = `<rect x="65" y="72" width="170" height="141" rx="35" ${metal}/><path d="M70 96H230M70 188H230" stroke="${ink}" stroke-width="3"/><path d="M84 107V172" stroke="white" stroke-width="6"/><g fill="#cedde5" stroke="${ink}" stroke-width="2"><circle cx="116" cy="140" r="15"/><circle cx="160" cy="166" r="14"/><circle cx="189" cy="132" r="14"/></g><path d="M49 139H20L31 128M251 139H280L269 150" fill="none" stroke="${ink}" stroke-width="3"/>`;
  } else if (spec.kind === 'filter') {
    body = `<path d="M72 53H228L164 145V183L136 193V145Z" ${glass}/><path d="M93 75H207L164 137H136Z" fill="#d7dfdf" fill-opacity=".5"/><path d="M109 200V239H191V200M150 192V214" fill="none" stroke="${ink}" stroke-width="3"/><path d="M87 61L140 137" stroke="white" stroke-width="5"/>`;
  } else if (spec.kind === 'centrifuge') {
    body = `<path d="M35 132V196C35 250 224 250 224 196V132" ${metal}/><ellipse cx="129" cy="132" rx="94" ry="64" ${glass}/><circle cx="129" cy="132" r="23" fill="#c8d8e2" stroke="${ink}" stroke-width="3"/><path d="M86 100L172 164M172 100L86 164" stroke="${ink}" stroke-width="8"/><path d="M246 96H278V207C278 232 246 232 246 207Z" ${glass}/><path d="M249 171H275V208Q262 227 249 208Z" fill="#c5d1d2" fill-opacity=".65"/>`;
  } else {
    body = glassVessel(spec, id);
    if (spec.kind === 'reflux') body += `<path d="M139 1H161V79H139Z" ${glass}/><path d="M150 3V77M139 18H123M161 61H177" fill="none" stroke="${ink}" stroke-width="3"/>`;
    if (spec.kind === 'inject') body += `<g data-part="syringe" transform="translate(${ports.inlet[0]} ${ports.inlet[1] - 118})"><path d="M-10 0H10M0 0V21M-9 21H9V69H-9ZM0 69V120" ${glass}/><path d="M-5 33V59" stroke="#c8d4d5" stroke-width="6"/></g>`;
    if (spec.kind === 'cool') body += `<path d="M257 100V179M247 168L257 179L267 168" fill="none" stroke="${ink}" stroke-width="3"/>`;
  }
  // Opposite ports: additions enter from the left; atmosphere enters at the
  // right opening. The three-neck gas line ends at the open side neck, never
  // across a wall or through the central reagent/syringe port.
  if (spec.added.length && spec.kind !== 'inject' && spec.kind !== 'chamber') {
    const [x, mouth] = ['furnace', 'closed-reactor', 'mill-jar', 'mortar-pestle', 'centrifuge'].includes(spec.kind)
      ? [75, 40] : spec.kind === 'filter' ? [110, 53] : ports.inlet;
    const y = mouth - 4;
    body += `<path data-part="addition-arrow" d="M31 17H${x}V${y}M${x - 6} ${y - 8}L${x} ${y}L${x + 6} ${y - 8}" fill="none" stroke="${ink}" stroke-width="2.5"/>`;
  }
  if (spec.gasLine) {
    const end = spec.vesselKind === 'three-neck-flask' && !['chamber', 'furnace', 'closed-reactor', 'mill-jar', 'filter', 'centrifuge'].includes(spec.kind)
      ? 'M276 17H195V57' : spec.kind === 'chamber' ? 'M276 17H237V52'
        : ['furnace', 'closed-reactor', 'mill-jar', 'filter', 'centrifuge'].includes(spec.kind) ? 'M276 17V40H240'
          : `M276 17H${ports.gas[0]}V${ports.gas[1] - 4}`;
    body += `<path data-part="gas-line" d="${end}" fill="none" stroke="#6c93a5" stroke-width="3" stroke-linecap="round"/>`;
  }
  return `<defs><linearGradient id="${id}-glass"><stop stop-color="#dcecf4" stop-opacity=".8"/><stop offset=".36" stop-color="#fafdff" stop-opacity=".55"/><stop offset="1" stop-color="#c3dbe8" stop-opacity=".7"/></linearGradient><linearGradient id="${id}-liquid" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#d7dfdf" stop-opacity=".5"/><stop offset="1" stop-color="#b7c7c9" stop-opacity=".65"/></linearGradient><linearGradient id="${id}-metal"><stop stop-color="#d6e2e9"/><stop offset=".45" stop-color="#f3f7fa"/><stop offset="1" stop-color="#b9ccd7"/></linearGradient></defs><ellipse cx="150" cy="247" rx="113" ry="7" fill="#7193a5" fill-opacity=".1"/>${body}`;
}

function factBlock(className, title, values) {
  if (!values.length) return null;
  const block = node('div'); block.className = className;
  Object.assign(block.style, {padding: '7px 9px', borderRadius: '8px', background: '#ffffffd9', border: '1px solid #dce6ec'});
  const heading = node('strong', title);
  Object.assign(heading.style, {display: 'block', fontWeight: '600', color: '#486475', marginBottom: '3px'});
  block.append(heading);
  for (const value of values) {const label = node('span', value); label.style.display = 'block'; block.append(label);}
  return block;
}

export function createReportedDrawing(spec, conditions) {
  const drawing = node('div'); drawing.className = 'reported-scene-drawing';
  drawing.dataset.stirring = String(spec.stirring);
  drawing.dataset.heating = String(spec.heating);
  Object.assign(drawing.style, {display: 'grid', gap: '8px', padding: '12px', borderRadius: '14px',
    background: 'linear-gradient(145deg,#f8fbfd,#edf3f6)', border: '1px solid #d8e3ea', boxSizing: 'border-box', width: '100%'});
  const upper = node('div'); upper.className = 'reported-scene-ports';
  Object.assign(upper.style, {display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: '8px', alignItems: 'end'});
  const feeds = spec.kind === 'chamber' ? [...spec.added.slice(0, 3),
    ...conditions.filter(c => /flux|beam|source/i.test(c.key)).map(c => `${c.key.replaceAll('_', ' ')}: ${c.value}`),
    ...(/\b(?:beam|flux)\b/i.test(spec.environment) && spec.sourceFeed ? [spec.environment] : [])] : spec.added.slice(0, 3);
  const inlet = factBlock('reported-scene-inlet', spec.kind === 'chamber' ? 'Sources / fluxes' : 'Added', feeds);
  const atmosphere = factBlock('reported-scene-atmosphere', 'Atmosphere', spec.environment ? [spec.environment] : []);
  if (inlet) {inlet.style.gridColumn = '1'; upper.append(inlet);}
  if (atmosphere) {atmosphere.style.gridColumn = '2'; upper.append(atmosphere);}
  if (inlet || atmosphere) drawing.append(upper);
  const middle = node('div'); middle.className = 'reported-scene-apparatus';
  const durations = conditions.filter(c => /duration|time/i.test(c.key)).map(c => c.value);
  const temperatures = conditions.filter(c => /temperature/i.test(c.key)).map(c => c.value);
  Object.assign(middle.style, {display: 'grid', gridTemplateColumns: durations.length ? 'minmax(0,1fr) minmax(60px,76px)' : 'minmax(0,1fr)', gap: '6px', alignItems: 'center'});
  const equipment = node('div'); equipment.className = 'reported-scene-equipment';
  Object.assign(equipment.style, {display: 'grid', justifyItems: 'center', minWidth: '0'});
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  const top = spec.kind === 'inject' ? Math.min(0, portsFor(spec).inlet[1] - 124) : 0;
  svg.setAttribute('viewBox', `0 ${top} 300 ${260 - top}`); svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', spec.kind.replaceAll('-', ' ') + ' operation diagram');
  Object.assign(svg.style, {display: 'block', width: '100%', height: 'auto', maxWidth: '340px'});
  svg.innerHTML = geometry(spec, `reported-art-${++sequence}`); // fixed markup only
  equipment.append(svg);
  if (spec.heating) {
    const plate = node('div'); plate.className = 'reported-scene-heating-plate';
    Object.assign(plate.style, {display: 'grid', gap: '3px', width: 'min(100%,220px)', boxSizing: 'border-box', textAlign: 'center', padding: '8px 10px', border: '1px solid #8aa2b2', borderTop: '5px solid #b6c7d2', borderRadius: '5px 5px 10px 10px', background: 'linear-gradient(#e4ecf1,#c4d3dd)', boxShadow: '0 3px 4px #4564761c'});
    const state = node('strong', 'HEATING');
    const lamp = node('i'); lamp.className = 'reported-scene-heating-indicator'; lamp.setAttribute('aria-hidden', 'true');
    Object.assign(lamp.style, {display: 'inline-block', width: '8px', height: '8px', marginLeft: '8px', borderRadius: '50%', background: '#dc9854', boxShadow: '0 0 5px #e8b982'});
    state.append(lamp); plate.append(state);
    for (const value of temperatures) plate.append(node('span', value));
    equipment.append(plate);
  } else if (temperatures.length) {
    // A reported temperature does not, by itself, invent a heated plate.
    equipment.append(factBlock('reported-scene-temperature', 'Temperature', temperatures));
  }
  middle.append(equipment);
  const time = factBlock('reported-scene-duration', 'Duration', durations);
  if (time) middle.append(time);
  drawing.append(middle);
  return drawing;
}
