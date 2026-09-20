import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';import {buildStigerScene} from './stiger-protocol.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));const out=path.join(root,'apparatus-review');fs.mkdirSync(path.join(out,'svg'),{recursive:true});
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');const checks=[];const rows=[];
function check(ok,label){checks.push({passed:!!ok,check:label});}
for(const name of fs.readdirSync(path.join(root,'canonical-drafts')).filter(s=>s.endsWith('.json')).sort()){
 const bytes=fs.readFileSync(path.join(root,'canonical-drafts',name));const r=JSON.parse(bytes);
 for(const o of r.operations){const s=buildStigerScene(o,r);check(!!s,r.record_id+'/'+o.id+' covered');if(!s)continue;
  check(!/undefined|NaN|null|<script|onload=/.test(s.svg),r.record_id+'/'+o.id+' safe finite SVG');
  check(buildStigerScene(o,{...r,sources:[{doi:'10.1021/not-this-paper'}]})===null,r.record_id+'/'+o.id+' wrong DOI rejected');
  check(buildStigerScene(o,{...r,record_id:'another-paper'})===null,r.record_id+'/'+o.id+' wrong record family rejected');
  check(buildStigerScene({...o,id:'unknown-operation'},r)===null,r.record_id+'/'+o.id+' unknown operation rejected');
  const fn=r.record_id+'--'+o.id+'.svg';fs.writeFileSync(path.join(out,'svg',fn),s.svg);
  rows.push({record_id:r.record_id,operation_id:o.id,action:o.action,source_record_sha256:sha(bytes),svg_sha256:sha(s.svg),svg:'svg/'+fn,caption:s.caption,source_evidence:o.evidence,source_label:o.label});
 }
}
check(rows.length===36,'Exactly current 36 canonical operations');
fs.writeFileSync(path.join(out,'scene-manifest.json'),JSON.stringify({module_sha256:sha(fs.readFileSync(path.join(root,'stiger-protocol.mjs'))),source_doi:'10.1021/la980800b',illustrative_only:true,eligible_training:false,rows},null,2));
fs.writeFileSync(path.join(out,'dispatch-validation.json'),JSON.stringify({status:checks.every(x=>x.passed)?'passed':'failed',passed:checks.filter(x=>x.passed).length,failed:checks.filter(x=>!x.passed).length,checks},null,2));console.log(JSON.stringify({stages:rows.length,actions:new Set(rows.map(x=>x.action)).size,passed:checks.filter(x=>x.passed).length,failed:checks.filter(x=>!x.passed).length}));
