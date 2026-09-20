import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const O=path.dirname(fileURLToPath(import.meta.url)),A=path.join(O,'../apparatus'),P=path.join(A,'../..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const api=await import(pathToFileURL(path.join(A,'pati2009-protocol.mjs')));
const manifest=read(path.join(P,'canonical-proposal/v1/record-manifest.json'));
const records=manifest.records.map(x=>read(x.path));
const bindings=read(path.join(A,'canonical-bindings.json')).bindings;
const published=read(path.join(A,'rendered-scenes.json'));
const configs=read(path.join(A,'scene-config.json')).configs;
let checks=0;const check=(v,m)=>{assert.ok(v,m);checks++},eq=(a,b,m)=>{assert.deepEqual(a,b,m);checks++};
const pointer=(o,p)=>p.split('/').slice(1).reduce((v,k)=>v[k.replaceAll('~1','/').replaceAll('~0','~')],o);
function freeze(o){if(o&&typeof o==='object'){Object.freeze(o);Object.values(o).forEach(freeze)}return o}
class El{constructor(t){this.tag=t;this.children=[];this.dataset={};this.style={};this.svg={style:{}}}append(...v){this.children.push(...v)}querySelector(s){assert.equal(s,'svg');return this.svg}}
globalThis.document={createElement:t=>new El(t)};
const before=JSON.stringify(records);freeze(records);const scenes=[];
for(const r of records){
 eq(api.pati2009SceneSelection.records[r.record_id]??[],r.operations.map(o=>o.id),'Exact per-record selection');
 for(const op of r.operations){
  const s=api.buildPati2009Scene(op,r),key=r.record_id+'--'+op.id;
  check(!!s,'Mapped operation '+key);eq(s.kind,key,'Scene ID');
  const b=bindings.find(x=>x.scene_id===key);check(!!b,'Binding exists');eq(pointer(r,b.operation_pointer),op,'Exact operation pointer');
  for(const k of ['inputs','outputs','retained_fraction'])eq(b[k]??null,op[k]??null,'Canonical '+k);
  eq(b.canonical_description,op.description,'Canonical description preserved');eq(s.description,b.human_prose,'Readable bound prose');
  const prior=published.find(x=>x.record_id===r.record_id&&x.operation_id===op.id);check(!!prior,'Saved execution');
  eq(s,Object.fromEntries(Object.entries(prior).filter(([k])=>!['record_id','operation_id'].includes(k))),'Exact execution replay');
  eq(s.svg,fs.readFileSync(path.join(A,'svg',key+'.svg'),'utf8'),'Exact original SVG');
  const qs=s.rows.filter(x=>x.kind==='operation_parameter');eq(qs.length,Object.keys(op.parameters).length,'No dropped/extra parameter');
  eq(qs.map(q=>q.pointer),Object.keys(op.parameters).map(k=>b.operation_pointer+'/parameters/'+k),'Exact parameter ordering/pointers');
  for(const q of qs){eq(q.quantity,pointer(r,q.pointer),'Unmodified quantity');check(q.value.length>0,'Display exists');if(q.quantity.approximate)check(q.value.startsWith('≈'),'Approximation display');}
  eq(s.rows.filter(x=>x.kind==='source_scope_note').map(({kind,...v})=>v),configs[key].notes,'Exact scope notes');
  eq(b.option_pointers,[],'No fabricated schedules');
  const art=api.createPati2009Art(op,r),grid=api.createPati2009ConditionGrid(op,r);
  eq(art.dataset.scene,key,'Actual art dispatch');eq(art.innerHTML,s.artSvg,'Art SVG exact');eq(grid.children.length,s.rows.length,'Actual condition count');
  for(let i=0;i<s.rows.length;i++){eq(grid.children[i].children[0].textContent,s.rows[i].label,'Label delivered');eq(grid.children[i].children[1].textContent,s.rows[i].value,'Value delivered')}
  const html=api.renderPati2009Markup(s);check(html.includes(s.artSvg),'Responsive markup art');check(!html.includes('undefined')&&!html.includes('NaN'),'Valid display');
  eq(api.buildPati2009Scene({...op,id:'stale-extra-operation'},r),null,'Unknown extra operation rejected');
  eq(api.buildPati2009Scene(op,{...r,record_id:'pati-2009-nonexistent'}),null,'Unknown record rejected');
  for(const source of [undefined,null,'matuhina2023','pati2009-old'])eq(api.buildPati2009Scene(op,{...r,lineage:{source_group:source}}),null,'Wrong source rejected');
  for(const other of records.filter(x=>!x.operations.some(o=>o.id===op.id)))eq(api.buildPati2009Scene(op,other),null,'Nonmember record/operation rejected');
  scenes.push({record_id:r.record_id,operation_id:op.id,...s});
 }
}
eq(JSON.stringify(records),before,'Readonly canonical inputs');eq(scenes.length,35,'35 scenes');eq(new Set(scenes.map(s=>s.record_id)).size,14,'14 operation records');
eq(new Set(scenes.map(s=>s.operation_id)).size,19,'19 distinct source operations');eq(scenes.reduce((n,s)=>n+s.rows.length,0),167,'167 display rows');eq(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='operation_parameter').length,0),43,'43 canonical numeric rows');
const scene=id=>scenes.find(s=>s.operation_id===id),text=id=>JSON.stringify(scene(id)),row=(id,k)=>scene(id).rows.find(x=>x.pointer?.endsWith('/'+k));
eq(row('drip','addition_rate').value,'3–4 mL/min','Source interval');eq(row('poststir','post_precipitation_stirring_duration').value,'1 h','Post precipitation hold');eq(row('ambient-dry','ambient_drying_duration').value,'24 h','Ambient drying');eq(row('diagnostic','filtrate_aliquot').value,'10 mL','Diagnostic volume');
eq(row('calcine','calcination_temperature').value,'200 °C','Calcination temperature');
check(scene('calcine').rows.some(x=>x.label==='Atmosphere'&&x.value.includes('Unreported')),'Calcination atmosphere unknown');check(scene('tga-acquire').description.includes('in air'),'TGA air');
check(text('diagnostic').includes('not returned'),'Diagnostic branch retained separately');check(text('xps-acquire').includes('<15 min')&&text('xps-acquire').includes('>5 h'),'Exposure context bounds');
check(text('xps-fit-analyze').includes('884.5')&&text('xps-fit-analyze').includes('884.8'),'Calibration conflict');
for(const r of records.filter(r=>r.record_id.endsWith('-route'))){
 const s=scenes.filter(s=>s.record_id===r.record_id);eq(s.length,8,'Eight preparation steps');
 const label={'ethanol':'Anhydrous ethanol','propanol':'1-Propanol','butanol':'1-Butanol'}[r.record_id.split('-')[2]];
 for(const x of s){check(x.title.startsWith(label),'Correct solvent title');check(x.rows.some(row=>row.label==='Selected solvent'&&row.value.startsWith(label)),'Solvent note');}
 const drip=s.find(x=>x.operation_id==='drip');eq(drip.rows.filter(x=>x.quantity?.unit==='mL').map(x=>x.quantity.value),[100,100],'Paired stock transfers');
}
const result={schema:'mattersyn-independent-apparatus-runtime-checks/1',reviewer:'/root/peng1998_reader_assets',status:'passed',checks,scenes:35,operation_records:14,source_operations:19,canonical_numeric_rows:43,display_rows:167,actual_module_executed:true,minimal_dom_factories_executed:true,mounted_browser_test:false,input_mutation:false,selection_contract:'Exact source-group, record-ID and operation-ID dispatch; all nonmember combinations and unknown extra IDs rejected. Does not attest that runtime IDs alone validate modified same-ID operation contents; immutable canonical transport is verified separately.'};
fs.writeFileSync(path.join(O,'runtime-checks.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
