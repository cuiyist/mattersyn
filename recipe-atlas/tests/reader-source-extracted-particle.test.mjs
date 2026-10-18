import test from 'node:test';
import assert from 'node:assert/strict';
import {particleGroups, particleDisplayDescriptor, mountParticleContext} from '../static/reader-particle.mjs';
import {particleShapeSVG} from '../static/particle-shapes.mjs';

function fixture() {
 const r={record_id:'synthetic-source-extracted-sphere',quality:{review_status:'source_extracted'},sources:[{id:'synthetic-source'}],products:[{
  sample_id:'synthetic-product',source_sample_label:'Reported product',recipe_link:'explicit',
  composition:{value:null,status:'not_reported',evidence:[]},phase:{value:null,status:'not_reported',evidence:[]},
  morphology:{value:'sphere',status:'reported',evidence:[{source_id:'synthetic-source',locator:'Main PDF p.2'}]},
  surface:{value:'NHC',status:'reported',evidence:[{source_id:'synthetic-source',locator:'Main PDF p.2'}]}
 }]};
 const presentation={presentation_status:'pending',primary_product:{default_sample_id:'synthetic-product'},allProductFacts:[{
  record_id:r.record_id,sample_id:'synthetic-product',kind:'measurement',label:'Diameter',value:'5.2 nm',status:'reported'
 }]};
 return {r,presentation};
}
function descriptor(r,presentation,interpretations={}) {
 const group=particleGroups(r,presentation).get(r.record_id+':synthetic-product');
 return particleDisplayDescriptor(r,group,presentation,interpretations);
}

function boundFact(r,presentation,kind='morphology') {
 const inputHash='0'.repeat(64),product=r.products[0],field=product[kind];
 presentation.productContexts=[{record_id:r.record_id,sample_id:product.sample_id,source:{data_path:'data/records/'+r.record_id+'.json',json_pointer:'/products/0',input_sha256:inputHash}}];
 return {record_id:r.record_id,sample_id:product.sample_id,kind:'product_fact',label:kind,value:field.value,status:field.status,
  source:{data_path:'data/records/'+r.record_id+'.json',json_pointer:'/products/0/'+kind,input_sha256:inputHash},source_locator:structuredClone(field.evidence)};
}

test('pointer-bound morphology, phase and surface facts do not repeat canonical fallback rows',()=>{
 const {r,presentation}=fixture();r.products[0].phase={value:'Synthetic reported phase',status:'reported',evidence:structuredClone(r.products[0].morphology.evidence)};
 const facts=['morphology','phase','surface'].map(kind=>boundFact(r,presentation,kind));presentation.allProductFacts.push(...facts);
 const before=JSON.stringify({r,presentation}),group=particleGroups(r,presentation).get(r.record_id+':synthetic-product');
 assert.equal(group.facts.length,4);for(const fact of facts)assert.ok(group.facts.includes(fact));
 assert.equal(particleDisplayDescriptor(r,group,presentation).sourceFact,facts[0]);
 assert.equal(JSON.stringify({r,presentation}),before);
});
test('value pointers also identify exactly the same bound product field',()=>{
 const {r,presentation}=fixture(),fact=boundFact(r,presentation);fact.source.json_pointer+='/value';presentation.allProductFacts.push(fact);
 const group=particleGroups(r,presentation).get(r.record_id+':synthetic-product');assert.equal(group.facts.filter(f=>f.label==='morphology'||f.kind==='morphology').length,1);
});
test('different values, source pages, field pointers, input pins and notes retain their distinct rows',()=>{
 const variants=[
  f=>{f.value='another reported value';},f=>{f.source_locator[0].locator='Main PDF p.3';},
  f=>{f.source.json_pointer='/products/1/morphology';},f=>{f.source.json_pointer='/products/0/surface';},
  f=>{f.source.input_sha256='1'.repeat(64);},f=>{f.source.data_path='data/records/another-record.json';},
  (f,r)=>{f.source.data_path='https://example.invalid/records/'+r.record_id+'.json';},
  f=>{f.status='author_derived';},(f,r)=>{r.products[0].morphology.note='Additional specimen limitation';}
 ];
 for(const mutate of variants){const {r,presentation}=fixture(),fact=boundFact(r,presentation);mutate(fact,r);presentation.allProductFacts.push(fact);
  const before=JSON.stringify({r,presentation}),group=particleGroups(r,presentation).get(r.record_id+':synthetic-product');
  assert.ok(group.facts.includes(fact));assert.equal(group.facts.filter(f=>f.label==='morphology'||f.kind==='morphology').length,2);
  assert.equal(JSON.stringify({r,presentation}),before);
 }
});
test('same-value facts from another specimen or record stay in their separate groups',()=>{
 for(const field of ['sample_id','record_id']){const {r,presentation}=fixture(),fact=boundFact(r,presentation);fact[field]='another-context';presentation.allProductFacts.push(fact);
  const groups=particleGroups(r,presentation),own=groups.get(r.record_id+':synthetic-product');
  assert.equal(groups.size,2);assert.equal(own.facts.filter(f=>f.kind==='morphology').length,1);
  assert.ok([...groups.values()].some(group=>group.facts.includes(fact)));
 }
});
test('reported SourceEx wire uses only the existing qualitative elongated primitive',()=>{
 const {r,presentation}=fixture();r.products[0].morphology.value='wire';const before=JSON.stringify({r,presentation}),d=descriptor(r,presentation);
 assert.equal(d.shape,'rod');assert.equal(d.morphology,'wire');assert.equal(d.composition,'Composition not assigned');
 assert.match(d.caption,/source-reported wire.*illustrative.*not to scale.*atomic reconstruction/);
 assert.match(particleShapeSVG(d.shape),/Schematic rod-shaped particle/);assert.equal(JSON.stringify({r,presentation}),before);
});
test('wire alias is unavailable to reviewed, unreported, unlocated or conflicting contexts',()=>{
 for(const status of ['pending','ready']){const {r,presentation}=fixture();r.quality.review_status='source_reviewed';presentation.presentation_status=status;r.products[0].morphology.value='wire';assert.equal(descriptor(r,presentation).shape,'neutral');}
 for(const mutate of [r=>{r.products[0].morphology.status='inherited';},r=>{r.products[0].morphology.evidence=[];},r=>{r.products[0].morphology.evidence[0].source_id='another-source';}]){
  const {r,presentation}=fixture();r.products[0].morphology.value='wire';mutate(r);assert.equal(descriptor(r,presentation).shape,'neutral');
 }
 const {r,presentation}=fixture();r.products[0].morphology.value='wire';presentation.allProductFacts.push({kind:'morphology',status:'reported',value:'rod',record_id:r.record_id,sample_id:'synthetic-product'});assert.equal(descriptor(r,presentation).shape,'neutral');
});
test('single film and specialized shapes stay honest when no matching existing primitive is available',()=>{
 for(const value of ['film','biprism','bifrustum','dot','circular']){const {r,presentation}=fixture();r.products[0].morphology.value=value;assert.equal(descriptor(r,presentation).shape,'neutral',value);}
});

