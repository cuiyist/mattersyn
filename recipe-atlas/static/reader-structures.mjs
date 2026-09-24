import {mountParticleContext} from './reader-particle.mjs?v=0.34.1';
import {el,button,link,badge,siteURL,disclosure,recordURL} from './reader-utils.mjs';
import {elementLegend,atomColors} from './chemical-viewer.mjs?v=0.34.1';
import {drawFiniteReference} from './finite-crystal-reference.mjs';
let registry;
const colors=atomColors;
export async function crystalReferences(r){registry??=fetch(siteURL('assets/crystal-references/registry.json'),{cache:'no-store'}).then(r=>r.json());return (await registry).entries.filter(x=>(x.record_ids||[]).includes(r.record_id)).map(ref=>ref.bindingScopes?.[r.record_id]?{...ref,scope:ref.bindingScopes[r.record_id],phaseScope:ref.bindingScopes[r.record_id],sample_context_note:null}:ref);}
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
 host.replaceChildren();const badges=el('div',undefined,'reader-badges');badges.append(badge(finite?'Illustration':scopeKind(ref),'reference'),badge('Not a sample reconstruction','scope'));host.append(badges,el('h3',ref.name));
 const view=el('div',undefined,'crystal-reference-view');view.tabIndex=0;view.setAttribute('aria-label',ref.name+' interactive crystal viewer');host.append(view);
 const controls=el('div',undefined,'protocol-controls'),caption=el('p',undefined,'reader-note');host.append(controls,caption);
 const downloads=el('div',undefined,'protocol-controls');downloads.append(link('Download CIF ↓','assets/crystal-references/'+ref.cifPath),link('Structure source ↗',ref.sourceUrl));for(const item of ref.additionalDownloads||[])downloads.append(link(item.label+' ↓','assets/crystal-references/'+item.path));host.append(downloads);
 const phaseScope=ref.phaseScope||ref.scope||ref.description;
 if(phaseScope){const brief=phaseScope.match(/^.*?[.!?](?=\s+[A-Z]|$)/s)?.[0]?.trim();host.append(el('p',brief||phaseScope,'reader-note reader-phase-scope'));}
 if(ref.sample_context_note)host.append(el('p',ref.sample_context_note,'reader-note reader-sample-scope'));
 const details=disclosure('Reference provenance',el('p','Reference type: '+scopeKind(ref)+'. This asset is not a measured synthesis-sample reconstruction.'));
 if(phaseScope)details.append(el('p',phaseScope));if(ref.scope&&ref.scope!==phaseScope)details.append(el('p',ref.scope));host.append(details);
 if(!window.$3Dmol){view.textContent='The interactive viewer could not load. The structure download is available.';return;}
 const model=await(await fetch(siteURL('assets/crystal-references/'+(finite?ref.finiteModelPath:ref.modelPath)))).json();if(!view.isConnected)return;
 const viewer=$3Dmol.createViewer(view,{backgroundColor:'#f7fafc'});let extent=1;
 function draw(n=1){viewer.clear();extent=n;if(finite){drawFiniteReference(viewer,model);caption.textContent=ref.finiteCaption||'Illustrative finite particle · reference lattice cropped to a declared envelope.';return;}
  const v=referenceCellVectors(model),point=(i,j,k)=>({x:i*v[0][0]+j*v[1][0]+k*v[2][0],y:i*v[0][1]+j*v[1][1]+k*v[2][1],z:i*v[0][2]+j*v[1][2]+k*v[2][2]});const aa=[];
  for(let i=0;i<n;i++)for(let j=0;j<n;j++)for(let k=0;k<n;k++){const off=point(i,j,k);for(const a of model.atoms)aa.push({serial:aa.length,elem:a.element??a.elem,x:a.x+off.x,y:a.y+off.y,z:a.z+off.z,properties:a.properties});}
  viewer.addModel().addAtoms(aa);viewer.setStyle({},{sphere:{radius:.32,colorfunc:a=>colors[a.elem]||'#8497aa'}});
  for(let axis=0;axis<3;axis++)for(const b of [0,n])for(const c of [0,n]){const start=[b,c];start.splice(axis,0,0);const end=[...start];end[axis]=n;viewer.addLine({start:point(...start),end:point(...end),color:'#7395a9',linewidth:1.5});}
  viewer.zoomTo();viewer.rotate(18,'y');viewer.rotate(-10,'x');viewer.zoom(1.2);viewer.render();
  caption.textContent=(ref.spaceGroup||'Reference cell')+' · a = '+model.cell.a+', b = '+model.cell.b+', c = '+model.cell.c+' Å; α = '+model.cell.alpha+'°, β = '+model.cell.beta+'°, γ = '+model.cell.gamma+'°. '+(n===1?'Unit cell.':'Repeated bulk cells, not a finite particle.')+' Drag to rotate; scroll to zoom.';
 }
 if(!finite){controls.append(button('Unit cell',()=>draw(1)),button('2 × 2 × 2 cells',()=>draw(2)));host.append(elementLegend(model.atoms.map(a=>a.element??a.elem).filter(x=>x!=='X')));if(ref.mixedOccupancy)host.append(el('p','Purple sites have mixed occupancy; they do not specify an ordered atom assignment.','reader-note'));}
 controls.append(button('−',()=>{viewer.zoom(1/1.2);viewer.render();}),button('Reset',()=>draw(extent)),button('+',()=>{viewer.zoom(1.2);viewer.render();}));draw();
 view.onkeydown=e=>{const turns={ArrowLeft:[-12,'y'],ArrowRight:[12,'y'],ArrowUp:[-12,'x'],ArrowDown:[12,'x']}[e.key];if(turns)viewer.rotate(...turns);else if(e.key==='Home')draw(extent);else if(['+','='].includes(e.key))viewer.zoom(1.15);else if(e.key==='-')viewer.zoom(1/1.15);else return;e.preventDefault();viewer.render();};
 const observer=new ResizeObserver(()=>{if(!view.isConnected){viewer.clear();observer.disconnect();return;}if(view.clientWidth&&view.clientHeight){viewer.resize();viewer.render();}});observer.observe(view);
}
export function finiteReferencesForRecord(refs,r){
 return refs.filter(ref=>ref.finiteModelPath&&(!Array.isArray(ref.finiteRecordIds)||ref.finiteRecordIds.includes(r.record_id))).map(ref=>({
  ...ref,
  name:ref.finiteName||ref.name,
  sourceType:ref.finiteSourceType||ref.sourceType,
  referenceType:ref.finiteReferenceType||ref.referenceType,
  phaseScope:ref.finiteScope||ref.phaseScope,
  scope:ref.finiteScope||ref.scope,
  sample_context_note:ref.finiteContextNote||ref.sample_context_note,
  displayPolicy:ref.finiteDisplayPolicy||ref.displayPolicy,
  cifPath:ref.finiteCifPath||ref.cifPath,
  cifSha256:ref.finiteCifSha256||ref.cifSha256,
  sourceUrl:ref.finiteSourceUrl||ref.sourceUrl,
  additionalDownloads:ref.finiteAdditionalDownloads||ref.additionalDownloads
 }));
}
export async function mountReaderStructures(host,r,presentation={}){
 const refs=await crystalReferences(r),finite=finiteReferencesForRecord(refs,r);if(!host.isConnected)return;
 const tabs=el('div',undefined,'reader-structure-tabs');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Structure views');const panels=el('div');host.append(tabs,panels);const loaded=new Set();
 const options=[['cell','Unit cell'],['particle','Particle morphology'],...(finite.length?[['finite','Atomistic particle']]:[])];
 for(const [key,label] of options){const panel=el('div',undefined,'reader-structure-panel');panel.id='reader-structure-'+key;panel.setAttribute('role','tabpanel');panel.hidden=true;panels.append(panel);const b=button(label,()=>select(key));b.setAttribute('role','tab');b.setAttribute('aria-controls',panel.id);b.dataset.view=key;tabs.append(b);}
 async function select(key){for(const b of tabs.children)b.setAttribute('aria-selected',String(b.dataset.view===key));for(const p of panels.children)p.hidden=p.id!=='reader-structure-'+key;if(loaded.has(key))return;loaded.add(key);const panel=panels.querySelector('#reader-structure-'+key);
  try{if(key==='particle'){await mountParticleContext(panel,r,presentation);return;}
  const entries=key==='finite'?finite:refs;if(entries.length){await mountReferenceChoices(panel,entries,r,key==='finite');return;}
  if(key==='cell'&&r.lineage.source_group==='heo2003'){const {mountHeoAverage}=await import('./heo2003-average-viewer.mjs');if(await mountHeoAverage(panel,r))return;}
  if(key==='cell'&&r.lineage.source_group==='lian2021'){const {mountLianBulk,eligibleBulkContexts}=await import('./lian2021-bulk-viewer.mjs');if(eligibleBulkContexts(r).length){await mountLianBulk(panel,r);return;}}
  panel.append(el('h3','Unit-cell reference not yet verified'),el('p','The reviewed source evidence remains available below. A phase-specific atomic model will be added when its coordinates and provenance can be verified.','reader-note'),link('Inspect structure evidence →',recordURL(r.record_id)+'#structures','reader-data-link'));
  }catch(error){panel.append(el('p','This structure view could not load. The complete evidence record remains available.','reader-note'));console.error(error);}
 }
 await select(refs.length?'cell':'particle');
}
