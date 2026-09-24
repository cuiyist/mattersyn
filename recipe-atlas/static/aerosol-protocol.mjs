/** Private integration candidate: source-scoped Littau continuous-flow apparatus.
 * Pure SVG/data builders need no browser; DOM adapters match protocol-visuals.mjs.
 * Source: 10.1021/j100108a019, main pp. 1–3, Fig. 1 and Experimental A.
 */
export const AEROSOL_ACTIONS = Object.freeze([
  'gas_feed', 'aerosol_pyrolysis', 'gas_dilution_quench',
  'aerosol_oxidation', 'sequential_bubbler_collection'
]);
const STAGE = Object.freeze({gas_feed:0,aerosol_pyrolysis:1,gas_dilution_quench:2,aerosol_oxidation:3,sequential_bubbler_collection:4});
const PALETTE = Object.freeze({ink:'#284b5b',muted:'#637e8c',line:'#7899ad',glass:'#e5f3fa',liquid:'#d6b66f',hot:'#c8754e',hotPale:'#f8e8dc',active:'#397d90',activePale:'#e8f3f5',paper:'#f8fcff'});
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const unit=x=>({'degC':'°C','cm3':'cm³'}[x]||x||'');
const nr='Not reported';
export function sourceQuantity(q,{oneDecimal=false}={}){
  if(!q||q.status==='not_reported')return nr;
  let value=q.value;
  if(value===null||value===undefined){
    if(q.minimum===null||q.minimum===undefined||q.maximum===null||q.maximum===undefined)return nr;
    value=`${q.minimum}–${q.maximum}`;
  }else if(oneDecimal&&typeof value==='number')value=value.toFixed(1);
  return `${q.approximate?'≈':''}${value}${q.unit?' '+unit(q.unit):''}`;
}
export function supportsAerosolOperation(o,r){
  return AEROSOL_ACTIONS.includes(o?.action)&&Array.isArray(r?.sources)&&r.sources.some(s=>String(s.doi||'').toLowerCase()==='10.1021/j100108a019');
}
const text=(x,y,value,size=18,extra='')=>`<text x="${x}" y="${y}" font-size="${size}" ${extra}>${esc(value)}</text>`;
const lines=(x,y,values,size=18,gap=23,extra='')=>values.map((v,i)=>text(x,y+i*gap,v,size,extra)).join('');
const pipe=(d,{color=PALETTE.line,width=5,dash='',extra=''}={})=>`<path d="${d}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round" ${dash?`stroke-dasharray="${dash}"`:''} ${extra}/>`;
const arrow=(x,y,color=PALETTE.active,rotation=0)=>`<path d="M-7 -5L2 0L-7 5Z" fill="${color}" transform="translate(${x} ${y}) rotate(${rotation})"/>`;
const box=(x,y,w,h,fill=PALETTE.paper,stroke=PALETTE.line,extra='')=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="9" fill="${fill}" stroke="${stroke}" stroke-width="2" ${extra}/>`;
const label=(x,y,title,value,width=200)=>box(x,y,width,57,'#ffffff','#d6e4eb')+text(x+12,y+21,title,13,`fill="${PALETTE.muted}"`)+text(x+12,y+44,value,18,'font-weight="650"');
const dot=(x,y,r=3,color=PALETTE.hot)=>`<circle cx="${x}" cy="${y}" r="${r}" fill="${color}"/>`;

function overview(action){
  const active=STAGE[action], names=['Gas feed','Furnace 1','Dilution','Furnace 2','Two bubblers'];
  let out=`<g data-role="process-topology"><path d="M70 82H694" fill="none" stroke="#c0d1da" stroke-width="3"/>`;
  for(let i=0;i<5;i++){
    const x=28+i*145,selected=i===active;
    out+=`<g data-stage="${AEROSOL_ACTIONS[i]}" data-active="${selected}">`+box(x,27,125,66,selected?PALETTE.activePale:'#ffffff',selected?PALETTE.active:'#c4d4dc')+text(x+62.5,49,`${i+1}. ${names[i]}`,12,'text-anchor="middle"');
    if(i===1||i===3)out+=box(x+28,58,68,22,selected?PALETTE.hotPale:'#f2f4f5',selected?PALETTE.hot:'#a9bdc9',`data-role="overview-furnace-${i===1?'1':'2'}"`)+pipe(`M${x+12} 69H${x+112}`,{width:4});
    else if(i===4)out+=`<g data-role="overview-serial-bubblers">${box(x+24,58,25,23,PALETTE.glass)}${box(x+76,58,25,23,PALETTE.glass)}${pipe(`M${x+47} 65H${x+79}`,{width:2})}${arrow(x+66,65,PALETTE.line)}</g>`;
    else if(i===2)out+=pipe(`M${x+62} 58V79M${x+22} 77H${x+102}`,{width:3})+arrow(x+62,74,PALETTE.active,90);
    else out+=pipe(`M${x+25} 60L${x+65} 77M${x+25} 77H${x+106}`,{width:3})+arrow(x+97,77);
    out+='</g>';
    if(i<4)out+=arrow(x+137,82,PALETTE.line);
  }
  return out+'</g>'+text(32,118,'Continuous-flow topology · selected stage highlighted · geometry not to scale',13,`fill="${PALETTE.muted}"`);
}

function cylinder(x,y,title){
  return `<g data-role="gas-cylinder">${box(x,y,57,88,PALETTE.glass)}${box(x+19,y-12,19,12,'#b7c9d3')}${pipe(`M${x+29} ${y-16}V${y-22}`,{width:3})}${text(x+28.5,y+43,title,18,'text-anchor="middle" font-weight="650"')}</g>`;
}
function feedScene(o,r){
  const p=o.parameters||{},stock=r.stocks?.find(s=>s.id==='disilane-He-stock');
  const fraction=sourceQuantity(stock?.concentrations?.reported_disilane_fraction);
  const stockFlow=sourceQuantity(p.stock_gas_flow,{oneDecimal:true});
  let out=text(34,161,'Gas preparation and flow control',22,'font-weight="650"');
  out+=cylinder(47,220,'Si₂H₆')+text(31,328,`${fraction} in He`,16)+text(30,350,'Supplied stock',14,`fill="${PALETTE.muted}"`);
  out+=cylinder(47,388,'He');
  out+=pipe('M104 258H232M330 258H435V334H670',{extra:'data-flow="stock-to-mixer"'})+arrow(207,258)+arrow(420,258)+arrow(648,334);
  out+=box(232,233,98,50)+lines(281,254,['MKS','controller'],14,18,'text-anchor="middle"');
  out+=text(224,219,stockFlow,18,'font-weight="650"');
  out+=pipe('M104 424H174M274 424H310M408 424H435V334',{extra:'data-flow="helium-through-purifier"'})+arrow(158,424)+arrow(298,424)+arrow(435,355,PALETTE.active,-90);
  out+=box(174,399,100,50,'#eef5ed')+lines(224,420,['Oxisorb','He purifier'],14,18,'text-anchor="middle"');
  out+=box(310,399,98,50)+lines(359,420,['MKS','controller'],14,18,'text-anchor="middle"');
  out+=`<circle cx="435" cy="334" r="7" fill="${PALETTE.active}"/>`+box(505,318,167,32,PALETTE.glass,PALETTE.line,'data-role="quartz-inlet"')+arrow(651,334);
  out+=label(486,214,'Combined pyrolysis feed',sourceQuantity(p.total_pyrolysis_feed),225);
  out+=text(517,299,'Quartz inlet',17)+text(492,382,`Internal diameter: ${sourceQuantity(p.quartz_inner_diameter)}`,16);
  out+=text(469,421,`Reactor: ${sourceQuantity(p.reactor_pressure)}`,18,'font-weight="650"')+text(470,445,'Absolute / gauge convention unstated',13,`fill="${PALETTE.muted}"`);
  return out;
}

function furnace(x,y,w,h,index){
  let out=`<g data-role="external-tube-furnace-${index}">`+box(x,y,w,h,PALETTE.hotPale,PALETTE.hot);
  for(let i=0;i<6;i++)out+=pipe(`M${x+24+i*29} ${y+15}v17M${x+24+i*29} ${y+h-15}v-17`,{color:'#d59877',width:3});
  return out+text(x+w/2,y+29,`EXTERNAL FURNACE ${index}`,13,'text-anchor="middle" fill="#945633"')+'</g>';
}
function quartz(x1,x2,y){return `<g data-role="quartz-tube">${pipe(`M${x1} ${y-15}H${x2}M${x1} ${y+15}H${x2}`,{width:3})}<path d="M${x1} ${y-14}H${x2}V${y+14}H${x1}Z" fill="${PALETTE.glass}" fill-opacity=".75"/>${pipe(`M${x1} ${y}H${x2}`,{width:2,color:'#91bac9',dash:'8 7'})}${arrow(x2-5,y)}</g>`;}
function pyrolysisScene(o){
  const p=o.parameters||{};
  let out=text(34,161,'Silicon aerosol formation in the first heated zone',22,'font-weight="650"');
  out+=furnace(233,243,228,129,1)+quartz(69,666,310)+arrow(213,310);
  out+=lines(78,213,['Dilute Si₂H₆ / He','from the gas mixer'],17,23);
  out+=box(496,185,220,104,'#ffffff','#d6e4eb')+text(508,205,'Experimental A',13,`fill="${PALETTE.muted}"`)+text(508,229,sourceQuantity(p.text_temperature),18,'font-weight="650"')+text(508,250,'Figure 1',13,`fill="${PALETTE.muted}"`)+text(508,275,sourceQuantity(p.figure_temperature),18,'font-weight="650"');
  out+=text(500,351,'Source temperatures conflict',14,'fill="#9b6029" font-weight="650"');
  for(const [x,y] of [[276,305],[300,316],[329,307],[357,314],[387,306],[422,312],[481,305]])out+=dot(x,y,3.5);
  out+=`<g data-role="wall-deposit">${pipe('M279 296H383',{width:5,color:'#a47547'})}${pipe('M335 294L370 213H436',{width:1.5,color:'#a47547',dash:'4 4'})}${lines(331,183,['Wall deposit','retained on tube'],15,19)}</g>`;
  out+=pipe('M246 399H447M246 391V407M447 391V407',{width:1.5})+text(347,426,`Heated length: ${sourceQuantity(p.zone_length)}`,17,'text-anchor="middle"');
  out+=text(67,463,`Gas velocity: ${sourceQuantity(p.linear_velocity)}`,17)+text(359,463,`Zone residence: ${sourceQuantity(p.residence_time)}`,18,'font-weight="650"');
  return out;
}

function aperture(x,y,labelText,role){
  return `<g data-role="${role}">${pipe(`M${x} ${y-29}V${y-5}M${x} ${y+5}V${y+29}`,{width:8})}${text(x,y+58,labelText,17,'text-anchor="middle"')}</g>`;
}
function dilutionScene(o){
  const p=o.parameters||{},ratio=p.dilution_ratio?.raw_text||nr,gasRatio=p.helium_per_oxygen_ratio?.raw_text||nr;
  let out=text(34,161,'Gas dilution and rapid cooling',22,'font-weight="650"');
  out+=quartz(53,700,322)+aperture(193,322,sourceQuantity(p.aperture),'first-aperture')+text(68,274,'Hot aerosol',18)+arrow(170,322);
  out+=pipe('M308 236V290L332 322M495 236V287L332 322',{extra:'data-flow="oxygen-helium-quench"'})+arrow(313,300,PALETTE.active,66)+arrow(354,314,PALETTE.active,164);
  out+=box(219,189,172,48)+text(305,219,`O₂ ${sourceQuantity(p.oxygen_flow)}`,17,'text-anchor="middle"');
  out+=box(413,189,182,48)+text(504,219,`He ${sourceQuantity(p.dilution_helium_flow)}`,17,'text-anchor="middle"');
  out+=`<circle cx="332" cy="322" r="13" fill="${PALETTE.activePale}" stroke="${PALETTE.active}" stroke-width="2"/>`;
  for(const [x,y] of [[108,316],[120,328],[141,316],[155,329],[390,317],[464,327],[548,316],[638,325]])out+=dot(x,y,3);
  out+=label(55,397,'Reported dilution',ratio,194)+label(274,397,'Diluent O₂ : He',gasRatio,193)+label(491,397,'After gas quench',sourceQuantity(p.cooled_temperature),214);
  out+=text(421,371,'Diluted aerosol →',17)+text(38,487,'Gas mixing follows the aperture; no cooling liquid is specified.',14,`fill="${PALETTE.muted}"`);
  return out;
}

function oxidationScene(o){
  const p=o.parameters||{};
  let out=text(34,161,'Surface oxidation in the second heated zone',22,'font-weight="650"');
  out+=furnace(270,243,228,129,2)+quartz(53,700,310)+aperture(182,310,sourceQuantity(p.aperture),'second-aperture');
  out+=lines(60,204,['Diluted aerosol','in O₂ / He'],17,23)+label(522,194,'Furnace temperature',sourceQuantity(p.temperature),187);
  for(const x of [313,355,397,449,537,610])out+=`<g data-role="schematic-oxidized-particle"><circle cx="${x}" cy="310" r="7" fill="#d9c08a" stroke="#8f6b48" stroke-width="1.5"/>${dot(x,310,3,PALETTE.ink)}</g>`;
  out+=text(58,435,`Gas velocity: ${sourceQuantity(p.linear_velocity)}`,17)+text(367,435,`Zone residence: ${sourceQuantity(p.residence_time)}`,18,'font-weight="650"');
  out+=lines(276,473,['Core / surface-layer symbols are schematic.','They do not specify atomic structure or a measured shell for each formulation.'],13,19,`fill="${PALETTE.muted}"`);
  return out;
}

function bubbler(x,y,withFrit,quantity,serial){
  let out=`<g data-role="${withFrit?'frit-collector':'prebubbler'}" data-serial-position="${serial}">`;
  out+=`<path d="M${x} ${y}V${y+126}Q${x+61} ${y+153} ${x+122} ${y+126}V${y}" fill="${PALETTE.glass}" fill-opacity=".8" stroke="${PALETTE.line}" stroke-width="3"/>`;
  out+=`<path d="M${x+3} ${y+67}Q${x+61} ${y+83} ${x+119} ${y+67}V${y+124}Q${x+61} ${y+150} ${x+3} ${y+124}Z" fill="${PALETTE.liquid}" fill-opacity=".55"/>`;
  out+=`<ellipse cx="${x+61}" cy="${y+67}" rx="58" ry="8" fill="${PALETTE.liquid}" fill-opacity=".25"/>`;
  out+=pipe(`M${x+30} ${y-19}V${y+108}`,{width:4,extra:'data-role="submerged-inlet"'});
  if(withFrit){
    out+=`<rect x="${x+13}" y="${y+105}" width="41" height="10" rx="2" fill="#f8fcff" stroke="${PALETTE.line}" stroke-width="1.5" data-role="silanized-coarse-glass-frit"/>`;
    for(let i=0;i<6;i++)out+=dot(x+17+i*6,y+110,1.3,PALETTE.line);
  }
  for(const [dx,dy] of [[28,94],[35,79],[25,62],[39,45]])out+=`<circle cx="${x+dx}" cy="${y+dy}" r="${withFrit?4:5}" fill="white" stroke="#8ba9b9" stroke-width="1.5"/>`;
  out+=text(x+61,y+183,withFrit?'Frit-collector fraction':'Prebubbler fraction',16,'text-anchor="middle" font-weight="650"')+text(x+61,y+207,`${quantity} ethylene glycol`,15,'text-anchor="middle"');
  return out+'</g>';
}
function collectionScene(o){
  const p=o.parameters||{};
  let out=text(34,161,'Sequential collection into two distinct liquid fractions',22,'font-weight="650"');
  out+=pipe('M40 222H250V235',{extra:'data-flow="cool-transfer-line"'})+arrow(193,222)+lines(39,197,['After furnace 2'],16,20);
  out+=lines(35,318,['Cooling before collection','is reported; its method,','temperature and time','are unspecified.'],14,20,`fill="${PALETTE.muted}"`);
  out+=bubbler(220,254,false,sourceQuantity(p.prebubbler_EG),1)+bubbler(488,254,true,sourceQuantity(p.collector_EG),2);
  out+=pipe('M318 275V221H518V235',{extra:'data-flow="prebubbler-to-frit-collector"'})+arrow(415,221);
  out+=pipe('M586 275V219H688',{extra:'data-flow="collector-exhaust"'})+arrow(680,219)+text(643,196,'Exhaust',15);
  out+=text(405,198,'In series',15,'text-anchor="middle"')+lines(631,323,['Coarse','treated frit'],14,19)+pipe('M622 340L543 363',{width:1.5,dash:'4 4'});
  out+=text(369,493,'Fractions remain separate; no pooling is specified.',14,'text-anchor="middle" fill="#637e8c"');
  return out;
}

function conditionEntries(o){
  const p=o.parameters||{},q=key=>sourceQuantity(p[key]),entry=(label,value,note='')=>({label,value,note});
  switch(o.action){
    case 'gas_feed': return [entry('Stock-mixture flow',sourceQuantity(p.stock_gas_flow,{oneDecimal:true}),'Flow of supplied Si₂H₆ / He stock, not pure disilane.'),entry('Combined pyrolysis feed',q('total_pyrolysis_feed')),entry('Disilane partial pressure',q('disilane_partial_pressure')),entry('Reported reactor pressure',q('reactor_pressure'),'Absolute/gauge convention is unspecified; not a collection pressure.'),entry('Inlet temperature',nr),entry('Run duration',nr),entry('Quartz internal diameter',q('quartz_inner_diameter'))];
    case 'aerosol_pyrolysis': return [entry('Temperature — Experimental A',q('text_temperature'),'Main p. 2, printed p. 1225.'),entry('Temperature — Figure 1',q('figure_temperature'),'Main p. 1, printed p. 1224; conflicts with Experimental A.'),entry('Heated-zone residence time',q('residence_time'),'Gas residence in the first heated zone; not the synthesis run duration.'),entry('Run duration',nr),entry('Reported reactor pressure',q('reactor_pressure'),'Absolute/gauge reference unspecified.'),entry('Heated-zone length',q('zone_length')),entry('Gas linear velocity',q('linear_velocity'))];
    case 'gas_dilution_quench': return [entry('Reported dilution ratio',p.dilution_ratio?.raw_text||nr,'Retain printed 1:23; do not recompute an exact final/feed factor.'),entry('Diluent O₂ : He',p.helium_per_oxygen_ratio?.raw_text||nr),entry('Oxygen flow — Figure 1',q('oxygen_flow')),entry('Helium flow — Figure 1',q('dilution_helium_flow')),entry('After-quench temperature',q('cooled_temperature')),entry('Cooling time',nr),entry('Exact local pressure',nr,'A reactor operating pressure is reported elsewhere; the local quench pressure is not separately resolved.'),entry('First aperture',q('aperture'))];
    case 'aerosol_oxidation': return [entry('Second-furnace temperature',q('temperature')),entry('Heated-zone residence time',q('residence_time'),'Gas residence in the second heated zone; not the synthesis run duration.'),entry('Run duration',nr),entry('Reported reactor pressure',q('reactor_pressure'),'Absolute/gauge reference unspecified.'),entry('Second aperture',q('aperture')),entry('Gas linear velocity',q('linear_velocity'))];
    case 'sequential_bubbler_collection': return [entry('Prebubbler liquid',q('prebubbler_EG'),'Ethylene glycol; first retained fraction.'),entry('Frit-collector liquid',q('collector_EG'),'Ethylene glycol; distinct second retained fraction.'),entry('Collection temperature',q('collection_temperature')),entry('Collection duration',q('collection_duration')),entry('Collection pressure',q('collection_pressure')),entry('Cooling before collection',nr,'Cooling is reported; method, rate and endpoint are unspecified.')];
    default:return [];
  }
}
const NOTES = Object.freeze({
  gas_feed:['sccm reference temperature and pressure are not stated.','Study-wide 3–30 ppm is contextual and is not a selectable range for this fixed formulation.'],
  aerosol_pyrolysis:['The 860 °C text and 865 °C Figure 1 labels conflict; both are retained.','Thermocouples were removed before disilane admission; no immersed probe is depicted.','Wall deposit is a retained side outcome, not a fabricated side-outlet pipe.'],
  gas_dilution_quench:['Aerosol passes the first aperture before gas dilution.','The reported dilution notation is retained without replacing it by an exact arithmetic flow ratio.'],
  aerosol_oxidation:['The protocol-level surface-oxide estimate is 1–2 nm; it is not a universal measured shell thickness.','The source does not establish an exact SiO₂ stoichiometry or an atomic-coordinate shell model.'],
  sequential_bubbler_collection:['Each vessel contains its own ethylene glycol charge; the two collected fractions remain distinct.','Approximately two-thirds of collected crystallites are reported in the second bubbler; this is not the separate one-third Si-feed mass-capture estimate.','The coarse frit is pretreated using printed SiH₂Cl₂ in toluene. This is prior apparatus treatment, not an added reactor feed; treatment amount, concentration, temperature, time and wash/dry details are unreported.','Reported daily solvent loss is an operational observation, not a collection duration.']
});

export function buildAerosolScene(o,r){
  if(!supportsAerosolOperation(o,r))return null;
  const renderer={gas_feed:feedScene,aerosol_pyrolysis:pyrolysisScene,gas_dilution_quench:dilutionScene,aerosol_oxidation:oxidationScene,sequential_bubbler_collection:collectionScene}[o.action];
  const title=o.label||o.action.replaceAll('_',' '),conditions=conditionEntries(o);
  const description=`${title}. Continuous-flow quartz apparatus with two external furnaces, gas dilution between apertures, then two serial ethylene-glycol bubblers. Selected stage: ${o.action}. Schematic, not to scale.`;
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" class="aerosol-apparatus-svg" viewBox="0 0 760 525" role="img" aria-label="${esc(description)}" data-scene="${esc(o.action)}" style="display:block;width:100%;height:auto;max-width:100%;font-family:Segoe UI,Arial,sans-serif;color:${PALETTE.ink}"><title>${esc(title)}</title><desc>${esc(description)}</desc><rect width="760" height="525" rx="18" fill="#fbfdff"/><g fill="${PALETTE.ink}">${overview(o.action)}${renderer(o,r)}</g></svg>`;
  return {scene:o.action,title,svg,conditions,notes:[...NOTES[o.action]],evidence:(o.evidence||[]).map(x=>({...x})),
    caption:'Source-linked apparatus schematic. Stage topology and labelled quantities follow the cited paper; geometry and particle symbols are schematic. The reported collection fractions remain separate.'};
}

export function createAerosolArt(o,r,prefix=''){
  const scene=buildAerosolScene(o,r);if(!scene)return null;
  const host=document.createElement('div');host.className='protocol-art protocol-art-aerosol';host.dataset.scene=scene.scene;
  // Override the generic flask grid: the SVG has its own responsive geometry.
  Object.assign(host.style,{display:'block',width:'100%',height:'auto',minHeight:'0',padding:'0'});
  host.innerHTML=scene.svg;return host;
}
export function createAerosolConditionGrid(o,r){
  const scene=buildAerosolScene(o,r);if(!scene)return null;
  const grid=document.createElement('dl');grid.className='protocol-condition-grid aerosol-condition-grid';
  for(const entry of scene.conditions){const cell=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=entry.label;dd.textContent=entry.value;cell.append(dt,dd);if(entry.note){const note=document.createElement('small');note.textContent=entry.note;cell.append(note);}grid.append(cell);}
  return grid;
}
