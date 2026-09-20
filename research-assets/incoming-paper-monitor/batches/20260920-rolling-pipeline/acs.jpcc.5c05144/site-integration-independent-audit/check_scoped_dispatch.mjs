import fs from 'node:fs';import path from 'node:path';import {fileURLToPath,pathToFileURL} from 'node:url';
const O=path.dirname(fileURLToPath(import.meta.url)),S='[local path redacted]';
const {buildSasongko2025Scene,sasongko2025SceneSelection}=await import(pathToFileURL(S+'/dist/sasongko2025-protocol.mjs'));
const checks=[],rows=[];const ck=(check,passed)=>checks.push({check,passed:!!passed});
const get=(o,p)=>p.split('/').filter(Boolean).reduce((x,k)=>x[k],o);
let selected=0,rejected=0;
for(const name of fs.readdirSync(S+'/data/records').filter(x=>x.endsWith('.json'))){
 const r=JSON.parse(fs.readFileSync(S+'/data/records/'+name,'utf8'));
 for(const o of r.operations){
  const scene=buildSasongko2025Scene(o,r),isJ=r.lineage.source_group==='sasongko2025';
  ck('Scoped dispatch '+r.record_id+'/'+o.id,isJ?!!scene:scene===null);
  if(!isJ){rejected++;continue;} selected++;
  ck('Exact scene identity '+scene.kind,scene.kind===r.record_id+'--'+o.id);
  ck('Explicit config membership '+scene.kind,sasongko2025SceneSelection.records[r.record_id].includes(o.id));
  for(const row of scene.rows){
   if(row.kind==='operation_parameter')ck('Operation row transport '+scene.kind+row.pointer,JSON.stringify(row.quantity)===JSON.stringify(get(r,row.pointer)));
   for(const q of row.quantities||[])ck('Comparison row transport '+scene.kind+q.pointer,JSON.stringify(q.quantity)===JSON.stringify(get(r,q.pointer)));
  }
  ck('Wrong source rejected '+scene.kind,buildSasongko2025Scene(o,{...r,lineage:{...r.lineage,source_group:'independent-negative-control'}})===null);
  ck('Unknown record rejected '+scene.kind,buildSasongko2025Scene(o,{...r,record_id:r.record_id+'-not-a-source-record'})===null);
  ck('Unknown operation rejected '+scene.kind,buildSasongko2025Scene({...o,id:o.id+'-not-a-source-operation'},r)===null);
  rows.push({record_id:r.record_id,operation_id:o.id,kind:scene.kind,row_count:scene.rows.length});
 }
}
ck('Exactly 21 selected source operation instances',selected===21);
const result={status:checks.every(x=>x.passed)?'passed':'failed',checks,selected,rejected,rows,browser_exercised:false};
fs.writeFileSync(O+'/scoped-dispatch-checks.json',JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,checks:checks.length,selected,rejected,failed:checks.filter(x=>!x.passed)}));
