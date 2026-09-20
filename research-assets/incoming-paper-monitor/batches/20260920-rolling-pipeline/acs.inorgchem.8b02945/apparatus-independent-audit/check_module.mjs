import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const here=path.dirname(fileURLToPath(import.meta.url));
const proposal=path.join(here,'../visuals/apparatus');
const canonical=path.join(here,'../canonical-proposal/draft-v2/records');
const mod=await import(pathToFileURL(path.join(proposal,'friedfeld2019-protocol.mjs')));
const records=fs.readdirSync(canonical).filter(x=>x.endsWith('.json')).map(x=>JSON.parse(fs.readFileSync(path.join(canonical,x))));
const freeze=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};
const resolve=(x,p)=>p.split('/').slice(1).reduce((v,k)=>v[k.replaceAll('~1','/').replaceAll('~0','~')],x);
const scenes=[];let operations=0,fieldChecks=0;const alternatives=new Set();
for(const record of records){
 const before=JSON.stringify(record);freeze(record);
 for(const operation of record.operations){
  operations++;
  const scene=mod.buildFriedfeld2019Scene(operation,record);
  assert(scene,`${record.record_id}:${operation.id}`);
  assert.equal(scene.kind,record.record_id+'--'+operation.id);
  assert.equal(mod.buildFriedfeld2019Scene(operation,{...record,lineage:{source_group:'other'}}),null);
  assert.equal(mod.buildFriedfeld2019Scene({...operation,id:'not-a-source-operation'},record),null);
  const opRows=scene.rows.filter(x=>x.kind==='operation_parameter');
  assert.equal(opRows.length,Object.keys(operation.parameters||{}).length);
  for(const row of scene.rows){
   if(row.quantity){assert.deepEqual(row.quantity,resolve(record,row.pointer));fieldChecks++;}
   for(const q of row.quantities||[]){assert.deepEqual(q.quantity,resolve(record,q.pointer));fieldChecks++;alternatives.add(record.record_id+q.pointer);}
   assert(!/undefined|\[object Object\]/.test(row.value));
  }
  assert(scene.artSvg.includes('<title>'));assert(scene.artSvg.includes('<desc>'));
  assert(!/undefined|\[object Object\]/.test(scene.artSvg));
  scenes.push({record_id:record.record_id,operation_id:operation.id,...scene});
 }
 assert.equal(before,JSON.stringify(record),'Module mutated canonical record');
}
const expectedAlternatives=new Set(records.flatMap(r=>(r.condition_options||[]).flatMap((o,i)=>Object.keys(o.parameters).map(k=>r.record_id+'/condition_options/'+i+'/parameters/'+k))));
assert.deepEqual([...alternatives].sort(),[...expectedAlternatives].sort());
assert.equal(operations,58);assert.equal(scenes.length,58);assert.equal(fieldChecks,115);
fs.writeFileSync(path.join(here,'independently-executed-scenes.json'),JSON.stringify(scenes,null,2)+'\n');
fs.writeFileSync(path.join(here,'module-checks.json'),JSON.stringify({status:'passed',reviewer:'/root',operations,exact_quantity_fields:fieldChecks,alternative_quantity_fields:alternatives.size,canonical_mutated:false,wrong_source_and_operation_rejected:true,mounted_browser_tested:false},null,2)+'\n');
console.log(JSON.stringify({status:'passed',operations,exact_quantity_fields:fieldChecks}));
