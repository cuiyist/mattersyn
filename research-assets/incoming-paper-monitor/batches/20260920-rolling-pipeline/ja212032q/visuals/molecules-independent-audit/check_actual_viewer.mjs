import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath,pathToFileURL} from 'node:url';
const A=path.dirname(fileURLToPath(import.meta.url)), M=path.join(A,'../molecules');
const mod='[local path redacted]';
const {chemicalEntry}=await import(pathToFileURL(mod));
const read=n=>JSON.parse(fs.readFileSync(path.join(M,n),'utf8'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const effective=process.argv.includes('--effective-v2');
const final=process.argv.includes('--effective-v3');
const bindingFile=final?'metadata-correction-v3/bindings-proposal.json':effective?'canonical-v2-rebind/bindings-proposal.json':'bindings-proposal.json';
const registryFile=final?'metadata-correction-v3/registry-additions.json':'registry-additions.json';
const reg=read(registryFile), bindings=read(bindingFile);
const entries=new Map(reg.entries.map(e=>[e.id,e])), baseline=JSON.stringify(bindings),entryBaseline=JSON.stringify([...entries]);
let checks=0; const test=(label,f)=>{f();checks++;};
for(const [rid,mapping] of Object.entries(bindings.recordBindings))for(const [mid,eid]of Object.entries(mapping)){
 const label=rid+'/'+mid,e=entries.get(eid),note=bindings.bindingNotes[rid][mid];
 test('false gate '+label,()=>assert.equal(chemicalEntry({entries,bindings},rid,mid),e));
 const b=structuredClone(bindings);b.bindingNotes[rid][mid].binding_approved=true;
 const got=chemicalEntry({entries,bindings:b},rid,mid);
 for(const key of ['name','caption','limitations'])test('source override '+label+key,()=>assert.deepEqual(got[key],note.viewOverrides[key]));
 test('visible source caption '+label,()=>assert.equal(got.sourceBindingCaption,note.viewOverrides.caption));
 for(const key of ['id','formula','svgPath','model2dPath','model3dPath','functionalGroups','provenance'])test('identity immutable '+label+key,()=>assert.deepEqual(got[key],e[key]));
 // A forbidden override must not replace geometry, identity or source provenance.
 Object.assign(b.bindingNotes[rid][mid].viewOverrides,{formula:'HACK',model3dPath:'wrong.json',id:'wrong',provenance:{wrong:true}});
 const denied=chemicalEntry({entries,bindings:b},rid,mid);
 for(const key of ['formula','model3dPath','id','provenance'])test('whitelist '+label+key,()=>assert.deepEqual(denied[key],e[key]));
 test('unknown material '+label,()=>assert.equal(chemicalEntry({entries,bindings},rid,'unknown-material'),undefined));
}
test('unknown record rejected',()=>assert.equal(chemicalEntry({entries,bindings},'unknown-record','ola'),undefined));
test('saved gates unchanged',()=>assert.equal(JSON.stringify(bindings),baseline));
test('registry unchanged',()=>assert.equal(JSON.stringify([...entries]),entryBaseline));
const report={schema:'mattersyn.independent_chemical_viewer_function_audit/1',status:'passed',auditor:'/root/peng1998_reader_assets',check_count:checks,
 scope:'Executed the actual shared chemicalEntry pure function for all88 proposed material slots, false and simulated true gates, scientific-field override rejection and unknown IDs. No mounted-browser or publication claim.',
 module_path:mod,module_sha256:sha(mod),bindings_sha256:sha(path.join(M,bindingFile)),registry_sha256:sha(path.join(M,registryFile)),
 no_author_or_site_files_changed:true};
fs.writeFileSync(path.join(A,final?'actual-viewer-checks-v3.json':effective?'actual-viewer-checks-v2.json':'actual-viewer-checks-v1.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,checks}));
