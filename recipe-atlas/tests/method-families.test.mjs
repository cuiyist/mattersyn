import test from 'node:test';
import assert from 'node:assert/strict';
import {METHOD_FAMILIES_SCHEMA, validateMethodFamilies, mountMethodFamilyList, chooseMethodRecord} from '../static/method-families.mjs';

class Element {
  constructor(tag) {this.tagName = tag; this.children = []; this.dataset = {}; this.attributes = {}; this.hidden = false; this._text = '';}
  append(...nodes) {this.children.push(...nodes);}
  set textContent(value) {this._text = String(value); this.children = [];}
  get textContent() {return this._text + this.children.map(c => c.textContent || '').join(' ');}
  setAttribute(key, value) {this.attributes[key] = String(value);}
}
const doc = {createElement: tag => new Element(tag)};
const records = ['a', 'b', 'c', 'd', 'e'].map(rid => ({record_id: rid, title: 'Own title ' + rid}));
function data() {return {schema: METHOD_FAMILIES_SCHEMA, default_record_id: 'a', families: [
  {id: 'largest', kind: 'other', label: 'Other methods', paper_count: 3, papers: [
    {citation: 'Alpha et al. (2001)', record_ids: ['a', 'b']}, {citation: 'Beta (2002)', record_ids: ['c']}, {citation: 'Gamma (2003)', record_ids: ['d']},
  ]}, {id: 'processing', kind: 'processing', label: 'Processing of material', paper_count: 1, papers: [{citation: 'Delta (2004)', record_ids: ['e']}]},
]};}
function mount(groups = data()) {const host = new Element('aside'), selected = []; const ui = mountMethodFamilyList(host, {groups, records, document: doc, onSelect: rid => selected.push(rid), initialFamilyLimit: 3, initialPapersPerFamily: 2}); return {host, selected, ui};}
function elements(node, tag) {return [node, ...node.children.flatMap(child => elements(child, tag))].filter(n => !tag || n.tagName === tag);}

test('one paper card folds variants; grouping never fetches or changes records', () => {
  const before = structuredClone(records), {ui} = mount();
  assert.equal(ui.familyCount, 2); assert.equal(ui.cardCount, 4);
  assert.equal(elements(ui.root, 'article').length, 4); assert.equal(elements(ui.root, 'select').length, 1);
  assert.deepEqual(elements(ui.root, 'option').map(x => x.value), ['a', 'b']); assert.deepEqual(records, before);
});
test('all method IDs remain selectable, including hidden cards and variants', () => {
  const {ui} = mount(); const cards = elements(ui.root, 'article'); assert.equal(cards[2].hidden, true);
  ui.select('d'); assert.equal(cards[2].hidden, false); assert.equal(cards[2].dataset.activeRecord, 'd');
  ui.select('b'); assert.equal(elements(ui.root, 'select')[0].value, 'b'); assert.equal(cards[0].dataset.activeRecord, 'b');
});
test('variant changes and paper button use existing select callback only', () => {
  const {ui, selected} = mount(); const variant = elements(ui.root, 'select')[0]; variant.value = 'b'; variant.onchange();
  assert.deepEqual(selected, ['b']); ui.select('b'); elements(ui.root, 'button')[0].onclick(); assert.deepEqual(selected, ['b', 'b']);
});
test('Show all expands papers inside their family without flattening families', () => {
  const {ui} = mount(); const toggle = elements(ui.root, 'button').find(x => x.textContent === 'Show all');
  assert.ok(toggle); toggle.onclick(); assert.equal(elements(ui.root, 'article')[2].hidden, false);
  assert.equal(elements(ui.root, 'section').length, 2); assert.equal(toggle.attributes['aria-expanded'], 'true');
  toggle.onclick(); assert.equal(elements(ui.root, 'article')[2].hidden, true);
});
test('collapse never hides active linked record and captions have no status distinction', () => {
  const {ui} = mount(); ui.select('d'); const toggle = elements(ui.root, 'button').find(x => x.textContent === 'Show fewer'); toggle.onclick();
  assert.equal(elements(ui.root, 'article')[2].hidden, false); assert.doesNotMatch(ui.root.textContent, /source_extracted|reviewed|machine.extract/i);
});
test('backend default is consumed literally; frontend does not choose another family', () => {
  const {ui, selected} = mount(); ui.select(data().default_record_id);
  assert.equal(elements(ui.root, 'article')[0].dataset.activeRecord, 'a'); assert.deepEqual(selected, []);
});
test('unknown, duplicate and missing links reject malformed metadata', () => {
  for (const mutate of [g => g.families[0].papers[0].record_ids.push('bad'), g => g.families[1].papers[0].record_ids.push('a'), g => g.families.pop()]) {
    const groups = data(); mutate(groups); assert.throws(() => validateMethodFamilies(groups, records));
  }
  const groups = data(); groups.default_record_id = 'c'; assert.throws(() => validateMethodFamilies(groups, records));
});
test('paper adoption count is explicit and separate from recipe variant count', () => {
  const {ui} = mount(); assert.match(ui.root.textContent, /3 papers/); assert.match(ui.root.textContent, /1 paper/); assert.doesNotMatch(ui.root.textContent, /5 papers/);
});

