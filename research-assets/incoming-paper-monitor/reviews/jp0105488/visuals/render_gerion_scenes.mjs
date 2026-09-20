import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {buildGerion2001Scene} from './gerion2001-protocol.mjs';
const V=path.dirname(fileURLToPath(import.meta.url)),B=path.dirname(V);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const scenes=[],checks=[];
const ck=(test,label)=>{checks.push({label,passed:!!test});if(!test)throw Error(label);};
fs.mkdirSync(path.join(V,'scene-svg'),{recursive:true});fs.mkdirSync(path.join(V,'review'),{recursive:true});
for(const file of fs.readdirSync(path.join(B,'canonical-drafts')).filter(n=>n.endsWith('.json')).sort()){
 const raw=fs.readFileSync(path.join(B,'canonical-drafts',file)),r=JSON.parse(raw);
 for(const o of r.operations){
  const before=JSON.stringify({o,r}),s=buildGerion2001Scene(o,r),key=r.record_id+'/'+o.id;
  ck(!!s,key+' mapped');ck(before===JSON.stringify({o,r}),key+' no canonical mutation');ck(!/undefined|NaN/.test(s.svg),key+' finite SVG');ck(s.svg.includes('viewBox="0 0 600 415"'),key+' expected viewport');
  const fname='scene-svg/'+r.record_id+'--'+o.id+'.svg';fs.writeFileSync(path.join(V,fname),s.svg);
  scenes.push({record_id:r.record_id,operation_id:o.id,file:fname,kind:s.kind,svg_sha256:sha(s.svg),record_sha256:sha(raw),parameters:o.parameters,environment:o.environment,inputs:o.inputs,outputs:o.outputs,evidence:o.evidence});
 }
}
ck(scenes.length===82,'All 82 operations have scenes');ck(new Set(scenes.map(s=>s.kind)).size===82,'All operation scene identities unique');
const get=(rid,id)=>fs.readFileSync(path.join(V,scenes.find(s=>s.record_id==='gerion-2001-'+rid&&s.operation_id===id).file),'utf8');
for(const rid of ['silica-silanization','mpa-exchange']){ck(get(rid,'precipitate').includes('Starting dispersion')&&get(rid,'precipitate').includes('Wet precipitate'),rid+' precipitation shows source and outcome');ck(get(rid,'clear').includes('Retain supernatant'),rid+' final fraction supernatant');}
ck(get('mpa-exchange','collect').includes('Retain pellet'),'MPA early pellet retained');
ck(get('mpa-exchange','dissolve').includes('Dried precipitate')&&get('mpa-exchange','dissolve').includes('Aqueous dispersion'),'MPA dry-to-aqueous distinction');
ck(get('silica-silanization','optional-filter').includes('0.22 mm'),'Optional filter printed mm conflict preserved');
ck(get('silica-silanization','clear').includes('branches are alternatives'),'Alternative workup branch acknowledged');
ck(get('hplc-acquisition','inspect-fractions').includes('Inspect each collected fraction separately'),'HPLC all fractions inspected');
ck(get('silica-silanization','column').includes('Only the fluorescent fraction is retained'),'Preparative column retains fluorescent fraction');
for(const [rid,id] of [['tem-acquisition','image'],['eels-acquisition','measure']]){const svg=get(rid,id);ck(svg.includes('Electron source')&&svg.includes('Dried specimen'),rid+' electron optics and grid specimen');ck(!svg.includes('>Specimen</text>'),rid+' no optical cuvette');}
ck(get('eels-acquisition','measure').includes('Energy-loss'),'EELS analyzer present');
ck(get('gel-salt-stability','incubate').includes('Incubate before loading'),'Salt incubation precedes gel');
ck(get('ellman-assay','prepare').includes('Matched blank'),'Ellman paired specimens separate');
ck(get('buffer-exchange','exchange').includes('alternatives, not three sequential'),'Buffer alternatives distinguished');
ck(get('cw-photostability','record').includes('0–4000 s'),'Photostability plot/time discrepancy retained');
for(const s of scenes.filter(s=>s.record_id==='gerion-2001-silica-silanization')){
 ck(get('silica-silanization',s.operation_id).includes('>N₂</text>')===(s.environment?.value==='Nitrogen'),s.operation_id+' nitrogen inlet matches selected reported atmosphere');
}
ck(buildGerion2001Scene({id:'x'}, {record_id:'other',sources:[]})===null,'Other papers excluded');
const out={module:'gerion2001-protocol.mjs',module_sha256:sha(fs.readFileSync(path.join(V,'gerion2001-protocol.mjs'))),record_count:28,operation_count:scenes.length,checks,scenes};
fs.writeFileSync(path.join(V,'scene-manifest.json'),JSON.stringify(out,null,2));
console.log(JSON.stringify({operation_count:scenes.length,checks:checks.length,module_sha256:out.module_sha256}));
