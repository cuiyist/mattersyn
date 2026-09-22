import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const P=path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Z]:)/i,'$1')),D='[local path redacted]';
const source=fs.readFileSync(D+'/protocol-references.mjs','utf8');
class E {constructor(tag,text,cls){this.tag=tag;this.textContent=text||'';this.className=cls||'';this.children=[];this.isConnected=true;}append(...x){this.children.push(...x);}setAttribute(){}querySelector(){return null;}}
globalThis.__refsFixture={E,links:[]};
const mocks=`const {E,links}=globalThis.__refsFixture; const el=(...x)=>new E(...x);const button=(label,fn,cls)=>{links.push(label);return new E('button',label,cls);};const isEquipment=()=>false;const recordURL=id=>id;const link=(label)=>new E('a',label);const chemicalRegistry=async()=>({});const chemicalEntry=(_,rid,mid)=>({id:mid});const openChemical=()=>{};`;
const module=await import('data:text/javascript;base64,'+Buffer.from(mocks+source.replace(/^import .*;\r?\n/gm,'')).toString('base64'));
const r=JSON.parse(fs.readFileSync(D+'/data/records/heo-2003-in66-route.json','utf8')),o=r.operations.find(x=>x.id==='host');
const node={textContent:o.description,parentElement:{closest:()=>null},replaceWith(){this.replaced=true;}};
globalThis.NodeFilter={SHOW_TEXT:4};globalThis.document={createTreeWalker(){let once=false;return {currentNode:node,nextNode(){if(once)return false;once=true;return true;}};},createDocumentFragment:()=>new E('fragment'),createTextNode:text=>new E('text',text)};
const host=new E('div');await module.mountProtocolReferences(host,r,o);
const panel=host.children.find(x=>x.className==='protocol-chemical-links');
assert.ok(panel);assert.deepEqual(panel.children.map(x=>x.textContent),['Sodium zeolite X','Fine Pyrex capillary']);
assert.ok(!globalThis.__refsFixture.links.includes('in'));assert.ok(!globalThis.__refsFixture.links.includes('Indium metal'));
const result={status:'passed',scope:'Actual corrected function with original Heo host-stage inputs and description; lower-case in is not linked to indium and no prose-derived indium chip is added. DOM fixture, not browser QA.',checks:3};
fs.writeFileSync(P+'/protocol-correction-tests.json',JSON.stringify(result,null,2)+'\n');console.log(result);
