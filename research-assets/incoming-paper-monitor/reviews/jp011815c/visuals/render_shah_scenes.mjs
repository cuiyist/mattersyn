import {readFileSync,writeFileSync,readdirSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';import {dirname,resolve} from 'node:path';import {createHash} from 'node:crypto';
import {buildShah2001Scene} from './shah2001-protocol.mjs';
const V=dirname(fileURLToPath(import.meta.url)),B=resolve(V,'..');mkdirSync(resolve(V,'scene-svg'),{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex'),checks=[],scenes=[];function check(v,name){checks.push({check:name,passed:Boolean(v)});}
const rows=[['a',1.8,14.9,60],['b',2.2,10.3,90],['c',2.9,8.2,70],['d',3.4,6,80],['e',3.4,5.7,90],['f',3.4,6,100],['g',3.6,5.8,70],['h',3.9,6.4,70],['i',4.9,11,70]];
for(const name of readdirSync(resolve(B,'canonical-drafts')).filter(x=>x.endsWith('.json')).sort()){
 const bytes=readFileSync(resolve(B,'canonical-drafts',name)),r=JSON.parse(bytes);
 for(const o of r.operations){const a=buildShah2001Scene(o,r);check(a?.svg,r.record_id+'/'+o.id+' has a source-specific scene');if(!a)continue;check(!/undefined|NaN|null/.test(a.svg),r.record_id+'/'+o.id+' has no missing-value artifacts');
 const file='scene-svg/'+r.record_id+'--'+o.id+'.svg';writeFileSync(resolve(V,file),a.svg);scenes.push({record_id:r.record_id,operation_id:o.id,file,source_record_sha256:sha(bytes),sha256:sha(a.svg),evidence:o.evidence,parameters:o.parameters});
 }
}
const map=Object.fromEntries(scenes.map(x=>[x.record_id+'/'+x.operation_id,readFileSync(resolve(V,x.file),'utf8').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ')]));
for(const [id,c,ratio,t]of rows){const key='shah-2001-ag-'+id;check(map[key+'/load'].includes(c+' mM'),id+' precursor concentration exact');check(map[key+'/inject'].includes(ratio+' mol/mol'),id+' ligand ratio exact');check(map[key+'/condition'].includes(t+' °C')&&map[key+'/condition'].includes('276 bar'),id+' paired reaction T/P exact');check(map[key+'/fill'].includes('138 bar')&&map[key+'/fill'].includes('20 °C'),id+' fill T/P distinct');check(map[key+'/hold'].includes('3 h'),id+' common hold retained');check(!map[key+'/inject'].includes('6.22 mg'),id+' no typical hydrogen mass transferred');}
for(const [metal,c,ratio]of [['ir',3.3,7.6],['pt',3.6,6.6]]){const key='shah-2001-'+metal;check(map[key+'/load'].includes(c+' mM'),metal+' concentration exact');check(map[key+'/inject'].includes(ratio+' mol/mol'),metal+' ratio exact');check(map[key+'/condition'].includes('80 °C')&&map[key+'/condition'].includes('276 bar'),metal+' reported T/P exact');check(map[key+'/fill'].includes('inherited'),metal+' fill inheritance disclosed');check(map[key+'/hold'].includes('inherited'),metal+' hold inheritance disclosed');check(!map[key+'/inject'].includes('6.22 mg'),metal+' no Ag hydrogen charge copied');}
for(const [k,words] of [
 ['ag-typical-framework/load',['5.9–16 mg']],['ag-typical-framework/fill',['14–18 mL','27 mL','138 bar','20 °C']],['ag-typical-framework/inject',['162–324 mg','6.22 mg','100 / 200 µL','800 µL']],
 ['recovery/cool',['room temperature']],['recovery/vent',['CO₂ vapor + H₂','not an isolated dry powder']],['recovery/precipitate',['Heptane','supernatant']],['recovery/redisperse',['Acetone','alternatives']],
 ['tem-eds/image',['200 kV','1.7 Å','not a measured sample lattice spacing']],['tem-eds/size',['≥400 particles']],['tem-eds/eds',['Oxford Link ISIS','Ag-specific']],
 ['growth-analysis/volume',['Assume spherical particles']],['growth-analysis/normalize',['ψ₁(η)']],['growth-analysis/moments',['µ₁ = r₃ / rₕ','µ₃ = r₁ / r₃']],['growth-analysis/cumulative',['ψ₂(η)','unit sticking probability']]
])for(const word of words)check(map['shah-2001-'+k]?.includes(word),k+' source value/qualifier '+word);
check(scenes.length===74,'Every current operation covered once');check(buildShah2001Scene({id:'load'},{record_id:'other',sources:[{doi:'10.1021/jp011815c'}]})===null,'Unrelated record rejected');
writeFileSync(resolve(V,'scene-manifest.json'),JSON.stringify({module_sha256:sha(readFileSync(resolve(V,'shah2001-protocol.mjs'))),operation_count:scenes.length,scenes},null,2)+'\n');
writeFileSync(resolve(V,'scene-validation.json'),JSON.stringify({status:checks.every(x=>x.passed)?'passed':'failed',checks,passed:checks.filter(x=>x.passed).length,check_count:checks.length},null,2)+'\n');
console.log(JSON.stringify({scenes:scenes.length,checks:checks.length,failed:checks.filter(x=>!x.passed)}));if(checks.some(x=>!x.passed))process.exitCode=1;
