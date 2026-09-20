import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {buildGu2004Scene,gu2004SceneSelection} from './gu2004-protocol.mjs';
const V=path.dirname(fileURLToPath(import.meta.url)),B=path.resolve(V,'../..'),sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const frozen=read(path.join(B,'canonical-record-manifest.json'));
const audit=read(path.join(B,'canonical-records-audit.json'));
if(audit.status!=='passed')throw Error('Canonical audit does not pass');
if(sha(fs.readFileSync(path.join(B,'canonical-record-manifest.json')))!==audit.bound_files['canonical-record-manifest.json'])throw Error('Frozen manifest changed');
fs.mkdirSync(path.join(V,'scene-svg'),{recursive:true});fs.mkdirSync(path.join(V,'review'),{recursive:true});
const scenes=[],checks=[];
function check(ok,label){checks.push({label,passed:!!ok});if(!ok)throw Error(label);}
for(const row of frozen.records){
 const raw=fs.readFileSync(row.path);check(sha(raw)===row.sha256,`${row.record_id}: frozen record`);
 const r=JSON.parse(raw);const selected=gu2004SceneSelection.records[r.record_id]??[];
 check(selected.length===r.operations.length,`${r.record_id}: selection coverage`);
 for(const [index,o] of r.operations.entries()){
  const previous=JSON.stringify(r),scene=buildGu2004Scene(o,r);
  check(!!scene,`${r.record_id}/${o.id}: scene selected`);check(JSON.stringify(r)===previous,`${r.record_id}/${o.id}: no mutation`);
  check(scene.svg.includes('viewBox="0 0 760 540"')&&!/undefined|NaN/.test(scene.svg),`${r.record_id}/${o.id}: SVG geometry`);
  const name=`scene-svg/${scene.kind}.svg`;fs.writeFileSync(path.join(V,name),scene.svg);
  scenes.push({record_id:r.record_id,operation_id:o.id,operation_pointer:`/operations/${index}`,stage:o.stage,scene_kind:scene.kind,svg_file:name,svg_sha256:sha(scene.svg),record_sha256:row.sha256,inputs:o.inputs,outputs:o.outputs,parameters:o.parameters,environment:o.environment,retained_fraction:o.retained_fraction,source_evidence:o.evidence,caption:scene.caption,illustration_status:'generic explanatory geometry; no invented source apparatus or measured structure',independent_visual_audit:'pending'});
 }
}
check(scenes.length===33,'All 33 operations covered');check(scenes.filter(x=>x.stage!=='characterization').length===21,'All 21 preparation operations covered');
const key=scenes.find(x=>x.operation_id==='hetero-preheat');check(key.parameters.duration.approximate===true&&key.parameters.temperature.approximate===false,'Approximate 5 min and reported 100°C preserved');
const output={schema:'mattersyn.private-apparatus-scenes.v1',source_id:'gu2004',created_at:new Date().toISOString(),module:'gu2004-protocol.mjs',module_sha256:sha(fs.readFileSync(path.join(V,'gu2004-protocol.mjs'))),renderer_sha256:sha(fs.readFileSync(fileURLToPath(import.meta.url))),canonical_manifest_sha256:sha(fs.readFileSync(path.join(B,'canonical-record-manifest.json'))),canonical_audit_sha256:sha(fs.readFileSync(path.join(B,'canonical-records-audit.json'))),selection:gu2004SceneSelection,counts:{records_with_operations:7,preparation_operations:21,acquisition_operations:12,total_scenes:scenes.length},checks,scenes,author_visual_check:'pending rendered inspection',independent_visual_audit:'pending',site_integration:'not performed',publication_approved:false};
fs.writeFileSync(path.join(V,'scene-manifest.json'),JSON.stringify(output,null,2)+'\n');
fs.writeFileSync(path.join(V,'diagram-selection.json'),JSON.stringify({module:output.module,export:'buildGu2004Scene',dom_export:'createGu2004Art',selection:output.selection,bindings:scenes.map(x=>({record_id:x.record_id,operation_id:x.operation_id,pointer:x.operation_pointer,scene_kind:x.scene_kind,svg_file:x.svg_file}))},null,2)+'\n');
console.log(JSON.stringify({scenes:scenes.length,checks:checks.length,module_sha256:output.module_sha256}));
