import {readFileSync,writeFileSync,readdirSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {buildPeng1998Scene} from './peng1998-protocol.mjs';
const V=dirname(fileURLToPath(import.meta.url)),B=resolve(V,'..'),out=resolve(V,'scene-svg');mkdirSync(out,{recursive:true});
const hash=s=>createHash('sha256').update(s).digest('hex'),checks=[],scenes=[];
function check(v,description){checks.push({check:description,passed:Boolean(v)});}
for(const file of readdirSync(resolve(B,'canonical-drafts')).filter(f=>f.endsWith('.json')).sort()){
 const bytes=readFileSync(resolve(B,'canonical-drafts',file)),r=JSON.parse(bytes);
 for(const o of r.operations){
  const scene=buildPeng1998Scene(o,r);check(scene?.svg,r.record_id+'/'+o.id+' renders a source-specific scene');if(!scene)continue;
  check(!/NaN|undefined|null/.test(scene.svg),r.record_id+'/'+o.id+' no missing-value artifacts');
  const filename=r.record_id+'--'+o.id+'.svg';writeFileSync(resolve(out,filename),scene.svg);
  scenes.push({record_id:r.record_id,operation_id:o.id,kind:scene.kind,file:'scene-svg/'+filename,sha256:hash(scene.svg),source_record_sha256:hash(bytes),evidence:o.evidence,parameters:o.parameters});
 }
}
check(scenes.length===28,'All 28 current operations rendered');check(buildPeng1998Scene({id:'heat'},{record_id:'peng-1998-cdse-focusing',sources:[{doi:'other'}]})===null,'Unrelated DOI rejected');
const byId=Object.fromEntries(scenes.map(s=>[s.record_id+'/'+s.operation_id,readFileSync(resolve(V,s.file),'utf8')]));
for(const [id,words] of [
 ['cdse-focusing/heat',['360 °C','4 g','Flowing Ar']],
 ['cdse-focusing/injection',['2.4 mL','&lt;0.1 s','300 °C']],
 ['cdse-focusing/grow',['300 °C','190 min']],
 ['cdse-focusing/refeed',['0.8 mL','190 min','Slow injection']],
 ['inas-focusing/heat',['300 °C','2 g']],
 ['inas-focusing/injection',['1 mL','&lt;0.1 s','250 °C']],
 ['inas-focusing/recover',['250 °C','260 °C']],
 ['inas-focusing/grow',['23 min','260 °C']],
 ['inas-focusing/refeed1',['0.5 mL','23 min']],
 ['inas-focusing/continue',['260 °C','158 min']],
 ['inas-focusing/refeed2',['0.8 mL','158 min']],
 ['incl3-top-stock/heat',['260 °C','0.33 g/mL','Ar']],
 ['incl3-top-stock/store',['Drybox','unreported']],
 ['cdse-aliquot-analysis/precipitate',['0.2 mL','2 mL','Methanol']],
 ['cdse-aliquot-analysis/adjust-od',['0.09 ± 0.02']],
 ['inas-aliquot-analysis/dilute',['Toluene','does not state methanol']],
 ['pl-size-analysis/convert',['high-energy half','Equal emission efficiency']]
])for(const word of words)check(byId['peng-1998-'+id]?.includes(word),id+' displays source value/qualification '+word);
for(const op of ['heat','injection','recover','grow','refeed1','continue','refeed2'])check(!/>Ar<|Flowing Ar/.test(byId['peng-1998-inas-focusing/'+op]),'InAs '+op+' has no unreported Ar-flow diagram');
writeFileSync(resolve(V,'scene-manifest.json'),JSON.stringify({module_sha256:hash(readFileSync(resolve(V,'peng1998-protocol.mjs'))),operation_count:scenes.length,scenes},null,2)+'\n');
writeFileSync(resolve(V,'scene-validation.json'),JSON.stringify({status:checks.every(c=>c.passed)?'passed':'failed',check_count:checks.length,passed:checks.filter(c=>c.passed).length,checks},null,2)+'\n');
console.log(JSON.stringify({scenes:scenes.length,checks:checks.length,failed:checks.filter(c=>!c.passed)}));
if(checks.some(c=>!c.passed))process.exitCode=1;
