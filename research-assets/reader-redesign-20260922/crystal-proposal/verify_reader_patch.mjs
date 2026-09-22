import fs from 'node:fs';
import assert from 'node:assert/strict';
import {scopeKind,referenceCellVectors,referencesForSample,referenceSampleChoices} from './reader-selection-helpers.testable.mjs';
const root=new URL('./',import.meta.url),site=new URL('[local path redacted]');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const additions=read(new URL('registry-additions.json',root)).entries;
const existing=read(new URL('assets/crystal-references/registry.json',site)).entries;
const scoped=additions.filter(x=>x.formula==='CsMnCl3');
const r=read(new URL('data/records/matuhina-2023-hot-injection-series.json',site));
const choices=referenceSampleChoices(scoped,r);
assert.equal(choices[0].sample_id,'nc150');
assert.equal(choices[0].phase.value,'cubic');
assert.equal(referencesForSample(scoped,'nc150').length,0);
for(const id of ['nc180-07','nc180-05','nc180-035','nc200'])assert.equal(referencesForSample(scoped,id).length,1);
assert.equal(referencesForSample(scoped,undefined).length,0);
assert.equal(scopeKind(additions.find(x=>x.formula==='FAPbI3')),'Computed reference');
assert.equal(scopeKind(existing.find(x=>x.id==='littau-1993-si-diamond-ideal-reference')),'Constructed reference');
assert.equal(scopeKind(additions.find(x=>x.formula==='Ag')),'Bulk reference');
// Legacy IDs are source-context annotations, not hard sample eligibility.
const inp=existing.find(x=>x.id==='inp-zinc-blende');
assert.equal(referencesForSample([inp],'unrelated-recipe-product').length,1);
assert.deepEqual(referenceSampleChoices([inp],r),[]);
let models=0;
for(const [entries,base] of [[additions,new URL('assets/crystal-references/',root)],[existing,new URL('assets/crystal-references/',site)]])for(const entry of entries){
 const model=read(new URL(entry.modelPath,base));
 assert.deepEqual(referenceCellVectors(model),model.cellVectors);
 models++;
}
const hex=referenceCellVectors({cell:{a:4,b:4,c:6,alpha:90,beta:90,gamma:120}});
assert.ok(Math.abs(hex[1][0]+2)<1e-10);
assert.ok(Math.abs(hex[1][1]-Math.sqrt(12))<1e-10);
assert.throws(()=>referenceCellVectors({cell:{a:1,b:1,c:1,alpha:90,beta:90,gamma:0}}));
assert.throws(()=>referenceCellVectors({cellVectors:[[0,0,0],[0,0,0],[0,0,0]]}));
console.log(JSON.stringify({status:'pass',modelsChecked:models,contextChoices:choices.map(x=>x.sample_id),checks:['nc150 cubic remains without reference','four rhombohedral contexts retain comparison','legacy context annotations do not become hard gates','computed/constructed/bulk labels distinct','cell vectors unchanged for all current/proposed models','hexagonal cell fallback and singular-cell rejection']},null,2));
