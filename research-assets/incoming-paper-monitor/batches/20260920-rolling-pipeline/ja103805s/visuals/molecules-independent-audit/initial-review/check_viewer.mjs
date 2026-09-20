import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {chemicalEntry} from '[local path redacted]';
const out=new URL('./',import.meta.url),input=new URL('../molecules/',out);
const read=name=>JSON.parse(fs.readFileSync(new URL(name,input),'utf8'));
const registry=read('registry-additions.json'),bindings=read('bindings-proposal.json'),slots=read('material-slot-map.json'),stocks=read('stock-component-map.json');
const entries=new Map(registry.entries.map(e=>[e.id,e])),data={registry,bindings,entries};
const before=JSON.stringify({registry,bindings});let checks=0;
const equal=(a,b)=>{assert.deepEqual(a,b);checks++;};
for(const s of slots){
 const actual=chemicalEntry(data,s.record_id,s.material_id);
 equal(actual.id,s.registry_id);equal(actual,entries.get(s.registry_id));equal(actual.model3dPath!==null,s.material_id==='species9');
 const approved=structuredClone(bindings),note=approved.bindingNotes[s.record_id][s.material_id];
 note.binding_approved=true;
 // A disposable injection verifies identity/model fields cannot be rewritten by scoped presentation metadata.
 note.viewOverrides.id='invalid-cross-material-id';note.viewOverrides.model3dPath='invalid-model.json';note.viewOverrides.formula='invalid-formula';
 const scoped=chemicalEntry({...data,bindings:approved},s.record_id,s.material_id);
 equal(scoped.id,actual.id);equal(scoped.model3dPath,actual.model3dPath);equal(scoped.formula,actual.formula);
 for(const key of ['name','caption','limitations'])equal(scoped[key],s.viewOverrides[key]);
 equal(scoped.sourceBindingCaption,s.viewOverrides.caption);
}
for(const s of stocks)for(const c of s.components)equal(chemicalEntry(data,s.record_id,c.material_id).id,c.registry_id);
equal(chemicalEntry(data,'foreign-record','species9'),undefined);equal(chemicalEntry(data,'evans-2010-pbse-qd','species9'),undefined);
equal(JSON.stringify({registry,bindings}),before);
const site='[local path redacted]';
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const report={status:'passed',checks,reviewer:'/root/peng1998_reader_assets',current_viewer_sha256:sha(site),scope:'Actual current chemicalEntry function, all private slots/components, false-gate behavior, disposable approved-caption overlays and forbidden identity/model overrides. This is not a browser/DOM/rotation test.',bound_files:{[site]:sha(site)}};
fs.writeFileSync(new URL('viewer-function-audit.json',out),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
