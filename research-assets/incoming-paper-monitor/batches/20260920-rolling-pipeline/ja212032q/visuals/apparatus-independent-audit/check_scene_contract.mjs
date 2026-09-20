// Distinct auditor: execute the final module; write only this audit directory.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const D=path.dirname(fileURLToPath(import.meta.url)),G=path.resolve(D,'../..'),A=path.join(G,'visuals/apparatus');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const freeze=read(path.join(A,'package-freeze.json'));
const checks=[];
const ck=(v,n)=>{if(!v)throw Error(n);checks.push(n);};
for(const[p,h]of Object.entries(freeze.bound_files||{}))ck(hash(p)===h,'Frozen hash '+p);
const mod=await import(pathToFileURL(path.join(A,'ghosh2012-protocol.mjs')).href);
const cm=read(path.join(G,'canonical-proposal/v2/record-manifest.json'));
const ptr=(x,p)=>p.split('/').slice(1).reduce((v,k)=>v[k.replaceAll('~1','/').replaceAll('~0','~')],x);
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
let scenes=[],parameterCount=0,scheduleCount=0;
for(const row of cm.records){
 ck(hash(row.path)===row.sha256,'Current canonical hash '+row.record_id);
 const r=read(row.path);
 for(let i=0;i<r.operations.length;i++){
  const op=r.operations[i],s=mod.buildGhosh2012Scene(op,r);ck(!!s,'Scene exists '+op.id);
  ck(s.kind===r.record_id+'--'+op.id,'Exact scene identity '+op.id);
  ck(s.caption.includes('schematic')&&s.svg.includes('explanatory'),'Schematic scope '+op.id);
  ck(mod.buildGhosh2012Scene(op,{...r,lineage:{...r.lineage,source_group:'foreign-source'}})===null,'Reject foreign source '+op.id);
  ck(mod.buildGhosh2012Scene(op,{...r,record_id:'foreign-record'})===null,'Reject foreign record '+op.id);
  ck(mod.buildGhosh2012Scene({...op,id:'foreign-operation'},r)===null,'Reject unknown operation '+op.id);
  const expected=Object.entries(op.parameters).map(([k,q])=>({pointer:`/operations/${i}/parameters/${k}`,quantity:q}));
  if(op.id==='compare-anneals')for(let j=0;j<r.condition_options.length;j++)for(const[k,q]of Object.entries(r.condition_options[j].parameters))expected.push({pointer:`/condition_options/${j}/parameters/${k}`,quantity:q});
  const actual=s.rows.filter(x=>x.quantity);
  ck(actual.length===expected.length,'Complete condition rows '+op.id);
  for(const e of expected){
   const hits=actual.filter(x=>x.pointer===e.pointer);ck(hits.length===1,'Unique condition '+op.id+e.pointer);
   const v=hits[0];ck(eq(v.quantity,ptr(r,e.pointer)),'Exact quantity '+op.id+e.pointer);
   ck(v.value!==''&&!v.value.includes('NaN')&&!v.value.includes('undefined'),'Finite text '+op.id+e.pointer);
   if(e.quantity.approximate)ck(v.value.includes('≈'),'Approximation '+op.id+e.pointer);
   if(e.quantity.minimum_exclusive)ck(v.value.includes('>')||v.value.includes('('),'Strict lower bound '+op.id+e.pointer);
   if(e.quantity.maximum_exclusive)ck(v.value.includes('<')||v.value.includes(')'),'Strict upper bound '+op.id+e.pointer);
   if(e.quantity.unit==='count'&&!/cycles/.test(e.pointer))ck(!/cycles/.test(v.value),'Noncycle count label '+op.id+e.pointer);
   if(v.kind==='operation_parameter')parameterCount++;else scheduleCount++;
  }
  ck(!s.rows.some(x=>x.kind==='operation_parameter'&&!x.pointer.startsWith(`/operations/${i}/`)),'No inherited adjacent parameters '+op.id);
  ck(!s.svg.includes('<script')&&!s.artSvg.includes('<script'),'Passive SVG '+op.id);
  scenes.push({record_id:r.record_id,operation_id:op.id,title:s.title,description:s.description,caption:s.caption,rows:s.rows,svg:s.svg,artSvg:s.artSvg});
 }
}
ck(scenes.length===33,'All 33 operations');
ck(new Set(scenes.map(s=>s.operation_id)).size===33,'33 distinct operation IDs');
ck(scheduleCount===10,'Five separate two-interval schedules');
const out={auditor:'/root/backlog_eta',status:'actual_module_contract_checks_passed',package_sha256:hash(path.join(A,'package-freeze.json')),module_sha256:hash(path.join(A,'ghosh2012-protocol.mjs')),counts:{scenes:scenes.length,operation_parameters:parameterCount,schedule_parameters:scheduleCount,display_rows:scenes.reduce((n,s)=>n+s.rows.length,0)},check_count:checks.length,checks};
fs.writeFileSync(path.join(D,'actual-module-validation.json'),JSON.stringify(out,null,2)+'\n');
fs.writeFileSync(path.join(D,'independent-scene-outputs.json'),JSON.stringify(scenes,null,2)+'\n');
console.log(JSON.stringify({check_count:checks.length,counts:out.counts,freeze:out.package_sha256}));
