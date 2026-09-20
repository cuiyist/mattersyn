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
export async function openChemical(entry){
 if(!dialog){dialog=el('dialog',undefined,'guide-molecule-dialog');document.body.append(dialog);dialog.addEventListener('close',()=>{viewer?.clear();viewer=null;});}
 viewer?.clear();viewer=null;dialog.replaceChildren();const head=el('header'),close=el('button','Close ×');close.type='button';close.onclick=()=>dialog.close();head.append(el('h2',entry.name),close);const host=el('div',undefined,'molecule-model');host.tabIndex=0;host.setAttribute('aria-label',entry.name+' structure viewer');dialog.append(head,el('p',entry.formula||'Source-defined mixture'),host);dialog.showModal();let scale=1,fit=null,depictionCaption=entry.caption||entry.depictionKind;
 if(entry.model3dPath&&window.$3Dmol){const model=await(await fetch(new URL(entry.model3dPath+'?sha='+entry.assetHashes.model3dPath,base))).json();if(!dialog.open)return;viewer=$3Dmol.createViewer(host,{backgroundColor:'#f7faff'});viewer.addModel().addAtoms(atoms(model));for(const atom of model.atoms.filter(a=>a.isotope)){const symbol=atom.element??atom.elem;viewer.addLabel((atom.isotope===2&&symbol==='H'?'²H':String(atom.isotope)+symbol),{position:{x:atom.x,y:atom.y,z:atom.z},fontSize:14,fontColor:'#174563',backgroundOpacity:0,inFront:true});}viewer.setStyle({},{stick:{radius:.13},sphere:{scale:.25}});fit=()=>{viewer.resize();viewer.zoomTo();viewer.zoom(Math.min(.9,host.clientWidth/host.clientHeight*.85));viewer.render();};if(host.clientWidth<350)viewer.rotate(90,'z');fit();depictionCaption=model.caption||depictionCaption;if(model.functionalGroups?.length){const panel=el('div',undefined,'functional-group-controls'),label=el('label'),toggle=el('input');toggle.type='checkbox';toggle.checked=true;label.append(toggle,document.createTextNode(' Highlight functional groups'));panel.append(label);const palette=['#d49737','#a174bc','#3aa7a2','#cf7182'];for(const [i,g] of model.functionalGroups.entries()){const badge=el('span',g.label);badge.style.borderLeft='4px solid '+palette[i%palette.length];badge.style.padding='4px 9px';panel.append(badge);}const style=()=>{if(!viewer)return;viewer.setStyle({},{stick:{radius:.13},sphere:{scale:.25}});if(toggle.checked)for(const [i,g] of model.functionalGroups.entries())viewer.setStyle({index:g.atomIndices},{stick:{radius:.16,color:palette[i%palette.length]},sphere:{scale:.28,color:palette[i%palette.length]}});viewer.render();};toggle.onchange=style;style();dialog.append(panel);}dialog.append(el('p','Drag to rotate; scroll to zoom. A reference or computed free-compound conformer does not establish solution speciation or surface binding.'));}
 else{const img=chemicalImage(entry);img.style.height='100%';img.loading='eager';host.style.overflow='auto';host.append(img);}
 const controls=el('div',undefined,'protocol-controls');for(const [label,factor] of [['−',1/1.2],['Reset',0],['+',1.2]]){const b=el('button',label);b.type='button';b.onclick=()=>{if(viewer){factor?viewer.zoom(factor):fit();viewer.render();}else{scale=factor?Math.max(.5,Math.min(4,scale*factor)):1;host.querySelector('img').style.transform=`scale(${scale})`;}};controls.append(b);}dialog.append(controls,el('p',depictionCaption));if(entry.sourceBindingCaption&&entry.sourceBindingCaption!==depictionCaption)dialog.append(el('p',entry.sourceBindingCaption,'guide-notice'));for(const note of new Set(entry.limitations||[]))if(note!==depictionCaption&&note!==entry.sourceBindingCaption)dialog.append(el('p',note));
 for(const url of entry.sourceUrls||[]){const a=el('a','Chemical reference ↗');a.href=url;a.target='_blank';a.rel='noopener';dialog.append(a,el('br'));}
 host.onkeydown=e=>{if(!viewer)return;const r={ArrowLeft:[-12,'y'],ArrowRight:[12,'y'],ArrowUp:[-12,'x'],ArrowDown:[12,'x']}[e.key];if(r)viewer.rotate(...r);else if(e.key==='Home')fit();else return;e.preventDefault();viewer.render();};
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
