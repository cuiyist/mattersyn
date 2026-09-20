import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const P=path.dirname(fileURLToPath(import.meta.url));
const A=path.join(P,'visuals','apparatus');
const mod=await import(pathToFileURL(path.join(A,'norberg2004-protocol.mjs')));
const manifest=JSON.parse(fs.readFileSync(path.join(A,'scene-manifest.json'),'utf8'));
const checks=[];
const ck=(label,ok)=>checks.push({label,passed:!!ok});
for(const scene of manifest.scenes){
  const r=JSON.parse(fs.readFileSync(path.join(P,'canonical-drafts',scene.record_id+'.json'),'utf8'));
  const o=r.operations.find(x=>x.id===scene.operation_id);
  const saved=JSON.stringify(r);
  const actual=mod.buildNorberg2004Scene(o,r);
  ck(scene.operation_id+' rendered exact frozen SVG',actual.svg===fs.readFileSync(path.join(A,scene.svg_file),'utf8'));
  ck(scene.operation_id+' immutable input',JSON.stringify(r)===saved);
  ck(scene.operation_id+' rejects unknown op',mod.buildNorberg2004Scene({...o,id:'unapproved-operation'},r)===null);
  ck(scene.operation_id+' rejects foreign source',mod.buildNorberg2004Scene(o,{...r,lineage:{source_group:'ribeiro2004'}})===null);
  ck(scene.operation_id+' rejects record mismatch',mod.buildNorberg2004Scene(o,{...r,record_id:'unapproved-record'})===null);
  ck(scene.operation_id+' no dynamic external calls',!/(<script|<iframe|https?:\/\/[^w])/i.test(actual.svg));
}
const output={schema:'mattersyn.independent-scene-module-check.v1',auditor:'/root/backlog_eta',at:new Date().toISOString(),module_sha256:createHash('sha256').update(fs.readFileSync(path.join(A,'norberg2004-protocol.mjs'))).digest('hex'),checks,count:checks.length,failures:checks.filter(x=>!x.passed),browser_review:false};
fs.writeFileSync(path.join(P,'visual-independent-module-checks.json'),JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify({count:checks.length,failures:output.failures}));
