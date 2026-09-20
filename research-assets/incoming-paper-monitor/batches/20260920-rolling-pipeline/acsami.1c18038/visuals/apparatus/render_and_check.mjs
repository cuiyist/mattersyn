import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {buildLian2021Scene,renderLian2021Markup,lian2021SceneSelection,createLian2021Art,createLian2021ConditionGrid} from './lian2021-protocol.mjs';
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
  const scene=buildLian2021Scene(o,r),binding=bindings.find(b=>b.record_id===r.record_id&&b.operation_id===o.id);
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
  check(buildLian2021Scene({...o,id:'unassigned'},r)===null,'Unknown operation rejected');
  check(buildLian2021Scene(o,{...r,lineage:{source_group:'other'}})===null,'Foreign paper rejected');
  check(buildLian2021Scene(o,{...r,record_id:'wrong-record'})===null,'Wrong context rejected');
  check(scene.artSvg.includes('<title>'),'Accessible title');check(renderLian2021Markup(scene).includes(scene.artSvg),'Responsive markup includes art');
  const art=createLian2021Art(o,r),grid=createLian2021ConditionGrid(o,r);
  check(art.innerHTML===scene.artSvg,'Actual art factory');check(art.dataset.scene===scene.kind,'Actual factory ID');check(grid.children.length===scene.rows.length,'Actual conditions factory');
  for(let i=0;i<scene.rows.length;i++){check(grid.children[i].children[0].textContent===scene.rows[i].label,'Actual condition label');check(grid.children[i].children[1].textContent===scene.rows[i].value,'Actual condition value');}
  fs.writeFileSync(path.join(A,'svg',o.id+'.svg'),scene.svg);
  scenes.push({record_id:r.record_id,operation_id:o.id,...scene});
 }
}
check(JSON.stringify(records)===before,'Deep-frozen input remains unchanged');
check(scenes.length===21,'Exactly 21 operations');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='operation_parameter').length,0)===34,'34 operation parameters');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='source_context').length,0)===7,'Five mass ratios plus two k-meshes');
const scene=id=>scenes.find(s=>s.operation_id===id),row=(id,label)=>scene(id).rows.find(r=>r.label===label);
check(row('nc-dissolve-filter','DMF solvent charge').value==='2000 µL','Whole-stock solvent charge');
check(row('nc-inject','Precursor-solution aliquot').value==='500 µL','Only aliquot injected');
check(row('spin-feed','DMF solvent charge').value==='1000 µL','Separate spin-feed stock');
check(row('spin-deposit','Precursor-solution aliquot').value==='200 µL','Separate coating aliquot');
check(row('dft-relax','Force stopping criterion').value==='<0.01 eV/Å','Strict convergence bound');
check(row('dft-relax','Compound A k-point mesh').value==='4x4x4','Compound A mesh');
check(row('dft-relax','Compound B k-point mesh').value==='2x4x4','Compound B mesh');
check(scene('film-cast').description.includes('film is retained'),'Peeled film is product');
check(bindings.find(x=>x.operation_id==='film-cast').retained_fraction==='composite-film','Canonical retained film');
check(scene('bulk-xps-tga').description.includes('Nitrogen is assigned only to TGA'),'N2 scoped to TGA only');
check(scene('nc-plqe').description.includes('dried nanocrystal powder'),'Powder PLQE scope');
check(scene('nc-inject').description.includes('no nanocrystal growth temperature'),'No inherited room temperature');
save('rendered-scenes.json',scenes);
const html=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lian 2021 · Apparatus review</title><style>body{font-family:Arial,sans-serif;background:#e8f0f6;color:#173a50;margin:0}main{max-width:1120px;margin:auto;padding:22px}article{padding:22px;background:#fff;border-radius:15px;margin:20px 0}h1{font-size:27px}h2{font-size:22px}select{font:inherit;padding:12px;max-width:100%}p{line-height:1.6}.meta{font-size:13px;color:#60788a}@media(max-width:450px){main{padding:10px}article{padding:14px}}</style></head><body><main><h1>Lian et al. 2021</h1><p>Private apparatus author proposal. All 21 canonical operations; independent source/visual audit and public integration remain separate.</p><select id="choose" aria-label="Select experimental operation">${scenes.map((s,i)=>`<option value="${i}">${i+1}. ${s.title}</option>`).join('')}</select><article id="scene"></article></main><script type="module">import {buildLian2021Scene,renderLian2021Markup} from './lian2021-protocol.mjs';const records=await(await fetch('./records.json')).json();const pairs=records.flatMap(r=>r.operations.map(o=>({r,o})));const choose=document.querySelector('#choose'),host=document.querySelector('#scene');function show(){const {r,o}=pairs[+choose.value],s=buildLian2021Scene(o,r);host.innerHTML='<h2>'+s.title+'</h2><p class="meta">'+r.record_id+' · '+o.id+'</p>'+renderLian2021Markup(s);}choose.addEventListener('change',show);show();</script></body></html>`;
fs.writeFileSync(path.join(A,'index.html'),html);
save('author-validation.json',{status:'passed_author_checks_not_independent_approval',author:'/root/norberg2004_extract',checks,operation_records:records.length,operations:scenes.length,canonical_parameters:34,additional_source_context_rows:7,total_display_rows:scenes.reduce((n,s)=>n+s.rows.length,0),tests:['Deep-frozen actual canonical objects executed without mutation','Exact operation and additional measurement pointers','Approximate and upper-bound quantities preserved','Foreign source, wrong record and unknown operation rejected','Actual art/condition factories executed using minimal DOM; not a browser test','Every displayed row in condition factory checked','Stock/aliquot, film retention, TGA-only nitrogen, powder PLQE and strict DFT force checks'],mounted_browser_test:false,scientific_independent_audit:false});
console.log(JSON.stringify({checks,scenes:scenes.length,rows:scenes.reduce((n,s)=>n+s.rows.length,0)}));
