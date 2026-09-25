const routeId = 'thomson-2010-bi2s3-ultrathin-nanowires';
const sourceId = 'thomson2010ja101908k';
const sourcePdfSha256 = '3ce8c6d86971ca1f31a4b986559f44ec3185b5b7672675b1dee0e4f50cabc0db';

const stages = {
  'prepare-sulfur-in-oleylamine': {
    kind: 'stock-vial', label: 'Sulfur-in-oleylamine stock',
    locator: 'Main PDF p. 2 (printed p. 9059), Experimental Section, Synthesis of Bi2S3 Nanowires',
    note: 'The article reports the charged amounts, but not stock-preparation temperature, duration, or dissolution endpoint.'
  },
  'suspend-bismuth-citrate': {
    kind: 'charge-flask', label: 'Three-neck reaction flask',
    locator: 'Main PDF p. 2 (printed p. 9059), Experimental Section, Synthesis of Bi2S3 Nanowires',
    note: 'Flask capacity, fill level, and stirring hardware/rate are not reported.'
  },
  'vacuum-heat-100c': {
    kind: 'vacuum-conditioning', label: 'Vacuum conditioning',
    locator: 'Main PDF p. 2 (printed p. 9059), Experimental Section, Synthesis of Bi2S3 Nanowires',
    note: 'Vacuum level and detailed heating apparatus are not reported.'
  },
  'nitrogen-heat-160c': {
    kind: 'nitrogen-heating', label: 'Nitrogen-atmosphere heating',
    locator: 'Main PDF p. 2 (printed p. 9059), Experimental Section, Synthesis of Bi2S3 Nanowires',
    note: 'The nitrogen step follows vacuum conditioning; the two atmospheres are sequential.'
  },
  'cool-to-130c': {
    kind: 'cooling', label: 'Cool before injection',
    locator: 'Main PDF p. 2 (printed p. 9059), Experimental Section, Synthesis of Bi2S3 Nanowires',
    note: 'No cooling rate or probe location is reported.'
  },
  'inject-sulfur-solution': {
    kind: 'septum-injection', label: 'Sulfur-solution injection',
    locator: 'Main PDF p. 2 (printed p. 9059), Experimental Section, Synthesis of Bi2S3 Nanowires',
    note: 'The source names syringe injection through a septum; injection rate and duration are not reported.'
  },
  'post-injection-growth': {
    kind: 'post-injection-hold', label: 'Post-injection growth hold',
    locator: 'Main PDF p. 2 (printed p. 9059), Experimental Section, Synthesis of Bi2S3 Nanowires',
    note: 'The source first cools to 130 °C before injection, then says temperature was “increased to 100 °C.” Preserve this unresolved sequence tension and the 15–45 min interval; no exact-time sample assignment is available.'
  },
  'quench-and-purify': {
    kind: 'quench-separate', label: 'Quench and precipitation workup',
    locator: 'Main PDF p. 2 (printed p. 9059), Experimental Section, Synthesis of Bi2S3 Nanowires',
    note: 'Toluene quench, acetone precipitation, centrifugation, and toluene redispersion are reported; solvent volumes and centrifuge settings are not.'
  },
  'hda-ligand-exchange': {
    kind: 'ligand-exchange', label: 'Post-growth HDA treatment',
    locator: 'Main PDF p. 3 (printed p. 9060), Experimental Section, Ligand Exchange with Hexadecylamine',
    note: 'This is a distinct post-growth treatment context. Exact excess, temperature, concentration, stirring rate, and parent-batch link are not reported.'
  },
  'hda-cleanup': {
    kind: 'exchange-cleanup', label: 'Exchange-product cleanup',
    locator: 'Main PDF p. 3 (printed p. 9060), Experimental Section, Ligand Exchange with Hexadecylamine',
    note: 'Vacuum drying is reported as overnight, but no drying temperature, solvent quantity, or centrifuge setting is stated.'
  },
  'prepare-nmr-aliquot': {
    kind: 'nmr-aliquot', label: 'NMR sample preparation',
    locator: 'Main PDF pp. 2–3 (printed pp. 9059–9060), NMR sample preparation',
    note: 'This preparation description is not a specific assignment to every plotted spectrum; Figures 6–7 identify CDCl3, while the concentration method below uses d8-toluene.'
  },
  'prepare-vt-nmr': {
    kind: 'vt-nmr-context', label: 'Variable-temperature NMR context',
    locator: 'Main PDF p. 7 (printed p. 9064), variable-temperature NMR',
    note: 'Characterization only: do not depict as a synthesis operation or transfer its temperature span to growth.'
  },
  'quantify-n-bi-by-nmr': {
    kind: 'nmr-concentration-method', label: 'NMR concentration-measurement method',
    locator: 'Main PDF p. 3 (printed p. 9060), Experimental Section, NMR',
    note: 'Method context only, with no named batch assignment: known CH2Br2 in 750 µL nanowire dispersion in d8-toluene, 45 s interscan delay, 400 MHz at 25 °C, referenced to proteo-solvent impurity. Do not apply these settings to Figures 6–7, whose captions specify CDCl3.'
  }
};

