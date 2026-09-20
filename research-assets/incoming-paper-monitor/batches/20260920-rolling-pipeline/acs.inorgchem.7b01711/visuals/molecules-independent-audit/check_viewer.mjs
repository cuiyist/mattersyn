import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import crypto from 'node:crypto';
const A=path.dirname(fileURLToPath(import.meta.url)),M=path.join(A,'../molecules');
const modulePath='[local path redacted]';
const {chemicalEntry}=await import(pathToFileURL(modulePath).href);
const read=n=>JSON.parse(fs.readFileSync(path.join(M,n),'utf8'));
const entries=read('registry-additions.json').entries,bindings=read('bindings-proposal.json');
const data={entries:new Map(entries.map(e=>[e.id,e])),bindings};
const initial=JSON.stringify(data.bindings),checks=[];
function check(v,s){checks.push({check:s,passed:!!v});}
for(const slot of read('material-slot-map.json').slots){
 const rid=slot.record_id,mid=slot.material_id,e=data.entries.get(slot.registry_id);
 check(chemicalEntry(data,rid,mid)===e,`${rid}/${mid}: unapproved notes do not alter reference`);
 const projection=structuredClone(bindings),note=projection.bindingNotes[rid][mid];
 note.binding_approved=true;
 // This temporary in-memory projection tests the renderer whitelist; it does not approve candidate data.
 note.viewOverrides.model3dPath='invalid-injected-model';note.viewOverrides.formula='invalid-injected-formula';
 const scoped=chemicalEntry({...data,bindings:projection},rid,mid);
 for(const k of ['name','caption','limitations'])check(JSON.stringify(scoped[k])===JSON.stringify(slot.viewOverrides[k]),`${rid}/${mid}: scoped ${k}`);
 check(scoped.sourceBindingCaption===slot.viewOverrides.caption,`${rid}/${mid}: source caption retained`);
 check(scoped.model3dPath===e.model3dPath&&scoped.formula===e.formula,`${rid}/${mid}: model and identity protected`);
 check(JSON.stringify(e)===JSON.stringify(data.entries.get(slot.registry_id)),`${rid}/${mid}: shared entry not mutated`);
 check(chemicalEntry(data,'unbound-record',mid)===undefined,`${rid}/${mid}: absent record rejected`);
 check(chemicalEntry(data,rid,'unbound-material')===undefined,`${rid}/${mid}: absent slot rejected`);
}
check(JSON.stringify(data.bindings)===initial,'frozen candidate data unchanged');
const result={status:checks.every(c=>c.passed)?'passed':'findings',check_count:checks.length,failures:checks.filter(c=>!c.passed),scope:'Actual installed chemicalEntry pure function, using a temporary in-memory approval projection only; no DOM/browser approval or file promotion.',module_sha256:crypto.createHash('sha256').update(fs.readFileSync(modulePath)).digest('hex'),module_path:modulePath};
fs.writeFileSync(path.join(A,'viewer-function-checks.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
