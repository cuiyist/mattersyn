import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=path=>readFileSync(new URL('../'+path,import.meta.url),'utf8');
test('homepage uses published labels and keeps the audited option explicit',()=>{
 const html=source('static/index.html');
 for(const text of ['Published materials','Published synthesis contribution','Published synthesis pages','Audited methods'])assert.ok(html.includes(text),text);
 for(const text of ['Reviewed materials','Verified synthesis pages','Unreviewed materials remain blank','source-verified synthesis contributions'])assert.ok(!html.includes(text),text);
 assert.ok(html.includes('value="reviewed"'));
 assert.ok(html.includes('atlas-app.mjs?v=0.6.0-r3'));
});
test('source-linked card and empty-state copy does not claim review',()=>{
 const app=source('static/atlas-app.mjs');
 assert.ok(app.includes('Source-linked synthesis records'));
 assert.ok(app.includes('No published synthesis page matches this selection yet.'));
 assert.ok(!app.includes('Reviewed synthesis records'));
});
test('audited display filter excludes extracted-only pages and includes mixed pages',()=>{
 const app=source('static/atlas-app.mjs');
 const expression=app.match(/const matches=materials\.filter\(m=>(.*)\);/)[1];
 const selected=new Set(),query='',exact=false,scope='reviewed';
 const matches=new Function('m','selected','query','exact','scope','return '+expression);
 for(const [reviewed,extracted,wanted] of [[0,1,false],[1,0,true],[1,1,true]]){
  const material={elements:['Zn','O'],formula:'ZnO',name:'Zinc oxide',reviewed_records:reviewed,source_extracted_records:extracted,route_records:reviewed+extracted};
  assert.equal(matches(material,selected,query,exact,scope),wanted);
  assert.equal(matches(material,selected,query,exact,'all'),true);
 }
});
test('inventory navigation and headings describe the published collection',()=>{
 const builder=source('scripts/build_inventory.py');
 for(const text of ['view the inventory','Published material systems','Contributing papers','Website source coverage and published collection'])assert.ok(builder.includes(text));
 assert.ok(!builder.includes('view the reviewed inventory'));
});
