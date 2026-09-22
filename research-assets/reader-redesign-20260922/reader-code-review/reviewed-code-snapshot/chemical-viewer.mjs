const base=new URL('assets/chemical-registry/',import.meta.url);
let registryPromise,dialog,viewer;
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
export function chemicalRegistry(){return registryPromise??=Promise.all(['registry.json','bindings.json'].map(async name=>{const r=await fetch(new URL(name,base),{cache:'no-store'});if(!r.ok)throw Error('Chemical registry unavailable');return r.json();})).then(([registry,bindings])=>({registry,bindings,entries:new Map(registry.entries.map(x=>[x.id,x]))}));}
export function chemicalEntry(data,recordId,materialId){
 const entry=data.entries.get(data.bindings.recordBindings[recordId]?.[materialId]);
 const note=data.bindings.bindingNotes?.[recordId]?.[materialId],overrides=note?.binding_approved?note.viewOverrides:null;
 if(!entry||!overrides)return entry;
 const scoped={...entry};for(const key of ['name','caption','limitations'])if(overrides[key]!==undefined)scoped[key]=overrides[key];
 scoped.sourceBindingCaption=overrides.caption;return scoped;
}
export function chemicalImage(entry){const img=el('img',undefined,'chemical-preview');img.src=new URL(entry.svgPath+'?sha='+entry.assetHashes.svgPath,base);img.alt=entry.name+' · '+entry.depictionKind;img.loading='lazy';return img;}
function atoms(model){const a=model.atoms.map((x,i)=>({index:i,serial:i,elem:x.element??x.elem,x:x.x,y:x.y,z:x.z,bonds:[],bondOrder:[]}));for(const b of model.bonds||[]){a[b.a].bonds.push(b.b);a[b.a].bondOrder.push(b.order);a[b.b].bonds.push(b.a);a[b.b].bondOrder.push(b.order);}return a;}
const elementNames={H:'Hydrogen',He:'Helium',Li:'Lithium',Be:'Beryllium',B:'Boron',C:'Carbon',N:'Nitrogen',O:'Oxygen',F:'Fluorine',Ne:'Neon',Na:'Sodium',Mg:'Magnesium',Al:'Aluminium',Si:'Silicon',P:'Phosphorus',S:'Sulfur',Cl:'Chlorine',Ar:'Argon',K:'Potassium',Ca:'Calcium',Sc:'Scandium',Ti:'Titanium',V:'Vanadium',Cr:'Chromium',Mn:'Manganese',Fe:'Iron',Co:'Cobalt',Ni:'Nickel',Cu:'Copper',Zn:'Zinc',Ga:'Gallium',Ge:'Germanium',As:'Arsenic',Se:'Selenium',Br:'Bromine',Kr:'Krypton',Rb:'Rubidium',Sr:'Strontium',Y:'Yttrium',Zr:'Zirconium',Nb:'Niobium',Mo:'Molybdenum',Ru:'Ruthenium',Rh:'Rhodium',Pd:'Palladium',Ag:'Silver',Cd:'Cadmium',In:'Indium',Sn:'Tin',Sb:'Antimony',Te:'Tellurium',I:'Iodine',Xe:'Xenon',Cs:'Caesium',Ba:'Barium',La:'Lanthanum',Ce:'Cerium',Pr:'Praseodymium',Nd:'Neodymium',Sm:'Samarium',Eu:'Europium',Gd:'Gadolinium',Tb:'Terbium',Dy:'Dysprosium',Ho:'Holmium',Er:'Erbium',Tm:'Thulium',Yb:'Ytterbium',Lu:'Lutetium',Hf:'Hafnium',Ta:'Tantalum',W:'Tungsten',Re:'Rhenium',Os:'Osmium',Ir:'Iridium',Pt:'Platinum',Au:'Gold',Hg:'Mercury',Tl:'Thallium',Pb:'Lead',Bi:'Bismuth',Th:'Thorium',U:'Uranium'};
export const atomColors={H:'#c3ccd8',C:'#63748b',N:'#4169d1',O:'#d5475b',F:'#72b866',P:'#e38b27',S:'#d2b128',Cl:'#54a66a',Br:'#a15b37',I:'#8757ae',Si:'#b3a18c',Se:'#db9944',Cd:'#298d9e',Pb:'#70839b',Cs:'#9878c5',Ag:'#91a4b3',Au:'#c4a446',Fe:'#bf7542',Zn:'#6d96ba',Ge:'#9484a8',Te:'#b79b57',La:'#809aad',Ce:'#aaa16d',Mo:'#738c9c',In:'#7e88b5',Co:'#4c83b5',Ni:'#5caa87',Ir:'#9d8fb5',Mn:'#be7eaf',Pt:'#a2afb9',Sn:'#718695',Al:'#b7bfc9',As:'#a48cc4',X:'#9975b3'};
let dialogGeneration=0;
export function elementLegend(elements){const legend=el('div',undefined,'element-legend');legend.setAttribute('aria-label','Element color legend');for(const sym of [...new Set(elements)].sort()){const item=el('span'),dot=el('i');dot.style.background=atomColors[sym]||'#8c91b0';item.append(dot,document.createTextNode(sym+' · '+(elementNames[sym]||sym)));legend.append(item);}return legend;}
export async function openChemical(entry){
 const generation=++dialogGeneration;
 if(!dialog){dialog=el('dialog',undefined,'guide-molecule-dialog reader-molecule-dialog');document.body.append(dialog);dialog.addEventListener('close',()=>{dialogGeneration++;viewer?.clear();viewer=null;});}
 viewer?.clear();viewer=null;dialog.replaceChildren();const head=el('header'),close=el('button','Close ×');close.type='button';close.onclick=()=>dialog.close();head.append(el('h2',entry.name),close);const host=el('div',undefined,'molecule-model');host.tabIndex=0;host.setAttribute('aria-label',entry.name+' structure viewer');dialog.append(head,el('p',entry.formula||'Source-defined composition','molecular-formula'),host);if(!dialog.open)dialog.showModal();let scale=1,fit=null,depictionCaption=entry.caption||entry.depictionKind;
 const controls=el('div',undefined,'protocol-controls'),info=el('p','Select an atom to identify it.','atom-inspection');
 try{
 if(entry.model3dPath&&window.$3Dmol){
  const response=await fetch(new URL(entry.model3dPath+'?sha='+entry.assetHashes.model3dPath,base));if(!response.ok)throw Error('Coordinate file unavailable');const model=await response.json();if(!dialog.open||generation!==dialogGeneration)return;
  viewer=$3Dmol.createViewer(host,{backgroundColor:'#f7faff'});viewer.addModel().addAtoms(atoms(model));
  let allLabels=false,highlight=true;const redraw=()=>{if(!viewer)return;viewer.removeAllLabels();viewer.removeAllShapes();viewer.setStyle({},{stick:{radius:.13,colorfunc:a=>atomColors[a.elem]||'#8c91b0'},sphere:{scale:.25,colorfunc:a=>atomColors[a.elem]||'#8c91b0'}});
   for(const a of model.atoms){const sym=a.element??a.elem;if(allLabels||!['C','H'].includes(sym)||a.isotope)viewer.addLabel((a.isotope?String(a.isotope):'')+sym,{position:{x:a.x,y:a.y,z:a.z},fontSize:13,fontColor:'#18334b',backgroundColor:'#ffffff',backgroundOpacity:.72,inFront:true});}
   if(highlight)for(const [i,g] of (model.functionalGroups||[]).entries())for(const index of g.atomIndices||[]){const a=model.atoms[index];if(a)viewer.addSphere({center:{x:a.x,y:a.y,z:a.z},radius:.52,color:['#d49737','#a174bc','#3aa7a2','#cf7182'][i%4],opacity:.19});}viewer.render();};
  viewer.setClickable({},true,a=>{info.textContent=(elementNames[a.elem]||a.elem)+' ('+a.elem+') · atom '+(a.index+1);});
  fit=()=>{viewer.resize();viewer.zoomTo();viewer.zoom(Math.min(.9,host.clientWidth/Math.max(host.clientHeight,1)*.85));viewer.render();};
  const labels=el('label'),labelCheck=el('input');labelCheck.type='checkbox';labelCheck.onchange=()=>{allLabels=labelCheck.checked;redraw();};labels.append(labelCheck,document.createTextNode(' Label every atom'));controls.append(labels);
  if(model.functionalGroups?.length){const groupLabel=el('label'),toggle=el('input');toggle.type='checkbox';toggle.checked=true;toggle.onchange=()=>{highlight=toggle.checked;redraw();};groupLabel.append(toggle,document.createTextNode(' Functional-group halos'));controls.append(groupLabel);const groups=el('div',undefined,'functional-group-controls');for(const [i,g] of model.functionalGroups.entries()){const item=el('span',g.label);item.style.borderLeft='4px solid '+['#d49737','#a174bc','#3aa7a2','#cf7182'][i%4];groups.append(item);}dialog.append(groups);}
  dialog.append(elementLegend(model.atoms.map(a=>a.element??a.elem)),info);redraw();fit();depictionCaption=model.caption||depictionCaption;
 }else{const img=chemicalImage(entry);img.loading='eager';host.classList.add('molecule-static');host.append(img);const symbols=(entry.formula||'').match(/[A-Z][a-z]?/g)||[];dialog.append(elementLegend(symbols.filter(x=>elementNames[x])));info.textContent='Component or connectivity representation; no 3D coordinates are assigned.';dialog.append(info);}
 }catch(error){host.replaceChildren(chemicalImage(entry));dialog.append(el('p','3D view unavailable. The verified chemical illustration is shown.'));}
 for(const [label,factor] of [['−',1/1.2],['Reset',0],['+',1.2]]){const b=el('button',label);b.type='button';b.onclick=()=>{if(viewer){factor?viewer.zoom(factor):fit();viewer.render();}else{scale=factor?Math.max(.5,Math.min(4,scale*factor)):1;const img=host.querySelector('img');if(img)img.style.transform=`scale(${scale})`;}};controls.append(b);}dialog.append(controls);
 const details=el('details',undefined,'model-source-details');details.append(el('summary','Structure source and interpretation'),el('p',depictionCaption));if(entry.sourceBindingCaption&&entry.sourceBindingCaption!==depictionCaption)details.append(el('p',entry.sourceBindingCaption));for(const note of new Set(entry.limitations||[]))if(note!==depictionCaption&&note!==entry.sourceBindingCaption)details.append(el('p',note));for(const url of entry.sourceUrls||[]){const a=el('a','Chemical reference ↗');a.href=url;a.target='_blank';a.rel='noopener';details.append(a,el('br'));}dialog.append(el('p',entry.depictionKind==='source_crystallographic_model'?'Source crystallographic model · see refinement scope below.':'Reference representation · molecular orientation and solution speciation are not assigned.','model-scope'),details);
 host.onkeydown=e=>{if(!viewer)return;const turn={ArrowLeft:[-12,'y'],ArrowRight:[12,'y'],ArrowUp:[-12,'x'],ArrowDown:[12,'x']}[e.key];if(turn)viewer.rotate(...turn);else if(e.key==='Home')fit();else return;e.preventDefault();viewer.render();};
}

