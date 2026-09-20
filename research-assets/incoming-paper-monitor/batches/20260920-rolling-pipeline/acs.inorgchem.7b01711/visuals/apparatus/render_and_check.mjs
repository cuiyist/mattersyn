import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {buildMorrison2017Scene,renderMorrison2017Markup,morrison2017SceneSelection,createMorrison2017Art,createMorrison2017ConditionGrid} from './morrison2017-protocol.mjs';
const A=path.dirname(fileURLToPath(import.meta.url));
const read=n=>JSON.parse(fs.readFileSync(path.join(A,n),'utf8'));
const save=(n,v)=>fs.writeFileSync(path.join(A,n),JSON.stringify(v,null,2)+'\n');
const records=read('records.json'),bindings=read('canonical-bindings.json').bindings,cfg=read('scene-config.json');
let checks=0;const check=(c,m)=>{assert.ok(c,m);checks++;};const scenes=[];
function deepFreeze(x){if(x&&typeof x==='object'){Object.freeze(x);for(const v of Object.values(x))deepFreeze(v);}return x;}
const before=JSON.stringify(records);deepFreeze(records);
class El{constructor(tag){this.tag=tag;this.children=[];this.style={};this.dataset={};this.svg={style:{}};}append(...x){this.children.push(...x);}querySelector(q){assert.equal(q,'svg');return this.svg;}}
globalThis.document={createElement:t=>new El(t)};
fs.mkdirSync(path.join(A,'svg'),{recursive:true});
for(const r of records){
 const full=JSON.parse(fs.readFileSync(bindings.find(b=>b.record_id===r.record_id).record_path,'utf8'));
 check(JSON.stringify(r.operations)===JSON.stringify(full.operations),'Canonical operations unchanged');
 check(JSON.stringify(r.materials)===JSON.stringify(full.materials),'Canonical materials unchanged');
 check(JSON.stringify(r.material_states)===JSON.stringify(full.material_states),'States unchanged');
 for(const o of r.operations){
  const scene=buildMorrison2017Scene(o,r),binding=bindings.find(b=>b.record_id===r.record_id&&b.operation_id===o.id);
  check(!!scene,'Scene exists');check(scene.kind===r.record_id+'--'+o.id,'Exact ID');
  check(scene.rows.filter(x=>x.kind==='operation_parameter').length===Object.keys(o.parameters).length,'All parameters visible');
  for(const [k,q] of Object.entries(o.parameters)){
   const rr=scene.rows.find(x=>x.pointer===binding.operation_pointer+'/parameters/'+k);
   check(JSON.stringify(rr.quantity)===JSON.stringify(q),'Exact quantity object');check(rr.value.length>0,'Readable value');
   if(q.approximate)check(rr.value.startsWith('≈'),'Approximation retained');
   if(q.maximum!=null&&q.minimum==null&&q.value==null)check(rr.value.startsWith(q.maximum_exclusive?'<':'≤'),'Upper bound retained');
  }
  for(const row of scene.rows.filter(x=>x.kind==='reported_observation_or_acquisition')){
   const index=Number(row.pointer.split('/')[2]);check(JSON.stringify(row.quantity)===JSON.stringify(full.measurements[index].value),'Actual canonical measurement');
  }
  check(buildMorrison2017Scene({...o,id:'unassigned'},r)===null,'Unknown operation rejected');
  check(buildMorrison2017Scene(o,{...r,lineage:{source_group:'other'}})===null,'Foreign paper rejected');
  check(buildMorrison2017Scene(o,{...r,record_id:'wrong-record'})===null,'Wrong context rejected');
  check(scene.artSvg.includes('<title>'),'Accessible title');check(renderMorrison2017Markup(scene).includes(scene.artSvg),'Responsive markup includes art');
  const art=createMorrison2017Art(o,r),grid=createMorrison2017ConditionGrid(o,r);
  check(art.innerHTML===scene.artSvg,'Actual art factory');check(art.dataset.scene===scene.kind,'Actual factory ID');check(grid.children.length===scene.rows.length,'Actual conditions factory');
  for(let i=0;i<scene.rows.length;i++){check(grid.children[i].children[0].textContent===scene.rows[i].label,'Actual condition label');check(grid.children[i].children[1].textContent===scene.rows[i].value,'Actual condition value');}
  fs.writeFileSync(path.join(A,'svg',o.id+'.svg'),scene.svg);
  scenes.push({record_id:r.record_id,operation_id:o.id,...scene});
 }
}
check(JSON.stringify(records)===before,'Deep-frozen input remains unchanged');
check(scenes.length===24,'Exactly 24 operations');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='operation_parameter').length,0)===62,'62 canonical parameters');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='reported_observation_or_acquisition').length,0)===8,'8 additional acquisition/observation quantities');
check(scenes.find(s=>s.operation_id==='hot-growth').rows.find(x=>x.label==='Orange observed by').value==='≤15 min','15 min not exact');
check(scenes.find(s=>s.operation_id==='nmr-heat').rows.find(x=>x.label==='Main-text thiourea observation').value==='2 h','2 h not onset bound');
check(scenes.find(s=>s.operation_id==='crystal-mount-measure').rows.find(x=>x.label==='Table 1 acquisition temperature').value==='100(2) K','Cryogenic acquisition and uncertainty');
check(scenes.find(s=>s.operation_id==='rt-combine').rows.find(x=>x.kind==='operation_parameter').value==='≈ 40 mM','Approximate saturated concentration');
check(cfg.configs['qb-tem'].prose.includes('shell-growth family'),'Independent TEM branch');
check(bindings.find(x=>x.operation_id==='qb-tem').inputs.includes('monolayer-shell-family'),'Actual TEM lineage');
save('rendered-scenes.json',scenes);
const html=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Morrison 2017 · Apparatus review</title><style>body{font-family:Arial,sans-serif;background:#e8f0f6;color:#173a50;margin:0}main{max-width:1120px;margin:auto;padding:22px}article{padding:22px;background:#fff;border-radius:15px;margin:20px 0}h1{font-size:27px}h2{font-size:22px}select{font:inherit;padding:12px;max-width:100%}p{line-height:1.6}.meta{font-size:13px;color:#60788a}@media(max-width:450px){main{padding:10px}article{padding:14px}}</style></head><body><main><h1>Morrison et al. 2017</h1><p>Private apparatus author proposal. All 24 canonical operations; independent source/visual audit and public integration remain separate.</p><select id="choose" aria-label="Select experimental operation">${scenes.map((s,i)=>`<option value="${i}">${i+1}. ${s.title}</option>`).join('')}</select><article id="scene"></article></main><script type="module">import {buildMorrison2017Scene,renderMorrison2017Markup} from './morrison2017-protocol.mjs';const records=await(await fetch('./records.json')).json();const pairs=records.flatMap(r=>r.operations.map(o=>({r,o})));const choose=document.querySelector('#choose'),host=document.querySelector('#scene');function show(){const {r,o}=pairs[+choose.value],s=buildMorrison2017Scene(o,r);host.innerHTML='<h2>'+s.title+'</h2><p class="meta">'+r.record_id+' · '+o.id+'</p>'+renderMorrison2017Markup(s);}choose.addEventListener('change',show);show();</script></body></html>`;
fs.writeFileSync(path.join(A,'index.html'),html);
save('author-validation.json',{status:'passed_author_checks_not_independent_approval',author:'/root/norberg2004_extract',checks,operation_records:records.length,operations:scenes.length,canonical_parameters:62,additional_observation_acquisition_rows:8,total_display_rows:scenes.reduce((n,s)=>n+s.rows.length,0),tests:['Deep-frozen actual canonical objects executed without mutation','Exact operation and additional measurement pointers','Approximate and upper-bound quantities preserved','Foreign source, wrong record and unknown operation rejected','Actual art/condition factories executed using minimal DOM; not a browser test','Every displayed row in condition factory checked','Explicit TEM branch, 2 h observation and 100(2) K acquisition checks'],mounted_browser_test:false,scientific_independent_audit:false});
console.log(JSON.stringify({checks,scenes:scenes.length,rows:scenes.reduce((n,s)=>n+s.rows.length,0)}));
