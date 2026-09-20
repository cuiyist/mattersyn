import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const o=path.dirname(fileURLToPath(import.meta.url));
const modulePath='[local path redacted]';
const {chemicalEntry}=await import(pathToFileURL(modulePath));
const read=n=>JSON.parse(fs.readFileSync(path.join(o,n),'utf8'));
const registry=read('registry-additions.json'),bindings=read('bindings-proposal.json');
const original=JSON.stringify(bindings),entries=new Map(registry.entries.map(e=>[e.id,e]));
let checks=0;
for(const [rid,map] of Object.entries(bindings.recordBindings)) for(const [mid,eid] of Object.entries(map)) {
 const before=chemicalEntry({entries,bindings},rid,mid);
 assert.equal(before,entries.get(eid));checks++;
 const simulated=structuredClone(bindings);simulated.bindingNotes[rid][mid].binding_approved=true;
 const after=chemicalEntry({entries,bindings:simulated},rid,mid),note=bindings.bindingNotes[rid][mid];
 assert.equal(after.caption,note.viewOverrides.caption);checks++;
 assert.equal(after.sourceBindingCaption,note.viewOverrides.caption);checks++;
 assert.equal(after.name,note.viewOverrides.name);checks++;
 assert.deepEqual(after.limitations,note.viewOverrides.limitations);checks++;
 assert.equal(after.model3dPath,entries.get(eid).model3dPath);checks++;
 assert.equal(after.formula,entries.get(eid).formula);checks++;
 assert.equal(after.svgPath,entries.get(eid).svgPath);checks++;
}
assert.equal(JSON.stringify(bindings),original);checks++;
assert.equal(chemicalEntry({entries,bindings},'unknown','missing'),undefined);checks++;
const report={status:'passed',author:'/root/backlog_eta',check_count:checks,
 module_path:modulePath,module_sha256:crypto.createHash('sha256').update(fs.readFileSync(modulePath)).digest('hex'),
 scope:'Actual chemicalEntry function exercised for all 64 proposed slots. False gates return unmodified base entries; in-memory true-gate simulation applies only the permitted display overrides. The saved bindings remain unapproved. This is not browser, publication or independent scientific approval.',
 saved_binding_approval_flags_changed:false,browser_validation:'not_claimed'};
fs.writeFileSync(path.join(o,'viewer-contract-validation.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,checks}));
