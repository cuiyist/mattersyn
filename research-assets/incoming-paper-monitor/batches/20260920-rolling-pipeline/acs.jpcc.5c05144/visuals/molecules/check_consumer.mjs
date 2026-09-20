import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const O=path.dirname(fileURLToPath(import.meta.url)),A=O,P=path.join(A,'../..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\ufeff/,''));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const checks=[];const ck=(v,n)=>{checks.push({check:n,passed:!!v});if(!v)throw Error(n);};
class Elem{
 constructor(tag,text=''){this.tagName=tag;this.textContent=text;this.children=[];this.style={};this.attrs={};this.value='0';this.isConnected=true;this.clientWidth=600;this.clientHeight=440;}
 append(...xs){this.children.push(...xs);}
 replaceChildren(...xs){this.children=[...xs];}
 setAttribute(k,v){this.attrs[k]=v;}
 addEventListener(){}
 showModal(){this.open=true;}
 close(){this.open=false;}
 querySelector(tag){return walk(this).find(x=>x!==this&&x.tagName===tag);}
}
const walk=e=>[e,...e.children.flatMap(walk)],texts=e=>walk(e).map(x=>x.textContent).filter(Boolean);
globalThis.document={body:new Elem('body'),createElement:t=>new Elem(t),createTextNode:t=>new Elem('#text',t)};
const registry=read(path.join(A,'registry-additions.json')),bindings=read(path.join(A,'bindings-proposal.json'));
const before=JSON.stringify({registry,bindings});
const entries=new Map(registry.entries.map(e=>[e.id,e])),approved=structuredClone(bindings);
for(const notes of Object.values(approved.bindingNotes))for(const n of Object.values(notes))n.binding_approved=true;
const data={registry,bindings:approved,entries},privateData={...data,bindings};
const solutions=read(path.join(A,'solution-components-proposal.json')),stockmap=read(path.join(A,'stock-component-map.json')).stocks;
const records=new Map(read(path.join(P,'canonical-proposal/v1/record-manifest.json')).records.map(x=>[x.record_id,read(x.path)]));
const fetched=[];globalThis.fetch=async u=>{
 const url=new URL(u);fetched.push(url.href);
 if(url.pathname.endsWith('/solution-components.json'))return{ok:true,json:async()=>solutions};
 const segment=url.pathname.split('/models/')[1];ck(!!segment&&path.basename(segment)===segment,'Only exact model request');
 const file=path.join(A,'models',segment);ck(fs.existsSync(file),'Model resolves in frozen package');
 ck(url.searchParams.get('sha')===sha(file),'Requested model digest exact');
 return{ok:true,json:async()=>read(file)};
};
let currentViewer;globalThis.window={};
globalThis.$3Dmol=window.$3Dmol={createViewer:()=>{
 currentViewer={atoms:null,styles:[],labels:[],calls:[],addModel(){return{addAtoms:x=>{this.atoms=x;}};},
 setStyle(a,b){this.styles.push([a,b]);},addLabel(...x){this.labels.push(x);},
 clear(){},resize(){this.calls.push('resize');},zoomTo(){this.calls.push('fit');},
 zoom(x){this.calls.push(['zoom',x]);},render(){this.calls.push('render');},rotate(...x){this.calls.push(['rotate',...x]);}};
 return currentViewer;
}};
const modulePath=path.join(A,'reference-snapshots/chemical-viewer.mjs');
const api=await import(pathToFileURL(modulePath));
let slots=0,dialogs=0,threeD=0,stockTransitions=0,contextTransitions=0;
for(const [rid,map] of Object.entries(bindings.recordBindings))for(const[mid,id]of Object.entries(map)){
 slots++;const raw=entries.get(id),note=bindings.bindingNotes[rid][mid];
 ck(api.chemicalEntry(privateData,rid,mid)===raw,'Private approval gate preserved '+rid+'/'+mid);
 const resolved=api.chemicalEntry(data,rid,mid);
 for(const k of ['name','caption','limitations'])ck(eq(resolved[k],note.viewOverrides[k]),'Exact approved caption field '+k);
 ck(resolved.sourceBindingCaption===note.viewOverrides.caption,'Source caption retained');
 ck(resolved.svgPath===raw.svgPath&&resolved.model3dPath===raw.model3dPath,'No model substitution');
 const injected=structuredClone(approved);injected.bindingNotes[rid][mid].viewOverrides.model3dPath='unapproved.json';
 ck(api.chemicalEntry({...data,bindings:injected},rid,mid).model3dPath===raw.model3dPath,'Geometry override rejected');
}
ck(slots===26,'All 26 slots executed');ck(api.chemicalEntry(data,'other-paper','oa')===undefined,'Cross-source exclusion');
ck(api.chemicalEntry(data,[...records.keys()][0],'unmapped')===undefined,'Unmapped slot exclusion');
for(const raw of entries.values()){
 const e={...raw,sourceBindingCaption:'Author test source context for '+raw.id};
 currentViewer=null;await api.openChemical(e);dialogs++;
 const dialog=document.body.children[0],all=texts(dialog);
 ck(dialog.open&&all.includes(e.name),'Exact popup identity');ck(all.includes(e.sourceBindingCaption),'Source caption visible alongside model');
 for(const l of new Set(e.limitations||[]))ck(all.includes(l),'Every limitation visible');
 const buttons=walk(dialog).filter(x=>x.tagName==='button');
 for(const label of ['−','Reset','+'])ck(buttons.some(x=>x.textContent===label),'Control exists '+label);
 if(e.model3dPath){
  threeD++;const model=read(path.join(A,e.model3dPath));
  ck(currentViewer.atoms.length===model.atoms.length,'3D atom count exact');
  for(let i=0;i<model.atoms.length;i++){
   const x=model.atoms[i],y=currentViewer.atoms[i];ck(y.elem===(x.element??x.elem)&&y.x===x.x&&y.y===x.y&&y.z===x.z,'3D coordinates unchanged');
   for(const b of model.bonds.filter(b=>b.a===i||b.b===i)){const j=b.a===i?b.b:b.a;ck(y.bonds.includes(j)&&y.bondOrder[y.bonds.indexOf(j)]===b.order,'Model bond exact');}
  }
  ck(all.includes(model.caption||e.caption),'Model provenance caption shown');
  for(const g of model.functionalGroups||[])ck(currentViewer.styles.some(x=>eq(x[0].index,g.atomIndices)),'Functional group exact indices');
  const toggle=walk(dialog).find(x=>x.tagName==='input');if(toggle){toggle.checked=false;toggle.onchange();toggle.checked=true;toggle.onchange();}
  for(const label of ['−','Reset','+'])buttons.find(x=>x.textContent===label).onclick();
  ck(currentViewer.calls.some(x=>Array.isArray(x)&&x[0]==='zoom'&&x[1]===1.2),'Zoom dispatch');
 }else{
  ck(currentViewer===null,'Symbol/2D has no fabricated 3D renderer');const img=walk(dialog).find(x=>x.tagName==='img');
  ck(String(img.src).includes(e.svgPath+'?sha='+e.assetHashes.svgPath),'Exact qualified image');
  buttons.find(x=>x.textContent==='+').onclick();ck(img.style.transform==='scale(1.2)','Image enlargement dispatch');
  buttons.find(x=>x.textContent==='Reset').onclick();ck(img.style.transform==='scale(1)','Image reset dispatch');
 }
}
function examineSelector(host,components,counter){
 const select=walk(host).find(x=>x.tagName==='select'),view=walk(host).find(x=>x.className==='solution-component-view');
 ck(select.children.length===components.length,'Every component option present');
 ck(texts(host).some(t=>t.includes('does not assign solution speciation')),'Solution caveat visible');
 for(let i=0;i<components.length;i++){
  select.value=String(i);select.onchange();const {entry,role}=components[i];
  ck(select.children[i].textContent===entry.name+' · '+role,'Exact option label/role');
  ck(texts(view).includes(entry.caption||entry.depictionKind),'Exact component caption');
  ck(String(view.children[0].src).includes(entry.svgPath+'?sha='+entry.assetHashes.svgPath),'Component asset exact');
  ck(texts(view).includes(entry.model3dPath?'Rotate component reference ↗':'Inspect component representation ↗'),'Appropriate 3D availability');
  counter();
 }
}
for(const s of stockmap){
 const r=records.get(s.record_id),stock=r.stocks.find(x=>x.id===s.stock_id),host=new Elem('div');api.mountStockComponents(host,r,stock,data);
 examineSelector(host,stock.components.map(c=>({entry:api.chemicalEntry(data,r.record_id,c.material_id),role:r.materials.find(m=>m.id===c.material_id).role.replaceAll('_',' ')})),()=>stockTransitions++);
}
for(const [rid,r]of records){
 const host=new Elem('div');await api.mountReagentComponents(host,r,data);const contexts=solutions.contexts.filter(x=>x.record_id===rid);
 ck(host.children.length===contexts.length,'Exact context dispatch '+rid);
 for(let j=0;j<contexts.length;j++){
  const c=contexts[j],section=host.children[j];ck(texts(section).includes(c.label)&&texts(section).includes(c.scope),'Context label and source scope visible');
  examineSelector(section,c.components.map(x=>({entry:{...entries.get(x.registry_id),...x.viewOverrides},role:x.role})),()=>contextTransitions++);
 }
}
const alien=new Elem('div');await api.mountReagentComponents(alien,{record_id:'other-paper'},data);ck(alien.children.length===0,'No stock contexts leak to other paper');
ck(stockTransitions===12&&contextTransitions===12,'All 24 component transitions executed');
ck(dialogs===13&&threeD===6,'All 13 identities including 6 reference-geometry entries');
ck(JSON.stringify({registry,bindings})===before,'Original registry and private binding objects unchanged');
const bound_files=Object.fromEntries([modulePath,path.join(A,'registry-additions.json'),path.join(A,'bindings-proposal.json'),path.join(A,'solution-components-proposal.json'),path.join(A,'stock-component-map.json'),fileURLToPath(import.meta.url)].map(p=>[path.resolve(p),sha(p)]));
const result={schema:'mattersyn-author-molecule-consumer-checks/1',independent_approval:false,author:'/root/peng1998_reader_assets',status:'passed',check_count:checks.length,counts:{slots,dialogs,threeD_entry_views:threeD,stockTransitions,contextTransitions},method:'Actual immutable chemical-viewer module executed with minimal DOM and 3Dmol data sink; approval flags changed only in in-memory copies. No mounted browser or rasterized WebGL claim.',bound_files,checks};
fs.writeFileSync(path.join(O,'consumer-checks.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,checks:checks.length,counts:result.counts}));
