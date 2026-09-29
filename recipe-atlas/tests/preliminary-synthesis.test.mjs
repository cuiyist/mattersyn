// Synthetic test data only: these fixtures are never copied into the public catalogue.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {SCHEMA,preparePreliminary,filterEntries,renderPreliminary,mountPreliminary,doiURL} from '../static/preliminary-synthesis.mjs';

const locator=()=>[{page:1,section:'Synthetic test method'}];
function fixture(overrides={}){
 const doi='10.1234/synthetic-fixture';
 return {schema:SCHEMA,entries:[{source_id:'prelim-'+createHash('sha256').update(doi).digest('hex').slice(0,16),doi,title:'Synthetic fixture — not a research source',citation:'Synthetic unit-test citation',document_sha256:'a'.repeat(64),document_role:'main',source_pages:2,inspected_pages:[1,2],material:{label:'Synthetic oxide fixture',elements:['Ce','O'],existing_hub_id:'synthetic-test-hub'},method_label:'Synthetic test method',scope:'Synthetic limited-method test only.',deferred:['Other synthetic variants are outside this test.'],precursors:[{name:'Synthetic precursor',amount:null,role:'Test input',locators:locator()}],operations:[{order:1,action:'Mix the synthetic test input.',conditions:[{parameter:'Temperature',reported:'20 °C'}],locators:locator()},{order:2,action:'Isolate the synthetic test product.',conditions:[],locators:locator()}],outcome:{sample_label:'Synthetic sample',link_basis:'The synthetic fixture explicitly links this outcome to the test method.',descriptors:[{kind:'phase',reported:'Synthetic test phase',technique:'Synthetic diffraction',locators:locator()}],locators:locator()},missing_fields:['Synthetic amount is not reported.'],review:{tier:'preliminary',author_source_checked:true,independent_audit:'pending',accuracy:'unmeasured',training_ready:false},extraction:{origin:'assistant_source_checked',recipe_scope_complete:true,omitted_variants:'Other variants are deferred in this synthetic fixture.',source_identity_checked:true},evidence_fingerprint:'b'.repeat(64),...overrides}]};
}

// Tiny DOM spy: assigning HTML is prohibited; all authored strings must remain text.
class Node {
 constructor(doc,tag){this.ownerDocument=doc;this.tagName=tag.toUpperCase();this.children=[];this.attributes={};this.events={};this.value='';this._text='';}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 set innerHTML(_value){throw Error('Unsafe HTML assignment');}
 append(...nodes){assert.ok(nodes.every(n=>n instanceof Node));this.children.push(...nodes);}
 replaceChildren(...nodes){this._text='';this.children=[];this.append(...nodes);}
 setAttribute(key,value){this.attributes[key]=String(value);}
 addEventListener(key,fn){this.events[key]=fn;}
 scrollIntoView(){this.scrolled=true;}
}
function descendants(node){return [node,...node.children.flatMap(descendants)];}
function documentFixture(){
 const doc={createElement:tag=>new Node(doc,tag)};
 doc.root=new Node(doc,'main');
 for(const [id,tag] of [['preliminary-results','div'],['preliminary-filters','form'],['preliminary-search','input'],['preliminary-element','select'],['preliminary-clear','button'],['preliminary-filter-context','p']]){const n=doc.createElement(tag);n.id=id;doc.root.append(n);}
 doc.getElementById=id=>descendants(doc.root).find(n=>n.id===id)||null;
 return doc;
}
const render=data=>{const doc=documentFixture();renderPreliminary(doc.getElementById('preliminary-results'),preparePreliminary(data));return doc;};

