import fs from 'node:fs';import path from 'node:path';import {pathToFileURL,fileURLToPath} from 'node:url';import crypto from 'node:crypto';
const O=path.dirname(fileURLToPath(import.meta.url)),L=path.dirname(O),S='[local path redacted]';const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const records=fs.readdirSync(S+'/data/records').filter(f=>f.endsWith('.json')).map(f=>read(S+'/data/records/'+f));const lian=records.filter(r=>r.lineage.source_group==='lian2021');
const checks=[];function ok(n,b){checks.push({check:n,passed:!!b});if(!b)throw Error(n);}
class Node{constructor(tag){this.tag=tag;this.textContent='';this.children=[];this.dataset={};this.style={};this.attrs={};this.listeners={};this.className='';this.classList={add(){},toggle(){}};}append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}setAttribute(k,v){this.attrs[k]=v;}addEventListener(k,v){this.listeners[k]=v;}querySelector(tag){if(tag==='svg'&&this.innerHTML?.includes('<svg'))return {style:{},outerHTML:this.innerHTML};return flat(this).find(n=>n.tag===tag);}}
const flat=n=>[n,...n.children.flatMap(x=>x instanceof Node?flat(x):[])];
globalThis.document={createElement:t=>new Node(t),createTextNode:t=>({textContent:t})};
const {buildLian2021Scene}=await import(pathToFileURL(S+'/dist/lian2021-protocol.mjs'));
const {mountProtocol}=await import(pathToFileURL(S+'/dist/protocol-visuals.mjs'));
let oldOps=0,stages=0,rows=0;
for(const r of records){
 if(r.lineage.source_group!=='lian2021'){for(const op of r.operations){ok(r.record_id+' excludes Lian '+op.id,buildLian2021Scene(op,r)===null);oldOps++;}continue;}
 if(!r.operations.length)continue;
 const host=new Node('host');mountProtocol(host,r);const buttons=host.children[0].children;
 ok(r.record_id+' stage buttons',buttons.length===r.operations.length);
 for(let i=0;i<r.operations.length;i++){
  buttons[i].listeners.click();const op=r.operations[i],scene=buildLian2021Scene(op,r),nodes=flat(host);
  ok(r.record_id+'/'+op.id+' source scene',scene?.kind===r.record_id+'--'+op.id);
  ok(r.record_id+'/'+op.id+' art dispatched',nodes.some(n=>n.dataset.scene===scene.kind));
  ok(r.record_id+'/'+op.id+' source caption',nodes.some(n=>n.textContent===scene.caption));
  const grids=nodes.filter(n=>n.tag==='dl'&&n.className==='protocol-condition-grid');ok(r.record_id+'/'+op.id+' one authoritative grid',grids.length===1);
  const visible=grids[0].children.map(row=>({label:row.children[0].textContent,value:row.children[1].textContent}));ok(r.record_id+'/'+op.id+' all exact display rows',JSON.stringify(visible)===JSON.stringify(scene.rows.map(row=>({label:row.label,value:row.value}))));
  ok(r.record_id+'/'+op.id+' enlargement control',nodes.some(n=>n.textContent==='Enlarge operation diagram ↗'));
  ok(r.record_id+'/'+op.id+' wrong-record excluded',buildLian2021Scene(op,{...r,record_id:r.record_id+'-wrong'})===null);
  rows+=scene.rows.length;stages++;
 }
}
ok('all21 Lian operations mounted',stages===21);ok('all122 authoritative display rows',rows===122);
const registry=read(S+'/dist/assets/chemical-registry/registry.json'),bindings=read(S+'/dist/assets/chemical-registry/bindings.json'),entries=new Map(registry.entries.map(e=>[e.id,e]));
const {chemicalEntry,chemicalImage}=await import(pathToFileURL(S+'/dist/chemical-viewer.mjs'));const slots=read(L+'/visuals/molecules/material-slot-map.json').slots;
for(const slot of slots){
 const e=chemicalEntry({entries,bindings},slot.record_id,slot.material_id);ok(slot.record_id+'/'+slot.material_id+' exact entry',e.id===slot.registry_id);
 for(const key of ['name','caption','limitations'])ok(slot.record_id+'/'+slot.material_id+' scoped '+key,JSON.stringify(e[key])===JSON.stringify(slot.viewOverrides[key]));
 ok(slot.record_id+'/'+slot.material_id+' source caption',e.sourceBindingCaption===slot.viewOverrides.caption);
 const img=chemicalImage(e);ok(e.id+' hashed image URI',new URL(img.src).searchParams.get('sha')===e.assetHashes.svgPath);
 for(const link of [...slot.quantity_links,...slot.grade_context_links,...slot.formulation_context_links]){let v=records.find(r=>r.record_id===link.record_id);for(const k of link.json_pointer.slice(1).split('/'))v=v[k];ok(slot.material_id+' exact source quantity '+link.json_pointer,JSON.stringify(v)===JSON.stringify(link.quantity));}
}
for(const r of lian)ok(r.record_id+' unknown slot rejected',chemicalEntry({entries,bindings},r.record_id,'not-a-slot')===undefined);
const bound_files={};for(const f of ['dist/protocol-visuals.mjs','dist/lian2021-protocol.mjs','dist/chemical-viewer.mjs','dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json'])bound_files[S+'/'+f]=crypto.createHash('sha256').update(fs.readFileSync(S+'/'+f)).digest('hex');
const report={status:'passed',scope:'actual Site protocol dispatch and chemicalEntry functions with a minimal DOM; no browser rendering or bulk model science audit',check_count:checks.length,counts:{old_operations_excluded:oldOps,lian_operations:stages,lian_display_rows:rows,material_slots:slots.length},checks,bound_files};fs.writeFileSync(O+'/actual-dispatch-checks.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:'passed',checks:checks.length,counts:report.counts}));