function componentSelector(host,label,components,scope){
 const available=components.filter(c=>c.entry);if(!available.length)return;
 const panel=el('div',undefined,'solution-components'),select=el('select',undefined,'guide-route-select'),view=el('div',undefined,'solution-component-view');
 select.setAttribute('aria-label','Chemical components of '+label);
 for(const [i,c] of available.entries()){const option=el('option',c.entry.name+' · '+c.role);option.value=String(i);select.append(option);}
 const render=()=>{const c=available[Number(select.value)];view.replaceChildren(chemicalImage(c.entry),el('p',c.entry.caption||c.entry.depictionKind,'chemical-caption'));const button=el('button',c.entry.model3dPath?'Rotate component reference ↗':'Inspect component representation ↗','molecule-link');button.type='button';button.onclick=()=>openChemical(c.entry);view.append(button);};
 panel.append(el('p','Select a solute or solvent component. Each is a separate reference; this view does not assign solution speciation or a solvent coordination shell.','guide-notice'),select,view);if(scope)panel.append(el('p',scope,'chemical-caption'));host.append(panel);select.onchange=render;render();
}
export function mountStockComponents(host,record,stock,data){
 const components=stock.components.map(c=>{const m=record.materials.find(m=>m.id===c.material_id);return {entry:chemicalEntry(data,record.record_id,c.material_id),role:(m?.role||'component').replaceAll('_',' ')};});
 componentSelector(host,stock.name,components);
}
let solutionContextsPromise;
export async function mountReagentComponents(host,record,data){
 solutionContextsPromise??=fetch(new URL('solution-components.json',base),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Solution component registry unavailable');return r.json();});
 const contexts=(await solutionContextsPromise).contexts.filter(c=>c.record_id===record.record_id);if(!host.isConnected)return;
 for(const c of contexts){const section=el('section',undefined,'stock-record');section.append(el('h4',c.label));componentSelector(section,c.label,c.components.map(x=>{const entry=data.entries.get(x.registry_id);return {entry:entry?{...entry,...x.viewOverrides,sourceBindingCaption:x.viewOverrides?.caption}:null,role:x.role};}),c.scope);host.append(section);}
}
export async function enhanceRecordChemicals(record){
 const data=await chemicalRegistry();for(const button of document.querySelectorAll('[data-material-id]')){const entry=chemicalEntry(data,record.record_id,button.dataset.materialId);if(!entry)continue;const card=button.closest('.reagent-record');card.querySelector('.chemical-formula').after(chemicalImage(entry));button.textContent=entry.model3dPath?'Explore molecular structure ↗':'Inspect chemical representation ↗';button.onclick=()=>openChemical(entry);button.after(el('p',entry.caption||entry.depictionKind,'chemical-caption'));}
 for(const card of document.querySelectorAll('[data-stock-id]')){const stock=record.stocks.find(s=>s.id===card.dataset.stockId);if(stock)mountStockComponents(card,record,stock,data);}
 const extra=document.getElementById('record-reagent-components');if(extra)await mountReagentComponents(extra,record,data);
}
