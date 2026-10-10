import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const css=readFileSync(new URL('../static/styles.css',import.meta.url),'utf8');
const html=readFileSync(new URL('../static/paper.html',import.meta.url),'utf8');
function checkWrapping(sheet){
  const rules=[...sheet.matchAll(/([^{}]+)\{([^{}]*)\}/g)].filter(m=>m[1].trim()==='#paper-title');
  assert.equal(rules.length,1,'paper title needs one explicit wrapping rule');
  const declarations=new Map(rules[0][2].split(';').filter(Boolean).map(d=>{const i=d.indexOf(':');return [d.slice(0,i).trim(),d.slice(i+1).trim()];}));
  assert.equal(declarations.get('overflow-wrap'),'anywhere');
  for(const key of ['overflow','overflow-x','text-overflow','clip','clip-path','height','max-height']) assert.equal(declarations.has(key),false,`${key} must not hide or truncate the title`);
  assert.notEqual(declarations.get('white-space'),'nowrap');
}
test('paper heading exposes the scoped wrapping target',()=>{
  assert.match(html,/<h1 id="paper-title">Paper<\/h1>/);
});
test('long uninterrupted paper-title text wraps without hiding content',()=>{
  const title='A title with '+ 'LongUninterruptedChemicalName'.repeat(3);
  assert.ok(title.split(' ').at(-1).length>80);
  checkWrapping(css);
});
test('missing wrapping, normal wrapping, clipping and truncation regressions reject',()=>{
  assert.throws(()=>checkWrapping(css.replace('#paper-title{overflow-wrap:anywhere}','')));
  for(const bad of ['overflow-wrap:normal','overflow-wrap:anywhere;white-space:nowrap','overflow-wrap:anywhere;overflow:hidden','overflow-wrap:anywhere;overflow-x:clip','overflow-wrap:anywhere;text-overflow:ellipsis','overflow-wrap:anywhere;max-height:1em']){
    assert.throws(()=>checkWrapping(css.replace('#paper-title{overflow-wrap:anywhere}',`#paper-title{${bad}}`)));
  }
});
