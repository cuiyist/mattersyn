/**
 * MatterSyn morphology artwork — qualitative, code-native illustrations.
 * These geometries are display design, not measured coordinates or dimensions.
 * Choose a key only from source-bound morphology metadata; never infer it here.
 * Color distinguishes illustrated regions and does not encode elemental identity.
 */

export const PARTICLE_SHAPES = Object.freeze([
  'sphere', 'cube', 'rod', 'ellipsoid', 'platelet', 'belt', 'star',
  'truncated-star', 'irregular', 'truncated-octahedron', 'assembly', 'sphere-assembly', 'wire-assembly', 'matrix',
  'nanotube-supported', 'core-shell', 'islands', 'layered-film', 'neutral',
]);

const LABELS = Object.freeze({
  sphere: 'Schematic spherical particle',
  cube: 'Schematic cubic particle',
  rod: 'Schematic rod-shaped particle',
  ellipsoid: 'Schematic ellipsoidal particle',
  platelet: 'Schematic thin platelet',
  belt: 'Schematic belt-shaped structure',
  star: 'Schematic projection of an eight-arm star-shaped particle',
  'truncated-star': 'Schematic projection of an eight-arm star-shaped particle with truncated tips',
  irregular: 'Schematic irregular particle',
  'truncated-octahedron': 'Schematic truncated-octahedral particle',
  assembly: 'Schematic assembly of particles; arrangement is illustrative',
  'sphere-assembly': 'Schematic spherical particle assembly; constituent count and arrangement are illustrative',
  'wire-assembly': 'Schematic wire-like particle assembly; constituent count and arrangement are illustrative',
  matrix: 'Schematic particles within a matrix; colors distinguish illustrative regions',
  'nanotube-supported': 'Schematic particles supported on a hollow nanotube',
  'core-shell': 'Schematic core and shell cross-section; colors distinguish illustrative regions',
  islands: 'Schematic separated material islands on a support',
  'layered-film': 'Schematic layered film; thicknesses and colors are illustrative',
  neutral: 'Morphology illustration unavailable for this source context',
});

const LEGENDS = Object.freeze({
  assembly: [{ color: '#268b89', label: 'Particles', note: 'Arrangement is illustrative.' }],
  'sphere-assembly': [{ color: '#268b89', label: 'Constituent particles', note: 'Spherical assembly; constituent count, size, and arrangement are illustrative.' }],
  'wire-assembly': [{ color: '#268b89', label: 'Constituent particles', note: 'Wire-like assembly; constituent count, size, and arrangement are illustrative.' }],
  matrix: [
    { color: '#268b89', label: 'Dispersed particles' },
    { color: '#d1ae61', label: 'Matrix', note: 'Region colors and arrangement are illustrative.' },
  ],
  'nanotube-supported': [
    { color: '#268b89', label: 'Supported particles' },
    { color: '#d1ae61', label: 'Nanotube support', note: 'Coverage and arrangement are illustrative.' },
  ],
  'core-shell': [
    { color: '#268b89', label: 'Core' },
    { color: '#d1ae61', label: 'Shell', note: 'Cross-section; relative thickness and colors are illustrative.' },
  ],
  islands: [
    { color: '#268b89', label: 'Material islands' },
    { color: '#d1ae61', label: 'Support', note: 'Coverage and arrangement are illustrative.' },
  ],
  'layered-film': [
    { color: '#268b89', label: 'Film layers' },
    { color: '#d1ae61', label: 'Support', note: 'Number of layers and thicknesses are illustrative.' },
  ],
});

const keyOf = shape => typeof shape === 'string' && Object.hasOwn(LABELS, shape) ? shape : 'neutral';

/** Returns fresh, safe metadata; text has no material-specific scientific claims. */
export function particleShapeInfo(shape) {
  const key = keyOf(shape);
  return {
    shape: key,
    ariaLabel: LABELS[key],
    legend: (LEGENDS[key] || []).map(item => ({ ...item })),
    illustrative: true,
  };
}

let instance = 0;
const coords = vertices => vertices.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
const polygon = (vertices, attributes = '') => `<polygon points="${coords(vertices)}" ${attributes}/>`;