test('pending extracted product displays reported shape while composition and phase stay unassigned',()=>{
 const {r,presentation}=fixture(),before=JSON.stringify({r,presentation}),d=descriptor(r,presentation);
 assert.equal(d.shape,'sphere');assert.equal(d.composition,'Composition not assigned');assert.equal(d.inferred,undefined);
 assert.match(d.caption,/illustrative.*not to scale.*atomic reconstruction/);
 const svg=particleShapeSVG(d.shape);assert.match(svg,/Schematic spherical particle/);assert.match(svg,/role="img"/);
 assert.doesNotMatch(svg,/5\.2|\bnm\b|Ag|NHC|atom|crystal phase/);
 assert.equal(JSON.stringify({r,presentation}),before);
 assert.equal(r.quality.review_status,'source_extracted');assert.equal(r.products[0].phase.value,null);
});
test('existing pending reviewed product still requires its specimen interpretation',()=>{
 const {r,presentation}=fixture();r.quality.review_status='source_reviewed';assert.equal(descriptor(r,presentation).shape,'neutral');
});
test('unreported or inferred morphology cannot supply the extracted fallback',()=>{
 for(const status of ['not_reported','inferred','author_derived','calculated','inherited']){
  const {r,presentation}=fixture();r.products[0].morphology.status=status;assert.equal(descriptor(r,presentation).shape,'neutral',status);
 }
});
test('missing, empty or foreign-source evidence cannot supply the fallback',()=>{
 for(const evidence of [[],[{source_id:'synthetic-source',locator:''}],[{source_id:'another-source',locator:'Main PDF p.2'}]]){
  const {r,presentation}=fixture();r.products[0].morphology.evidence=evidence;assert.equal(descriptor(r,presentation).shape,'neutral');
 }
});
test('unknown, negated or conflicting reported shapes remain unknown',()=>{
 for(const value of ['unknown','No spheres observed','spheres and cubes']){
  const {r,presentation}=fixture();r.products[0].morphology.value=value;assert.equal(descriptor(r,presentation).shape,'neutral',value);
 }
});
test('a pending extracted product cannot borrow conflicting facts or another record',()=>{
 const {r,presentation}=fixture();presentation.allProductFacts.push({kind:'morphology',status:'reported',value:'rod',record_id:r.record_id,sample_id:'synthetic-product'});
 assert.equal(descriptor(r,presentation).shape,'neutral');
 const group=particleGroups(r,presentation).get(r.record_id+':synthetic-product');group.recordId='another-record';
 assert.equal(particleDisplayDescriptor(r,group,presentation).shape,'neutral');
});
test('facts without a canonical product cannot assign a pending extracted illustration',()=>{
 const {r,presentation}=fixture();r.products=[];presentation.productContexts=[{record_id:r.record_id,sample_id:'synthetic-product'}];
 presentation.allProductFacts.push({kind:'morphology',status:'reported',value:'sphere',record_id:r.record_id,sample_id:'synthetic-product'});
 assert.equal(descriptor(r,presentation).shape,'neutral');
});
test('shape-only fallback does not assign interfaces, supports or assemblies',()=>{
 for(const value of ['core-shell sphere','nanotube-supported particles','sphere assembly']){
  const {r,presentation}=fixture();r.products[0].morphology.value=value;assert.equal(descriptor(r,presentation).shape,'neutral',value);
 }
});
test('ordinary nonpending rendering and explicit specimen interpretation are preserved',()=>{
 const {r,presentation}=fixture();r.quality.review_status='source_reviewed';presentation.presentation_status='ready';
 assert.equal(descriptor(r,presentation).shape,'sphere');presentation.presentation_status='pending';
 const interpretation={shape:'ellipsoid',label:'Explicit specimen illustration',rationale:'Scoped interpretation'};
 const d=descriptor(r,presentation,{[r.record_id+':synthetic-product']:interpretation});
 assert.equal(d.shape,'ellipsoid');assert.equal(d.inferred,interpretation);
});

