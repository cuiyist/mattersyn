import fs from 'node:fs';import {pathToFileURL} from 'node:url';
const a=process.argv[2],out=process.argv[3];
const m=await import(pathToFileURL(a+'/sasongko2025-protocol.mjs'));
const rs=JSON.parse(fs.readFileSync(a+'/records.json','utf8'));
let count=0;const checks=[];
class E{constructor(t){this.tagName=t;this.style={};this.dataset={};this.children=[];this.innerHTML='';this.textContent='';}append(...x){this.children.push(...x);}querySelector(){return{style:{}};}}
globalThis.document={createElement:t=>new E(t)};
for(const r of rs)for(const o of r.operations){const s=m.buildSasongko2025Scene(o,r),art=m.createSasongko2025Art(o,r),grid=m.createSasongko2025ConditionGrid(o,r);if(!s||art.dataset.scene!==r.record_id+'--'+o.id||grid.children.length!==s.rows.length)throw Error('Selection '+o.id);if(m.buildSasongko2025Scene(o,{...r,lineage:{source_group:'foreign'}})!==null||m.buildSasongko2025Scene({...o,id:'unknown'},r)!==null)throw Error('Scope');if(!s.rows.every(x=>typeof x.value==='string'&&!/undefined|NaN/.test(x.value)))throw Error('Value');checks.push({record:r.record_id,operation:o.id,rows:s.rows.length,passed:true});count++;}
if(count!==21)throw Error('Count');fs.writeFileSync(out,JSON.stringify({status:'passed',scenes:count,checks},null,2));