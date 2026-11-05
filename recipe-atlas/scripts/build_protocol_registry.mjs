// Derive which records each per-paper protocol module draws, and write
// static/protocol-module-registry.mjs. Every module's exported scene, art,
// condition-grid and decoration functions are run on every operation of every
// record in data/records, as protocol-visuals.mjs calls them (a condition grid
// only follows its own module's scene). A module
// is listed for each source group where any call returns something (or throws).
// Modules drawing more than MAX_GROUPS source groups are loaded for every record.
//
//   node recipe-atlas/scripts/build_protocol_registry.mjs          write the registry
//   node recipe-atlas/scripts/build_protocol_registry.mjs --check  fail if it is stale
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const STATIC=path.join(ROOT,'static');
const TARGET=path.join(STATIC,'protocol-module-registry.mjs');
export const MAX_GROUPS=3;

class FakeElement{
 constructor(tag='div'){this.tagName=String(tag).toUpperCase();this.children=[];this.dataset={};this.style={};this.attributes={};this.className='';this._html='';this._text='';
  this.classList={add:()=>{},remove:()=>{},toggle:()=>{},contains:()=>false};}
 append(...c){this.children.push(...c);} appendChild(c){this.children.push(c);return c;} prepend(...c){this.children.unshift(...c);}
 replaceChildren(...c){this.children=[...c];} remove(){} insertAdjacentHTML(_,h){this._html+=h;} insertAdjacentElement(_,e){this.children.push(e);return e;}
 setAttribute(k,v){this.attributes[k]=String(v);} getAttribute(k){return this.attributes[k]??null;} removeAttribute(k){delete this.attributes[k];}
 addEventListener(){} querySelector(){return null;} querySelectorAll(){return [];} closest(){return null;} cloneNode(){return new FakeElement(this.tagName);}
 set innerHTML(v){this._html=String(v);} get innerHTML(){return this._html;} set textContent(v){this._text=String(v);this.children=[];} get textContent(){return this._text;}
 get firstChild(){return this.children[0]||null;} get firstElementChild(){return this.children[0]||null;}
 get changed(){return this.children.length>0||this._html!==''||this._text!==''||Object.keys(this.attributes).length>0||this.className!=='';}
}
export function installFakeDocument(){
 const doc={createElement:t=>new FakeElement(t),createElementNS:(_,t)=>new FakeElement(t),createTextNode:t=>{const n=new FakeElement('#text');n.textContent=t;return n;},
  createDocumentFragment:()=>new FakeElement('#fragment'),body:new FakeElement('body'),documentElement:new FakeElement('html'),querySelector:()=>null,querySelectorAll:()=>[],getElementById:()=>null};
 globalThis.document=doc;globalThis.window??=globalThis;globalThis.location??={href:'https://fixture.invalid/',search:''};
 return doc;
}
const moduleKey=file=>file.replace(/^\.\//,'').replace(/\?.*$/,'');
// protocol-visuals calls a condition grid only after that module's own scene matched,
// except the Williamson context note, which it calls for every operation.
const UNCONDITIONAL_GRIDS=new Set(['createWilliamson2021ConditionGrid']);
const called=name=>!/ConditionGrid$/.test(name)||UNCONDITIONAL_GRIDS.has(name);
function draws(name,fn,o,r){
 if(/^decorate/.test(name)){const host=new FakeElement('div');const out=fn(host,o,r);return out!==host||host.changed;}
 if(/^create.*Art$/.test(name))return Boolean(fn(o,r,''));
 return Boolean(fn(o,r));
}

export async function deriveRegistry(){
 installFakeDocument();
 const {PAPER_PROTOCOLS}=await import(pathToFileURL(path.join(STATIC,'protocol-modules.mjs')).href);
 const {reactorDisplayRecord}=await import(pathToFileURL(path.join(STATIC,'reactor-lines.mjs')).href);
 const modules=[];
 for(const entry of PAPER_PROTOCOLS){
  const module=await import(pathToFileURL(path.join(STATIC,moduleKey(entry.file))).href+(entry.file.includes('?')?entry.file.slice(entry.file.indexOf('?')):''));
  for(const name of entry.names)if(typeof module[name]!=='function')throw Error(`${entry.file} does not export ${name}`);
  modules.push({key:moduleKey(entry.file),names:entry.names,module,groups:new Set()});
 }
 const dir=path.join(ROOT,'data/records');
 for(const file of fs.readdirSync(dir).filter(f=>f.endsWith('.json')).sort()){
  const r=JSON.parse(fs.readFileSync(path.join(dir,file),'utf8'));
  if(!r.operations?.length)continue;
  const group=r.lineage?.source_group||'';
  let displayRecord;try{displayRecord=reactorDisplayRecord(r);}catch{displayRecord=r;}
  for(const m of modules){
   if(m.groups.has(group))continue;
   outer:for(const o of displayRecord.operations)for(const name of m.names.filter(called)){
    let hit;try{hit=draws(name,m.module[name],o,displayRecord);}catch{hit=true;}
    if(hit){m.groups.add(group);break outer;}
   }
  }
 }
 const registry={};
 for(const m of modules.sort((a,b)=>a.key.localeCompare(b.key)))registry[m.key]=m.groups.size>MAX_GROUPS?'*':[...m.groups].sort();
 return registry;
}

export function renderRegistry(registry){
 return '// Generated by recipe-atlas/scripts/build_protocol_registry.mjs; do not edit by hand.\n'+
  '// Per-paper protocol module -> the record source groups it draws (\'*\': every record).\n'+
  'export const PROTOCOL_SOURCE_GROUPS=Object.freeze('+JSON.stringify(registry,null,1).replace(/"/g,"'")+');\n';
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const text=renderRegistry(await deriveRegistry());
 if(process.argv.includes('--check')){
  const current=fs.existsSync(TARGET)?fs.readFileSync(TARGET,'utf8'):'';
  if(current!==text){console.error('protocol-module-registry.mjs is stale; run node recipe-atlas/scripts/build_protocol_registry.mjs');process.exit(1);}
  console.log('protocol-module-registry.mjs is current');
 }else{fs.writeFileSync(TARGET,text);console.log('wrote',path.relative(process.cwd(),TARGET));}
}