function starVertices(truncated = false) {
  const points = [];
  const at = (radius, angle) => [200 + radius * Math.cos(angle), 148 + radius * Math.sin(angle)];
  for (let i = 0; i < 8; i++) {
    const angle = -Math.PI / 2 + i * Math.PI / 4;
    const tip = at(109, angle);
    const before = at(43, angle - Math.PI / 8);
    const after = at(43, angle + Math.PI / 8);
    if (truncated) {
      points.push([tip[0] * .77 + before[0] * .23, tip[1] * .77 + before[1] * .23]);
      points.push([tip[0] * .77 + after[0] * .23, tip[1] * .77 + after[1] * .23]);
    } else points.push(tip);
    points.push(after);
  }
  return points;
}

function starBody(g, truncated) {
  const points = starVertices(truncated);
  return polygon(points.map(([x, y]) => [x, y + 13]), 'fill="#236d6d" stroke="#205e60" stroke-width="1.2" stroke-linejoin="round"')
    + polygon(points, `fill="url(#${g}-teal)" stroke="#307e7d" stroke-width="1.2" stroke-linejoin="round"`)
    + points.map((point, i) => polygon([[200, 148], point, points[(i + 1) % points.length]], `fill="${i % 2 ? '#125c65' : '#d4f0dc'}" opacity="${i % 2 ? '.12' : '.24'}"`)).join('');
}

/** A true truncated-octahedral envelope, projected from schematic polyhedron vertices. */
function truncatedOctahedron() {
  const permutations = [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
  const unique = new Map();
  for (const perm of permutations) for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
    const p = [perm[0] * sx, perm[1] * sy, perm[2] * sz];
    unique.set(p.join(','), p);
  }
  const vertices = [...unique.values()];
  const faces = [];
  for (let axis = 0; axis < 3; axis++) for (const sign of [-1, 1]) {
    const normal = [0,0,0]; normal[axis] = sign;
    faces.push({ normal, vertices: vertices.filter(v => v[axis] === sign * 2) });
  }
  for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
    const normal = [sx, sy, sz];
    faces.push({ normal, vertices: vertices.filter(v => v[0] * sx + v[1] * sy + v[2] * sz === 3) });
  }
  const camera = [.502, .722, .610];
  const depth = v => v.reduce((sum, n, i) => sum + n * camera[i], 0);
  const project = ([x,y,z]) => [200 + (x * .82 - y * .57) * 45, 150 + (x * .35 + y * .5 - z * .88) * 45];
  return faces.filter(face => depth(face.normal) > 0).sort((a,b) => depth(a.normal) - depth(b.normal)).map(face => {
    const points = face.vertices.map(project);
    const center = points.reduce((s,v) => [s[0] + v[0] / points.length, s[1] + v[1] / points.length], [0,0]);
    points.sort((a,b) => Math.atan2(a[1]-center[1],a[0]-center[0]) - Math.atan2(b[1]-center[1],b[0]-center[0]));
    const [nx,ny,nz] = face.normal;
    const light = Math.max(0, Math.min(1, (.18 * nx - .1 * ny + .72 * nz + 1) / 2));
    const palette = ['#266c71','#2b7e7e','#38948e','#66afa0','#9cccc0'];
    return polygon(points, `fill="${palette[Math.min(4, Math.floor(light * 5))]}" stroke="#d5e9d8" stroke-width="1.25" stroke-linejoin="round"`);
  }).join('');
}

