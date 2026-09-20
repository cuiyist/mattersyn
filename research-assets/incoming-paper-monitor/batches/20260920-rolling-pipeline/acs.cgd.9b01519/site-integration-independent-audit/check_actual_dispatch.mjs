import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
const A=path.dirname(fileURLToPath(import.meta.url)),G=path.dirname(A),S='[local path redacted]';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const checks=[];const check=(ok,label)=>{checks.push({passed:!!ok,check:label});if(!ok)throw Error(label);};
class El{
 constructor(tag){this.tag=tag;this.children=[];this.style={};this.dataset={};this.attributes={};this.events={};this.svg={style:{}};this.className='';this.classList={add:()=>{},toggle:()=>{}};}
 append(...x){this.children.push(...x);} replaceChildren(...x){this.children=[...x];}setAttribute(k,v){this.attributes[k]=v;}addEventListener(k,f){this.events[k]=f;}querySelector(s){if(s==='svg')return this.svg;throw Error('unexpected query '+s);}
}
globalThis.document={createElement:t=>new El(t)};
const actual=await import(pathToFileURL(path.join(S,'dist/sommer2020-protocol.mjs')));
const original=await import(pathToFileURL(path.join(G,'visuals/apparatus/sommer2020-protocol.mjs')));
const protocol=await import(pathToFileURL(path.join(S,'dist/protocol-visuals.mjs')));
const chemicals=await import(pathToFileURL(path.join(S,'dist/chemical-viewer.mjs')));
const records=fs.readdirSync(path.join(S,'data/records')).filter(x=>x.endsWith('.json')).map(x=>read(path.join(S,'data/records',x)));
const entries=read(path.join(S,'dist/assets/chemical-registry/registry.json')),bindings=read(path.join(S,'dist/assets/chemical-registry/bindings.json'));
const data={entries:new Map(entries.entries.map(e=>[e.id,e])),bindings};
let stages=0,rows=0,parameters=0,alternatives=0,slots=0,foreign=0;
for(const r of records){
 if(r.lineage.source_group!=='sommer2020'){
  for(const o of r.operations){check(actual.buildSommer2020Scene(o,r)===null,'foreign record excluded '+r.record_id+' '+o.id);foreign++;}continue;
 }
 const before=JSON.stringify(r);const host=new El('section');protocol.mountProtocol(host,r);
 if(r.operations.length)check(host.children[0].children.length===r.operations.length,'actual stage button count '+r.record_id);
 for(let i=0;i<r.operations.length;i++){
  const o=r.operations[i],scene=actual.buildSommer2020Scene(o,r),expected=original.buildSommer2020Scene(o,r);
  check(JSON.stringify(scene)===JSON.stringify(expected),'exact audited scene '+r.record_id+' '+o.id);
  host.children[0].children[i].events.click();const stage=host.children[1];const visual=stage.children[0],copy=stage.children[1];
  check(visual.children[0].dataset.scene===scene.kind,'actual dispatcher art '+o.id);check(visual.children[0].innerHTML===scene.artSvg,'actual dispatcher SVG '+o.id);
  check(visual.children[1].textContent===scene.caption,'actual source caption '+o.id);
  const grids=copy.children.filter(x=>x.tag==='dl'&&x.className==='protocol-condition-grid');
  check(grids.length===1,'one condition grid no generic duplicate '+o.id);check(grids[0].children.length===scene.rows.length,'all actual condition rows '+o.id);
  for(let j=0;j<scene.rows.length;j++){
   check(grids[0].children[j].children[0].textContent===scene.rows[j].label,'condition label '+o.id+'/'+j);
   check(grids[0].children[j].children[1].textContent===scene.rows[j].value,'condition value '+o.id+'/'+j);
  }
  check(actual.buildSommer2020Scene({...o,id:'unknown'},r)===null,'unknown op excluded '+o.id);
  check(actual.buildSommer2020Scene(o,{...r,record_id:'wrong'})===null,'wrong record excluded '+o.id);
  stages++;rows+=scene.rows.length;parameters+=scene.rows.filter(x=>x.kind==='operation_parameter').length;alternatives+=scene.rows.filter(x=>x.kind==='alternative_schedule_group').reduce((n,x)=>n+x.quantities.length,0);
 }
 for(const m of r.materials){
  const entry=chemicals.chemicalEntry(data,r.record_id,m.id),eid=bindings.recordBindings[r.record_id][m.id],base=entries.entries.find(x=>x.id===eid),note=bindings.bindingNotes[r.record_id][m.id];
  check(entry?.id===eid,'actual material viewer resolves '+r.record_id+'/'+m.id);
  for(const k of ['model2dPath','model3dPath','assetHashes','formula','functionalGroups'])check(JSON.stringify(entry[k])===JSON.stringify(base[k]),'no structural override '+m.id+'/'+k);
  check(entry.sourceBindingCaption===note.viewOverrides.caption,'source caption applied '+r.record_id+'/'+m.id);slots++;
 }
 check(JSON.stringify(r)===before,'canonical input not mutated '+r.record_id);
}
check(stages===31,'31 actual stages');check(rows===168,'168 exact rows');check(parameters===50,'50 parameters');check(slots===62,'62 actual material bindings');check(alternatives===155,'155 exact grouped schedule quantities');
const bound={};for(const rel of ['dist/sommer2020-protocol.mjs','dist/protocol-visuals.mjs','dist/chemical-viewer.mjs','dist/quantity-value.mjs','dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json'])bound[path.join(S,rel)]=sha(path.join(S,rel));bound[fileURLToPath(import.meta.url)]=sha(fileURLToPath(import.meta.url));
const out={status:'passed',scope:'Actual installed modules with a minimal DOM harness; not a browser visual audit.',check_count:checks.length,counts:{stages,rows,parameters,alternatives,slots,foreign_operations_excluded:foreign},checks,bound_files:bound};fs.writeFileSync(path.join(A,'actual-dispatch-checks.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify({status:out.status,check_count:checks.length,counts:out.counts}));
