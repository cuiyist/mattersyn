import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {buildGhosh2012Scene,renderGhosh2012Markup,ghosh2012SceneSelection,createGhosh2012Art,createGhosh2012ConditionGrid} from './ghosh2012-protocol.mjs';
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
  const scene=buildGhosh2012Scene(o,r),binding=bindings.find(b=>b.record_id===r.record_id&&b.operation_id===o.id);
  check(!!scene,'Scene exists');check(scene.kind===r.record_id+'--'+o.id,'Exact ID');
  check(scene.rows.filter(x=>x.kind==='operation_parameter').length===Object.keys(o.parameters).length,'All parameters visible');
  for(const [k,q] of Object.entries(o.parameters)){
   const rr=scene.rows.find(x=>x.pointer===binding.operation_pointer+'/parameters/'+k);
   check(JSON.stringify(rr.quantity)===JSON.stringify(q),'Exact quantity object');check(rr.value.length>0,'Readable value');
   if(q.approximate)check(rr.value.startsWith('≈'),'Approximation retained');
   if(q.maximum!=null&&q.minimum==null&&q.value==null)check(rr.value.startsWith(q.maximum_exclusive?'<':'≤'),'Upper bound retained');
  }
  for(const row of scene.rows.filter(x=>x.kind==='source_context')){
   const index=Number(row.pointer.split('/')[2]);check(JSON.stringify(row.quantity)===JSON.stringify(full.measurements[index].value),'Actual canonical measurement');
  }
  check(buildGhosh2012Scene({...o,id:'unassigned'},r)===null,'Unknown operation rejected');
  check(buildGhosh2012Scene(o,{...r,lineage:{source_group:'other'}})===null,'Foreign paper rejected');
  check(buildGhosh2012Scene(o,{...r,record_id:'wrong-record'})===null,'Wrong context rejected');
  check(scene.artSvg.includes('<title>'),'Accessible title');check(renderGhosh2012Markup(scene).includes(scene.artSvg),'Responsive markup includes art');
  const art=createGhosh2012Art(o,r),grid=createGhosh2012ConditionGrid(o,r);
  check(art.innerHTML===scene.artSvg,'Actual art factory');check(art.dataset.scene===scene.kind,'Actual factory ID');check(grid.children.length===scene.rows.length,'Actual conditions factory');
  for(let i=0;i<scene.rows.length;i++){check(grid.children[i].children[0].textContent===scene.rows[i].label,'Actual condition label');check(grid.children[i].children[1].textContent===scene.rows[i].value,'Actual condition value');}
  fs.writeFileSync(path.join(A,'svg',o.id+'.svg'),scene.svg);
  scenes.push({record_id:r.record_id,operation_id:o.id,...scene});
 }
}
check(JSON.stringify(records)===before,'Deep-frozen input remains unchanged');
check(scenes.length===33,'Exactly 33 operations');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='operation_parameter').length,0)===70,'70 exact operation parameters');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='alternative_schedule_parameter').length,0)===10,'10 exact alternative schedule parameters');
const scene=id=>scenes.find(s=>s.operation_id===id),row=(id,p)=>scene(id).rows.find(r=>r.pointer?.endsWith('/'+p));
check(row('large-feed','initial_growth_time').value.startsWith('≈'),'Initial 10-minute growth remains approximate');
check(row('shell-charge','washed_core_amount').value.startsWith('≈'),'Core amount remains approximate');
check(row('shell-cycles','post_cadmium_anneal').quantity.value===2.5,'Preferred post-Cd 2.5 h');
check(scene('compare-anneals').rows.filter(r=>r.kind==='alternative_schedule_parameter').length===10,'Five independent paired schedules');
check(row('single-analyze','prose_on_time_threshold').value.startsWith('>'),'Strict >99% prose threshold');
check(row('single-acquire','total_measurement_time').value.startsWith('>'),'Greater than one hour');
check(Object.keys(records.find(r=>r.record_id.endsWith('ftir-procedure')).operations[0].parameters).join()==='washing_cycles','Preparation has only wash control');
check(Object.keys(records.find(r=>r.record_id.endsWith('xrd-procedure')).operations[0].parameters).length===0,'No scan controls on deposition');
check(bindings.find(b=>b.operation_id==='shell-withdraw').retained_fraction==='remaining-shell-growth','Remaining growth mixture retained');
check(scene('single-acquire').rows.some(r=>r.value.includes('CCD detector')&&r.value.includes('not a specimen')),'Nitrogen is detector cooling only');
check(scene('core-control-wash').description.includes('Upstream synthesis')&&scene('core-control-wash').rows.some(r=>r.value.includes('does not inherit')),'Seven-nanometer control does not inherit core synthesis');
for(const s of scenes)for(const rr of s.rows.filter(x=>x.kind==='alternative_schedule_parameter')){
 const r=records.find(x=>x.record_id===s.record_id),parts=rr.pointer.split('/'),q=r.condition_options[+parts[2]].parameters[parts[4]];
 check(JSON.stringify(rr.quantity)===JSON.stringify(q),'Exact alternative canonical quantity');
}
save('rendered-scenes.json',scenes);
const html=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ghosh 2012 · Apparatus review</title><style>body{font-family:Arial,sans-serif;background:#e8f0f6;color:#173a50;margin:0}main{max-width:1120px;margin:auto;padding:22px}article{padding:22px;background:#fff;border-radius:15px;margin:20px 0}h1{font-size:27px}h2{font-size:22px}select{font:inherit;padding:12px;max-width:100%}p{line-height:1.6}.meta{font-size:13px;color:#60788a}@media(max-width:450px){main{padding:10px}article{padding:14px}}</style></head><body><main><h1>Ghosh et al. 2012</h1><p>Private apparatus author proposal. All 33 canonical operations; independent source/visual audit and public integration remain separate.</p><select id="choose" aria-label="Select experimental operation">${scenes.map((s,i)=>`<option value="${i}">${i+1}. ${s.title}</option>`).join('')}</select><article id="scene"></article></main><script type="module">import {buildGhosh2012Scene,renderGhosh2012Markup} from './ghosh2012-protocol.mjs';const records=await(await fetch('./records.json')).json();const pairs=records.flatMap(r=>r.operations.map(o=>({r,o})));const choose=document.querySelector('#choose'),host=document.querySelector('#scene');function show(){const {r,o}=pairs[+choose.value],s=buildGhosh2012Scene(o,r);host.innerHTML='<h2>'+s.title+'</h2><p class="meta">'+r.record_id+' · '+o.id+'</p>'+renderGhosh2012Markup(s);}choose.addEventListener('change',show);show();</script></body></html>`;
fs.writeFileSync(path.join(A,'index.html'),html);
save('author-validation.json',{status:'passed_author_checks_not_independent_approval',author:'/root/norberg2004_extract',checks,operation_records:records.length,operations:scenes.length,canonical_parameters:70,alternative_schedule_parameters:10,total_display_rows:scenes.reduce((n,s)=>n+s.rows.length,0),tests:['Deep-frozen actual canonical objects executed without mutation','Exact operation and additional measurement pointers','Approximate and upper-bound quantities preserved','Foreign source, wrong record and unknown operation rejected','Actual art/condition factories executed using minimal DOM; not a browser test','Every displayed row in condition factory checked','Stock/aliquot, retained fractions, separate alternatives, strict threshold and CCD-only nitrogen checks'],mounted_browser_test:false,scientific_independent_audit:false});
console.log(JSON.stringify({checks,scenes:scenes.length,rows:scenes.reduce((n,s)=>n+s.rows.length,0)}));
