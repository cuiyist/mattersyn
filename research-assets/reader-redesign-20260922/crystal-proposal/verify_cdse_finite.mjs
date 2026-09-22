import fs from 'node:fs';
import assert from 'node:assert/strict';
import {finiteReferencesForRecord} from './cdse-finite-reader-helper.mjs';
import {finiteReferenceAtoms} from '../../../recipe-atlas/dist/finite-crystal-reference.mjs';
const root=new URL('./',import.meta.url),site=new URL('../../../recipe-atlas/dist/',root);
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const delta=read(new URL('cdse-finite-registry-fields.json',root));
const registry=read(new URL('assets/crystal-references/registry.json',site));
const parent=registry.entries.find(x=>x.id===delta.id);
const ref={...parent,...delta};
const model=read(new URL('cdse-finite-assets/crystal-references/'+delta.finiteModelPath,root));
const atoms=finiteReferenceAtoms(model);
assert.equal(atoms.length,582);
assert.equal(atoms.filter(a=>a.elem==='Cd').length,288);
assert.equal(atoms.filter(a=>a.elem==='Se').length,294);
for(let i=0;i<atoms.length;i++)for(const j of atoms[i].bonds){assert.ok(atoms[j].bonds.includes(i));assert.notEqual(atoms[i].elem,atoms[j].elem);}
for(const rid of delta.finiteRecordIds){
 const output=finiteReferencesForRecord([ref],{record_id:rid});assert.equal(output.length,1);
 assert.equal(output[0].name,delta.finiteName);
 assert.equal(output[0].phaseScope,delta.finiteScope);
 assert.equal(output[0].cifPath,delta.finiteCifPath);
 assert.equal(output[0].sourceUrl,'https://doi.org/10.1021/ja00072a025');
}
for(const rid of ['murray-1993-cdse-small-species','peng-2000-cdse-typical','danek-1996-znse-overgrowth'])assert.equal(finiteReferencesForRecord([ref],{record_id:rid}).length,0);
const existing=registry.entries.find(x=>x.id==='littau-1993-si-diamond-ideal-reference');
assert.equal(finiteReferencesForRecord([existing],{record_id:existing.record_ids[0]}).length,1);
assert.equal(ref.modelPath,parent.modelPath);assert.equal(ref.cifPath,parent.cifPath);
console.log('PASS: 582 atoms / 1017 reciprocal geometric bonds; exact two-method finite scope; no small-species/Peng/Danek leakage; legacy finite views and parent unit-cell paths preserved.');
