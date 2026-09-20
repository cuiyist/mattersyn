import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';import {buildYaoScene} from './yao-protocol.mjs';
const R=path.dirname(fileURLToPath(import.meta.url));const A=path.join(R,'apparatus-review');const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const m=JSON.parse(fs.readFileSync(path.join(A,'scene-manifest.json')));const changes=[];const checks=[];
for(const [rid,oid] of [['yao-1998-resin-conditioning','wash-water'],['yao-1998-tem','distribution']]){
 const b=fs.readFileSync(path.join(R,'canonical-drafts',rid+'.json'));const r=JSON.parse(b);const o=r.operations.find(x=>x.id===oid);const s=buildYaoScene(o,r);const i=m.rows.findIndex(x=>x.record_id===rid&&x.operation_id===oid);const row=m.rows[i];const before=row.svg_sha256;
 checks.push({check:rid+'/'+oid+' no unsupported endpoint or histogram depth',passed:!s.svg.includes('Wash until')&&(oid!=='distribution'||s.svg.includes('≈4 µm: histogram region'))});
 checks.push({check:rid+'/'+oid+' wrong DOI rejected',passed:buildYaoScene(o,{...r,sources:[{doi:'other'}]})===null});
 checks.push({check:rid+'/'+oid+' finite safe SVG',passed:!/(undefined|NaN|<script)/.test(s.svg)});
 fs.writeFileSync(path.join(A,row.svg),s.svg);row.svg_sha256=sha(s.svg);row.source_record_sha256=sha(b);changes.push({index:i,record_id:rid,operation_id:oid,svg:row.svg,old_sha256:before,new_sha256:row.svg_sha256,contact_sheet:'contact-'+String(Math.floor(i/6)+1).padStart(2,'0')+'.png'});
}
m.module_sha256=sha(fs.readFileSync(path.join(R,'yao-protocol.mjs')));fs.writeFileSync(path.join(A,'scene-manifest.json'),JSON.stringify(m,null,2));fs.writeFileSync(path.join(A,'correction-validation.json'),JSON.stringify({module_sha256:m.module_sha256,status:checks.every(x=>x.passed)?'passed':'failed',scope:'Only two wording changes; unchanged dispatch and 45 frames retained from full pass',checks,changes},null,2));console.log(JSON.stringify({module_sha256:m.module_sha256,changed:changes.length,passed:checks.filter(x=>x.passed).length}));