function body(shape, g) {
  const ball = (x,y,r) => `<circle cx="${x}" cy="${y}" r="${r}" fill="url(#${g}-ball)" stroke="#367f7d" stroke-width=".85"/>`;
  const ground = (width = 94, y = 254) => `<ellipse cx="200" cy="${y}" rx="${width}" ry="9" fill="url(#${g}-shadow)"/>`;
  switch (shape) {
    case 'sphere': return ground(92,254) + ball(200,145,89) + `<path d="M147 99C161 77 182 69 202 69" fill="none" stroke="#f1f8df" stroke-width="3.5" stroke-linecap="round" opacity=".5"/>`;
    case 'cube': return ground(116,260)
      + `<path d="M200 50L302 102L200 160L98 102Z" fill="url(#${g}-top)" stroke="#4e9690" stroke-width="1.3"/>
      <path d="M98 102L200 160V254L98 195Z" fill="url(#${g}-teal)" stroke="#3a7f7d" stroke-width="1.3"/>
      <path d="M200 160L302 102V195L200 254Z" fill="url(#${g}-side)" stroke="#3a7f7d" stroke-width="1.3"/>
      <path d="M99 102L200 160L301 103M200 161V252" fill="none" stroke="#cbe7cd" stroke-width="1.5" opacity=".65"/>`;
    case 'rod': return ground(122,245) + `<g transform="rotate(-26 200 152)">
      <path d="M106 111H286C307 111 321 129 321 152S307 193 286 193H106Z" fill="url(#${g}-cylinder)" stroke="#387d7d" stroke-width="1.1"/>
      <ellipse cx="106" cy="152" rx="28" ry="41" fill="url(#${g}-top)" stroke="#4c9690" stroke-width="1.1"/>
      <path d="M126 122H284" stroke="#e6f4d5" stroke-width="2" stroke-linecap="round" opacity=".55"/>
      </g>`;
    case 'ellipsoid': return ground(117,247) + `<g transform="rotate(-24 200 146)"><ellipse cx="200" cy="146" rx="124" ry="63" fill="url(#${g}-ball)" stroke="#3d8380" stroke-width="1.1"/><path d="M113 121C134 100 172 91 213 95" fill="none" stroke="#f0f5d8" stroke-width="2.6" stroke-linecap="round" opacity=".5"/></g>`;
    case 'platelet': return ground(136,241)
      + `<path d="M70 157L124 92L260 80L331 135V156L277 221L141 233L70 178Z" fill="#277479" stroke="#377c7d" stroke-width="1.2"/>
      <path d="M70 157L124 92L260 80L331 135L277 200L141 212Z" fill="url(#${g}-top)" stroke="#50988e" stroke-width="1.2"/>
      <path d="M70 157L141 212L277 200L331 135M141 212V232M277 200V220" fill="none" stroke="#b1d8c1" stroke-width="1.2"/>`;
    case 'belt': return ground(143,247)
      + `<path d="M64 183L270 76L329 112V130L123 237L64 201Z" fill="#286f76" stroke="#347777" stroke-width="1.2"/>
      <path d="M64 183L270 76L329 112L123 219Z" fill="url(#${g}-top)" stroke="#55968d" stroke-width="1.2"/>
      <path d="M123 219V237M65 183L123 219L328 112" fill="none" stroke="#c7e5ca" stroke-width="1.25"/>
      <path d="M89 182L272 88" fill="none" stroke="#eef4d5" stroke-width="1.5" opacity=".48"/>`;
    case 'star': return ground(108,264) + starBody(g, false);
    case 'truncated-star': return ground(108,252) + starBody(g, true);
    case 'irregular': return ground(113,251)
      + `<path d="M118 82C139 66 157 76 178 60C199 48 223 70 244 68C267 66 278 83 279 105C303 120 294 139 307 154C315 174 294 188 293 207C288 228 261 222 245 239C227 251 208 234 188 241C169 248 153 228 137 230C112 229 117 201 101 190C85 177 100 156 94 139C87 117 109 112 108 96Z" fill="url(#${g}-ball)" stroke="#438681" stroke-width="1.2"/>
      <path d="M120 111L163 90L187 129L154 170L112 153Z" fill="#d7ebce" opacity=".14"/>
      <path d="M185 70L241 85L267 116L222 142L187 129L163 90Z" fill="#d7ebce" opacity=".12"/>
      <path d="M154 170L206 173L244 227L188 236L144 215Z" fill="#0c616c" opacity=".1"/>`;
    case 'truncated-octahedron': return ground(111,267) + truncatedOctahedron();
    case 'assembly': return ground(125,260)
      + ball(179,91,39) + ball(240,119,43) + ball(128,149,42)
      + ball(186,155,47) + ball(273,180,41) + ball(154,212,42) + ball(219,217,43);
    case 'sphere-assembly': return ground(116,270)
      + ball(202,75,29) + ball(245,91,28) + ball(274,128,29) + ball(274,173,29)
      + ball(249,216,28) + ball(208,235,28) + ball(165,221,29) + ball(132,187,28)
      + ball(123,144,28) + ball(141,102,28) + ball(168,79,28)
      + ball(164,130,30) + ball(209,112,31) + ball(240,158,32)
      + ball(159,176,30) + ball(201,172,33) + ball(207,213,25);
    case 'wire-assembly': return ground(139,252) + `<g transform="rotate(-22 200 154)">`
      + ball(95,139,24) + ball(135,137,25) + ball(176,136,25) + ball(217,138,25) + ball(258,139,25) + ball(299,145,24)
      + ball(111,172,24) + ball(152,173,24) + ball(193,171,25) + ball(234,173,25) + ball(275,173,24)
      + '</g>';
    case 'matrix': return ground(133,266)
      + `<path d="M75 112L228 62L325 112L172 164Z" fill="#eadcb7" stroke="#c4b278" stroke-width="1.1"/>
      <path d="M75 112L172 164V256L75 204Z" fill="#ddd0a8" fill-opacity=".68" stroke="#c3b17d" stroke-width="1.1"/>
      <path d="M172 164L325 112V204L172 256Z" fill="#c4ad77" fill-opacity=".38" stroke="#c3b17d" stroke-width="1.1"/>`
      + ball(144,128,23) + ball(224,112,20) + ball(281,151,23) + ball(208,174,25) + ball(122,188,20) + ball(244,218,20)
      + `<path d="M75 112L172 164L325 112V204L172 256L75 204Z" fill="#eddfb9" fill-opacity=".16" stroke="#bda976" stroke-width="1.4"/>
      <path d="M172 164V256" stroke="#bba16a" stroke-width="1.2" opacity=".65"/>`;
    case 'nanotube-supported': return ground(137,251)
      + `<g transform="rotate(-24 200 157)">
      <path d="M90 113H302C319 113 333 132 333 157S319 201 302 201H90Z" fill="url(#${g}-gold-cylinder)" stroke="#ab8a4c" stroke-width="1.2"/>
      <ellipse cx="90" cy="157" rx="29" ry="44" fill="#e4cc8c" stroke="#ae8e50" stroke-width="1.2"/>
      <ellipse cx="90" cy="157" rx="20" ry="32" fill="#6d674e" stroke="#967b43" stroke-width="1"/>
      <path d="M83 128C96 124 106 139 108 151" fill="none" stroke="#504e3f" stroke-width="4" opacity=".4"/>`
      + ball(148,118,20) + ball(225,117,18) + ball(286,166,22) + ball(201,183,20) + ball(132,181,18)
      + '</g>';
    case 'core-shell': return ground(107,259)
      + `<circle cx="200" cy="146" r="98" fill="url(#${g}-gold)" stroke="#b29355" stroke-width="1.25"/>
      <circle cx="200" cy="146" r="69" fill="url(#${g}-ball)" stroke="#387c7b" stroke-width="1.15"/>
      <path d="M129 90A92 92 0 0 1 253 70" fill="none" stroke="#fff4cc" stroke-width="3" stroke-linecap="round" opacity=".72"/>
      <circle cx="200" cy="146" r="69" fill="none" stroke="#fff5ce" stroke-width="2.4" opacity=".65"/>`;
    case 'islands': return ground(140,259)
      + `<path d="M54 168L216 96L348 164V184L186 256L54 188Z" fill="#b49a61" stroke="#a8905f" stroke-width="1.1"/>
      <path d="M54 168L216 96L348 164L186 236Z" fill="url(#${g}-gold)" stroke="#baa16d" stroke-width="1.1"/>
      <path d="M186 236V256" stroke="#dfc991" stroke-width="1.1"/>
      <path d="M95 161C100 141 119 133 136 139C154 142 154 155 153 171C138 185 108 185 95 173Z" fill="url(#${g}-teal)" stroke="#468781" stroke-width="1.1"/>
      <path d="M166 136C170 113 195 103 215 110C237 114 241 130 235 143C216 157 184 157 166 143Z" fill="url(#${g}-ball)" stroke="#468781" stroke-width="1.1"/>
      <path d="M220 180C224 156 249 146 266 151C285 155 292 175 286 187C265 202 240 200 220 190Z" fill="url(#${g}-teal)" stroke="#468781" stroke-width="1.1"/>
      <path d="M159 199C160 183 175 176 190 180C205 185 207 196 204 203C189 214 173 213 159 206Z" fill="url(#${g}-ball)" stroke="#468781" stroke-width="1.1"/>`;
    case 'layered-film': {
      const layers = [
        { y: 23, top: '#e0c887', side: '#b69a61', h: 20 },
        { y: 0, top: '#78b9a7', side: '#397d7e', h: 13 },
        { y: -20, top: '#b5d9bf', side: '#5f9f90', h: 13 },
      ];
      return ground(139,262) + layers.map(({y,top,side,h}) => `<path d="M66 ${156+y}L212 ${83+y}L337 ${148+y}V${148+y+h}L191 ${221+y+h}L66 ${156+y+h}Z" fill="${side}" stroke="#68938a" stroke-width="1.05"/><path d="M66 ${156+y}L212 ${83+y}L337 ${148+y}L191 ${221+y}Z" fill="${top}" stroke="#9cbdaa" stroke-width="1.05"/><path d="M191 ${221+y}V${221+y+h}" stroke="#d1e4c8" stroke-width="1"/>`).join('');
    }
    default: return `<rect x="93" y="77" width="214" height="156" rx="25" fill="#f4f7f2" stroke="#b9cdc3" stroke-width="1.3" stroke-dasharray="5 7"/>
      <path d="M135 126H265M135 155H238M135 184H254" stroke="#a9c3b7" stroke-width="7" stroke-linecap="round" opacity=".55"/>
      <path d="M94 101V94A17 17 0 0 1 111 77M289 233A18 18 0 0 0 307 215V208" fill="none" stroke="#c3aa70" stroke-width="2"/>`;
  }
}

