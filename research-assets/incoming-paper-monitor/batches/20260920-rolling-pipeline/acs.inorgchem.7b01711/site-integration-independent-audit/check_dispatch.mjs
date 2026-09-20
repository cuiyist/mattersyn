import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const A=path.dirname(fileURLToPath(import.meta.url));
const S='[local path redacted]';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const checks=[];const ck=(x,s)=>checks.push({ok:!!x,label:s});
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.style={};this.attrs={};this.textContent='';this.events={};this.className='';this.classList={add:(...x)=>{this.className+=' '+x.join(' ');},toggle:()=>{}};}
 append(...n){this.children.push(...n);}
 replaceChildren(...n){this.children=[...n];}
 setAttribute(k,v){this.attrs[k]=v;}
 addEventListener(k,f){this.events[k]=f;}
 querySelector(q){if(q==='svg'&&this.innerHTML?.includes('<svg'))return {style:{},outerHTML:this.innerHTML};return this.children.find(c=>c.tag===q)||this.children.map(c=>c.querySelector?.(q)).find(Boolean)||null;}
}
globalThis.document={createElement:t=>new Element(t),body:new Element('body')};
const dispatch=await import(pathToFileURL(path.join(S,'dist/protocol-visuals.mjs')));
const mod=await import(pathToFileURL(path.join(S,'dist/morrison2017-protocol.mjs')));
const records=fs.readdirSync(path.join(S,'data/records')).filter(x=>x.endsWith('.json')).map(x=>read(path.join(S,'data/records',x)));
const original=JSON.stringify(records);let operations=0,rows=0,foreign=0;
for(const r of records){
 if(r.lineage.source_group!=='morrison2017'){
  for(const o of r.operations){foreign++;ck(mod.buildMorrison2017Scene(o,r)===null,'foreign operation rejected '+r.record_id+' '+o.id);}
  continue;
 }
 const host=new Element('div');dispatch.mountProtocol(host,r);
 if(!r.operations.length){ck(host.children.length===0,'zero operation record unmounted '+r.record_id);continue;}
 const [bar,display]=host.children;ck(bar.children.length===r.operations.length,'integrated stage button count '+r.record_id);
 for(const [i,o] of r.operations.entries()){
  operations++;bar.children[i].events.click();const scene=mod.buildMorrison2017Scene(o,r),[visual,copy]=display.children;
  ck(visual.children[0].dataset.scene===scene.kind,'exact scene selected '+r.record_id+' '+o.id);
  ck(visual.children[0].innerHTML===scene.artSvg,'actual dispatched artwork '+o.id);
  ck(visual.children[1].textContent===scene.caption,'actual dispatched caption '+o.id);
  ck(copy.children[1].textContent===o.label&&copy.children[2].textContent===o.description,'selected source operation text '+o.id);
  const grids=copy.children.filter(c=>c.tag==='dl');ck(grids.length===1,'only source condition grid '+o.id);
  const grid=grids[0];ck(grid.children.length===scene.rows.length,'no generic duplicate condition rows '+o.id);
  for(const [j,x] of scene.rows.entries()){rows++;ck(grid.children[j].children[0].textContent===x.label&&grid.children[j].children[1].textContent===x.value,'exact integrated condition '+o.id+' '+j);}
  ck(bar.children[i].attrs['aria-pressed']==='true','active selection state '+o.id);
 }
}
ck(JSON.stringify(records)===original,'actual integrated module does not mutate any canonical record');
ck(operations===24&&rows===155,'24 operations and 155 adjacent rows dispatched');
const files=['dist/protocol-visuals.mjs','dist/morrison2017-protocol.mjs','dist/quantity-value.mjs'];
const out={at:new Date().toISOString(),status:checks.every(x=>x.ok)?'passed':'open_findings',scope:'Actual shared mountProtocol dispatch in a minimal DOM, not a browser/visual science re-audit.',counts:{operations,rows,foreign_operations_rejected:foreign,checks:checks.length},failures:checks.filter(x=>!x.ok),bound_files:Object.fromEntries([...files.map(x=>[path.join(S,x),hash(path.join(S,x))]),[fileURLToPath(import.meta.url),hash(fileURLToPath(import.meta.url))]])};
fs.writeFileSync(path.join(A,'integration-dispatch-checks.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify({...out,bound_files:undefined},null,2));
