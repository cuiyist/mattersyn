import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const O=path.dirname(fileURLToPath(import.meta.url));
const S='[local path redacted]';
const M=await import(pathToFileURL(path.join(S,'dist/friedfeld2019-protocol.mjs')));
const checks=[];const ck=(name,pass)=>checks.push({check:name,pass:!!pass});
let scenes=0,excluded=0;
for(const name of fs.readdirSync(path.join(S,'data/records')).filter(n=>n.endsWith('.json'))){
 const r=JSON.parse(fs.readFileSync(path.join(S,'data/records',name),'utf8'));
 for(const o of r.operations){
  const a=M.buildFriedfeld2019Scene(o,r);
  if(r.lineage.source_group==='friedfeld2019'){
   scenes++;ck(`recognized exact pair ${r.record_id}/${o.id}`,a?.kind===`${r.record_id}--${o.id}`);
   ck(`source-group rejection ${r.record_id}/${o.id}`,M.buildFriedfeld2019Scene(o,{...r,lineage:{...r.lineage,source_group:'unrelated'}})===null);
   ck(`unknown operation rejection ${r.record_id}/${o.id}`,M.buildFriedfeld2019Scene({...o,id:'not-a-source-operation'},r)===null);
   ck(`unknown record rejection ${r.record_id}/${o.id}`,M.buildFriedfeld2019Scene(o,{...r,record_id:'unrelated-record'})===null);
  }else{excluded++;ck(`old record excluded ${r.record_id}/${o.id}`,a===null);}
 }
}
ck('58 actual Friedfeld instances',scenes===58);
const output={scope:'Actual imported module factory dispatch only; no browser/DOM claim.',
 runtime:process.execPath,passed:checks.every(x=>x.pass),executed:checks.length,
 friedfeld_operation_instances:scenes,unrelated_operation_instances:excluded,checks};
fs.writeFileSync(path.join(O,'integration-dispatch-checks.json'),JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify({passed:output.passed,executed:checks.length,scenes,excluded}));
