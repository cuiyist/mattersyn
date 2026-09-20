import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import {buildDabbousiScene} from './dabbousi-protocol.mjs';
const root=path.dirname(fileURLToPath(import.meta.url)),out=path.join(root,'apparatus-review');
fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const checks=[],files=[];
const check=(ok,name)=>{checks.push({check:name,passed:!!ok});};
for(const f of fs.readdirSync(path.join(root,'canonical-drafts')).filter(s=>s.endsWith('.json')).sort()){
 const bytes=fs.readFileSync(path.join(root,'canonical-drafts',f)),r=JSON.parse(bytes);
 for(const o of r.operations){const s=buildDabbousiScene(o,r);check(!!s,`${r.record_id}/${o.id} supported`);if(!s)continue;
  const name=`${r.record_id}--${o.id}.svg`;
  fs.writeFileSync(path.join(out,name),s.svg);
  files.push({file:name,recordId:r.record_id,operationId:o.id,action:o.action,sourceRecordSha256:sha(bytes),sha256:sha(s.svg),caption:s.caption});
  check(!/NaN|undefined|null/.test(s.svg),`${name} finite labels`);
  check(!/<script|onload=|javascript:|https?:\/(?!\/www.w3.org)/i.test(s.svg),`${name} passive SVG`);
  check(buildDabbousiScene(o,{...r,sources:[{doi:'10.1021/cm9503137'}]})===null,`${name} rejects other DOI`);
  if(o.action==='dropwise_addition'){check(s.svg.includes('Addition funnel')&&!s.svg.toLowerCase().includes('pump'),`${name} source addition funnel`);}
  if(o.action==='filtration')check(!/PTFE|Ar backfill/.test(s.svg),`${name} no invented filter/gas identity`);
  if(r.record_id==='dabbousi-1997-zns-overgrowth'&&['heat-seeds','dose'].includes(o.id))check(!/180 °C|140 °C|220 °C/.test(s.svg)&&s.svg.includes('Source-paired T'),`${name} no arbitrary selected temperature`);
 }
}
check(buildDabbousiScene({action:'unsupported'},{sources:[{doi:'10.1021/jp971091y'}]})===null,'Unknown action is not silently rendered');
check(files.length===60,'All 60 reported canonical operations rendered');
const report={sourceDoi:'10.1021/jp971091y',sourceSha256:'dac183303049a3275d4f1874c66ac0ceece9895bc175f7f7e9727ef7c9cd8f9d',moduleSha256:sha(fs.readFileSync(path.join(root,'dabbousi-protocol.mjs'))),status:checks.every(x=>x.passed)?'passed':'failed',checkCount:checks.length,errors:checks.filter(x=>!x.passed),checks,files,visualReview:'pending'};
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,count:files.length,actions:[...new Set(files.map(x=>x.action))].length,errors:report.errors}));
if(report.errors.length)process.exitCode=1;
