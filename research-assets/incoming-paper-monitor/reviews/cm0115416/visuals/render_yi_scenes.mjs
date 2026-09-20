import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {buildYi2002Scene} from './yi2002-protocol.mjs';
const V=path.dirname(fileURLToPath(import.meta.url)),B=path.dirname(V);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const scenes=[],checks=[];
const ck=(test,label)=>{checks.push({label,passed:!!test});if(!test)throw Error(label);};
fs.mkdirSync(path.join(V,'scene-svg'),{recursive:true});fs.mkdirSync(path.join(V,'review'),{recursive:true});
for(const file of fs.readdirSync(path.join(B,'canonical-drafts')).filter(n=>n.endsWith('.json')).sort()){
 const raw=fs.readFileSync(path.join(B,'canonical-drafts',file)),r=JSON.parse(raw);
 for(const o of r.operations){
  const before=JSON.stringify({o,r}),s=buildYi2002Scene(o,r),key=r.record_id+'/'+o.id;
  ck(!!s,key+' mapped');ck(before===JSON.stringify({o,r}),key+' no canonical mutation');ck(!/undefined|NaN/.test(s.svg),key+' finite SVG');ck(s.svg.includes('viewBox="0 0 600 420"'),key+' expected viewport');
  const fname='scene-svg/'+r.record_id+'--'+o.id+'.svg';fs.writeFileSync(path.join(V,fname),s.svg);
  scenes.push({record_id:r.record_id,operation_id:o.id,file:fname,kind:s.kind,svg_sha256:sha(s.svg),record_sha256:sha(raw),parameters:o.parameters,environment:o.environment,inputs:o.inputs,outputs:o.outputs,evidence:o.evidence});
 }
}
const out={module:'yi2002-protocol.mjs',module_sha256:sha(fs.readFileSync(path.join(V,'yi2002-protocol.mjs'))),record_count:18,operation_count:scenes.length,checks,scenes};
fs.writeFileSync(path.join(V,'scene-manifest.json'),JSON.stringify(out,null,2));
console.log(JSON.stringify({operation_count:scenes.length,checks:checks.length,module_sha256:out.module_sha256}));

