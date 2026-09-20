import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const O=path.dirname(fileURLToPath(import.meta.url)),F=path.dirname(O),B=path.join(F,'visuals/molecular-bindings'),A=path.join(B,'consumer-fixture');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\ufeff/,'')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const checks=[];function ck(name,ok){checks.push({check:name,passed:!!ok});if(!ok)throw Error(name);}
class Element{constructor(tag,text){Object.assign(this,{tag,textContent:text,children:[],style:{},attrs:{},value:'0',isConnected:true,clientWidth:600,clientHeight:440});}append(...x){this.children.push(...x);}replaceChildren(...x){this.children=x;}setAttribute(k,v){this.attrs[k]=v;}addEventListener(){}showModal(){this.open=true;}close(){this.open=false;}querySelector(t){return nodes(this).find(x=>x!==this&&x.tag===t);}}
const nodes=x=>[x,...x.children.flatMap(nodes)],words=x=>nodes(x).map(e=>e.textContent).filter(Boolean);
globalThis.document={body:new Element('body'),createElement:t=>new Element(t),createTextNode:t=>new Element('#text',t)};
const registry=read(path.join(A,'registry-additions.json')),binding=read(path.join(B,'bindings-proposal.json')),slots=read(path.join(B,'material-slot-map.json')).slots,stocks=read(path.join(B,'stock-component-map.json')).stocks,solutions=read(path.join(B,'solution-components-proposal.json'));
const before=JSON.stringify({registry,binding,solutions}),entries=new Map(registry.entries.map(x=>[x.id,x])),privateData={registry,bindings:binding,entries},approved=structuredClone(binding);
for(const notes of Object.values(approved.bindingNotes))for(const n of Object.values(notes))n.binding_approved=true;
const data={registry,bindings:approved,entries};let sink;
globalThis.window={};globalThis.$3Dmol=window.$3Dmol={createViewer:()=>{sink={atoms:[],calls:[],addModel(){return{addAtoms:a=>this.atoms=a};},setStyle(){},addLabel(){},clear(){},resize(){},zoomTo(){},zoom(x){this.calls.push(['zoom',x]);},render(){},rotate(...x){this.calls.push(['rotate',...x]);}};return sink;}};
globalThis.fetch=async u=>{const url=new URL(u);if(url.pathname.endsWith('/solution-components.json'))return{ok:true,json:async()=>solutions};const rel='models/'+url.pathname.split('/models/')[1];const p=path.join(A,rel);ck('exact model request SHA',url.searchParams.get('sha')===sha(p));return{ok:true,json:async()=>read(p)};};
const modulePath='[local path redacted]';
ck('actual consumer equals frozen consumer',sha(modulePath)===sha(path.join(A,'reference-snapshots/chemical-viewer.mjs')));
const api=await import(pathToFileURL(modulePath));
for(const s of slots){
 const e=api.chemicalEntry(data,s.record_id,s.material_id),raw=entries.get(s.registry_id);
 ck(s.record_id+'/'+s.material_id+' exact qualified reference',e.id===s.registry_id&&e.svgPath===raw.svgPath&&e.model3dPath===raw.model3dPath);
 ck('private unapproved override not applied',api.chemicalEntry(privateData,s.record_id,s.material_id)===raw);
 for(const k of ['name','caption','limitations'])ck('approved exact '+k,JSON.stringify(e[k])===JSON.stringify(s.viewOverrides[k]));
 const hostile=structuredClone(approved);hostile.bindingNotes[s.record_id][s.material_id].viewOverrides.model3dPath='wrong.json';
 ck('model override cannot replace geometry',api.chemicalEntry({...data,bindings:hostile},s.record_id,s.material_id).model3dPath===raw.model3dPath);
 sink=null;await api.openChemical(e);const dialog=document.body.children[0];ck('scoped caption visible',words(dialog).includes(s.viewOverrides.caption));
 for(const note of e.limitations)ck('limitation visible',words(dialog).includes(note));
 const buttons=nodes(dialog).filter(x=>x.tag==='button');for(const label of ['+','−','Reset'])buttons.find(x=>x.textContent===label).onclick();
 if(e.model3dPath){
  const model=read(path.join(A,e.model3dPath));ck('actual exact reference atom coordinates',JSON.stringify(sink.atoms.map(x=>[x.elem,x.x,x.y,x.z]))===JSON.stringify(model.atoms.map(x=>[x.element??x.elem,x.x,x.y,x.z])));
  const host=nodes(dialog).find(x=>x.className==='molecule-model');host.onkeydown({key:'ArrowLeft',preventDefault(){}});ck('keyboard rotation dispatched',sink.calls.some(x=>x[0]==='rotate'&&x[1]===-12&&x[2]==='y'));
 }else ck('no 3D fabricated for symbol or 2D',sink===null);
}
ck('unmapped record rejected',api.chemicalEntry(data,'different-paper','ode')===undefined);
ck('unmapped material rejected',api.chemicalEntry(data,slots[0].record_id,'nonexistent')===undefined);
const records=new Map(read(path.join(F,'canonical-proposal/draft-v2/record-manifest.json')).records.map(x=>[x.record_id,read(x.path)]));let stockTransitions=0,contextTransitions=0;
for(const s of stocks){const r=records.get(s.record_id),host=new Element('section');api.mountStockComponents(host,r,r.stocks.find(x=>x.id===s.stock_id),data);const select=nodes(host).find(x=>x.tag==='select');ck('stock option count',select.children.length===s.components.length);for(let i=0;i<s.components.length;i++){select.value=String(i);select.onchange();stockTransitions++;const c=s.components[i],entry=api.chemicalEntry(data,r.record_id,c.material_id);ck('stock exact component asset',String(nodes(host).find(x=>x.tag==='img').src).includes(entry.svgPath+'?sha='+entry.assetHashes.svgPath));}}
for(const [rid,r]of records){const host=new Element('section');await api.mountReagentComponents(host,r,data);const contexts=solutions.contexts.filter(x=>x.record_id===rid);ck('only exact record solution contexts',host.children.length===contexts.length);for(let j=0;j<contexts.length;j++){const c=contexts[j],section=host.children[j];ck('source scope visible',words(section).includes(c.scope));const select=nodes(section).find(x=>x.tag==='select');for(let i=0;i<c.components.length;i++){select.value=String(i);select.onchange();contextTransitions++;ck('stock caption transport',words(section).includes(c.components[i].viewOverrides.caption));}}}
const absent=new Element('div');await api.mountReagentComponents(absent,{record_id:'different-paper'},data);ck('no cross-source context',absent.children.length===0);
ck('all transitions executed',stockTransitions===16&&contextTransitions===16);
ck('read only data',before===JSON.stringify({registry,binding,solutions}));
const out={status:'passed',check_count:checks.length,counts:{slot_openings:slots.length,stockTransitions,contextTransitions},method:'Independent harness importing the actual current consumer, minimal DOM plus coordinate sink. No browser or rendered WebGL claim.',module_path:modulePath,module_sha256:sha(modulePath),checks};
fs.writeFileSync(path.join(O,'consumer-independent-checks.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify({status:out.status,check_count:checks.length,counts:out.counts}));