test('empty catalogue states no preliminary publication',()=>{
 const raw={schema:SCHEMA,entries:[]};
 const doc=render(raw);assert.match(doc.root.textContent,/No preliminary contributions have been published yet/);
 assert.equal(descendants(doc.root).filter(n=>n.tagName==='ARTICLE').length,0);
 assert.match(doc.root.textContent,/Separate from reviewed dataset and verified pair counts/);
});
test('actual public catalogue validates and excludes synthetic fixtures',()=>{
 const raw=JSON.parse(readFileSync(new URL('../static/data/preliminary-synthesis.json',import.meta.url),'utf8'));
 const view=preparePreliminary(raw);
 assert.equal(view.status,'ready');
 assert.equal(view.entries.length,raw.entries.length);
 for(const entry of view.entries){
  assert.doesNotMatch(entry.doi,/synthetic-fixture/);
  assert.doesNotMatch(entry.title,/Synthetic fixture/);
  assert.equal(entry.review.independent_audit,'pending');
  assert.equal(entry.review.accuracy,'unmeasured');
  assert.equal(entry.review.training_ready,false);
 }
});
test('synthetic nonempty display retains scope, null amount, ordered method and exact locators',()=>{
 const data=fixture(),doc=render(data),text=doc.root.textContent;
 for(const value of ['INDEPENDENT AUDIT PENDING','Accuracy unmeasured; training excluded','Precursors','Not reported','Ordered synthesis protocol','Linked structural outcome','p. 1 · Synthetic test method','Variant coverage:','Synthetic amount is not reported.'])assert.ok(text.includes(value),value);
 assert.equal(descendants(doc.root).filter(n=>n.tagName==='OL')[0].children.length,2);
 assert.ok(doc.getElementById(data.entries[0].source_id));
});
test('hostile authored markup stays literal text and only safe links are created',()=>{
 const data=fixture({title:'<img src=x onerror=alert(1)>'});
 data.entries[0].outcome.link_basis='<script>alert(1)</script>';
 const doc=render(data),nodes=descendants(doc.root);
 assert.ok(doc.root.textContent.includes('<img src=x onerror=alert(1)>'));
 assert.equal(nodes.filter(n=>['IMG','SCRIPT','IFRAME'].includes(n.tagName)).length,0);
 const anchors=nodes.filter(n=>n.tagName==='A');
 assert.ok(anchors.every(n=>n.href.startsWith('https://doi.org/')||n.href.startsWith('#prelim-')||n.href==='material.html?id=synthetic-test-hub'));
 assert.equal(anchors[0].rel,'noopener noreferrer');
 assert.throws(()=>doiURL('javascript:alert(1)'));
 assert.equal(new URL(doiURL('10.1234/example?x=#frag')).origin,'https://doi.org');
 assert.ok(doiURL('10.1234/example?x=#frag').includes('%3F'));
});
test('display refuses altered admission labels and unknown public evidence keys',()=>{
 for(const mutate of [e=>e.review.training_ready=true,e=>e.review.tier='gold',e=>e.review.accuracy='99%',e=>e.review.independent_audit='passed',e=>e.review.author_source_checked=false,e=>e.extraction.recipe_scope_complete=false,e=>e.extraction.source_identity_checked=false,e=>e.raw_quote='Private source text',e=>e.material.existing_hub_id='../unsafe',e=>e.doi='https://example.org/source']){
  const data=fixture();mutate(data.entries[0]);assert.equal(preparePreliminary(data).status,'unavailable');
 }
});
test('shape checks reject duplicate identities, bad pages, order and hash coercion',()=>{
 for(const mutate of [d=>d.entries.push(structuredClone(d.entries[0])),d=>d.entries[0].operations[1].order=3,d=>d.entries[0].precursors[0].locators[0].page=3,d=>d.entries[0].inspected_pages=[1,1],d=>d.entries[0].document_sha256=['a'.repeat(64)],d=>d.entries[0].material.elements=['NotAnElement'],d=>d.entries[0].source_pages=5001,d=>d.entries[0].scope='x'.repeat(601)]){
  const data=fixture();mutate(data);assert.equal(preparePreliminary(data).status,'unavailable');
 }
 const privatePath=['C:',String.fromCharCode(92),'private','evidence'].join('');
 assert.equal(preparePreliminary(fixture({scope:privatePath})).status,'unavailable');
});
test('material and element filters work without a reviewed hub or changing input',()=>{
 const data=fixture(),view=preparePreliminary(data);
 data.entries[0].title='Changed caller title';assert.notEqual(view.entries[0].title,data.entries[0].title);
 assert.equal(filterEntries(view.entries,{element:'Ce'}).length,1);
 assert.equal(filterEntries(view.entries,{element:'Pb'}).length,0);
 assert.equal(filterEntries(view.entries,{query:'oxide',hub:'synthetic-test-hub'}).length,1);
 assert.equal(filterEntries(view.entries,{hub:'another-hub'}).length,0);
 const noHub=fixture();noHub.entries[0].material.existing_hub_id=null;
 assert.equal(filterEntries(preparePreliminary(noHub).entries,{query:'oxide'}).length,1);
 assert.equal(descendants(render(noHub).root).filter(n=>n.href?.startsWith('material.html')).length,0);
});
test('mount uses fixed local public JSON, URL filters, source anchors and clear control',async()=>{
 const doc=documentFixture(),data=fixture();let request;
 await mountPreliminary(doc,{search:'?hub=synthetic-test-hub&element=Ce',hash:'#'+data.entries[0].source_id,fetcher:async(...args)=>{request=args;return {ok:true,json:async()=>data};}});
 assert.deepEqual(request,['data/preliminary-synthesis.json',{credentials:'omit'}]);
 assert.equal(doc.getElementById('preliminary-results').attributes['aria-busy'],'false');
 assert.equal(doc.getElementById(data.entries[0].source_id).scrolled,true);
 const query=doc.getElementById('preliminary-search');query.value='does not match';query.events.input();assert.match(doc.root.textContent,/No preliminary contributions match/);
 doc.getElementById('preliminary-clear').events.click();assert.ok(doc.getElementById(data.entries[0].source_id));
});
test('failed fetch and invalid public shapes never render contributions',async()=>{
 for(const fetcher of [async()=>{throw Error('offline');},async()=>({ok:false}),async()=>({ok:true,json:async()=>({schema:SCHEMA,entries:[{title:'invalid'}]})})]){
  const doc=documentFixture();await mountPreliminary(doc,{fetcher});
  assert.match(doc.root.textContent,/No unvalidated contribution is shown/);
  assert.equal(descendants(doc.root).filter(n=>n.tagName==='ARTICLE').length,0);
 }
});
test('page has explicit review boundaries and same-origin downloadable data',()=>{
 const html=readFileSync(new URL('../static/preliminary-synthesis.html',import.meta.url),'utf8');
 assert.match(html,/Independent scientific audit pending/);assert.match(html,/Accuracy unmeasured/);assert.match(html,/Training excluded/);
 assert.match(html,/href="data\/preliminary-synthesis.json" download="preliminary-synthesis.json"/);
 assert.equal((html.match(/<script/g)||[]).length,1);
});
