import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const O=path.dirname(fileURLToPath(import.meta.url)), A=path.join(O,'../apparatus'), P=path.join(A,'../..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const api=await import(pathToFileURL(path.join(A,'matuhina2023-protocol.mjs')));
const manifest=read(path.join(P,'canonical-proposal/v1/record-manifest.json'));
const full=manifest.records.map(x=>read(x.path));
const bindings=read(path.join(A,'canonical-bindings.json')).bindings;
const published=read(path.join(A,'rendered-scenes.json'));
const configs=read(path.join(A,'scene-config.json')).configs;
let checks=0; const check=(b,m)=>{assert.ok(b,m);checks++};
const eq=(a,b,m)=>{assert.deepEqual(a,b,m);checks++};
function freeze(x){if(x&&typeof x==='object'){Object.freeze(x);Object.values(x).forEach(freeze)}return x;}
function pointer(o,p){return p.split('/').slice(1).reduce((v,k)=>v[k.replaceAll('~1','/').replaceAll('~0','~')],o)}
class El {constructor(t){this.tag=t;this.children=[];this.style={};this.dataset={};this.svg={style:{}}}append(...v){this.children.push(...v)}querySelector(s){assert.equal(s,'svg');return this.svg}}
globalThis.document={createElement:t=>new El(t)};
const before=JSON.stringify(full);freeze(full);const all=[];
for(const r of full){
 for(const op of r.operations){
  const s=api.buildMatuhina2023Scene(op,r);check(!!s,op.id+' mapped');
  const b=bindings.find(x=>x.record_id===r.record_id&&x.operation_id===op.id);check(!!b,op.id+' binding');
  eq(pointer(r,b.operation_pointer),op,'Exact operation pointer');
  for(const k of ['inputs','outputs','retained_fraction'])eq(b[k]??null,op[k]??null,'Binding '+k);
  eq(b.canonical_description,op.description,'Canonical description');
  eq(s.kind,r.record_id+'--'+op.id,'Record scoped scene');eq(s.description,b.human_prose,'Human prose binding');
  eq(s,published.find(x=>x.record_id===r.record_id&&x.operation_id===op.id)&&Object.fromEntries(Object.entries(published.find(x=>x.record_id===r.record_id&&x.operation_id===op.id)).filter(([k])=>!['record_id','operation_id'].includes(k))),'Frozen render equals executed module');
  eq(s.svg,fs.readFileSync(path.join(A,'svg',op.id+'.svg'),'utf8'),'Exact SVG replay');
  const qrows=s.rows.filter(x=>x.kind==='operation_parameter');eq(qrows.length,Object.keys(op.parameters).length,'All operation quantities');
  for(const qrow of qrows){eq(qrow.quantity,pointer(r,qrow.pointer),'Unchanged canonical quantity');check(qrow.value.length>0,'Nonempty display');if(qrow.quantity.approximate)check(qrow.value.startsWith('≈ '),'Approximation visible');}
  const groups=s.rows.filter(x=>x.kind==='alternative_schedule_group');eq(groups.map(x=>x.pointer),b.option_pointers,'Exact grouped options');
  for(const group of groups){const option=pointer(r,group.pointer);eq(group.label,option.label,'Sample option label');eq(group.quantities.length,Object.keys(option.parameters).length,'Complete option quantities');for(const q of group.quantities)eq(q.quantity,pointer(r,q.pointer),'Exact option quantity');}
  eq(s.rows.filter(x=>x.kind==='source_scope_note').map(({kind,...v})=>v),configs[op.id].notes,'Notes replay');
  const art=api.createMatuhina2023Art(op,r),grid=api.createMatuhina2023ConditionGrid(op,r);
  eq(art.dataset.scene,s.kind,'Art factory dispatch');eq(art.innerHTML,s.artSvg,'Art factory exact SVG');eq(grid.children.length,s.rows.length,'Condition count');
  s.rows.forEach((row,i)=>{eq(grid.children[i].children[0].textContent,row.label,'Visible label');eq(grid.children[i].children[1].textContent,row.value,'Visible value')});
  check(api.renderMatuhina2023Markup(s).includes(s.artSvg),'Responsive markup retains art');
  eq(api.buildMatuhina2023Scene({...op,id:'unknown'},r),null,'Unknown operation excluded');
  eq(api.buildMatuhina2023Scene(op,{...r,lineage:{source_group:'other'}}),null,'Foreign source excluded');
  for(const other of full.filter(x=>x.record_id!==r.record_id))eq(api.buildMatuhina2023Scene(op,other),null,'Other record excluded');
  all.push({record_id:r.record_id,operation_id:op.id,...s});
 }
}
eq(JSON.stringify(full),before,'Inputs not mutated');eq(all.length,39,'All 39 operations');
eq(new Set(all.map(x=>x.record_id)).size,14,'14 source contexts');
const count=k=>all.reduce((n,s)=>n+s.rows.filter(x=>x.kind===k).length,0);
eq(count('operation_parameter'),67,'67 operation quantities');
eq(all.reduce((n,s)=>n+s.rows.length,0),168,'168 display rows');
const scene=id=>all.find(s=>s.operation_id===id), param=(id,k)=>scene(id).rows.find(x=>x.pointer?.endsWith('/'+k));
eq(param('cs-reactivate','pre_injection_degassing_duration').value,'≥30 min','Explicit lower bound');
eq(param('nc-grow-quench','hold_after_injection').value,'5 s','Five second hold');
eq(param('tem-deposit','absorbance_at_280_nm').value,'0.2 dimensionless','TEM dilution absorbance');
for(const id of ['nc-inject','nc-grow-quench']){
 const options=scene(id).rows.filter(x=>x.kind==='alternative_schedule_group');eq(options.length,5,'Five source alternatives, not Cartesian combinations');
 const values=options.map(g=>Object.fromEntries(g.quantities.map(q=>[q.pointer.split('/').at(-1),q.quantity.value])));
 eq(values.map(q=>[q.injection_temperature,q.reported_loading_Mn_Cs,q.cs_oleate_aliquot]),[[150,.7,2],[180,.7,2],[180,.5,3],[180,.35,4],[200,.7,2]],'Exact source paired preparations');
}
check(scene('hexane-spin').description.includes('No visible precipitation'),'Failed precipitation retained');
check(scene('ipa-or-etoac').rows.some(x=>x.value.includes('IPA OR ethyl acetate')),'Alternative trials');
check(scene('nc-grow-quench').rows.some(x=>x.value.includes('external coolant')),'Bath not ingredient');
check(scene('ta-acquire').rows.some(x=>x.label==='Figure S6'&&x.value.includes('180@NCs//0.7 only')),'S6 sample scope');
check(scene('ta-acquire').rows.some(x=>x.value.includes('not the NC-dispersion solvent')),'Heavy water continuum boundary');
check(scene('icp-dissolve').description.includes('nitric acid'),'Destructive digest');
check(scene('ltpl-deposit').description.includes('180@NCs//0.5'),'LTPL sample identity');
check(scene('age-specimens').rows.some(x=>x.value.includes('different contexts')),'Films distinct from dispersions');
check(scene('lsc-age-remeasure').rows.some(x=>x.value.includes('same film')),'Same device film only when explicit');
const output={schema:'mattersyn-independent-apparatus-runtime-checks/1',reviewer:'/root/peng1998_reader_assets',status:'passed',checks,scenes:all.length,records:14,operation_quantities:67,option_quantity_appearances:30,display_rows:168,actual_module_executed:true,minimal_dom_factories_executed:true,browser_test:false,tests:['Full canonical objects read independently from record manifest','Complete source/record/operation exclusion matrix','Exact rows, option groups, quantity objects and SVG replay','Paired source schedules and lower-bound/approximation display','Actual factories with minimal DOM','Source-specific fraction, TA, ICP, LTPL, aging and device boundaries']};
fs.writeFileSync(path.join(O,'runtime-checks.json'),JSON.stringify(output,null,2)+'\n');console.log(JSON.stringify(output));
