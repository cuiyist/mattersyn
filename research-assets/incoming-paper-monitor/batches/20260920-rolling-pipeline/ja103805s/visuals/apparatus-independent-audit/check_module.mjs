import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {buildEvans2010Scene,renderEvans2010Markup,evans2010SceneSelection} from '../apparatus/v1/evans2010-protocol.mjs';
const O=new URL('./',import.meta.url),V=new URL('../apparatus/v1/',import.meta.url),B=new URL('../../',import.meta.url);
const read=(root,n)=>JSON.parse(readFileSync(new URL(n,root),'utf8'));
const sha=(root,n)=>createHash('sha256').update(readFileSync(new URL(n,root))).digest('hex');
const compact=read(V,'records.json'),expected=read(V,'rendered-scenes.json');let checks=0,rows=0,params=0;
function freeze(x){if(x&&typeof x==='object'){Object.freeze(x);for(const y of Object.values(x))freeze(y);}return x;}
const before=JSON.stringify(compact);freeze(compact);
const report=[];
for(const r of compact){
 const canonical=read(B,`canonical-proposal/v3/${r.record_id}.json`);
 for(const key of Object.keys(r)){assert.deepEqual(r[key],canonical[key]);checks++;}
 assert.deepEqual(evans2010SceneSelection.records[r.record_id],r.operations.map(x=>x.id));checks++;
 for(const op of r.operations){
  const s=buildEvans2010Scene(op,r),e=expected.find(x=>x.operation_id===op.id);
  assert.ok(s);checks++;
  assert.equal(s.svg,readFileSync(new URL(`svg/${op.id}.svg`,V),'utf8'));checks++;
  assert.deepEqual(s.rows,e.rows);checks++;
  assert.equal(s.title,op.label);assert.equal(s.description,op.description);checks+=2;
  assert.ok(s.caption.includes('explanatory'));checks++;
  let idx=0;
  for(const [key,q]of Object.entries(op.parameters||{})){
   const row=s.rows[idx++];assert.equal(row.label,key.replaceAll('_',' '));checks++;
   if(typeof q.value==='number'){
    const numeric=row.value.match(/^(?:≈ )?(-?(?:\d+(?:\.\d+)?|\.\d+))/);
    assert.ok(numeric,op.id+key);assert.equal(Number(numeric[1]),q.value);checks+=2;
    const unit={degC:'°C',uL:'µL',angstrom:'Å',um:'µm',degree:'°'}[q.unit]||q.unit;
    assert.ok(row.value.includes(unit));checks++;
   }else if(q.value!==null){assert.ok(row.value.includes(String(q.value)));checks++;}
   if(q.approximate){assert.ok(row.value.startsWith('≈'));checks++;}
   if(q.qualifier){assert.ok(row.value.includes(q.qualifier));checks++;}
   params++;
  }
  if(op.environment?.value){assert.deepEqual(s.rows[idx++],{label:'Environment',value:op.environment.value});checks++;}
  if(op.endpoint?.value){assert.deepEqual(s.rows[idx++],{label:'Endpoint',value:op.endpoint.value});checks++;}
  const markup=renderEvans2010Markup(s);assert.ok(markup.includes(s.artSvg));checks++;
  assert.equal(buildEvans2010Scene({...op,id:'unknown-operation'},r),null);checks++;
  assert.equal(buildEvans2010Scene(op,{...r,lineage:{source_group:'other-source'}}),null);checks++;
  const different=compact.find(x=>x.record_id!==r.record_id);assert.equal(buildEvans2010Scene(op,different),null);checks++;
  rows+=s.rows.length;report.push({operation_id:op.id,canonical_record:r.record_id,parameter_count:Object.keys(op.parameters||{}).length,condition_count:s.rows.length,svg_replay_identical:true});
 }
}
assert.equal(JSON.stringify(compact),before);checks++;
assert.equal(report.length,46);assert.equal(rows,153);checks+=2;
const result={status:'passed_independent_module_and_canonical_transport_checks',auditor:'/root/norberg2004_extract',checks,scenes:report.length,conditions:rows,canonical_parameter_rows:params,per_operation:report,source_module_sha256:sha(V,'evans2010-protocol.mjs'),scope:'Executed author module read-only on deeply frozen actual input fragments; every stored SVG replayed identically, all numeric values/units/qualifiers and exact canonical operation objects checked. This supports, but does not replace, independent original-source and rendered-scene inspection.',mounted_browser_test:false};
writeFileSync(new URL('module-checks.json',O),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({checks,scenes:report.length,conditions:rows,params}));
