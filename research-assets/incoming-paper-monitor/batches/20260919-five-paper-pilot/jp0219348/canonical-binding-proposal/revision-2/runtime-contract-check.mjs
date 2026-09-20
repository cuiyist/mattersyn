import fs from 'node:fs';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const p="C:\\Users\\jiacu\\Desktop\\mattersyn\\research-assets\\incoming-paper-monitor\\batches\\20260919-five-paper-pilot\\jp0219348\\canonical-binding-proposal\\revision-2";
const read=n=>JSON.parse(fs.readFileSync(p+'/'+n,'utf8'));
const {chemicalEntry}=await import(pathToFileURL("C:\\Users\\jiacu\\Desktop\\mattersyn\\recipe-atlas\\dist\\chemical-viewer.mjs").href);
const bindings=read('bindings-proposal.json');
const maps=read('material-slot-map.json').bindings;
const entries=new Map();
for(const x of maps){const file="C:\\Users\\jiacu\\Desktop\\mattersyn\\research-assets\\incoming-paper-monitor\\batches\\20260919-five-paper-pilot\\jp0219348"+'/'+x.reference.file;const all=JSON.parse(fs.readFileSync(file,'utf8'));entries.set(x.registry_id,all.entries[Number(x.reference.json_pointer.split('/').at(-1))]);}
let checks=0;
for(const x of maps){const base=entries.get(x.registry_id);assert.equal(chemicalEntry({entries,bindings},x.record_id,x.material_id),base);checks++;}
// Approval below exists only in a transient test fixture. The authored files stay false.
const fixture=structuredClone(bindings);
for(const x of maps){const note=fixture.bindingNotes[x.record_id][x.material_id];note.binding_approved=true;note.viewOverrides.formula='PROHIBITED_TEST_OVERRIDE';const scoped=chemicalEntry({entries,bindings:fixture},x.record_id,x.material_id);assert.equal(scoped.name,x.viewOverrides.name);assert.equal(scoped.caption,x.viewOverrides.caption);assert.equal(scoped.sourceBindingCaption,x.viewOverrides.caption);assert.deepEqual(scoped.limitations,x.viewOverrides.limitations);assert.equal(scoped.formula,entries.get(x.registry_id).formula);assert.equal(scoped.model3dPath,entries.get(x.registry_id).model3dPath);checks+=6;}
const feed=chemicalEntry({entries,bindings:fixture},'heo-2003-in66-route','feed-water');const wash=chemicalEntry({entries,bindings:fixture},'heo-2003-in66-route','wash-water');assert.notEqual(feed.caption,wash.caption);assert.ok(feed.caption.includes('grade is unreported'));assert.ok(wash.caption.includes('deionized'));checks+=3;
console.log(JSON.stringify({status:'passed',checks,scope:'Actual chemicalEntry function; pending and hypothetical approved in-memory fixtures only. No DOM, browser, asset science or public integration audit.'}));
