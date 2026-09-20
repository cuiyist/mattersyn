import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';import {buildVeinotScene} from './veinot-protocol.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));const out=path.join(root,'apparatus-review');fs.mkdirSync(out,{recursive:true});fs.mkdirSync(path.join(out,'svg'),{recursive:true});
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');const checks=[];const rows=[];
function check(ok,label){checks.push({passed:!!ok,check:label});}
for(const name of fs.readdirSync(path.join(root,'canonical-drafts')).filter(s=>s.endsWith('.json')).sort()){
 const bytes=fs.readFileSync(path.join(root,'canonical-drafts',name));const r=JSON.parse(bytes);
 for(const o of r.operations){const s=buildVeinotScene(o,r);check(!!s,r.record_id+'/'+o.id+' covered');if(!s)continue;
  check(!/undefined|NaN|null|<script|onload=/.test(s.svg),r.record_id+'/'+o.id+' safe finite SVG');
  check(buildVeinotScene(o,{...r,sources:[{doi:'10.1021/not-this-paper'}]})===null,r.record_id+'/'+o.id+' wrong DOI rejected');
  check(buildVeinotScene({...o,action:'unknown'},r)===null,r.record_id+'/'+o.id+' unknown action rejected');
  const fn=r.record_id+'--'+o.id+'.svg';fs.writeFileSync(path.join(out,'svg',fn),s.svg);
  rows.push({record_id:r.record_id,operation_id:o.id,action:o.action,source_record_sha256:sha(bytes),svg_sha256:sha(s.svg),svg:'svg/'+fn,caption:s.caption,source_evidence:o.evidence,source_label:o.label});
 }
}
check(rows.length===133,'Exactly current 133 canonical operations');check(new Set(rows.map(x=>x.action)).size===41,'Exactly 41 distinct source actions');
fs.writeFileSync(path.join(out,'scene-manifest.json'),JSON.stringify({module_sha256:sha(fs.readFileSync(path.join(root,'veinot-protocol.mjs'))),source_doi:'10.1021/cm970189m',illustrative_only:true,eligible_training:false,rows},null,2));
fs.writeFileSync(path.join(out,'dispatch-validation.json'),JSON.stringify({status:checks.every(x=>x.passed)?'passed':'failed',passed:checks.filter(x=>x.passed).length,failed:checks.filter(x=>!x.passed).length,checks},null,2));console.log(JSON.stringify({stages:rows.length,actions:new Set(rows.map(x=>x.action)).size,passed:checks.filter(x=>x.passed).length,failed:checks.filter(x=>!x.passed).length}));
