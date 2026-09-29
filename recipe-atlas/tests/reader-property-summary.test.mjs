import test from 'node:test';
import assert from 'node:assert/strict';

// Synthetic UI fixtures only. No scientific evidence is created by these tests.
class Node {
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this._text='';}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=children;this._text='';}
 setAttribute(name,value){this.attributes[name]=String(value);}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent??String(c)).join(' ');}
 set innerHTML(_){throw Error('Unexpected HTML rendering');}
}
globalThis.document={createElement:tag=>new Node(tag),body:new Node('body')};
const {renderProperties}=await import('../static/reader-app.mjs');
const walk=n=>[n,...n.children.flatMap(c=>c instanceof Node?walk(c):[])];
const nodes=(n,tag)=>walk(n).filter(x=>x.tagName===tag);
const evidence={source_id:'synthetic-source',locator:'Synthetic main p. 2, Figure 1'};
const measurement=(overrides={})=>({id:'gap-a',sample_id:'sample-a',property:'optical_band_gap',
 technique:'Synthetic optical analysis',value:{value:3.7,unit:'eV',status:'reported',evidence:[evidence]},
 conditions:'Sample A dispersion only',evidence:[evidence],...overrides});
const record=(measurements=[measurement()])=>({record_id:'synthetic-route',lineage:{source_group:'synthetic-source'},
 products:[{sample_id:'sample-a',source_sample_label:'Sample A'}],measurements});
const figure=(overrides={})=>({id:'figure-1',source_id:'synthetic-source',title:'Synthetic optical figure',
 category:'property',public_asset:'assets/synthetic-property.png',summary:'Synthetic software figure.',...overrides});
const host=()=>new Node('section');

test('property image and numeric summary appear together without mirrored fact duplicates',()=>{
 const h=host(),r=record(),p={propertyFacts:[{label:'Optical band gap',value:'3.7 eV'}]},before=JSON.stringify({r,p});
 assert.equal(renderProperties(h,[figure()],r,p),1);
 assert.equal(nodes(h,'img').length,1);
 assert.deepEqual(nodes(h,'dd').map(n=>n.textContent),['3.7 eV']);
 assert.match(h.textContent,/Property results/);
 assert.equal(JSON.stringify({r,p}),before);
});

test('text-only property evidence and legacy optical figures do not suppress results',()=>{
 for(const f of [figure({public_asset:null}),figure({category:'optical'})]){
  const h=host();renderProperties(h,[f],record());
  assert.deepEqual(nodes(h,'dd').map(n=>n.textContent),['3.7 eV']);
  assert.match(h.textContent,/Synthetic optical figure/);
 }
});

test('each result retains specimen, conditions, source locator, basis and qualifier',()=>{
 const m=measurement({value:{minimum:3.7,maximum:4.1,maximum_exclusive:true,unit:'eV',status:'author_derived',
  qualifier:'Fit interval only',basis:'Dispersed sample; not the film',note:'Uncertainty not supplied',evidence:[evidence]}});
 const h=host();renderProperties(h,[figure()],record([m]));
 for(const text of ['Sample A','Synthetic optical analysis','Sample A dispersion only','Fit interval only',
  'Dispersed sample; not the film','Uncertainty not supplied','Value status: author derived','synthetic-source','Synthetic main p. 2, Figure 1'])assert.ok(h.textContent.includes(text),text);
 assert.deepEqual(nodes(h,'dd').map(n=>n.textContent),['[3.7, 4.1) eV']);
 assert.equal(walk(h).filter(n=>n.className==='reader-fact-source').length,1);
});

test('exact duplicates collapse but equal values from different conditions or specimens remain',()=>{
 const a=measurement(),b=measurement({id:'gap-b',sample_id:'sample-b'}),c=measurement({id:'gap-c',conditions:'Dried film only'});
 const h=host();assert.equal(renderProperties(h,[],record([a,structuredClone(a),b,c])),3);
 assert.equal(nodes(h,'dd').length,3);
 assert.match(h.textContent,/sample-b/);assert.match(h.textContent,/Dried film only/);
});

test('more than four observations stay available with their own scopes',()=>{
 const measurements=Array.from({length:6},(_,i)=>measurement({id:'gap-'+i,sample_id:'sample-'+i,conditions:'Condition '+i}));
 const h=host();renderProperties(h,[figure()],record(measurements));
 assert.equal(nodes(h,'dd').length,6);
 const extra=nodes(h,'details').find(n=>n.textContent.includes('Additional property results (2)'));
 assert.ok(extra);assert.equal(nodes(extra,'dd').length,2);
 assert.ok(extra.textContent.includes('Condition 4'));assert.ok(extra.textContent.includes('Condition 5'));
});

test('no-figure records retain their numeric summary',()=>{
 const h=host();renderProperties(h,[],record());
 assert.equal(nodes(h,'img').length,0);assert.equal(nodes(h,'dd').length,1);
 assert.doesNotMatch(h.textContent,/No property result/);
});

