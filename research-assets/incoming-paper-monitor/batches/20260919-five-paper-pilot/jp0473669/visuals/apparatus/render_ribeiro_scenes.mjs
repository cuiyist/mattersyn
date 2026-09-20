import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
import {buildRibeiro2004Scene,createRibeiro2004Art,ribeiro2004SceneSelection} from './ribeiro2004-protocol.mjs';
const O=path.dirname(fileURLToPath(import.meta.url)),B=path.resolve(O,'../..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const plan=read(path.join(B,'visual-preparation-plan.json')),frozen=read(path.join(B,'canonical-record-manifest.json'));
if(sha(path.join(B,'visual-preparation-plan.json'))!=='b9751dabb6dd97068bce5bea101eee30243ddb2c05b08808d7aad183872c0a74')throw Error('Changed plan');
const checks=[],scenes=[],inputs={};
const ck=(ok,check)=>{checks.push({check,passed:!!ok});if(!ok)throw Error(check);};
fs.mkdirSync(path.join(O,'scene-svg'),{recursive:true});
globalThis.document={createElement:tag=>({tagName:tag,className:'',dataset:{},style:{},innerHTML:''})};
for(const row of frozen.records){
 ck(sha(row.path)===row.sha256&&row.sha256===plan.record_hashes[row.record_id],row.record_id+' frozen canonical');inputs[row.path]=row.sha256;const r=read(row.path);
 ck((ribeiro2004SceneSelection.records[r.record_id]??[]).length===r.operations.length,row.record_id+' complete operation mapping');
 for(const [i,o] of r.operations.entries()){
  const before=JSON.stringify(r),s=buildRibeiro2004Scene(o,r);ck(!!s,row.record_id+'/'+o.id+' scene exists');
  ck(JSON.stringify(r)===before,o.id+' immutable input');ck(!/NaN|undefined/.test(s.svg)&&s.svg.includes('viewBox="0 0 900 650"'),o.id+' finite SVG');
  ck(buildRibeiro2004Scene(o,{...r,lineage:{source_group:'other'}})===null,o.id+' reject other paper');
  ck(buildRibeiro2004Scene(o,{...r,record_id:'ribeiro-2004-growth-model'})===null,o.id+' reject wrong Ribeiro record');
  const dom=createRibeiro2004Art(o,r);ck(dom.dataset.scene===s.kind&&dom.innerHTML===s.svg,o.id+' DOM wrapper compatibility');
  const name='scene-svg/'+s.kind+'.svg';fs.writeFileSync(path.join(O,name),s.svg);
  for(const condition of s.condition_rows.filter(x=>x.pointer)){
   const resolved=condition.pointer.slice(1).split('/').reduce((obj,k)=>obj[Array.isArray(obj)?Number(k):k],r);ck(resolved!==undefined,o.id+' typed pointer '+condition.pointer);
  }
  const ip=plan.operation_scenes.find(x=>x.record_id===row.record_id&&x.operation_id===o.id);ck(ip.json_pointer===`/operations/${i}`&&JSON.stringify(ip.parameters_from_canonical)===JSON.stringify(o.parameters),o.id+' plan/operation agreement');
  scenes.push({record_id:r.record_id,operation_id:o.id,operation_pointer:`/operations/${i}`,stage:o.stage,scene_kind:s.kind,svg_file:name,svg_sha256:sha(path.join(O,name)),record_sha256:row.sha256,inputs:o.inputs,outputs:o.outputs,depends_on:o.depends_on,parameters:o.parameters,environment:o.environment,endpoint:o.endpoint,retained_fraction:o.retained_fraction,source_evidence:o.evidence,condition_rows:s.condition_rows,extra_measurements:s.extra_measurements,note:s.note,caption:s.caption,independent_visual_audit:'pending'});
 }
}
ck(scenes.length===13,'All 13 operations');ck(scenes.filter(x=>x.operation_id.endsWith('acquisition')).length===4,'Four acquisition operations and nine specimen/reaction preparation operations');
const by=Object.fromEntries(scenes.map(x=>[x.operation_id,x]));
ck(by['ph-treatment-sonicate'].parameters.duration.value===2&&by['ph-treatment-sonicate'].parameters.duration.unit==='min','Source sonication is two minutes');
ck(by['ph-treatment-age'].parameters.duration.value===24&&by['ph-treatment-age'].environment.value===null,'Ageing 24 h with unknown environment');
ck(by['hydrolysis-hydrolyze'].parameters.water_to_tin_relative_ratio.approximate&&by['hydrolysis-hydrolyze'].condition_rows[1].resolved==='≈ 500:1 · basis unspecified','Relative ratio retained without invented basis');
ck(by['ph-treatment-redisperse'].parameters.measurement_pH_after_base.value===null,'Unknown final measurement pH');
ck(by['hydrolysis-dialyze'].retained_fraction==='dialyzed-colloid-series','Dialysis retains colloid');
ck(by['tem-preparation-wet-grid'].parameters.wetting_duration.value===20,'20 second wetting');
ck(by['tem-acquisition'].parameters.accelerating_voltage.value===200&&by['tem-acquisition'].parameters.particle_count_lower_bound.minimum===200,'TEM voltage and lower count bound');
for(const [p,digest] of Object.entries(inputs))ck(sha(p)===digest,'Input unchanged '+p);
const output={schema:'mattersyn.private-apparatus-scenes.v1',source_id:'ribeiro2004',author:'/root/backlog_eta',created_at:new Date().toISOString(),module:'ribeiro2004-protocol.mjs',module_sha256:sha(path.join(O,'ribeiro2004-protocol.mjs')),renderer_sha256:sha(fileURLToPath(import.meta.url)),canonical_manifest_sha256:sha(path.join(B,'canonical-record-manifest.json')),canonical_audit_sha256:sha(path.join(B,'canonical-records-audit.json')),source_main_sha256:Object.values(frozen.source_pdf_hashes)[0],plan_sha256:sha(path.join(B,'visual-preparation-plan.json')),selection:ribeiro2004SceneSelection,counts:{records_with_operations:6,total_scenes:13,preparation_operations:9,acquisition_operations:4},input_hashes:inputs,checks,scenes,author_visual_check:'pending actual PNG inspection',independent_visual_audit:'pending',site_integration:'not performed',publication_approved:false};
fs.writeFileSync(path.join(O,'scene-manifest.json'),JSON.stringify(output,null,2)+'\n');
fs.writeFileSync(path.join(O,'diagram-selection.json'),JSON.stringify({module:output.module,export:'buildRibeiro2004Scene',dom_export:'createRibeiro2004Art',selection:output.selection,bindings:scenes.map(x=>({record_id:x.record_id,operation_id:x.operation_id,pointer:x.operation_pointer,scene_kind:x.scene_kind,svg_file:x.svg_file}))},null,2)+'\n');
console.log(JSON.stringify({scenes:scenes.length,checks:checks.length,manifest_sha256:sha(path.join(O,'scene-manifest.json'))}));
