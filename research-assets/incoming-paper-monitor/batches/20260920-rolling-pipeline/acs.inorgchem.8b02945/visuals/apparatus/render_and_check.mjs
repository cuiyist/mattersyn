import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {buildFriedfeld2019Scene,renderFriedfeld2019Markup,friedfeld2019SceneSelection,createFriedfeld2019Art,createFriedfeld2019ConditionGrid} from './friedfeld2019-protocol.mjs';
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
  const scene=buildFriedfeld2019Scene(o,r),binding=bindings.find(b=>b.record_id===r.record_id&&b.operation_id===o.id);
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
  check(buildFriedfeld2019Scene({...o,id:'unassigned'},r)===null,'Unknown operation rejected');
  check(buildFriedfeld2019Scene(o,{...r,lineage:{source_group:'other'}})===null,'Foreign paper rejected');
  check(buildFriedfeld2019Scene(o,{...r,record_id:'wrong-record'})===null,'Wrong context rejected');
  check(scene.artSvg.includes('<title>'),'Accessible title');check(renderFriedfeld2019Markup(scene).includes(scene.artSvg),'Responsive markup includes art');
  const art=createFriedfeld2019Art(o,r),grid=createFriedfeld2019ConditionGrid(o,r);
  check(art.innerHTML===scene.artSvg,'Actual art factory');check(art.dataset.scene===scene.kind,'Actual factory ID');check(grid.children.length===scene.rows.length,'Actual conditions factory');
  for(let i=0;i<scene.rows.length;i++){check(grid.children[i].children[0].textContent===scene.rows[i].label,'Actual condition label');check(grid.children[i].children[1].textContent===scene.rows[i].value,'Actual condition value');}
  fs.writeFileSync(path.join(A,'svg',scene.kind+'.svg'),scene.svg);fs.writeFileSync(path.join(A,'svg',scene.kind+'--art.svg'),scene.artSvg);
  scenes.push({record_id:r.record_id,operation_id:o.id,...scene});
 }
}
check(JSON.stringify(records)===before,'Deep-frozen input remains unchanged');
check(scenes.length===58,'Exactly 58 operations');
const expectedParameters=records.reduce((n,r)=>n+r.operations.reduce((a,o)=>a+Object.keys(o.parameters).length,0),0);
const expectedOptions=bindings.reduce((n,b)=>n+b.option_selections.reduce((a,p)=>a+p.keys.length,0),0);
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='operation_parameter').length,0)===expectedParameters,'All operation parameters');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='alternative_schedule_group').reduce((a,g)=>a+g.quantities.length,0),0)===expectedOptions,'All selected source option parameters');
const scene=id=>scenes.find(s=>s.operation_id===id),row=(id,p)=>scene(id).rows.find(r=>r.pointer?.endsWith('/'+p));
check(new Set(scenes.map(s=>s.kind)).size===58,'Unique exact record-operation scenes');
check(new Set(scenes.map(s=>s.operation_id)).size===34,'All 34 source operations');
check(row('dry-flask','oven_temperature').value==='160 °C','Oven temperature');
check(row('dry-flask','drying_duration').value==='overnight','Qualitative duration preserved');
check(row('acid-cold-hold','cold_hold_temperature').value==='-76 °C','Cold bath temperature');
check(row('acid-ambient-hold','ambient_hold_duration').value==='8 h','Ambient duration');
check(row('acid-crystallize','crystallization_temperature').value==='0 °C','Zero temperature preserved');
check(row('acid-extract','ether_extraction_repetitions').value==='3 count','Neutral count unit');
check(row('acid-nmr-analyze','13c_frequency').value==='176 MHz','Nucleus-specific frequency');
check(scene('tga-analyze').rows.some(x=>x.label==='Atmosphere'&&x.value.startsWith('Not reported')),'TGA does not inherit reaction gas');
check(scene('dsc-analyze').rows.some(x=>x.label==='Atmosphere'&&x.value.startsWith('Unreported')),'DSC gas unknown');
check(scene('xrd-analyze').rows.some(x=>x.value.includes('no Cu Kα')),'No invented wavelength');
check(scene('tem-analyze').rows.some(x=>x.value.includes('not relabeled as an SAED')),'Local FFT scope');
check(scene('acid-condense').description.includes('static vacuum'),'Static vacuum reported');
check(scene('acid-quench').description.includes('dropwise'),'Dropwise methanol');
check(scene('distill-solvent').rows.some(x=>x.value.includes('distillate is not')),'Residue retained');
check(scene('transfer-purify').rows.some(x=>x.value.includes('separately reported fractions')),'Separate GPC fractions');
const varied=scenes.find(x=>x.record_id.endsWith('conversion-concentration')&&x.operation_id==='sonicate-msc');
check(varied.rows.find(x=>x.pointer?.endsWith('/condition_specific_msc_mass')).quantity.value===null,'No invented varied mass');
check(!varied.rows.some(x=>x.kind==='operation_parameter'&&x.quantity.value===20),'No representative 20 mg in varied branch');
const counts=new Map();
for(const ss of scenes)for(const g of ss.rows.filter(x=>x.kind==='alternative_schedule_group'))for(const q of g.quantities){const k=ss.record_id+q.pointer;counts.set(k,(counts.get(k)||0)+1);}
for(const r of records)for(const [i,opt]of (r.condition_options||[]).entries())for(const k of Object.keys(opt.parameters))check(counts.get(r.record_id+'/condition_options/'+i+'/parameters/'+k)===1,'Each alternative parameter appears once at relevant stage');
for(const s of scenes)for(const group of s.rows.filter(x=>x.kind==='alternative_schedule_group'))for(const rr of group.quantities){
 const r=records.find(x=>x.record_id===s.record_id),parts=rr.pointer.split('/'),q=r.condition_options[+parts[2]].parameters[parts[4]];
 check(JSON.stringify(rr.quantity)===JSON.stringify(q),'Exact alternative canonical quantity');
}
save('rendered-scenes.json',scenes);
const html=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Friedfeld 2019 · Apparatus review</title><style>body{font-family:Arial,sans-serif;background:#e8f0f6;color:#173a50;margin:0}main{max-width:1120px;margin:auto;padding:22px}article{padding:22px;background:#fff;border-radius:15px;margin:20px 0}h1{font-size:27px}h2{font-size:22px}select{font:inherit;padding:12px;max-width:100%}p{line-height:1.6}.meta{font-size:13px;color:#60788a}@media(max-width:450px){main{padding:10px}article{padding:14px}}</style></head><body><main><h1>Friedfeld et al. 2019</h1><p>Private apparatus author proposal. All 58 canonical operations; independent source/visual audit and public integration remain separate.</p><select id="choose" aria-label="Select experimental operation">${scenes.map((s,i)=>`<option value="${i}">${i+1}. ${s.title}</option>`).join('')}</select><article id="scene"></article></main><script type="module">import {buildFriedfeld2019Scene,renderFriedfeld2019Markup} from './friedfeld2019-protocol.mjs';const records=await(await fetch('./records.json')).json();const pairs=records.flatMap(r=>r.operations.map(o=>({r,o})));const choose=document.querySelector('#choose'),host=document.querySelector('#scene');function show(){const {r,o}=pairs[+choose.value],s=buildFriedfeld2019Scene(o,r);host.innerHTML='<h2>'+s.title+'</h2><p class="meta">'+r.record_id+' · '+o.id+'</p>'+renderFriedfeld2019Markup(s);}choose.addEventListener('change',show);show();</script></body></html>`;
fs.writeFileSync(path.join(A,'index.html'),html);
save('author-validation.json',{status:'passed_author_checks_not_independent_approval',author:'/root/norberg2004_extract',checks,operation_records:records.length,operations:scenes.length,canonical_parameters:expectedParameters,alternative_schedule_parameters:expectedOptions,total_display_rows:scenes.reduce((n,s)=>n+s.rows.length,0),tests:['Deep-frozen actual canonical objects executed without mutation','Exact operation and additional measurement pointers','Approximate and upper-bound quantities preserved','Foreign source, wrong record and unknown operation rejected','Actual art/condition factories executed using minimal DOM; not a browser test','Every displayed row in condition factory checked','Friedfeld source-specific cold holds, external coolant separation, fraction flow, variant mass missingness and analysis context checks'],mounted_browser_test:false,scientific_independent_audit:false});
console.log(JSON.stringify({checks,scenes:scenes.length,rows:scenes.reduce((n,s)=>n+s.rows.length,0)}));
