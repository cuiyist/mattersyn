import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
import {buildNagasaki2004Scene,nagasaki2004OperationIds} from './nagasaki2004-protocol.mjs';
const V=path.dirname(fileURLToPath(import.meta.url)),B=path.resolve(V,'../..');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));const save=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n');
fs.mkdirSync(path.join(V,'scene-svg'),{recursive:true});fs.mkdirSync(path.join(V,'review'),{recursive:true});
if(fs.existsSync(path.join(V,'author-visual-check.json')))throw Error('Author freeze exists; deliberate revision required.');
const checks=[],scenes=[],bound={};const check=(name,ok)=>{checks.push({check:name,passed:!!ok});if(!ok)throw Error(name);};
let observed=[];
for(const file of fs.readdirSync(path.join(B,'canonical-drafts')).filter(x=>x.endsWith('.json')).sort()){
 const p=path.join(B,'canonical-drafts',file),r=read(p);bound[p]=sha(p);
 for(const o of r.operations){const s=buildNagasaki2004Scene(o,r);check(r.record_id+'/'+o.id+' has meaningful scene',!!s);observed.push(o.id);
  check(s.kind+' does not imply inert reaction atmosphere',!s.svg.includes('Inert;'));
  check(s.kind+' has current operation title',s.svg.includes('<title>'));
  const filename='scene-svg/'+s.kind+'.svg';fs.writeFileSync(path.join(V,filename),s.svg);
  scenes.push({record_id:r.record_id,operation_id:o.id,scene_kind:s.kind,svg_file:filename,svg_sha256:sha(path.join(V,filename)),canonical_file:p,canonical_sha256:sha(p),operation:JSON.parse(JSON.stringify(o)),caption:s.caption,condition_rows:s.conditionRows});
 }
}
check('All36canonical operations covered',scenes.length===36);
check('No extra unused or duplicate scene configuration',new Set(observed).size===36&&observed.every(x=>nagasaki2004OperationIds.includes(x))&&nagasaki2004OperationIds.length===36);
check('Other source cannot select module',buildNagasaki2004Scene({id:observed[0]},{lineage:{source_group:'gu2004'},record_id:'gu-2004-heterodimer'})===null);
const ch=read(path.join(B,'canonical-drafts/nagasaki-2004-aldehyde-polymer.json')).operations.find(o=>o.id==='hydrolyze-acetal');
check('Visible10:1v/v matches both canonical ratio parts',ch.parameters.acetic_acid_relative_volume_parts.value===10&&ch.parameters.water_relative_volume_parts.value===1);
for(const f of ['canonical-record-manifest.json','canonical-records-audit.json','reader-source-audit.json'])bound[path.join(B,f)]=sha(path.join(B,f));
save(path.join(V,'scene-manifest.json'),{schema:'mattersyn.private-apparatus-scenes.v1',source_id:'nagasaki2004',author:'/root',created_at:new Date().toISOString(),module:'nagasaki2004-protocol.mjs',module_sha256:sha(path.join(V,'nagasaki2004-protocol.mjs')),renderer_sha256:sha(fileURLToPath(import.meta.url)),counts:{total_scenes:scenes.length,records_with_operations:new Set(scenes.map(s=>s.record_id)).size},scenes,checks,bound_inputs:bound,author_visual_check:'pending rendered inspection',independent_visual_audit:'pending',site_integration:'not performed',publication_approved:false});
console.log(JSON.stringify({scenes:scenes.length,checks:checks.length}));