/**
 * Returns self-contained SVG markup, with no external dependencies or user HTML.
 * Optional labelKey accepts only PARTICLE_SHAPES keys; no arbitrary aria text.
 * Every invocation owns its gradient IDs, including multiple copies of one shape.
 */
export function particleShapeSVG(shape, labelKey = shape) {
  const key = keyOf(shape);
  const label = typeof labelKey === 'string' && Object.hasOwn(LABELS, labelKey) ? LABELS[labelKey] : LABELS[key];
  const g = `ms-morph-${++instance}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 310" role="img" aria-label="${label}" preserveAspectRatio="xMidYMid meet" class="particle-shape-art" focusable="false">
  <defs>
    <radialGradient id="${g}-ball" cx=".29" cy=".24" r=".86"><stop offset="0" stop-color="#c4dfbf"/><stop offset=".34" stop-color="#66afa0"/><stop offset=".72" stop-color="#2b8584"/><stop offset="1" stop-color="#205c69"/></radialGradient>
    <linearGradient id="${g}-teal" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="#9bcbb1"/><stop offset=".45" stop-color="#58a798"/><stop offset="1" stop-color="#27757c"/></linearGradient>
    <linearGradient id="${g}-top" x1="0" y1="0" x2=".9" y2="1"><stop stop-color="#d3e6c7"/><stop offset=".55" stop-color="#95c7ae"/><stop offset="1" stop-color="#5ba493"/></linearGradient>
    <linearGradient id="${g}-side" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#47988f"/><stop offset="1" stop-color="#225e6a"/></linearGradient>
    <linearGradient id="${g}-cylinder" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#74b7a4"/><stop offset=".24" stop-color="#b8dabb"/><stop offset=".56" stop-color="#4f9f91"/><stop offset="1" stop-color="#216471"/></linearGradient>
    <radialGradient id="${g}-gold" cx=".29" cy=".2" r=".95"><stop stop-color="#f6eccb"/><stop offset=".5" stop-color="#ddc58a"/><stop offset="1" stop-color="#b39455"/></radialGradient>
    <linearGradient id="${g}-gold-cylinder" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#d8bf82"/><stop offset=".25" stop-color="#f1e4bc"/><stop offset=".58" stop-color="#ceb273"/><stop offset="1" stop-color="#9f824c"/></linearGradient>
    <radialGradient id="${g}-shadow"><stop stop-color="#2c6b67" stop-opacity=".16"/><stop offset="1" stop-color="#2c6b67" stop-opacity="0"/></radialGradient>
  </defs>
  ${body(key, g)}
  </svg>`;
}
