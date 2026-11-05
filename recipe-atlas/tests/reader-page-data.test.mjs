import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {deriveRegistry,renderRegistry,installFakeDocument} from '../scripts/build_protocol_registry.mjs';

const visuals=readFileSync(new URL('../static/protocol-visuals.mjs',import.meta.url),'utf8');
const registryText=readFileSync(new URL('../static/protocol-module-registry.mjs',import.meta.url),'utf8');

test('the protocol module registry is current for every record',async()=>{
 // Re-derived from data/records by running each module exactly as protocol-visuals calls it.
 assert.equal(renderRegistry(await deriveRegistry()),registryText,'run node recipe-atlas/scripts/build_protocol_registry.mjs');
});

test('paper protocol scripts are not imported up front',async()=>{
 const {PAPER_PROTOCOLS}=await import('../static/protocol-modules.mjs');
 const papers=new Set(PAPER_PROTOCOLS.map(m=>m.file.replace(/^\.\//,'').replace(/\?.*$/,'')));
 for(const [,file] of visuals.matchAll(/^import \{[^}]+\} from '\.\/([^'?]+)[^']*';$/gm))assert.ok(!papers.has(file),file+' is imported statically');
 const onDisk=readdirSync(new URL('../static/',import.meta.url)).filter(f=>f.endsWith('-protocol.mjs'));
 for(const file of onDisk)assert.ok(papers.has(file),file+' is missing from protocol-modules.mjs');
 for(const m of PAPER_PROTOCOLS)for(const name of m.names)assert.match(visuals,new RegExp('P\\.'+name+'\\('),name+' is not called through the lazy table');
});

class Element{constructor(t){this.tagName=t;this.children=[];this.dataset={};this.className='';}append(...c){this.children.push(...c);}}
installFakeDocument();
globalThis.document.body.dataset={};
const {readerPresentations,attachReaderSlices}=await import('../static/reader-app.mjs');

test('a material page loads labels for its records and a view only for the record it opens',async()=>{
 const fetched=[];
 const files={'data/reader/materials/m1.json':{schema:'mattersyn-reader-material/1',material:{record_ids:['a','b']},method_labels:{b:'Hot injection'}},
  'data/records/a.json':{record_id:'a'},'data/records/b.json':{record_id:'b'},'data/reader/records/a.json':{figures:[1],scopeLabel:'A'}};
 const load=async path=>{fetched.push(path);if(!(path in files))throw Error('missing '+path);return structuredClone(files[path]);};
 const presentations=await readerPresentations(false,load),store=new Map();
 assert.deepEqual(presentations,{records:{},materials:{}});
 await attachReaderSlices(presentations,'m1',['a','b'],load,store);
 assert.deepEqual(fetched,['data/reader/materials/m1.json']);
 assert.equal(presentations.records.b.method_label,'Hot injection');
 const record=await store.get('data/records/a.json');
 assert.deepEqual(record,{record_id:'a'});
 assert.deepEqual(presentations.records.a,{figures:[1],scopeLabel:'A'});
 assert.deepEqual(fetched.sort(),['data/reader/materials/m1.json','data/reader/records/a.json','data/records/a.json']);
 assert.equal(await store.get('data/records/a.json'),record,'each record is fetched once');
 assert.deepEqual(await store.get('data/records/b.json'),{record_id:'b'});
 assert.equal(presentations.records.b.method_label,'Hot injection','a record without a view keeps its label');
});

test('record pages find their materials and eligibility from the index',async()=>{
 const load=async()=>({schema:'mattersyn-reader-index/1',record_materials:{a:['m1','m2'],b:['m1'],c:[]}});
 const presentations=await readerPresentations(true,load);
 assert.deepEqual(Object.keys(presentations.records).sort(),['a','b','c']);
 assert.deepEqual(presentations.materials.m1.record_ids.sort(),['a','b']);
 assert.deepEqual(presentations.materials.m2.record_ids,['a']);
});

test('without per-page files the reader falls back to the combined presentation',async()=>{
 const combined=async()=>({records:{a:{scopeLabel:'A'}},materials:{m1:{record_ids:['a']}}});
 const presentations={records:{},materials:{}};
 await attachReaderSlices(presentations,'m1',['a'],async()=>{throw Error('404');},new Map(),combined);
 assert.deepEqual(presentations.records.a,{scopeLabel:'A'});
});

test('a record outside every material page still loads its own view',async()=>{
 const files={'data/records/x.json':{record_id:'x'},'data/reader/records/x.json':{scopeLabel:'X'}};
 const load=async path=>{if(!(path in files))throw Error('missing '+path);return files[path];};
 const presentations={records:{x:{}},materials:{}},store=new Map();
 await attachReaderSlices(presentations,undefined,['x'],load,store,async()=>{throw Error('combined file must not be needed');});
 assert.deepEqual(await store.get('data/records/x.json'),{record_id:'x'});
 assert.deepEqual(presentations.records.x,{scopeLabel:'X'});
});