test('CI DOM metadata exposes exact per-paper variant membership and selected record', () => {
 const {ui}=mount();const cards=elements(ui.root,'article');assert.deepEqual(JSON.parse(cards[0].dataset.recordIds),['a','b']);ui.select('b');assert.equal(elements(ui.root,'button')[0].dataset.recordId,'b');
});

test('identical own titles still produce distinguishable variant options', () => {
 const same=records.map(r=>({...r,title:'Identical source title'}));const host=new Element('aside');const ui=mountMethodFamilyList(host,{groups:data(),records:same,document:doc,onSelect:()=>{}});const options=elements(ui.root,'option');assert.equal(options[0].textContent,'Variant 1 - Identical source title');assert.equal(options[1].textContent,'Variant 2 - Identical source title');assert.notEqual(options[0].textContent,options[1].textContent);assert.deepEqual(options.map(o=>o.value),['a','b']);
});

test('first three ordered families get their own first two cards and one toggle expands all',()=>{
 const {ui}=mount();const cards=elements(ui.root,'article'),families=elements(ui.root,'section');assert.equal(cards.filter(c=>!c.hidden).length,3);assert.equal(families[1].hidden,false);
 assert.equal(ui.root.dataset.initialFamilyLimit,'3');assert.equal(ui.root.dataset.initialPapersPerFamily,'2');assert.equal(ui.root.dataset.initialCardLimit,undefined);
 const toggles=elements(ui.root,'button').filter(b=>b.className==='reader-family-toggle');assert.equal(toggles.length,1);ui.select('a');toggles[0].onclick();assert.equal(cards.filter(c=>!c.hidden).length,4);assert.equal(families[1].hidden,false);assert.equal(cards[0].dataset.activeRecord,'a');
 toggles[0].onclick();assert.equal(cards.filter(c=>!c.hidden).length,3);assert.equal(families[1].hidden,false);
});
test('deep link to a preview-hidden family expands all cards and keeps its selected variant visible',()=>{
 const f=manyFamilies(),host=new Element('aside'),ui=mountMethodFamilyList(host,{...f,document:doc,onSelect:()=>{}});ui.select('component-0-variant');assert.ok(elements(ui.root,'article').every(c=>!c.hidden));assert.ok(elements(ui.root,'section').every(s=>!s.hidden));assert.equal(elements(ui.root,'select')[0].value,'component-0-variant');assert.equal(elements(ui.root,'article').find(c=>c.dataset.activeRecord==='component-0-variant').hidden,false);
});
test('default policy respects method links and falls back only for older material data',()=>{
 assert.equal(chooseMethodRecord(data(),records,'b'),'b');assert.equal(chooseMethodRecord(data(),records),'a');assert.equal(chooseMethodRecord(null,[records[2],records[0]]),'c');assert.equal(chooseMethodRecord(null,[]),null);
});


