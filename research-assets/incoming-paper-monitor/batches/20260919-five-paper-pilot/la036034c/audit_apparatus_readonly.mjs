import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const B=path.dirname(fileURLToPath(import.meta.url));
const A=path.join(B,'visuals/apparatus');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const checks=[],bound={},coverage=[];
const check=(id,ok,detail)=>checks.push({id,passed:!!ok,...(detail===undefined?{}:{detail})});
const bind=p=>{bound[p]=sha(p);return bound[p];};
const moduleFile=path.join(A,'nagasaki2004-protocol.mjs');
const moduleText=fs.readFileSync(moduleFile,'utf8');
const {buildNagasaki2004Scene,createNagasaki2004Art,nagasaki2004OperationIds}=await import(pathToFileURL(moduleFile));
const manifest=read(path.join(A,'scene-manifest.json'));
bind(moduleFile);bind(path.join(A,'scene-manifest.json'));
check('module exact manifest hash',sha(moduleFile)===manifest.module_sha256);
const cfgSections=new Map([...moduleText.matchAll(/\n '([^']+)':\{([\s\S]*?)(?=\r?\n '|\r?\n\};)/g)].map(m=>[m[1],m[2]]));
const records=fs.readdirSync(path.join(B,'canonical-drafts')).filter(f=>f.endsWith('.json')).map(f=>{const p=path.join(B,'canonical-drafts',f);bind(p);return [p,read(p)];});
const independentQuantity=q=>{
 const units={degC:'°C',degree:'°',micromol:'µmol'};
 let v=q.value;
 if(v===null||v===undefined){if(q.minimum!=null||q.maximum!=null)v=`${q.minimum??'…'}–${q.maximum??'…'}`;else return 'Not reported';}
 return `${q.approximate?'≈ ':''}${v}${q.unit?' '+(units[q.unit]||q.unit):''}`;
};
globalThis.document={createElement:tag=>({tagName:tag,dataset:{},style:{},innerHTML:'',className:''})};
const encountered=[];
for(const [p,r] of records){
 for(const [index,o] of r.operations.entries()){
  const id=r.record_id+'::'+o.id;encountered.push(o.id);
  const entries=manifest.scenes.filter(s=>s.record_id===r.record_id&&s.operation_id===o.id);
  check(id+' unique manifest operation',entries.length===1);if(entries.length!==1)continue;
  const m=entries[0],s=buildNagasaki2004Scene(o,r);
  check(id+' actual canonical operation copy',same(m.operation,o));
  check(id+' actual canonical file hash',m.canonical_sha256===sha(p));
  check(id+' selected scene exists',!!s);if(!s)continue;
  check(id+' caption exact generation',s.caption===m.caption);
  check(id+' condition rows exact generation',same(s.conditionRows,m.condition_rows));
  check(id+' selected kind exact',s.kind===m.scene_kind);
  const svg=path.join(A,m.svg_file);bind(svg);
  check(id+' SVG exact generation',fs.readFileSync(svg,'utf8')===s.svg);
  check(id+' SVG manifest hash',sha(svg)===m.svg_sha256);
  check(id+' no nonfinite SVG coordinates',!/(?:NaN|Infinity|undefined)/.test(s.svg));
  const node=createNagasaki2004Art(o,r);
  check(id+' mounted SVG exact',node?.innerHTML===s.svg);
  check(id+' mounted scope',node?.dataset?.scene==='nagasaki2004-'+s.kind&&node?.className.includes('protocol-art-nagasaki2004'));
  const qLinks=[...(cfgSections.get(o.id)||'').matchAll(/Q\('([^']*)','([^']*)'\)/g)].map(m=>({label:m[1],parameter:m[2]}));
  for(const link of qLinks){
   check(id+' quantity parameter exists '+link.parameter,!!o.parameters[link.parameter]);
   const row=s.conditionRows.find(row=>row.label===link.label);
   check(id+' quantity value '+link.parameter,!!row&&row.value===independentQuantity(o.parameters[link.parameter]));
  }
  const explicit=Object.entries(o.parameters).filter(([k,q])=>q&&typeof q==='object'&&(q.value!==null&&q.value!==undefined||q.minimum!=null||q.maximum!=null)).map(([k])=>k);
  const exceptional=o.id==='hydrolyze-acetal'?['acetic_acid_relative_volume_parts','water_relative_volume_parts']:[];
  const omitted=explicit.filter(k=>!qLinks.some(q=>q.parameter===k)&&!exceptional.includes(k));
  check(id+' all reported parameter quantities exposed',omitted.length===0,omitted);
  if(o.id==='hydrolyze-acetal')check(id+' ratio is source 10:1 v/v',o.parameters.acetic_acid_relative_volume_parts.value===10&&o.parameters.water_relative_volume_parts.value===1&&s.conditionRows.some(row=>row.value==='10:1 v/v'));
  const png=path.join(A,'review',s.kind+'.png');check(id+' actual preview exists',fs.existsSync(png));if(fs.existsSync(png))bind(png);
  coverage.push({record_id:r.record_id,operation_id:o.id,operation_pointer:'/operations/'+index,scene_kind:s.kind,canonical_sha256:sha(p),svg_sha256:sha(svg),quantity_links:qLinks,non_quantity_context_parameters:Object.keys(o.parameters).filter(k=>!explicit.includes(k)),caption:s.caption,condition_rows:s.conditionRows});
 }
}
check('exact 36 canonical operations',encountered.length===36);
check('exact unique configuration universe',new Set(encountered).size===36&&nagasaki2004OperationIds.length===36&&nagasaki2004OperationIds.every(x=>encountered.includes(x)));
check('exact manifest universe',manifest.scenes.length===36);
check('different source rejected',buildNagasaki2004Scene({id:encountered[0]},{lineage:{source_group:'gu2004'},record_id:'gu-2004-test'})===null);
check('different record prefix rejected',buildNagasaki2004Scene({id:encountered[0]},{lineage:{source_group:'nagasaki2004'},record_id:'other-test'})===null);
check('unknown operation rejected',buildNagasaki2004Scene({id:'not-an-operation'},{lineage:{source_group:'nagasaki2004'},record_id:'nagasaki-2004-test'})===null);
for(const f of ['source-facts.json','source-inventory.json','page-coverage.json','canonical-record-manifest.json','canonical-records-audit.json','reader-source-audit.json'])bind(path.join(B,f));
for(const f of ['render-validation.json','render-nagasaki-scenes.mjs','render-nagasaki-previews.py','freeze-nagasaki-apparatus.py'])bind(path.join(A,f));
for(const f of fs.readdirSync(path.join(A,'review')).filter(x=>/^contact-\d+\.png$/.test(x)))bind(path.join(A,'review',f));
const authorFile=path.join(A,'author-visual-check.json');
if(fs.existsSync(authorFile)){
 const author=read(authorFile);bind(authorFile);
 for(const [p,h] of Object.entries(author.bound_files||{}))check('author current binding '+p,fs.existsSync(p)&&sha(p)===h);
}
const failures=checks.filter(x=>!x.passed);
const out={schema:'mattersyn.independent-apparatus-runtime-check.v1',source_id:'nagasaki2004',auditor:'/root/peng1998_reader_assets',created_at:new Date().toISOString(),status:failures.length?'findings':'passed',scope:'Read-only actual module, mounted API with DOM stub, exact canonical/SVG/PNG bindings; this does not assert a live browser or a scientific visual audit.',counts:{records:records.length,scenes:encountered.length,checks:checks.length,failures:failures.length},checks,failures,coverage,bound_files:bound,helper_sha256:sha(fileURLToPath(import.meta.url))};
fs.writeFileSync(path.join(B,'apparatus-independent-runtime-check.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({status:out.status,counts:out.counts,failures},null,2));
