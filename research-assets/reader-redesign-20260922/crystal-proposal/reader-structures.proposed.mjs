import {el,button,link,badge,siteURL,disclosure,recordURL} from './reader-utils.mjs';
import {elementLegend} from './chemical-viewer.mjs';
import {drawFiniteReference} from './finite-crystal-reference.mjs';
let registry;
const colors={H:'#c3ccd8',C:'#63748b',N:'#4169d1',O:'#d5475b',P:'#e38b27',S:'#d2b128',Cl:'#54a66a',Br:'#a15b37',I:'#8757ae',Si:'#b3a18c',Se:'#db9944',Cd:'#298d9e',Pb:'#70839b',Cs:'#9878c5',Ag:'#91a4b3',Ge:'#9484a8',Te:'#b79b57',Fe:'#bf7542',Zn:'#6d96ba',La:'#809aad',Ce:'#aaa16d',Mo:'#738c9c',In:'#7e88b5',Co:'#4c83b5',Ni:'#5caa87',Ir:'#9d8fb5',Mn:'#be7eaf',Pt:'#a2afb9',Sn:'#718695',Al:'#b7bfc9',As:'#a48cc4',X:'#9975b3'};
export async function crystalReferences(r){registry??=fetch(siteURL('assets/crystal-references/registry.json'),{cache:'no-store'}).then(r=>r.json());return (await registry).entries.filter(x=>(x.record_ids||[]).includes(r.record_id));}
export function scopeKind(ref){
 const kind=[ref.sourceType,ref.referenceType,ref.name,ref.description].filter(Boolean).join(' ');
 if(/comput|DFT|PBE/i.test(kind))return 'Computed reference';
 if(/construct|ideal_reference|ideal reference/i.test(kind))return 'Constructed reference';
 return 'Bulk reference';
}
export function referenceCellVectors(model){
 const supplied=model.cellVectors??model.latticeVectors;
 let v=supplied;
 if(!v){
  const c=model.cell??model,{a,b,c:cc,alpha,beta,gamma}=c;
  if(![a,b,cc,alpha,beta,gamma].every(Number.isFinite))throw Error('Reference cell metadata is incomplete');
  const rad=Math.PI/180,ca=Math.cos(alpha*rad),cb=Math.cos(beta*rad),cg=Math.cos(gamma*rad),sg=Math.sin(gamma*rad);
  if(Math.abs(sg)<1e-8)throw Error('Reference cell has a singular angle');
  const cy=(ca-cb*cg)/sg,cz2=1-cb*cb-cy*cy;
  if(cz2<=0)throw Error('Reference cell angles are invalid');
  v=[[a,0,0],[b*cg,b*sg,0],[cc*cb,cc*cy,cc*Math.sqrt(cz2)]];
 }
 if(!Array.isArray(v)||v.length!==3||v.some(row=>!Array.isArray(row)||row.length!==3||!row.every(Number.isFinite)))throw Error('Reference cell vectors are invalid');
 const det=v[0][0]*(v[1][1]*v[2][2]-v[1][2]*v[2][1])-v[0][1]*(v[1][0]*v[2][2]-v[1][2]*v[2][0])+v[0][2]*(v[1][0]*v[2][1]-v[1][1]*v[2][0]);
 if(det<=1e-8)throw Error('Reference cell has non-positive volume');
 return v;
}
// Existing sample_context_ids sometimes describe evidence context rather than
// eligibility. Only an explicit sample_context_choice policy imposes this gate.
export function referencesForSample(entries,sampleId){
 return entries.filter(ref=>ref.displayPolicy!=='sample_context_choice'||(ref.sample_context_ids||[]).includes(sampleId));
}
export function referenceSampleChoices(entries,r){
 if(!entries.some(ref=>ref.displayPolicy==='sample_context_choice'))return [];
 const scopedIds=new Set(entries.filter(ref=>ref.displayPolicy==='sample_context_choice').flatMap(ref=>ref.sample_context_ids||[]));
 const seen=new Set();
 return (r.products||[]).filter(p=>p.sample_id&&(p.phase?.value||scopedIds.has(p.sample_id))).filter(p=>{if(seen.has(p.sample_id))return false;seen.add(p.sample_id);return true;});
}
async function mountReferenceChoices(panel,entries,r,finite){
 const contexts=referenceSampleChoices(entries,r),scopeNote=el('p',undefined,'reader-note reader-sample-scope'),choose=el('select',undefined,'reader-method-select'),display=el('div');
 let sampleSelect,activeEntries=[],generation=0;
 if(contexts.length){
  sampleSelect=el('select',undefined,'reader-method-select');sampleSelect.setAttribute('aria-label','Source specimen context for unit-cell comparison');
  for(const p of contexts){const opt=el('option',p.sample_id+(p.phase?.value?' · source reports '+p.phase.value:''));opt.value=p.sample_id;sampleSelect.append(opt);}
  panel.append(sampleSelect);
 }
 choose.setAttribute('aria-label',finite?'Choose a finite particle reference':'Choose a component and reference phase');
 panel.append(scopeNote,choose,display);
 const render=async()=>{
  const token=++generation,ref=activeEntries.find(x=>x.id===choose.value);display.replaceChildren();
  if(!ref){display.append(el('p',activeEntries.length?'Choose an independently sourced reference for comparison. This choice does not assign a phase to the synthesis specimen.':'No suitable unit-cell reference is supplied for this selected source context. Its reported phase remains source evidence, not a verified atomic reconstruction.','reader-note'));return;}
  try{await drawReference(display,ref,finite);}catch(error){if(token===generation)display.replaceChildren(el('p','Structure unavailable: '+error.message,'reader-note'));}
 };
 const refresh=async()=>{
  const sample=contexts.find(p=>p.sample_id===sampleSelect?.value);
  activeEntries=referencesForSample(entries,sample?.sample_id);
  scopeNote.textContent=sample?'Selected source context: '+sample.sample_id+(sample.phase?.value?' · source reports '+sample.phase.value:'')+'. The reference does not independently verify that phase assignment.':'Independent reference comparison. Component unit cells do not reconstruct an interface or complete particle.';
  choose.replaceChildren();
  const requiresChoice=activeEntries.length>1;
  if(requiresChoice){const prompt=el('option',finite?'Choose a finite reference':'Choose a component and reference phase');prompt.value='';prompt.disabled=true;prompt.selected=true;choose.append(prompt);}
  const groups=new Map();
  for(const ref of activeEntries){const formula=ref.formula||'Reference';if(!groups.has(formula)){const group=el('optgroup');group.label=formula+' · independent reference';groups.set(formula,group);choose.append(group);}const option=el('option',ref.name+' · '+scopeKind(ref));option.value=ref.id;groups.get(formula).append(option);}
  choose.hidden=activeEntries.length===0;
  if(!requiresChoice&&activeEntries.length)choose.value=activeEntries[0].id;
  await render();
 };
 choose.onchange=render;if(sampleSelect)sampleSelect.onchange=refresh;await refresh();
}
async function drawReference(host,ref,finite=false){
 host.replaceChildren();const badges=el('div',undefined,'reader-badges');badges.append(badge(scopeKind(ref),'reference'),badge('Not a sample reconstruction','scope'));host.append(badges,el('h3',ref.name));
 const view=el('div',undefined,'crystal-reference-view');view.tabIndex=0;view.setAttribute('aria-label',ref.name+' interactive crystal viewer');host.append(view);
 const controls=el('div',undefined,'protocol-controls'),caption=el('p',undefined,'reader-note');host.append(controls,caption);
 const downloads=el('div',undefined,'protocol-controls');downloads.append(link('Download CIF ↓','assets/crystal-references/'+ref.cifPath),link('Structure source ↗',ref.sourceUrl));for(const item of ref.additionalDownloads||[])downloads.append(link(item.label+' ↓','assets/crystal-references/'+item.path));host.append(downloads);
 const phaseScope=ref.phaseScope||ref.scope||ref.description;
 if(phaseScope)host.append(el('p',phaseScope,'reader-note reader-phase-scope'));
 if(ref.sample_context_note)host.append(el('p',ref.sample_context_note,'reader-note reader-sample-scope'));
 const details=disclosure('Reference provenance',el('p','Reference type: '+scopeKind(ref)+'. This asset is not a measured synthesis-sample reconstruction.'));
 if(ref.scope&&ref.scope!==phaseScope)details.append(el('p',ref.scope));host.append(details);
 if(!window.$3Dmol){view.textContent='The interactive viewer could not load. The structure download is available.';return;}
 const model=await(await fetch(siteURL('assets/crystal-references/'+(finite?ref.finiteModelPath:ref.modelPath)))).json();if(!view.isConnected)return;
 const viewer=$3Dmol.createViewer(view,{backgroundColor:'#f7fafc'});let extent=1;
 function draw(n=1){viewer.clear();extent=n;if(finite){drawFiniteReference(viewer,model);caption.textContent=ref.finiteCaption||'Illustrative finite particle · reference lattice cropped to a declared envelope.';return;}
  const v=referenceCellVectors(model),point=(i,j,k)=>({x:i*v[0][0]+j*v[1][0]+k*v[2][0],y:i*v[0][1]+j*v[1][1]+k*v[2][1],z:i*v[0][2]+j*v[1][2]+k*v[2][2]});const aa=[];
  for(let i=0;i<n;i++)for(let j=0;j<n;j++)for(let k=0;k<n;k++){const off=point(i,j,k);for(const a of model.atoms)aa.push({serial:aa.length,elem:a.element??a.elem,x:a.x+off.x,y:a.y+off.y,z:a.z+off.z,properties:a.properties});}
  viewer.addModel().addAtoms(aa);viewer.setStyle({},{sphere:{radius:.32,colorfunc:a=>colors[a.elem]||'#8497aa'}});
  for(let axis=0;axis<3;axis++)for(const b of [0,n])for(const c of [0,n]){const start=[b,c];start.splice(axis,0,0);const end=[...start];end[axis]=n;viewer.addLine({start:point(...start),end:point(...end),color:'#7395a9',linewidth:1.5});}
  viewer.zoomTo();viewer.rotate(18,'y');viewer.rotate(-10,'x');viewer.zoom(.85);viewer.render();
  caption.textContent=(ref.spaceGroup||'Reference cell')+' · a = '+model.cell.a+', b = '+model.cell.b+', c = '+model.cell.c+' Å. '+(n===1?'Unit cell.':'Repeated bulk cells, not a finite particle.')+' Drag to rotate; scroll to zoom.';
 }
 if(!finite){controls.append(button('Unit cell',()=>draw(1)),button('2 × 2 × 2 cells',()=>draw(2)));host.append(elementLegend(model.atoms.map(a=>a.element??a.elem).filter(x=>x!=='X')));if(ref.mixedOccupancy)host.append(el('p','Purple sites have mixed occupancy; they do not specify an ordered atom assignment.','reader-note'));}
 controls.append(button('−',()=>{viewer.zoom(1/1.2);viewer.render();}),button('Reset',()=>draw(extent)),button('+',()=>{viewer.zoom(1.2);viewer.render();}));draw();
 view.onkeydown=e=>{const turns={ArrowLeft:[-12,'y'],ArrowRight:[12,'y'],ArrowUp:[-12,'x'],ArrowDown:[12,'x']}[e.key];if(turns)viewer.rotate(...turns);else if(e.key==='Home')draw(extent);else if(['+','='].includes(e.key))viewer.zoom(1.15);else if(e.key==='-')viewer.zoom(1/1.15);else return;e.preventDefault();viewer.render();};
 const observer=new ResizeObserver(()=>{if(!view.isConnected){viewer.clear();observer.disconnect();return;}if(view.clientWidth&&view.clientHeight){viewer.resize();viewer.render();}});observer.observe(view);
}
function particleArt(r,presentation){
 const values=(presentation.productFacts||[]).filter(f=>/morphology|shape/i.test(f.label||f.kind||'')).map(f=>[f.label,f.value].join(' ')).join(' ');const architecture=r.material.architecture||r.architecture||'';const formula=r.material.formula;
 const core=/core.?shell|CdSe\/CdS|CdSe\/ZnS|CdS\/HgS/i.test(architecture+' '+formula),doped=/doped|:|Yb|Er/.test(formula+' '+values),cube=/cub(e|ic|oid)|rectangular/i.test(values),rod=/rod|wire|belt|elongated/i.test(values),sphere=/spher|round/i.test(values);
 let paths='';
 if(core)paths='<circle cx="195" cy="150" r="99" fill="#a8d3d9" opacity=".65" stroke="#669daa" stroke-width="2"/><circle cx="195" cy="150" r="61" fill="#5e8da9" opacity=".85"/><path d="M253 182L315 207" stroke="#669daa"/><text x="316" y="212" fill="#386177" font-size="14">Shell</text><path d="M190 155L89 216" stroke="#547c99"/><text x="53" y="227" fill="#386177" font-size="14">Core</text>';
 else if(cube)paths='<path d="M100 99L210 49L302 102L192 155Z" fill="#b7dce2"/><path d="M100 99L192 155V269L100 209Z" fill="#80aebd"/><path d="M192 155L302 102V212L192 269Z" fill="#6092a9"/>';
 else if(rod)paths='<path d="M73 149L283 52L327 81L117 180Z" fill="#badbe1"/><path d="M73 149L117 180V230L73 196Z" fill="#779fb1"/><path d="M117 180L327 81V129L117 230Z" fill="#5890a7"/>';
 else if(sphere)paths='<circle cx="200" cy="150" r="100" fill="url(#particle-shade)"/><ellipse cx="179" cy="112" rx="58" ry="38" fill="white" opacity=".12"/>';
 else paths='<path d="M140 65L245 60L294 144L253 237L146 249L89 157Z" fill="#e4eff3" stroke="#8badbd" stroke-width="2" stroke-dasharray="6 6"/><text x="195" y="156" text-anchor="middle" fill="#54778c" font-size="19">'+formula.replace(/[<&>]/g,'')+'</text>';
 if(doped)paths+='<circle cx="169" cy="112" r="7" fill="#c79849"/><circle cx="236" cy="168" r="7" fill="#c79849"/><circle cx="148" cy="198" r="7" fill="#c79849"/><text x="195" y="287" text-anchor="middle" fill="#93703a" font-size="12">Dopants are illustrative; positions are not measured</text>';
 const host=el('div',undefined,'reader-product-illustration');host.innerHTML='<svg viewBox="0 0 400 310" role="img" aria-label="Illustrative particle architecture, not an atomistic reconstruction"><defs><radialGradient id="particle-shade"><stop stop-color="#bfdce3"/><stop offset="1" stop-color="#5687a2"/></radialGradient></defs>'+paths+'</svg>';
 return {host,caption:(cube||rod||sphere||core?'Particle architecture schematic · not to scale.':'Material identity schematic · shape is not assigned.')+(doped?' Dopant positions and concentration are not encoded.':'')};
}
export async function mountReaderStructures(host,r,presentation={}){
 const refs=await crystalReferences(r),finite=refs.filter(x=>x.finiteModelPath);if(!host.isConnected)return;
 const tabs=el('div',undefined,'reader-structure-tabs');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Structure views');const panels=el('div');host.append(tabs,panels);const loaded=new Set();
 const options=[['cell','Unit cell'],['particle','Particle morphology'],...(finite.length?[['finite','Atomistic particle']]:[])];
 for(const [key,label] of options){const panel=el('div',undefined,'reader-structure-panel');panel.id='reader-structure-'+key;panel.setAttribute('role','tabpanel');panel.hidden=true;panels.append(panel);const b=button(label,()=>select(key));b.setAttribute('role','tab');b.setAttribute('aria-controls',panel.id);b.dataset.view=key;tabs.append(b);}
 async function select(key){for(const b of tabs.children)b.setAttribute('aria-selected',String(b.dataset.view===key));for(const p of panels.children)p.hidden=p.id!=='reader-structure-'+key;if(loaded.has(key))return;loaded.add(key);const panel=panels.querySelector('#reader-structure-'+key);
  try{if(key==='particle'){
   const all=presentation.allProductFacts||presentation.productFacts||[],groups=new Map();
   for(const f of all){const id=(f.record_id||r.record_id)+':'+(f.sample_id||'context');if(!groups.has(id))groups.set(id,{label:f.scope||f.sample_id||'Source specimen',facts:[]});groups.get(id).facts.push(f);}
   const choose=el('select',undefined,'reader-method-select'),display=el('div');choose.setAttribute('aria-label','Particle specimen or reported context');for(const [id,g] of groups){const option=el('option',g.label);option.value=id;choose.append(option);}if(groups.size)panel.append(choose);panel.append(display);
   const show=()=>{const selected=groups.get(choose.value),facts=selected?.facts||[],layout=el('div',undefined,'reader-product-layout'),art=particleArt(r,{...presentation,productFacts:facts}),copy=el('div');copy.append(badge('Illustration','reference'),el('h3',r.material.formula),el('p',art.caption,'reader-note'));const dl=el('dl',undefined,'reader-product-facts');for(const f of facts.slice(0,5)){const row=el('div');row.append(el('dt',f.label),el('dd',typeof f.value==='object'?JSON.stringify(f.value):String(f.value)));if(f.scope)row.append(el('small',f.scope));dl.append(row);}if(!dl.children.length)dl.append(el('p','Particle dimensions and morphology have not been assigned to this specimen.','reader-note'));copy.append(dl,link('Complete specimen evidence →',recordURL(r.record_id)+'#structures','reader-data-link'));layout.append(art.host,copy);display.replaceChildren(layout);};choose.onchange=show;show();return;
  }
  const entries=key==='finite'?finite:refs;if(entries.length){await mountReferenceChoices(panel,entries,r,key==='finite');return;}
  if(key==='cell'&&r.lineage.source_group==='heo2003'){const {mountHeoAverage}=await import('./heo2003-average-viewer.mjs');if(await mountHeoAverage(panel,r))return;}
  if(key==='cell'&&r.lineage.source_group==='lian2021'){const {mountLianBulk,eligibleBulkContexts}=await import('./lian2021-bulk-viewer.mjs');if(eligibleBulkContexts(r).length){await mountLianBulk(panel,r);return;}}
  panel.append(el('h3','Unit-cell reference not yet verified'),el('p','The reviewed source evidence remains available below. A phase-specific atomic model will be added when its coordinates and provenance can be verified.','reader-note'),link('Inspect structure evidence →',recordURL(r.record_id)+'#structures','reader-data-link'));
  }catch(error){panel.append(el('p','This structure view could not load. The complete evidence record remains available.','reader-note'));console.error(error);}
 }
 await select(refs.length?'cell':'particle');
}