function manyFamilies() {
 const families=[],all=[];
 for(const [id,kind,count] of [['own-a','synthesis',5],['own-b','synthesis',4],['own-other','other',3],['component','component',20],['processing','processing',9]]) {
  const papers=[];for(let i=0;i<count;i++){const ids=[`${id}-${i}`];if(id==='component'&&i===0)ids.push('component-0-variant');for(const rid of ids)all.push({record_id:rid,title:'Own '+rid});papers.push({citation:`Own author ${id} ${i}`,record_ids:ids});}
  families.push({id,kind,label:id==='component'?'ZnS as shell or component':id==='processing'?'Processing of ZnS':id,paper_count:count,papers});
 }
 return {records:all,groups:{schema:METHOD_FAMILIES_SCHEMA,default_record_id:'own-a-0',families}};
}
function mountedMany(){const f=manyFamilies(),host=new Element('aside');return {...f,ui:mountMethodFamilyList(host,{...f,document:doc,onSelect:()=>{}})};}
test('J preview is first three backend-ordered families with top two papers each, not first six globally',()=>{
 const {ui}=mountedMany(),families=elements(ui.root,'section');assert.deepEqual(families.map(f=>elements(f,'article').filter(c=>!c.hidden).length),[2,2,2,0,0]);assert.deepEqual(families.map(f=>f.hidden),[false,false,false,true,true]);assert.equal(elements(ui.root,'article').filter(c=>!c.hidden).length,6);assert.match(ui.root.textContent,/ZnS as shell or component/);assert.match(ui.root.textContent,/20 papers/);
});
test('larger component and processing groups never reorder an own family or default',()=>{
 const {ui,groups,records:all}=mountedMany();assert.deepEqual(elements(ui.root,'section').map(f=>f.dataset.familyId),groups.families.map(f=>f.id));assert.equal(chooseMethodRecord(groups,all),'own-a-0');ui.select('own-a-0');assert.equal(elements(ui.root,'article')[0].dataset.activeRecord,'own-a-0');
});
test('Show fewer retains only a deliberately selected outside-preview card as an explicit-link exception',()=>{
 const {ui}=mountedMany();ui.select('component-0-variant');const toggle=elements(ui.root,'button').find(b=>b.className==='reader-family-toggle');assert.equal(toggle.attributes['aria-expanded'],'true');toggle.onclick();assert.equal(toggle.attributes['aria-expanded'],'false');const families=elements(ui.root,'section');assert.deepEqual(families.map(f=>elements(f,'article').filter(c=>!c.hidden).length),[2,2,2,1,0]);assert.equal(elements(ui.root,'article').find(c=>c.dataset.activeRecord==='component-0-variant').hidden,false);ui.select('own-a-0');assert.deepEqual(families.map(f=>elements(f,'article').filter(c=>!c.hidden).length),[2,2,2,0,0]);
});
test('a hidden third card or fourth family needs Show all even when total is fewer than six',()=>{
 for(const [counts,visible] of [[[3],2],[[1,1,1,1],3]]){const all=[],families=counts.map((n,f)=>({id:'f'+f,kind:'synthesis',label:'Own'+f,paper_count:n,papers:Array.from({length:n},(_,p)=>{const rid=`f${f}p${p}`;all.push({record_id:rid,title:rid});return{citation:rid,record_ids:[rid]}})}));const g={schema:METHOD_FAMILIES_SCHEMA,default_record_id:'f0p0',families},ui=mountMethodFamilyList(new Element('aside'),{groups:g,records:all,document:doc,onSelect:()=>{}});assert.equal(elements(ui.root,'article').filter(c=>!c.hidden).length,visible);assert.equal(elements(ui.root,'button').filter(b=>b.className==='reader-family-toggle').length,1);}
});
test('fewer than three own families include following component and processing families without padding cards',()=>{
 const f=manyFamilies();f.groups.families=[f.groups.families[0],f.groups.families[3],f.groups.families[4]];const allowed=new Set(f.groups.families.flatMap(g=>g.papers.flatMap(p=>p.record_ids)));f.records=f.records.filter(r=>allowed.has(r.record_id));const ui=mountMethodFamilyList(new Element('aside'),{...f,document:doc,onSelect:()=>{}});assert.deepEqual(elements(ui.root,'section').map(s=>elements(s,'article').filter(c=>!c.hidden).length),[2,2,2]);
});
test('preview options reject invalid counts without fetching or modifying records',()=>{
 for(const options of [{initialFamilyLimit:0},{initialFamilyLimit:1.5},{initialPapersPerFamily:0},{initialPapersPerFamily:NaN}])assert.throws(()=>mountMethodFamilyList(new Element('aside'),{groups:data(),records,document:doc,onSelect:()=>{},...options}));
});
