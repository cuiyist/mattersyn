import {compactDrawingFacts} from './protocol-record-fit.mjs?v=0.45.0';
// Record-derived protocol drawings. Own-field labels use textContent only.
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
    <path data-part="apparatus-outline" d="${shape}" fill="url(#${id}-glass)" stroke="${ink}" stroke-width="2.5"/>
    <g clip-path="url(#${id}-vessel)">
      ${liquid ? `<path d="M63 175Q150 188 237 175V254H63Z" fill="#d6b66f" fill-opacity=".58"/><ellipse cx="150" cy="177" rx="87" ry="10" fill="#e3c77f" fill-opacity=".6"/>` : ''}
      <path d="M102 93V150Q83 194 110 218M137 38V113" fill="none" stroke="white" stroke-opacity=".85" stroke-width="6" stroke-linecap="round"/>
      ${spec.stirring ? '<path data-part="stir-bar" d="M134 219H166" stroke="#748f9e" stroke-width="7" stroke-linecap="round"/>' : ''}
    </g>
    ${['flask', 'three-neck-flask'].includes(spec.vesselKind) ? `<ellipse cx="150" cy="28" rx="22" ry="5" fill="#f8fcff" stroke="${ink}" stroke-width="2"/>` : ''}
    ${spec.vesselKind === 'three-neck-flask' ? `<path d="M94 61H116M184 61H206" stroke="${ink}" stroke-width="3"/>` : ''}`;
}

// Fixed geometry bounds only: no dimensions are inferred from scientific data.
// Tight, centered viewBoxes make the actual vessel large without stretching it.
export function reportedDrawingViewport(spec) {
  const fixedWidths = {chamber:300,furnace:300,centrifuge:300,'mill-jar':300,'closed-reactor':172,filter:186,'mortar-pestle':205};
  const vesselWidths = {'three-neck-flask':180,flask:168,tube:86,vial:108,beaker:144,plain:140};
  const width = fixedWidths[spec.kind] || vesselWidths[spec.vesselKind] || vesselWidths.plain;
  const fixedMinY = {furnace:51,centrifuge:68,'mill-jar':72,'closed-reactor':16,filter:53,'mortar-pestle':29};
  const vesselMinY = {'three-neck-flask':23,flask:23,tube:67,vial:69,beaker:67,plain:83};
  const needsTopLeaders = (spec.added||[]).length > 0 || spec.gasLine || (typeof spec.environment === 'string' && spec.environment.trim());
  const top = spec.kind === 'inject' ? Math.min(0,portsFor(spec).inlet[1]-124)
    : ['chamber','reflux'].includes(spec.kind) || needsTopLeaders ? 0
      : Math.max(0,(fixedMinY[spec.kind] ?? vesselMinY[spec.vesselKind] ?? vesselMinY.plain)-8);
  const bottom = spec.kind === 'chamber' ? 290 : 260;
  return {x:150-width/2,y:top,width,height:bottom-top,bottom};
}

function geometry(spec, id, facts) {
  const metal = `fill="url(#${id}-metal)" stroke="${ink}" stroke-width="2.5"`;
  const glass = `fill="url(#${id}-glass)" stroke="${ink}" stroke-width="2.5"`;
  const ports = portsFor(spec),view = reportedDrawingViewport(spec),left = view.x+view.width*.08,right = view.x+view.width*.92;
  let body;
  let leaders = '';
  if (spec.kind === 'chamber') {
    const beamSources=facts.sources.filter(source=>source.identified);
    body=`<circle data-part="round-chamber" cx="150" cy="147" r="106" ${metal}/><circle cx="150" cy="147" r="89" fill="#f7fbfd" stroke="#b8ccd8" stroke-width="2"/>
      <path d="M25 132H46V164H25ZM254 132H275V164H254Z" ${metal}/><path d="M28 127V169M272 127V169" stroke="${ink}" stroke-width="4"/>
      <path data-part="substrate-holder" d="M106 181H194V190H106Z" fill="#b5c9d5" stroke="${ink}" stroke-width="2"/><path data-part="substrate-stem" d="M134 190H166V218H134Z" fill="#b5c9d5" stroke="${ink}" stroke-width="2"/>
      <path data-part="substrate" d="M115 176H185V181H115Z" fill="#b6a6a0" stroke="${ink}" stroke-width="1.5"/>
      ${facts.heaterTemperatures.length||spec.heating?`<path data-part="substrate-heater" d="M125 199H175V208H125Z" fill="${spec.heating?'#d9b18e':'#cbd7de'}" stroke="${ink}" stroke-width="1.5"/>`:''}`;
    const n=beamSources.length;
    beamSources.forEach((source,i)=>{
      const angle=(-145+(n===1?55:i*110/(n-1)))*Math.PI/180;
      const x=150+104*Math.cos(angle),y=147+104*Math.sin(angle),ix=150+83*Math.cos(angle),iy=147+83*Math.sin(angle);
      const target=128+(n===1?22:i*44/(n-1));
      body+=`<path data-part="source-port" data-source-index="${i}" d="M${(x-5).toFixed(1)} ${(y-5).toFixed(1)}L${(ix-5).toFixed(1)} ${(iy-5).toFixed(1)}M${(x+5).toFixed(1)} ${(y+5).toFixed(1)}L${(ix+5).toFixed(1)} ${(iy+5).toFixed(1)}" stroke="${ink}" stroke-width="3"/>`;
      const labelIndex=facts.sources.indexOf(source);
      leaders+=`<path data-part="source-leader" data-source-index="${i}" d="M${((labelIndex+.5)*300/Math.max(facts.sources.length,1)).toFixed(1)} 2L${x.toFixed(1)} ${y.toFixed(1)}" fill="none" stroke="${ink}" stroke-width="1.2"/>`;
      if(spec.beamSystem)body+=`<path data-part="source-beam" data-source-index="${i}" d="M${ix.toFixed(1)} ${iy.toFixed(1)}L${target.toFixed(1)} 176" fill="none" stroke="#9eacb8" stroke-width="2" stroke-dasharray="5 4"/>`;
      else body+=`<path data-part="source-feed" data-source-index="${i}" d="M${ix.toFixed(1)} ${iy.toFixed(1)}L${target.toFixed(1)} 176" fill="none" stroke="${ink}" stroke-width="2"/>`;
    });
    facts.sources.forEach((source,i)=>{if(!source.identified)leaders+=`<path data-part="unassigned-source-leader" d="M${((i+.5)*300/Math.max(facts.sources.length,1)).toFixed(1)} 2L42 140" fill="none" stroke="${ink}" stroke-width="1.2"/>`;});
    if(facts.flowHeaterTemperatures.length)leaders+=`<path data-part="heater-label-leader" d="M150 209V290" fill="none" stroke="${ink}" stroke-width="1.2"/>`;
  } else if (spec.kind === 'closed-reactor') {
    body = `<rect x="91" y="64" width="118" height="173" rx="25" ${metal}/><path d="M79 64H221V46H79ZM103 28H197V46M115 16V28M185 16V28" ${metal}/><path d="M107 84V206" stroke="white" stroke-width="8" stroke-opacity=".65"/>`;
  } else if (spec.kind === 'furnace') {
    body = `<rect x="27" y="51" width="246" height="185" rx="18" ${metal}/><rect x="49" y="77" width="202" height="128" rx="8" fill="#f5f1e9" stroke="${ink}" stroke-width="2"/><path d="M113 155H187L175 186H125Z" fill="#dce5e9" stroke="${ink}" stroke-width="3"/><path d="M61 84V196" stroke="white" stroke-width="5"/>`;
  } else if (spec.kind === 'mortar-pestle') {
    body = `<path d="M65 135H235Q219 228 150 232Q81 228 65 135Z" ${metal}/><ellipse cx="150" cy="135" rx="85" ry="17" fill="#c3d1d9" stroke="${ink}" stroke-width="2.5"/><path d="M177 163L234 50Q241 34 228 29Q216 24 209 40L157 155Q151 168 162 173Q172 177 177 163Z" ${metal}/><path d="M82 157Q96 205 126 214" fill="none" stroke="white" stroke-width="6"/>`;
  } else if (spec.kind === 'mill-jar') {
    body = `<rect x="65" y="72" width="170" height="141" rx="35" ${metal}/><path d="M70 96H230M70 188H230" stroke="${ink}" stroke-width="3"/><path d="M84 107V172" stroke="white" stroke-width="6"/><g fill="#cedde5" stroke="${ink}" stroke-width="2"><circle cx="116" cy="140" r="15"/><circle cx="160" cy="166" r="14"/><circle cx="189" cy="132" r="14"/></g><path d="M49 139H20L31 128M251 139H280L269 150" fill="none" stroke="${ink}" stroke-width="3"/>`;
  } else if (spec.kind === 'filter') {
    body = `<path d="M72 53H228L164 145V183L136 193V145Z" ${glass}/><path d="M93 75H207L164 137H136Z" fill="#e3c77f" fill-opacity=".6"/><path d="M109 200V239H191V200M150 192V214" fill="none" stroke="${ink}" stroke-width="3"/><path d="M87 61L140 137" stroke="white" stroke-width="5"/>`;
  } else if (spec.kind === 'centrifuge') {
    body = `<path d="M35 132V196C35 250 224 250 224 196V132" ${metal}/><ellipse cx="129" cy="132" rx="94" ry="64" ${glass}/><circle cx="129" cy="132" r="23" fill="#c8d8e2" stroke="${ink}" stroke-width="3"/><path d="M86 100L172 164M172 100L86 164" stroke="${ink}" stroke-width="8"/><path d="M246 96H278V207C278 232 246 232 246 207Z" ${glass}/><path d="M249 171H275V208Q262 227 249 208Z" fill="#d6b66f" fill-opacity=".58"/>`;
  } else {
    body = glassVessel(spec, id);
    if (spec.kind === 'reflux') body += `<path data-part="reflux-condenser" d="M139 1H161V79H139Z" ${glass}/><path data-part="reflux-lines" d="M150 3V77M139 18H123M161 61H177" fill="none" stroke="${ink}" stroke-width="3"/>`;
    if (spec.kind === 'inject') body += `<g data-part="syringe" transform="translate(${ports.inlet[0]} ${ports.inlet[1] - 118})"><path d="M-10 0H10M0 0V21M-9 21H9V69H-9ZM0 69V120" ${glass}/><path d="M-5 33V59" stroke="#c8d4d5" stroke-width="6"/></g>`;
    if (spec.kind === 'cool') {const x=view.x+view.width-5;body += `<path data-part="cooling-arrow" d="M${x} 100V179M${x-2.5} 168L${x} 179L${x+2.5} 168" fill="none" stroke="${ink}" stroke-width="2"/>`;}
  }
  // Opposite ports: additions enter from the left; atmosphere enters at the
  // right opening. The three-neck gas line ends at the open side neck, never
  // across a wall or through the central reagent/syringe port.
  if (spec.added.length && spec.kind !== 'inject' && spec.kind !== 'chamber') {
    const [x, mouth] = ['furnace', 'closed-reactor', 'mill-jar', 'mortar-pestle', 'centrifuge'].includes(spec.kind)
      ? [75, 40] : spec.kind === 'filter' ? [110, 53] : ports.inlet;
    const y = mouth - 4;
    leaders += `<path data-part="addition-arrow" d="M${left} 17H${x}V${y}M${x - 6} ${y - 8}L${x} ${y}L${x + 6} ${y - 8}" fill="none" stroke="${ink}" stroke-width="1.4"/>`;
  }
  if (spec.gasLine && (facts.atmosphere || !spec.environment)) {
    const end = spec.vesselKind === 'three-neck-flask' && !['chamber', 'furnace', 'closed-reactor', 'mill-jar', 'filter', 'centrifuge'].includes(spec.kind)
      ? `M${right} 17H195V57` : spec.kind === 'chamber' ? `M${right} 17V147H275`
        : ['furnace', 'closed-reactor', 'mill-jar', 'filter', 'centrifuge'].includes(spec.kind) ? `M${right} 17V40H${Math.min(240,view.x+view.width-15)}`
          : `M${right} 17H${ports.gas[0]}V${ports.gas[1] - 4}`;
    leaders += `<path data-part="gas-line" d="${end}" fill="none" stroke="#6c93a5" stroke-width="1.4" stroke-linecap="round"/>`;
    if(spec.kind==='inject')leaders+=`<path data-part="gas-label-leader" d="M${right} ${Math.min(0,ports.inlet[1]-124)}V17" fill="none" stroke="#6c93a5" stroke-width="1.4"/>`;
  }
  else if(facts.atmosphere)leaders+=`<path data-part="atmosphere-leader" d="M${right} 17V126H${Math.min(238,view.x+view.width-8)}" fill="none" stroke="${ink}" stroke-width="1.2"/>`;
  if(spec.kind==='inject'&&facts.added.length)leaders+=`<path data-part="addition-label-leader" d="M${left} ${ports.inlet[1]-122}H${ports.inlet[0]-13}" fill="none" stroke="${ink}" stroke-width="1.2"/>`;
  return `<defs><linearGradient id="${id}-glass"><stop stop-color="#dcecf4" stop-opacity=".8"/><stop offset=".36" stop-color="#fafdff" stop-opacity=".55"/><stop offset="1" stop-color="#c3dbe8" stop-opacity=".7"/></linearGradient><linearGradient id="${id}-metal"><stop stop-color="#d6e2e9"/><stop offset=".45" stop-color="#f3f7fa"/><stop offset="1" stop-color="#b9ccd7"/></linearGradient></defs><ellipse cx="150" cy="247" rx="${Math.min(113,view.width/2-5)}" ry="7" fill="#7193a5" fill-opacity=".1"/><g data-part="apparatus-body">${body}</g><g data-part="leader-line">${leaders}</g>`;
}

const clean = value => typeof value === 'string' ? value.trim() : '';
const normalized = value => clean(value).toLowerCase().replace(/[\s_-]+/g,' ');
const conditionKind = key => /duration|time/i.test(key) ? 'duration' : /temperature/i.test(key) ? 'temperature' : /flux|beam/i.test(key) ? 'flux' : 'other';
const elementNames = {gallium:'Ga',arsenic:'As',antimony:'Sb',phosphorus:'P',indium:'In',cadmium:'Cd',zinc:'Zn',selenium:'Se',sulfur:'S',sulphur:'S',tellurium:'Te',aluminum:'Al',aluminium:'Al'};
function identity(value) {
  const label=clean(value).replace(/\s+(?:atoms?|source|beam|flux)$/i,'').trim();
  if(Object.hasOwn(elementNames,normalized(label)))return elementNames[normalized(label)];
  const formulas=['Ga','As','As2','As4','Sb','Sb2','Sb4','P','P2','P4','In','Cd','Zn','Se','S','Te','Al'];
  const token=formulas.find(formula=>formula.toLowerCase()===label.toLowerCase());if(token)return token;
  return null;
}
const family = id => /^(?:As|Sb|P)[24]?$/.test(id||'') ? id.replace(/[24]$/,'') : id;
function fluxPrefix(key) {
  const prefix=clean(key).replace(/[_ -]+/g,' ').replace(/\s*(?:beam )?flux(?:es)?(?:\s.*)?$/i,'').trim();
  return identity(prefix);
}
function sourceClause(clause) {
  const c=clean(clause).replace(/^(?:under|with)\s+/i,'');
  const match=/^(.+?)\s+((?:beam|flux)(?:es|s)?)(.*)$/i.exec(c);
  const id=match?identity(match[1]):null;
  // The source name may already be an added-material label. Keep every own
  // value/qualification after that redundant name visible, including on merge.
  const detail=match?clean(match[3]).replace(/^[:=]\s*/,''):'';
  return id?{id,label:match[1]+' '+match[2],detail}:null;
}

// Pure own-field DTO for row deduplication. No paper/recipe material expansion.
// All flux conditions are printed. An unqualified flux is visible but does not
// invent a named source or an additional physical beam.
export function reportedDrawingFacts(spec, formattedConditions = []) {
  const rows=formattedConditions.filter(c=>c&&clean(c.key)&&clean(c.value));
  const durations=rows.filter(c=>conditionKind(c.key)==='duration');
  const temperatures=rows.filter(c=>conditionKind(c.key)==='temperature');
  const fluxes=rows.filter(c=>conditionKind(c.key)==='flux');
  const added=(spec.added||[]).map((full,index)=>({full:clean(full),label:clean(spec.addedLabels?.[index])||clean(full),index}));
  const sources=[];
  const locate=(id)=>sources.find(s=>s.id===id)||((id&&family(id)===id)?(()=>{const candidates=sources.filter(s=>s.identified&&family(s.id)===id);return candidates.length===1?candidates[0]:null;})():null);
  const add=(id,label,identified)=>{const existing=locate(id);if(existing)return existing;const entry={id,label,identified,conditionKeys:[],lines:[],fluxConditions:[],addedIndices:[],environmentClauses:[]};sources.push(entry);return entry;};
  if(spec.kind==='chamber')for(const a of added.slice(0,3)){const id=identity(a.label)||identity(a.full)||'added-'+a.index;const s=add(id,a.label,true);s.addedIndices.push(a.index);}
  if(spec.kind==='chamber')for(const c of fluxes){
    const id=fluxPrefix(c.key),ambiguous=id&&family(id)===id&&sources.filter(s=>s.identified&&family(s.id)===id).length>1;
    const s=add(ambiguous?'unassigned-'+id:id||'unassigned-flux',ambiguous?'Reported '+id+' flux':id||'Reported flux',Boolean(id)&&!ambiguous);
    s.conditionKeys.push(c.key);s.fluxConditions.push(c);
  }
  const atmosphere=[];
  // Split only explicit independent clauses, never numbers/units/chemical names.
  const environment=clean(spec.environment).replace(/(flux|beams?)\s*\+\s*(?=(?:N2|Ar|He|H2|O2|air|vacuum|nitrogen|argon)\b)/ig,'$1; ');
  const clauses=environment.split(/\s*[;,]\s*|\s+\+\s+|\s+under\s+/i).filter(Boolean);
  const sourceEnvironment=[];
  for(const clause of clauses){
    const own=spec.kind==='chamber'?sourceClause(clause):null;
    if(!own){
      if(spec.kind==='chamber'&&/\b(?:beam|flux)\b/i.test(clause)){const s=add('unassigned-environment','Reported source/flux',false);s.lines.push(clause);s.environmentClauses.push(clause);sourceEnvironment.push(clause);}
      else atmosphere.push(clause);
      continue;
    }
    let s=locate(own.id);
    if(!s){const generic=sources.filter(x=>x.identified&&x.id===family(own.id));if(generic.length===1){s=generic[0];s.id=own.id;s.label=own.label;}}
    if(!s)s=add(own.id,own.label,true);
    if(own.detail&&!s.lines.includes(own.detail))s.lines.push(own.detail);
    s.environmentClauses.push(clause);sourceEnvironment.push(clause);
  }
  const sourceTemperatures=spec.kind==='chamber'?temperatures.filter(c=>/source|effusion|cell/i.test(c.key)):[];
  if(sourceTemperatures.length){const s=add('source-temperature','Source temperature',false);for(const c of sourceTemperatures){s.conditionKeys.push(c.key);s.lines.push(c.key.replaceAll('_',' ')+': '+c.value);}}
  for(const s of sources)for(const c of s.fluxConditions){
    const key=c.key.replaceAll('_',' '),label=s.identified?key.replace(/^.+?\s+(?=(?:beam\s+)?flux\b)/i,''):key;
    s.lines.push(s.identified&&s.fluxConditions.length===1?c.value:label+': '+c.value);
  }
  const heaterTemperatures=temperatures.filter(c=>!sourceTemperatures.includes(c));
  const primaryHeaterTemperature=heaterTemperatures[0]||null;
  // A compact face has room for one short typed value. Longer values keep
  // their full original formatted text in the existing flow/leader path. This
  // chooses layout only: no quantity text is parsed, shortened or truncated.
  const short=primaryHeaterTemperature?.shortValue;
  const primaryHeaterShortValue=spec.kind==='chamber'&&typeof short==='string'&&clean(short)&&Array.from(short).length<=12?short:null;
  return {added:added.slice(0,3),addedIndicesShown:added.slice(0,3).map(x=>x.index),sources,atmosphere:atmosphere.join('; '),sourceEnvironment,
    heaterTemperatures,sourceTemperatures,primaryHeaterShortValue,
    flowHeaterTemperatures:spec.kind==='chamber'?(primaryHeaterShortValue?heaterTemperatures.slice(1):heaterTemperatures):[],
    durations,temperatures,fluxes,fluxConditionKeysShown:spec.kind==='chamber'?fluxes.map(c=>c.key):[],durationConditionKeysShown:durations.map(c=>c.key),temperatureConditionKeysShown:temperatures.map(c=>c.key),
    substrateLabels:spec.kind==='chamber'?(spec.substrates||[]).filter(clean):[],environmentShown:Boolean(clean(spec.environment)),vesselNameShown:false};
}

function annotation(className, title, values, titleOnly = false) {
  if(!values.length&&(!titleOnly||!title))return null;
  const host=node('div');host.className=className;
  Object.assign(host.style,{display:'grid',gap:'3px',minWidth:'0',padding:'0',background:'none',border:'0'});
  if(title){const heading=node('strong',title);Object.assign(heading.style,{fontWeight:'600',color:'#486475'});host.append(heading);}
  for(const value of values)host.append(node('span',value));
  return host;
}

export function createReportedDrawing(spec, conditions = [], options = {}) {
  const displayedConditions=options.fallback?conditions.map(c=>{const value=c.drawingValue&&c.drawingValue!==c.value?c.drawingValue+' ↗':c.value;return {...c,value,shortValue:value.length<=12?value:null};}):conditions;
  const originalFacts=reportedDrawingFacts(spec,displayedConditions);
  const compact=options.compact?compactDrawingFacts(originalFacts,spec,conditions,options):{facts:originalFacts,fullFacts:[]};
  const facts=compact.facts,drawing=node('div');drawing.className='reported-scene-drawing';
  drawing.dataset.layout='leader-lines-v2';drawing.dataset.stirring=String(Boolean(spec.stirring));drawing.dataset.heating=String(Boolean(spec.heating));
  drawing.reportedFacts=facts;drawing.reportedFullFacts=compact.fullFacts;drawing.reportedViewport=reportedDrawingViewport(spec);
  drawing.dataset.fitCompact=String(Boolean(options.compact));
  Object.assign(drawing.style,{display:'grid',gridTemplateColumns:'minmax(0,1fr)',gap:'8px',padding:'8px',background:'radial-gradient(ellipse at 50% 54%,#f0f5f8,transparent 72%)',boxSizing:'border-box',width:'100%',minWidth:'0',position:'relative'});
  const upper=node('div');upper.className='reported-scene-ports';Object.assign(upper.style,{display:'grid',gridTemplateColumns:'minmax(0,1fr) minmax(0,1fr)',gap:'12px',alignItems:'end'});
  let inlet;
  if(spec.kind==='chamber'&&facts.sources.length){
    inlet=node('div');inlet.className='reported-scene-inlet';Object.assign(inlet.style,{display:'grid',gridTemplateColumns:`repeat(${facts.sources.length},minmax(0,1fr))`,gap:'7px 0',gridColumn:'1 / -1',alignItems:'end'});
    for(const source of facts.sources){const cell=annotation('reported-scene-source',source.label,source.lines,true);cell.style.padding='0 3px';cell.dataset.sourceId=source.id;cell.style.textAlign='center';inlet.append(cell);}
  }else inlet=annotation('reported-scene-inlet',options.compact?'':'Added',options.fallback&&facts.added.length?[facts.added.map(x=>x.label).join('; ')]:facts.added.map(x=>x.label));
  const atmosphere=annotation('reported-scene-atmosphere','',facts.atmosphere?[facts.atmosphere]:[]);
  if(inlet)upper.append(inlet);if(atmosphere){atmosphere.style.gridColumn='2';atmosphere.style.textAlign='right';upper.append(atmosphere);}if(inlet||atmosphere)drawing.append(upper);
  const equipment=node('div');equipment.className='reported-scene-apparatus';Object.assign(equipment.style,{display:'grid',justifyItems:'center',minWidth:'0',width:'100%'});
  const plot=node('div');plot.className='reported-scene-geometry';Object.assign(plot.style,{position:'relative',width:'100%',minWidth:'0'});
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg'),view=reportedDrawingViewport(spec),bottom=view.bottom;
  svg.setAttribute('viewBox',`${view.x} ${view.y} ${view.width} ${view.height}`);svg.setAttribute('role','img');svg.setAttribute('aria-label',spec.kind.replaceAll('-',' ')+' operation diagram');
  svg.dataset.reportedApparatus='true';
  const scale=options.scale;
  const fitted=Number.isFinite(scale)&&scale>0;
  if(fitted){drawing.dataset.recordGeometryScale=String(scale);svg.dataset.geometryScale=String(scale);}
  Object.assign(svg.style,{display:'block',width:fitted?view.width*scale+'px':'100%',height:options.measureOnly?'0px':fitted?view.height*scale+'px':'auto',maxWidth:'none',margin:'0 auto'});
  svg.innerHTML=geometry(spec,`reported-art-${++sequence}`,facts);if(fitted)svg.querySelector?.('g[data-part="leader-line"]')?.setAttribute('display','none');plot.append(svg);equipment.append(plot);
  if(spec.heating||facts.primaryHeaterShortValue){
    const plate=node('div');plate.className='reported-scene-heating-plate';if(!spec.heating)plate.dataset.passive='true';
    Object.assign(plate.style,{display:options.compact?'flex':'grid',flexWrap:'wrap',alignItems:'center',justifyContent:'center',gap:options.compact?'4px 8px':'3px',width:'min(78%,300px)',minWidth:'0',marginTop:'-5px',boxSizing:'border-box',textAlign:'center',padding:options.compact?'4px 6px':'6px 8px',borderTop:'4px solid #b6c7d2',borderRadius:'3px 3px 8px 8px',background:'linear-gradient(#e4ecf1,#c4d3dd)'});
    if(spec.kind==='chamber'){
      plate.dataset.heaterFront='true';
      Object.assign(plate.style,{position:'absolute',left:'50%',top:(205/bottom*100)+'%',transform:'translate(-50%,-50%)',display:'flex',alignItems:'center',justifyContent:'center',gap:'4px',width:'max-content',maxWidth:'76%',whiteSpace:'nowrap',marginTop:'0',padding:'1px 6px',border:'1px solid #7899ad',borderTop:'1px solid #7899ad',borderRadius:'2px',background:'#d6e2e9'});
    }
    if(spec.heating){const lamp=node('i');lamp.className='reported-scene-heating-indicator';lamp.setAttribute('aria-hidden','true');Object.assign(lamp.style,{display:'inline-block',width:'7px',height:'7px',marginLeft:'7px',borderRadius:'50%',background:'#dc9854',boxShadow:'0 0 4px #e8b982'});if(spec.kind==='chamber')lamp.style.marginLeft=facts.primaryHeaterShortValue?'0':'5px';if(spec.kind==='chamber'&&facts.primaryHeaterShortValue)plate.append(lamp);else{const state=node('strong','HEATING');state.append(lamp);plate.append(state);}}
    const values=spec.kind==='chamber'?(facts.primaryHeaterShortValue?[facts.primaryHeaterShortValue]:[]):facts.heaterTemperatures.map(c=>`${c.key.replaceAll('_',' ')}: ${c.shortValue||c.value}`);
    const temp=annotation('reported-scene-temperature','',values);if(temp)plate.append(temp);(spec.kind==='chamber'?plot:equipment).append(plate);
  }
  const flowTemperatures=spec.kind==='chamber'?facts.flowHeaterTemperatures:!spec.heating?facts.heaterTemperatures:[];
  if(flowTemperatures.length){const temp=annotation('reported-scene-temperature','',flowTemperatures.map(c=>`${c.key.replaceAll('_',' ')}: ${c.value}`));temp.style.textAlign='center';temp.style.width='90%';equipment.append(temp);const leader=document.createElementNS('http://www.w3.org/2000/svg','svg');leader.setAttribute('viewBox','0 0 2 12');leader.style.width='2px';leader.style.height='12px';leader.style.marginTop='-8px';leader.setAttribute('aria-hidden','true');leader.innerHTML='<g data-part="leader-line"><path d="M1 0V12" stroke="#7899ad" stroke-width="1.2"/></g>';if(equipment.insertBefore)equipment.insertBefore(leader,temp);else equipment.append(leader);}
  if(facts.substrateLabels.length)equipment.append(annotation('reported-scene-substrate','Reported substrate',facts.substrateLabels));
  drawing.append(equipment);
  drawing.updateAnnotationLayout=()=>updateFittedAnnotations(drawing,svg,plot,spec,facts,options);
  const duration=annotation('reported-scene-duration',options.compact?'':'Duration',facts.durations.map(c=>facts.durations.length>1?c.key.replaceAll('_',' ')+': '+c.value:c.value));if(duration){duration.style.textAlign='center';duration.style.justifySelf='center';const leader=document.createElementNS('http://www.w3.org/2000/svg','svg');leader.setAttribute('viewBox','0 0 2 14');leader.setAttribute('aria-hidden','true');leader.style.width='2px';leader.style.height='14px';leader.style.justifySelf='center';leader.innerHTML='<g data-part="leader-line"><path d="M1 0V14" stroke="#7899ad" stroke-width="1.2"/></g>';duration.children.length?duration.insertBefore?.(leader,duration.children[0]):null;if(!duration.insertBefore)duration.append(leader);drawing.append(duration);}
  return drawing;
}



// Pixel overlay connects fixed-font labels to the scaled, unchanged openings.
function updateFittedAnnotations(drawing,svg,plot,spec,facts,options){
 if(!(Number.isFinite(options.scale)&&options.scale>0)||typeof drawing.getBoundingClientRect!=='function'||!svg.getScreenCTM)return;
 const rect=drawing.getBoundingClientRect(),matrix=svg.getScreenCTM();if(!matrix||!rect.width)return;
 drawing.querySelector?.('svg[data-part="annotation-leaders"]')?.remove();
 const overlay=document.createElementNS('http://www.w3.org/2000/svg','svg');overlay.dataset.part='annotation-leaders';
 overlay.setAttribute('data-part','annotation-leaders');overlay.setAttribute('aria-hidden','true');
 Object.assign(overlay.style,{position:'absolute',left:'0',top:'0',width:'100%',height:'100%',pointerEvents:'none',overflow:'visible'});
 overlay.setAttribute('viewBox',`0 0 ${rect.width} ${rect.height}`);
 const point=(x,y)=>({x:matrix.a*x+matrix.c*y+matrix.e-rect.left,y:matrix.b*x+matrix.d*y+matrix.f-rect.top});
 const edge=node=>{const r=node.getBoundingClientRect();return {x:(r.left+r.right)/2-rect.left,y:r.bottom-rect.top+2};};
 const line=(label,target,arrow=false)=>{if(!label)return;const start=edge(label),p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('data-part','leader-line');const elbow=Math.min(target.y-6,Math.max(start.y+6,target.y-12));p.setAttribute('d',`M${start.x} ${start.y}V${elbow}H${target.x}V${target.y}`+(arrow?`M${target.x-4} ${target.y-5}L${target.x} ${target.y}L${target.x+4} ${target.y-5}`:''));p.setAttribute('fill','none');p.setAttribute('stroke','#7899ad');p.setAttribute('stroke-width','1.2');overlay.append(p);};
 const sources=[...drawing.querySelectorAll('.reported-scene-source')];
 if(spec.kind==='chamber'){
  const identified=facts.sources.filter(s=>s.identified);
  sources.forEach((label,index)=>{const source=facts.sources[index],i=identified.indexOf(source);if(i<0){line(label,point(42,140));return;}const angle=identified.length===1?-Math.PI/2:-Math.PI*.82+i*(Math.PI*.64/Math.max(identified.length-1,1));line(label,point(150+107*Math.cos(angle),147+107*Math.sin(angle)));});
 }else{
  const port=portsFor(spec);line(drawing.querySelector('.reported-scene-inlet'),point(port.inlet[0],spec.kind==='inject'?port.inlet[1]-124:port.inlet[1]-6),spec.kind!=='inject');
  line(drawing.querySelector('.reported-scene-atmosphere'),point(port.gas[0],port.gas[1]));
 }
 const plate=drawing.querySelector('[data-heater-front="true"]');
 if(plate){const holder=svg.querySelector('[data-part="substrate-holder"]')?.getBoundingClientRect(),bounds=plate.getBoundingClientRect(),plotRect=plot.getBoundingClientRect();const anchor=point(150,205);let cy=anchor.y-(plotRect.top-rect.top);if(holder)cy=Math.max(cy,holder.bottom-plotRect.top+bounds.height/2+3);plate.style.top=cy+'px';plot.style.minHeight=Math.max(reportedDrawingViewport(spec).height*options.scale,cy+bounds.height/2+3)+'px';}
 drawing.append(overlay);
}