class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.style={};this.isConnected=true;this.value='';}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=[...children];}
 setAttribute(name,value){this[name]=value;}
}
test('actual mount renders the sphere, retains measurements, and leaves unknown shape without art',async()=>{
 const oldDocument=globalThis.document,oldFetch=globalThis.fetch;
 globalThis.document={createElement:tag=>new Element(tag),createTextNode:text=>({textContent:text})};
 globalThis.fetch=async()=>({ok:true,json:async()=>({entries:{}})});
 try{
  const {r,presentation}=fixture(),before=JSON.stringify({r,presentation}),panel=new Element('section');
  const mounted=await mountParticleContext(panel,r,presentation),layout=mounted.display.children[0];
  assert.equal(layout.children.length,2);assert.match(layout.children[0].innerHTML,/Schematic spherical particle/);
  const texts=[];const visit=e=>{if(e.textContent)texts.push(e.textContent);for(const c of e.children||[])visit(c);};visit(panel);
  assert.ok(texts.includes('5.2 nm'));assert.ok(texts.includes('NHC'));assert.ok(texts.includes('Composition not assigned'));
  assert.ok(texts.some(t=>/not a micrograph.*exact structure–recipe training label/.test(t)));
  assert.equal(JSON.stringify({r,presentation}),before);
  r.products[0].morphology.value='unknown';const unknown=await mountParticleContext(new Element('section'),r,presentation);
  assert.equal(unknown.display.children[0].children.length,1);
 }finally{globalThis.document=oldDocument;globalThis.fetch=oldFetch;}
});

// A single specimen is context text, not a native select that clips its label on phones.
test('one particle context keeps its complete label visible as wrapping ordinary text',async()=>{
 const oldDocument=globalThis.document,oldFetch=globalThis.fetch;
 globalThis.document={createElement:tag=>new Element(tag),createTextNode:text=>({textContent:text})};
 globalThis.fetch=async()=>({ok:true,json:async()=>({entries:{}})});
 try{
  const {r,presentation}=fixture(),fullLabel='A long synthetic specimen context '.repeat(10);
  r.products[0].source_sample_label=fullLabel;
  const before=JSON.stringify({r,presentation}),panel=new Element('section'),mounted=await mountParticleContext(panel,r,presentation);
  assert.equal(mounted.groups.size,1);assert.equal(panel.children[0].tagName,'p');
  assert.equal(panel.children[0].textContent,fullLabel);assert.match(panel.children[0].className,/reader-particle-context/);
  assert.ok(!panel.children.some(child=>child.tagName==='select'));
  assert.equal(JSON.stringify({r,presentation}),before);
 }finally{globalThis.document=oldDocument;globalThis.fetch=oldFetch;}
});
test('multiple particle specimens retain the existing selector and exact selected evidence',async()=>{
 const oldDocument=globalThis.document,oldFetch=globalThis.fetch;
 globalThis.document={createElement:tag=>new Element(tag),createTextNode:text=>({textContent:text})};
 globalThis.fetch=async()=>({ok:true,json:async()=>({entries:{}})});
 try{
  const {r,presentation}=fixture(),other=structuredClone(r.products[0]);
  other.sample_id='second-product';other.source_sample_label='Second source specimen';other.morphology.value='unknown';r.products.push(other);
  presentation.allProductFacts.push({record_id:r.record_id,sample_id:other.sample_id,kind:'measurement',label:'Diameter',value:'9.1 nm',status:'reported'});
  const before=JSON.stringify({r,presentation}),panel=new Element('section'),mounted=await mountParticleContext(panel,r,presentation);
  assert.equal(mounted.groups.size,2);assert.equal(panel.children[0],mounted.choose);assert.equal(mounted.choose.tagName,'select');
  mounted.choose.value=r.record_id+':'+other.sample_id;mounted.choose.onchange();
  const texts=[];const visit=e=>{if(e.textContent)texts.push(e.textContent);for(const c of e.children||[])visit(c);};visit(mounted.display);
  assert.ok(texts.includes('9.1 nm'));assert.ok(!texts.includes('5.2 nm'));assert.equal(JSON.stringify({r,presentation}),before);
 }finally{globalThis.document=oldDocument;globalThis.fetch=oldFetch;}
});