test('figure-only records do not acquire an empty-result warning or invented facts',()=>{
 const h=host();assert.equal(renderProperties(h,[figure()],record([])),0);
 assert.equal(nodes(h,'img').length,1);assert.equal(nodes(h,'dd').length,0);
 assert.doesNotMatch(h.textContent,/No property result|Property results/);
});

test('empty property sections preserve the existing honest note and classification',()=>{
 const h=host();renderProperties(h,[],record([measurement({property:'diameter'})]));
 assert.equal(nodes(h,'dd').length,0);assert.match(h.textContent,/No property result is assigned/);
});

test('strict scalar bounds and source text are displayed as text, without HTML execution',()=>{
 const h=host(),m=measurement({conditions:'Synthetic <img src=x onerror=alert(1)> condition',
  value:{maximum:5,maximum_exclusive:true,approximate:true,unit:'eV',status:'reported'}});
 renderProperties(h,[],record([m]));
 assert.deepEqual(nodes(h,'dd').map(n=>n.textContent),['≈<5 eV']);
 assert.match(h.textContent,/<img src=x onerror=alert\(1\)>/);
 assert.equal(nodes(h,'img').length,0);
});

test('prefer the source sample label and fall back only when it is absent',()=>{
 for(const label of ['Source specimen A','',null,undefined]){
  const r=record();r.products[0].source_sample_label=label;
  const h=host();renderProperties(h,[],r);
  if(label){assert.ok(h.textContent.includes(label));assert.ok(!h.textContent.includes('sample-a'));}
  else assert.ok(h.textContent.includes('sample-a'));
  assert.ok(h.textContent.includes(evidence.source_id));
  assert.ok(h.textContent.includes(evidence.locator));
 }
});


const propertyFact=(index=0,overrides={})=>({record_id:'synthetic-route',sample_id:'sample-a',measurement_id:'gap-a',
 source:{data_path:'data/records/synthetic-route.json',json_pointer:'/measurements/'+index+'/value'},...overrides});
test('explicit source-bound property measurements render beyond the legacy name list',()=>{
 for(const property of ['specific_surface_area','zeta_potential','photocatalytic_degradation_efficiency','power_conversion_efficiency']){
  const h=host(),r=record([measurement({property})]),p={propertyFacts:[propertyFact()]};
  const before=JSON.stringify({r,p});assert.equal(renderProperties(h,[figure()],r,p),1);
  assert.deepEqual(nodes(h,'dd').map(n=>n.textContent),['3.7 eV']);assert.equal(nodes(h,'img').length,1);
  assert.equal(JSON.stringify({r,p}),before);
 }
});
test('whole-measurement pointers are supported and mirrored facts never duplicate values',()=>{
 const h=host(),r=record([measurement({property:'specific_surface_area'})]);
 const a=propertyFact(),b=propertyFact(0,{source:{...a.source,json_pointer:'/measurements/0'}});
 assert.equal(renderProperties(h,[],r,{propertyFacts:[a,b,a]}),1);assert.equal(nodes(h,'dd').length,1);
});
test('foreign record, sample and measurement bindings cannot add a property',()=>{
 const invalid=[propertyFact(0,{record_id:'foreign'}),propertyFact(0,{sample_id:'foreign'}),
  propertyFact(0,{measurement_id:'foreign'}),propertyFact(0,{source:{data_path:'data/records/foreign.json',json_pointer:'/measurements/0/value'}}),
  propertyFact(0,{record_id:undefined}),propertyFact(0,{sample_id:undefined})];
 for(const f of invalid){const h=host();assert.equal(renderProperties(h,[],record([measurement({property:'specific_surface_area'})]),{propertyFacts:[f]}),0);}
});
test('malformed or out-of-range property pointers are ignored without inventing observations',()=>{
 for(const pointer of ['/measurements/-1/value','/measurements/00/value','/measurements/1/value','/measurements/0/value/value','/measurements/0/property','measurements/0','/measurements/0/value~1','/measurements/99999999999999999999/value','']){
  const f=propertyFact(0,{source:{data_path:'data/records/synthetic-route.json',json_pointer:pointer}}),h=host();
  assert.equal(renderProperties(h,[],record([measurement({property:'zeta_potential'})]),{propertyFacts:[f]}),0);
 }
});
test('presentation labels and amounts cannot replace canonical quantities',()=>{
 const h=host(),f=propertyFact(0,{label:'forged title',value:'999 kg'});
 renderProperties(h,[],record([measurement({property:'specific_surface_area'})]),{propertyFacts:[null,f]});
 assert.deepEqual(nodes(h,'dd').map(n=>n.textContent),['3.7 eV']);assert.doesNotMatch(h.textContent,/forged title|999 kg/);
});