const descriptions = {
  'stock-vial': 'A stock-solution vial and transfer arrow; no heat source is shown.',
  'charge-flask': 'A three-neck flask with a source-defined initial charge; vessel size and liquid level are not encoded.',
  'vacuum-conditioning': 'A flask connected to a generic vacuum line; no vacuum gauge value is implied.',
  'nitrogen-heating': 'A generic heated flask with a nitrogen line; no particular heater or flow rate is asserted.',
  'cooling': 'A reaction flask with outward cooling marks; no rate or cooling bath is implied.',
  'septum-injection': 'A septum-port flask and syringe indicate the reported injection action only.',
  'post-injection-hold': 'A reaction flask on a generic heater; temperature wording remains in the source-linked note.',
  'quench-separate': 'A transfer into a workup vial beside a generic centrifuge symbol.',
  'ligand-exchange': 'Two solution contexts with an exchange arrow; the graphic does not imply stoichiometric excess or batch lineage.',
  'exchange-cleanup': 'A separated-material workflow with a vacuum-drying symbol; no temperature is shown.',
  'nmr-aliquot': 'An aliquot vial and generic NMR tube; no spectrum or structure is synthesized by the graphic.',
  'vt-nmr-context': 'An NMR tube next to a generic variable-temperature instrument symbol; values remain in the adjacent condition text.',
  'nmr-concentration-method': 'An NMR concentration-method context with a reference-solution vial and spectrometer symbol; no batch identity is implied.'
};

