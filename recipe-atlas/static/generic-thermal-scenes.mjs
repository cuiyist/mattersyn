const SVG_NS = 'http://www.w3.org/2000/svg';

const refluxMarkup = `
  <title>Reflux apparatus schematic</title>
  <desc>A stirred vessel below a vertical condenser. Geometry and colors are illustrative.</desc>
  <rect x="130" y="22" width="76" height="115" rx="15" fill="#edf7fb" stroke="#52778b" stroke-width="4"/>
  <path d="M143 31V122M193 31V122" stroke="#9cb8c5" stroke-width="2"/>
  <path d="M168 4V20M168 138V155" stroke="#52778b" stroke-width="4"/>
  <path d="M168 155V171" stroke="#52778b" stroke-width="4"/>
  <path d="M143 48H117V72M193 112H219V88" fill="none" stroke="#52778b" stroke-width="3"/>
  <path d="M113 71l4-8 5 8M215 89l4 8 5-8" fill="none" stroke="#52778b" stroke-width="2"/>
  <path d="M130 171H206L222 203C222 235 202 254 168 254S114 235 114 203Z" fill="#e4f2f8" fill-opacity=".8" stroke="#52778b" stroke-width="4"/>
  <path d="M119 211Q168 225 217 211" fill="none" stroke="#9fc8d4" stroke-width="3"/>
  <path d="M168 178V225M152 225H184" stroke="#52778b" stroke-width="3" stroke-linecap="round"/>
  <path d="M123 263H213L224 282H112Z" fill="#dce7ec" stroke="#7896a5" stroke-width="3"/>
  <path d="M145 272q5-8 10 0t10 0t10 0" fill="none" stroke="#cc8c55" stroke-width="3"/>
  <text x="168" y="18" text-anchor="middle" font-size="11" fill="#36596d">CONDENSER</text>
  <text x="168" y="303" text-anchor="middle" font-size="12" fill="#36596d">illustrative heat source</text>
`;

const refluxWaterLabels = `
  <text x="93" y="72" text-anchor="end" font-size="10" fill="#36596d">water in</text>
  <text x="239" y="90" text-anchor="start" font-size="10" fill="#36596d">water out</text>
`;

const thermalTreatmentMarkup = `
  <title>Thermal treatment schematic</title>
  <desc>A sample container shown in a generic heating zone. Equipment geometry is illustrative.</desc>
  <rect x="47" y="51" width="242" height="184" rx="18" fill="#f1f4f4" stroke="#607987" stroke-width="4"/>
  <rect x="75" y="82" width="186" height="117" rx="10" fill="#fff8ee" stroke="#b67a55" stroke-width="3"/>
  <path d="M103 177v-17q20-18 40 0t40 0t40 0v17q-20 16-40 0t-40 0t-40 0" fill="none" stroke="#d39a63" stroke-width="3"/>
  <path d="M130 144h76l-8 20h-60z" fill="#dbe8ed" stroke="#627f8d" stroke-width="3"/>
  <path d="M141 140h54" stroke="#627f8d" stroke-width="3"/>
  <path d="M90 225v17M246 225v17M111 244h114" stroke="#607987" stroke-width="4"/>
  <circle cx="271" cy="61" r="5" fill="#56a6a2"/>
  <text x="168" y="73" text-anchor="middle" font-size="12" fill="#36596d">HEATING ZONE · SCHEMATIC</text>
  <text x="168" y="283" text-anchor="middle" font-size="12" fill="#36596d">schematic only · see text for reported equipment</text>
`;

function appendSVG(host, markup, extra = '') {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 336 312');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', host.getAttribute('aria-label'));
  svg.setAttribute('style', 'display:block;width:100%;max-height:320px;margin:auto');
  svg.innerHTML = markup + extra;
  host.append(svg);
}

export function genericThermalSceneKind(operation, operationType) {
  const action = String(operation?.action || '').toLowerCase();
  const label = String(operation?.label || '').toLowerCase();
  if (operationType === 'heat' && /reflux/.test(`${action} ${label}`)) return 'reflux';
  if (/\b(calcine|calcination|anneal|annealing|sinter|sintering)\b/.test(`${action} ${label}`)) return 'thermal-treatment';
  return null;
}

export function createGenericThermalScene(operation, operationType) {
  const sceneKind = genericThermalSceneKind(operation, operationType);
  if (!sceneKind) return null;

  const host = document.createElement('div');
  host.className = `protocol-art protocol-art-${sceneKind}`;
  host.dataset.scene = sceneKind;
  const action = String(operation?.action || '').toLowerCase();
  const label = String(operation?.label || '').toLowerCase();
  const description = String(operation?.description || '').toLowerCase();
  const waterCondenser = /water[- ]cooled condenser|water condenser/.test(`${action} ${label} ${description}`);
  if (sceneKind === 'reflux') {
    host.setAttribute('role', 'img');
    host.setAttribute('aria-label', 'Reflux stage schematic with a condenser and heated reaction vessel');
    appendSVG(host, refluxMarkup, waterCondenser ? refluxWaterLabels : '');
  } else {
    host.setAttribute('role', 'img');
    host.setAttribute('aria-label', 'Illustrative thermal-treatment stage; apparatus geometry is not source-specific');
    appendSVG(host, thermalTreatmentMarkup);
  }
  return host;
}
