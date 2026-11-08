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
function mount(groups = data()) {const host = new Element('aside'), selected = []; const ui = mountMethodFamilyList(host, {groups, records, document: doc, onSelect: rid => selected.push(rid), initialPaperLimit: 2}); return {host, selected, ui};}
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
test('largest Other default is consumed literally; component does not choose another default', () => {
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

test('the global initial card limit hides empty family headings and one toggle expands all families',()=>{
 const {ui}=mount();const cards=elements(ui.root,'article'),families=elements(ui.root,'section');assert.equal(cards.filter(c=>!c.hidden).length,2);assert.equal(families[1].hidden,true);
 const toggles=elements(ui.root,'button').filter(b=>b.className==='reader-family-toggle');assert.equal(toggles.length,1);ui.select('a');toggles[0].onclick();assert.equal(cards.filter(c=>!c.hidden).length,4);assert.equal(families[1].hidden,false);assert.equal(cards[0].dataset.activeRecord,'a');
 toggles[0].onclick();assert.equal(cards.filter(c=>!c.hidden).length,2);assert.equal(families[1].hidden,true);
});
test('deep link to a globally hidden family expands all cards and keeps the selected variant visible',()=>{
 const {ui}=mount();ui.select('e');assert.ok(elements(ui.root,'article').every(c=>!c.hidden));assert.ok(elements(ui.root,'section').every(f=>!f.hidden));assert.equal(elements(ui.root,'article')[3].dataset.activeRecord,'e');
});
test('default policy respects method links and falls back only for older material data',()=>{
 assert.equal(chooseMethodRecord(data(),records,'b'),'b');assert.equal(chooseMethodRecord(data(),records),'a');assert.equal(chooseMethodRecord(null,[records[2],records[0]]),'c');assert.equal(chooseMethodRecord(null,[]),null);
});
