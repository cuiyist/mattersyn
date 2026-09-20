import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const out=path.dirname(fileURLToPath(import.meta.url));
const review=path.dirname(out);
const moduleFile=path.join(review,'danek-protocol.mjs');
const moduleBytes=fs.readFileSync(moduleFile);
fs.writeFileSync(path.join(out,'source-snapshot.mjs'),moduleBytes);
const {buildDanekScene}=await import(pathToFileURL(path.join(out,'source-snapshot.mjs')));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
fs.mkdirSync(path.join(out,'scenes'),{recursive:true});
const inventory=[];
for(const file of fs.readdirSync(path.join(review,'canonical-drafts')).filter(x=>x.endsWith('.json')).sort()){
 const raw=fs.readFileSync(path.join(review,'canonical-drafts',file));
 const record=JSON.parse(raw);
 for(const op of record.operations){
  const scene=buildDanekScene(op,record);
  const row={record_id:record.record_id,record_sha256:hash(raw),operation_id:op.id,action:op.action,label:op.label,covered:!!scene};
  if(scene){
   row.file=`scenes/${record.record_id}--${op.id}.svg`;row.sha256=hash(scene.svg);row.caption=scene.caption;
   fs.writeFileSync(path.join(out,row.file),scene.svg);
  }
  inventory.push(row);
 }
}
const fixture={id:'heat',action:'heating',label:'Guard fixture',parameters:{}};
const guards={wrong_doi_returns_null:buildDanekScene(fixture,{sources:[{doi:'10.1021/another'}]})===null,
 no_sources_returns_null:buildDanekScene(fixture,{})===null,
 undefined_record_returns_null:buildDanekScene(fixture,undefined)===null,
 unsupported_action_returns_null:buildDanekScene({...fixture,action:'not_supported'},{sources:[{doi:'10.1021/cm9503137'}]})===null,
 target_doi_is_enabled:!!buildDanekScene(fixture,{sources:[{doi:'10.1021/cm9503137'}]})};
fs.writeFileSync(path.join(out,'scene-inventory.json'),JSON.stringify({module_sha256:hash(moduleBytes),module_file:'danek-protocol.mjs',source_doi:'10.1021/cm9503137',guard_checks:guards,operations:inventory},null,2));
console.log(JSON.stringify({module_sha256:hash(moduleBytes),operations:inventory.length,covered:inventory.filter(x=>x.covered).length,guards}));
