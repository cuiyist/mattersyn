// Independent replay; writes only this audit directory, never author previews.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const A=path.dirname(fileURLToPath(import.meta.url)),V=path.resolve(A,'../apparatus'),R=path.resolve(A,'../..');
const mod=await import(pathToFileURL(path.join(V,'sommer2020-protocol.mjs')).href);
const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const records=load(path.join(V,'records.json')),saved=load(path.join(V,'rendered-scenes.json')),config=load(path.join(V,'scene-config.json'));
let checks=0;const categories={};const ck=(ok,cat)=>{checks++;categories[cat]=(categories[cat]||0)+1;assert.ok(ok,cat);};
const identical=(a,b)=>{assert.deepEqual(a,b);checks++;categories.exact_object=(categories.exact_object||0)+1;};
const at=(o,p)=>p.split('/').slice(1).reduce((a,k)=>a[k],o);
const freeze=o=>{if(o&&typeof o==='object'){Object.freeze(o);Object.values(o).forEach(freeze);}return o;};
class Element{constructor(t){this.tag=t;this.children=[];this.style={};this.dataset={};this.svg={style:{}};}append(...v){this.children.push(...v);}querySelector(s){assert.equal(s,'svg');return this.svg;}}
globalThis.document={createElement:t=>new Element(t)};
const hashes={},used=new Set(),typed=[],summary=[],before=JSON.stringify(records);freeze(records);
for(const r of records){
 const p=path.join(R,'canonical-proposal/v2',r.record_id+'.json');hashes[p]=sha(p);identical(r,load(p));
 for(const [index,o] of r.operations.entries()){
  const cfg=config.configs[o.id],s=mod.buildSommer2020Scene(o,r);ck(!!s,'scene_exists');used.add(o.id);
  identical({record_id:r.record_id,operation_id:o.id,...s},saved.find(x=>x.operation_id===o.id));
  ck(s.svg===fs.readFileSync(path.join(V,'svg',o.id+'.svg'),'utf8'),'saved_svg_exact_replay');
  ck(cfg.operation_pointer===`/operations/${index}`&&cfg.record_id===r.record_id,'exact_record_operation_dispatch');
  identical(s.rows.filter(x=>x.kind==='operation_parameter').map(x=>x.pointer).sort(),Object.keys(o.parameters).map(k=>`/operations/${index}/parameters/${k}`).sort());
  for(const row of s.rows){
   if(row.kind==='operation_parameter'){
    identical(row.quantity,at(r,row.pointer));typed.push({record_id:r.record_id,operation_id:o.id,pointer:row.pointer,value:row.value,quantity:row.quantity});
   }else if(row.kind==='alternative_schedule_group'){
    const opt=at(r,row.pointer);ck(cfg.option_pointers.includes(row.pointer),'selected_option_pointer');identical(row.quantities.map(q=>q.pointer).sort(),Object.keys(opt.parameters).map(k=>row.pointer+'/parameters/'+k).sort());
    for(const q of row.quantities){identical(q.quantity,at(r,q.pointer));typed.push({record_id:r.record_id,operation_id:o.id,...q});}
   }else ck(row.kind==='source_scope_note','only_scoped_note_rows');
  }
  ck(mod.buildSommer2020Scene({...o,id:'foreign'},r)===null,'unknown_operation_rejected');
  ck(mod.buildSommer2020Scene(o,{...r,record_id:'unrelated-record'})===null,'foreign_record_rejected');
  ck(mod.buildSommer2020Scene(o,{...r,lineage:{source_group:'unrelated'}})===null,'foreign_source_rejected');
  const art=mod.createSommer2020Art(o,r),grid=mod.createSommer2020ConditionGrid(o,r);
  ck(art.innerHTML===s.artSvg&&art.dataset.scene===s.kind,'actual_art_factory');ck(grid.children.length===s.rows.length,'actual_condition_count');
  s.rows.forEach((x,i)=>{ck(grid.children[i].children[0].textContent===x.label,'actual_condition_label');ck(grid.children[i].children[1].textContent===x.value,'actual_condition_value');});
  const html=mod.renderSommer2020Markup(s);ck(html.includes(s.artSvg)&&html.includes(s.description),'markup_exact_payload');
  ck(!/undefined|NaN|\[object Object\]/.test(html),'no_broken_render_tokens');
  summary.push({record_id:r.record_id,operation_id:o.id,row_count:s.rows.length});
 }
}
for(const t of typed){const q=t.quantity;
 if(q.approximate)ck(t.value.startsWith('≈'),'approximation_visible');
 if(q.value===null&&q.minimum!=null&&q.maximum==null)ck(t.value.startsWith(q.minimum_exclusive?'>':'≥'),'lower_bound_visible');
 if(q.value===null&&q.maximum!=null&&q.minimum==null)ck(t.value.startsWith(q.maximum_exclusive?'<':'≤'),'upper_bound_visible');
 if(q.value===null&&q.maximum!=null&&q.minimum!=null)ck(t.value.includes(String(q.minimum))&&t.value.includes(String(q.maximum)),'range_endpoints_visible');
 ck(t.value.length>0,'nonempty_quantity');
}
ck(used.size===31&&records.length===12,'31_operations_12_records');identical([...used].sort(),Object.keys(config.configs).sort());
identical(mod.sommer2020SceneSelection.records,Object.fromEntries(records.map(r=>[r.record_id,r.operations.map(o=>o.id)])));
ck(JSON.stringify(records)===before,'no_input_mutation');ck(typed.length===205,'205_typed_values');
ck(saved.reduce((n,s)=>n+s.rows.length,0)===168,'168_display_rows');
for(const p of [path.join(V,'sommer2020-protocol.mjs'),path.join(V,'records.json'),path.join(V,'rendered-scenes.json'),path.join(V,'scene-config.json'),fileURLToPath(import.meta.url)])hashes[p]=sha(p);
fs.writeFileSync(path.join(A,'module-replay-checks.json'),JSON.stringify({status:'passed',reviewer:'/root/norberg2004_extract',author:'/root',checks,categories,scenes:summary,typed_values:typed,bound_files:hashes,limitations:['Minimal DOM factories exercised; no mounted browser approval from this test.','Scientific interpretation is independently recorded in the separate manual source audit.']},null,2)+'\n');
console.log(JSON.stringify({status:'passed',checks,operations:used.size,typed:typed.length}));
