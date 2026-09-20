import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {buildWaferScene,supportsWaferOperation,WAFER_ACTIONS} from './wafer-protocol.mjs';
const HERE=path.dirname(fileURLToPath(import.meta.url)),records=path.join(HERE,'../canonical-drafts');
const output=path.join(HERE,'scene-previews');fs.mkdirSync(output,{recursive:true});
let scenes=[];
for(const file of fs.readdirSync(records).filter(x=>x.endsWith('.json'))){
 const r=JSON.parse(fs.readFileSync(path.join(records,file),'utf8'));
 for(const o of r.operations){
  const scene=buildWaferScene(o,r);
  if(!scene)throw Error('Missing source operation: '+r.record_id+'/'+o.id);
  if(supportsWaferOperation(o,{...r,sources:[{doi:'10.0000/unrelated'}]}))throw Error('Source guard failed');
  const name=r.record_id+'--'+o.id+'.svg';
  fs.writeFileSync(path.join(output,name),scene.svg);
  scenes.push({record_id:r.record_id,operation_id:o.id,action:o.action,file:'scene-previews/'+name,svg_sha256:crypto.createHash('sha256').update(scene.svg).digest('hex')});
 }
}
const actions=new Set(scenes.map(x=>x.action));
if(WAFER_ACTIONS.some(x=>!actions.has(x)))throw Error('An expected action was not exercised');
const report={status:'passed_builder_and_source_guards',source:'10.1021/jp951903v',module_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(HERE,'wafer-protocol.mjs'))).digest('hex'),record_operation_scenes:scenes.length,distinct_action_scenes:actions.size,scenes,visual_review:'Pending root browser inspection of integrated UI; SVG text-bound checks are separate.'};
fs.writeFileSync(path.join(HERE,'scene-checks.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(HERE,'preview.html'),'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Heath 1996 source-scoped diagrams</title><style>body{font:16px Segoe UI,sans-serif;background:#f1f6fa;color:#284b5b;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px}article{background:white;padding:12px;border-radius:12px}img{width:100%;height:auto}h2{font-size:15px}</style><h1>Heath 1996 technical process diagrams</h1><p>Private integration preview. Geometry and particle symbols are explanatory, not measured reconstructions.</p><main>'+scenes.map(x=>'<article><h2>'+x.record_id+' · '+x.operation_id+'</h2><img alt="'+x.action+' schematic" src="'+x.file+'"></article>').join('')+'</main></html>');
console.log(JSON.stringify({status:report.status,scenes:scenes.length,actions:actions.size,module_sha256:report.module_sha256}));
