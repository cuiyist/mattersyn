import { readFileSync,writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import { chemicalEntry } from './reference-snapshots/chemical-viewer.mjs';
const dir=new URL('./',import.meta.url);
const read=n=>JSON.parse(readFileSync(new URL(n,dir),'utf8'));
const sha=n=>createHash('sha256').update(readFileSync(new URL(n,dir))).digest('hex');
const registry=read('registry-additions.json'),bindings=read('bindings-proposal.json'),slots=read('material-slot-map.json'),stocks=read('stock-component-map.json');
const data={registry,bindings,entries:new Map(registry.entries.map(e=>[e.id,e]))};
const before=JSON.stringify({registry,bindings});let checks=0;
for(const slot of slots){
 const actual=chemicalEntry(data,slot.record_id,slot.material_id);
 assert.equal(actual.id,slot.registry_id);checks++;
 assert.equal(actual,data.entries.get(slot.registry_id));checks++;
 assert.equal(slot.binding_approved,false);checks++;
 // A disposable clone tests the existing approved-overlay behavior without
 // approving, publishing or changing any proposal file.
 const cloned=structuredClone(data.bindings);
 cloned.bindingNotes[slot.record_id][slot.material_id].binding_approved=true;
 const applied=chemicalEntry({...data,bindings:cloned},slot.record_id,slot.material_id);
 for(const k of ['name','caption','limitations']){assert.deepEqual(applied[k],slot.viewOverrides[k]);checks++;}
 assert.equal(applied.id,actual.id);checks++;
}
for(const stock of stocks)for(const component of stock.components){
 assert.equal(chemicalEntry(data,stock.record_id,component.material_id).id,component.registry_id);checks++;
}
assert.equal(chemicalEntry(data,'foreign-record','dpp'),undefined);checks++;
assert.equal(chemicalEntry(data,slots[0].record_id,'unknown-material'),undefined);checks++;
assert.equal(JSON.stringify({registry,bindings}),before);checks++;
writeFileSync(new URL('viewer-contract-author-check.json',dir),JSON.stringify({status:'passed_pure_function_contract_checks',checks,source:'Retained byte-identical snapshot of current chemical-viewer.mjs; chemicalEntry imported and executed directly.',viewer_module_sha256:sha('reference-snapshots/chemical-viewer.mjs'),bindings_sha256:sha('bindings-proposal.json'),registry_sha256:sha('registry-additions.json'),slots:slots.length,stock_components:stocks.reduce((n,s)=>n+s.components.length,0),scope:'Pure lookup and approved-overlay behavior on disposable clones only. No DOM, mouse interaction, mounted 3D renderer or public website test.',actual_binding_approval:false,independent_audit:'pending'},null,2)+'\n');
console.log(JSON.stringify({checks,slots:slots.length}));