const esc = x => String(x ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const paths = {
  vial: '<path d="M145 70H255V91H239V247Q200 268 161 247V91H145Z" fill="#edf6fa" stroke="#608497" stroke-width="4"/><path d="M163 180Q200 188 237 180V245Q200 260 163 245Z" fill="#d8bc79" opacity=".65"/>',
  flask: '<path d="M179 55H221V139C271 157 294 194 279 237C264 275 136 275 121 237C106 194 129 157 179 139Z" fill="#edf6fa" stroke="#608497" stroke-width="4"/><path d="M128 216Q200 229 272 216" fill="none" stroke="#d2b26c" stroke-width="12" opacity=".72"/><path d="M181 58H219M176 48H224" stroke="#608497" stroke-width="4"/>',
  threeNeck: '<path d="M180 50V136C130 151 106 190 117 232C128 273 272 273 283 232C294 190 270 151 220 136V50" fill="#edf6fa" stroke="#608497" stroke-width="4"/><path d="M156 51V28H176V52M190 51V21H210V51M224 51V28H244V52" fill="#edf6fa" stroke="#608497" stroke-width="4"/><path d="M120 212Q200 226 280 212" fill="none" stroke="#d2b26c" stroke-width="12" opacity=".72"/>',
  vacuum: '<path d="M181 55H219V136C269 155 291 194 279 236C267 274 133 274 121 236C109 194 131 155 181 136Z" fill="#edf6fa" stroke="#608497" stroke-width="4"/><path d="M201 56V28H104V72" fill="none" stroke="#718f9d" stroke-width="5"/><rect x="87" y="70" width="34" height="16" rx="4" fill="#d7e7ed" stroke="#718f9d" stroke-width="3"/>',
  n2: '<path d="M182 56H218V137C268 155 291 195 279 237C267 275 133 275 121 237C109 195 132 155 182 137Z" fill="#edf6fa" stroke="#608497" stroke-width="4"/><path d="M199 55V28H292V73" fill="none" stroke="#668fa1" stroke-width="5"/><path d="M284 62L292 73L300 62" fill="none" stroke="#668fa1" stroke-width="4"/><rect x="102" y="249" width="196" height="18" rx="8" fill="#c49a61" opacity=".8"/>',
  cool: '<path d="M182 57H218V137C268 155 291 194 279 236C267 274 133 274 121 236C109 194 132 155 182 137Z" fill="#edf6fa" stroke="#608497" stroke-width="4"/><path d="M98 140l20-8M96 172l23 0M100 204l20 8M302 140l-20-8M304 172l-23 0M300 204l-20 8" stroke="#78a9bd" stroke-width="5" stroke-linecap="round"/>',
  syringe: '<path d="M112 91L193 172M101 101L123 80M104 78L179 153M190 168L209 149L218 158L199 177M212 146L231 127" stroke="#718b97" stroke-width="7" stroke-linecap="round"/><path d="M229 126L248 107" stroke="#718b97" stroke-width="3"/>',
  growth: '<path d="M180 58H220V137C270 155 292 195 280 236C268 274 132 274 120 236C108 195 130 155 180 137Z" fill="#edf6fa" stroke="#608497" stroke-width="4"/><circle cx="172" cy="192" r="7" fill="#567384"/><circle cx="205" cy="212" r="7" fill="#567384"/><circle cx="231" cy="187" r="7" fill="#567384"/><rect x="112" y="250" width="176" height="16" rx="8" fill="#c49a61" opacity=".8"/>',
  centrifuge: '<circle cx="156" cy="181" r="79" fill="#f0f7fa" stroke="#6c8d9a" stroke-width="4"/><circle cx="156" cy="181" r="17" fill="#9bb5c1"/><path d="M106 131L206 231M106 231L206 131" stroke="#6c8d9a" stroke-width="10"/><path d="M251 133H322V231Q286 244 251 231Z" fill="#e6f2f6" stroke="#6c8d9a" stroke-width="4"/><path d="M254 204H319" stroke="#88b6c4" stroke-width="17" opacity=".6"/>',
  exchange: '<path d="M49 108H131L124 229Q90 244 56 229Z" fill="#edf6fa" stroke="#6c8d9a" stroke-width="4"/><path d="M205 108H287L280 229Q246 244 212 229Z" fill="#edf6fa" stroke="#6c8d9a" stroke-width="4"/><path d="M131 168H205M189 153L205 168L189 183" fill="none" stroke="#708d9b" stroke-width="5"/><circle cx="79" cy="196" r="6" fill="#8292aa"/><circle cx="98" cy="204" r="6" fill="#8292aa"/><circle cx="236" cy="199" r="6" fill="#8292aa"/>',
  dry: '<path d="M93 120H307V237H93Z" fill="#edf4f7" stroke="#6c8d9a" stroke-width="4"/><path d="M107 144H293V225H107Z" fill="#fff" stroke="#9eb5bf" stroke-width="2"/><path d="M121 205Q200 216 279 205" stroke="#d5b46d" stroke-width="10"/><path d="M108 98H292" stroke="#6c8d9a" stroke-width="5"/><path d="M200 98V66H315" fill="none" stroke="#6c8d9a" stroke-width="5"/>',
  nmr: '<rect x="92" y="76" width="76" height="170" rx="22" fill="#edf6fa" stroke="#6a8d9d" stroke-width="4"/><path d="M100 174Q130 182 160 174V232H100Z" fill="#a8cbd7" opacity=".65"/><rect x="218" y="76" width="76" height="170" rx="22" fill="#e5eef3" stroke="#6a8d9d" stroke-width="4"/><path d="M201 117V210" stroke="#8097a3" stroke-width="7"/><path d="M184 137H218M184 190H218" stroke="#8097a3" stroke-width="7"/>',
  concentration: '<path d="M80 114H153V235Q116 250 80 235Z" fill="#edf6fa" stroke="#6c8d9a" stroke-width="4"/><path d="M92 201Q116 207 141 201V232Q116 243 92 232Z" fill="#b8cbd5"/><path d="M232 68H296V249H232Z" fill="#eaf1f4" stroke="#6c8d9a" stroke-width="4"/><path d="M245 90H283V228H245Z" fill="#fff" stroke="#a4bac4" stroke-width="2"/><path d="M198 160H226M216 150L226 160L216 170" fill="none" stroke="#718b97" stroke-width="4"/>'
};
const stageDraw = {
  'stock-vial': ['vial', 'Make injection stock'],
  'charge-flask': ['flask', 'Charged precursor suspension'],
  'vacuum-conditioning': ['vacuum', 'Vacuum conditioning'],
  'nitrogen-heating': ['n2', 'N₂ atmosphere'],
  'cooling': ['cool', 'Cooling'],
  'septum-injection': ['threeNeck', 'Septum injection'],
  'post-injection-hold': ['growth', 'Post-injection hold'],
  'quench-separate': ['centrifuge', 'Quench / separate'],
  'ligand-exchange': ['exchange', 'Post-growth exchange'],
  'exchange-cleanup': ['dry', 'Cleanup / dry'],
  'nmr-aliquot': ['nmr', 'Aliquot preparation'],
  'vt-nmr-context': ['nmr', 'Variable-temperature NMR'],
  'nmr-concentration-method': ['concentration', 'Concentration-measurement method']
};

function stageFor(o, r) {
  if (r?.record_id !== routeId || r?.lineage?.source_group !== sourceId) return null;
  const stage = stages[o?.id];
  return stage ? { ...stage, draw: stageDraw[stage.kind], operationId: o.id, sourceSha256: sourcePdfSha256 } : null;
}
export function buildThomson2010Scene(o, r) {
  const s = stageFor(o, r);
  return s ? { ...s, caption: `${s.locator}. ${s.note} Geometry and vessels in the illustration are conceptual, not measured.` } : null;
}
export function createThomson2010Art(o, r) {
  const s = stageFor(o, r);
  if (!s) return null;
  const [key, label] = s.draw;
  const host = document.createElement('div');
  host.className = `protocol-art protocol-art-thomson2010 protocol-art-thomson2010-${s.kind}`;
  const desc = `${descriptions[s.kind]} Source locator: ${s.locator}. ${s.note}`;
  host.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 320" role="img" aria-label="${esc(label)}"><title>${esc(label)}</title><desc>${esc(desc)}</desc><rect x="8" y="8" width="384" height="304" rx="20" fill="#f6fafc"/>${paths[key]}<text x="200" y="294" text-anchor="middle" font-family="system-ui,sans-serif" font-size="14" font-weight="600" fill="#35596b">${esc(label)}</text></svg>`;
  const svg = host.firstElementChild;
  svg.style.width = '100%';
  svg.style.height = '100%';
  return host;
}
export const THOMSON2010_READER_SCENES = stages;
