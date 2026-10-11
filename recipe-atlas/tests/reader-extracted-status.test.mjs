import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {defaultCrystalReferences} from '../static/crystal-defaults.mjs';

class Element{
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.className='';this._text='';}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=[...children];this._text='';}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(child=>child.textContent||'').join(' ');}
}
const priorDocument=globalThis.document;
globalThis.document={body:{dataset:{}},createElement:tag=>new Element(tag)};
const {methodBadges,interpretationFallback}=await import('../static/reader-app.mjs');
globalThis.document=priorDocument;
const record=status=>({record_id:'fixture',method:'synthetic_method',sources:[{year:2020,authors:'Fixture Author'}],quality:{review_status:status}});
const withDOM=callback=>{
 const prior=globalThis.document;
 globalThis.document={createElement:tag=>new Element(tag)};
 try{return callback();}finally{globalThis.document=prior;}
};

test('neutral method header retains citation and canonical extraction status',()=>withDOM(()=>{
 const r=record('source_extracted'),before=JSON.stringify(r);
 const host=new Element('div');host.textContent='Stale extraction notice';
 host.replaceChildren(methodBadges(r,{method_label:'Source synthesis'}));
 assert.match(host.textContent,/Source synthesis/);
 assert.match(host.textContent,/2020 · Fixture Author et al\./);
 assert.doesNotMatch(host.textContent,/machine extracted|source extracted|not independently audited/i);
 assert.equal(host.children[0].children.length,2);
 assert.equal(JSON.stringify(r),before);
}));
test('switching methods uses neutral badges without claiming a review',()=>withDOM(()=>{
 const host=new Element('div');
 for(const status of ['source_extracted','source_reviewed','pending',undefined]){
  const r=record(status),before=JSON.stringify(r);host.replaceChildren(methodBadges(r));
  assert.equal(host.children[0].children.length,2);
  assert.doesNotMatch(host.textContent,/extracted|audited|reviewed/i);
  assert.equal(JSON.stringify(r),before);
 }
}));
test('metadata never overrides canonical status or creates a review badge',()=>withDOM(()=>{
 const r=record('source_extracted');r.review_status='source_reviewed';
 assert.doesNotMatch(methodBadges(r).textContent,/reviewed|audited|extracted/i);
 assert.equal(r.quality.review_status,'source_extracted');
}));

const entries=[{id:'core',formula:'CdSe',name:'Bulk wurtzite CdSe reference · core comparison',spaceGroupNumber:186,modelPath:'models/core.json',cifPath:'core.cif',referenceOnly:true},
 {id:'shell',formula:'ZnS',name:'Bulk ZnS reference · shell comparison',spaceGroupNumber:216,modelPath:'models/shell.json',cifPath:'shell.cif',referenceOnly:true}];
const componentRecord=(status,architecture)=>({...record(status),material:{formula:'CdSe–ZnS',components:['CdSe','ZnS'],architecture},products:[]});
test('extracted component default titles are neutral for every architecture without altering library objects',()=>{
 for(const architecture of [undefined,'unresolved','single_material','core_shell','core_multishell','composite']){
  const r=componentRecord('source_extracted',architecture),before=JSON.stringify({r,entries});
  const refs=defaultCrystalReferences(entries,r);
  assert.equal(refs.length,2);
  assert.deepEqual(refs.map(ref=>ref.name),['Bulk wurtzite CdSe reference','Bulk ZnS reference']);
  assert.ok(refs.every(ref=>ref.roleByRecord.fixture==='Component reference'));
  assert.deepEqual(refs.map(({id,formula,spaceGroupNumber,modelPath,cifPath,referenceOnly})=>({id,formula,spaceGroupNumber,modelPath,cifPath,referenceOnly})),
   entries.map(({id,formula,spaceGroupNumber,modelPath,cifPath,referenceOnly})=>({id,formula,spaceGroupNumber,modelPath,cifPath,referenceOnly})));
  assert.equal(JSON.stringify({r,entries}),before);
 }
});
test('audited and other non-extracted component default titles retain their core and shell suffixes',()=>{
 for(const status of ['source_reviewed','audited','pending',undefined]){
  for(const architecture of [undefined,'unresolved','core_shell','core_multishell','composite']){
   const r=componentRecord(status,architecture),before=JSON.stringify({r,entries});
   const refs=defaultCrystalReferences(entries,r);
   assert.deepEqual(refs.map(ref=>ref.name),entries.map(ref=>ref.name));
   assert.equal(JSON.stringify({r,entries}),before);
  }
 }
});


test('source-extracted interpretation fallback makes no implicit review claim',()=>{
 const r=record('source_extracted'),before=JSON.stringify(r);
 assert.equal(interpretationFallback(r),'Further interpretation is available in the original source.');
 assert.doesNotMatch(interpretationFallback(r),/review|audit|extract/i);
 assert.equal(JSON.stringify(r),before);
});
test('audited interpretation fallback remains unchanged',()=>{
 for(const status of ['source_reviewed','audited',undefined]){
  const r=record(status),before=JSON.stringify(r);
  assert.equal(interpretationFallback(r),'Interpretation is available with the original source and complete review.');
  assert.equal(JSON.stringify(r),before);
 }
});
