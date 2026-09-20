import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import crypto from 'node:crypto';
import {buildRibeiro2004Scene,resolveRibeiro2004Rows,ribeiro2004SceneSelection} from './visuals/apparatus/ribeiro2004-protocol.mjs';
const R=path.dirname(fileURLToPath(import.meta.url)),V=path.join(R,'visuals'),A=path.join(V,'apparatus');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,'')),sha=s=>crypto.createHash('sha256').update(s).digest('hex'),checks=[],rows=[];
function ck(ok,label){checks.push({passed:!!ok,label});if(!ok)throw Error(label);}
const sm=read(path.join(A,'scene-manifest.json'));
for(const file of fs.readdirSync(path.join(R,'canonical-drafts')).filter(x=>x.endsWith('.json'))){const r=read(path.join(R,'canonical-drafts',file));
 for(const [i,o]of r.operations.entries()){
  const before=JSON.stringify(r),s=buildRibeiro2004Scene(o,r),original=sm.scenes.find(x=>x.operation_id===o.id&&x.record_id===r.record_id);
  ck(!!s&&!!original,o.id+' exact source selection');ck(s.svg===fs.readFileSync(path.join(A,'scene-svg',s.kind+'.svg'),'utf8'),o.id+' frozen SVG replay');ck(before===JSON.stringify(r),o.id+' no canonical mutation');
  ck(buildRibeiro2004Scene({...o,id:'unknown-operation'},r)===null,o.id+' unknown operation rejected');ck(buildRibeiro2004Scene(o,{...r,lineage:{...r.lineage,source_group:'other'}})===null,o.id+' foreign source rejected');ck(buildRibeiro2004Scene(o,{...r,record_id:'ribeiro-2004-unassigned'})===null,o.id+' wrong record rejected');
  for(const row of resolveRibeiro2004Rows(o,r)){let q=null;if(row.pointer){q=row.pointer.split('/').slice(1).reduce((a,k)=>a[k],r);ck(q!==undefined,o.id+' exact quantity pointer '+row.pointer);}
   rows.push({record_id:r.record_id,operation_id:o.id,operation_pointer:`/operations/${i}`,label:row.label,kind:row.kind,pointer:row.pointer,canonical_quantity:q,display:row.resolved});}
 }
}
ck(new Set(rows.map(x=>x.operation_id)).size===13,'All 13 operations replayed');
const out={scope:'Independent read-only replay; not browser approval',module_sha256:sha(fs.readFileSync(path.join(A,'ribeiro2004-protocol.mjs'))),checks,rows};fs.writeFileSync(path.join(R,'visual-scene-independent-replay.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify({checks:checks.length,rows:rows.length,operations:13}));
