// A consumer smoke test, not a browser or visual-layout audit.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import crypto from 'node:crypto';
const dir=path.dirname(fileURLToPath(import.meta.url));
const reader=JSON.parse(fs.readFileSync(path.join(dir,'ribeiro2004.json'),'utf8'));
class Element{
 constructor(tag,text=''){this.tag=tag;this.children=[];this.localText=text;this.dataset={};this.listeners={};this.hidden=false;this.value='';}
 set textContent(value){this.localText=String(value);this.children=[];}
 get textContent(){return this.localText+this.children.map(c=>typeof c==='string'?c:c.textContent).join('');}
 append(...xs){this.children.push(...xs);}
 replaceChildren(...xs){this.localText='';this.children=xs;}
 setAttribute(k,v){this[k]=v;}
 addEventListener(k,v){this.listeners[k]=v;}
}
globalThis.document={createElement:t=>new Element(t),createTextNode:t=>new Element('#text',t)};
const site='[local path redacted]';
const {sourceItemCard,mountSourceSections}=await import(pathToFileURL(site).href);
const checks=[];
function check(name,c){checks.push({check:name,passed:!!c});if(!c)throw new Error(name);}
const flat=reader.reader_sections.flatMap(s=>s.items),texts=new Map();
for(const item of flat){
 const card=sourceItemCard(item,{compact:true,sourceDoi:reader.doi,sourceId:reader.paper_id});texts.set(item.id,card.textContent);
 check('title and prose '+item.id,card.textContent.includes(item.title)&&card.textContent.includes(item.text));
 for(const f of item.facts)check('fact label rendered '+f.id,card.textContent.includes(f.label));
 check('source locator rendered '+item.id,item.evidence.some(e=>card.textContent.includes(e.locator)));
 check('no raw metadata dump '+item.id,!card.textContent.includes('source_sha256')&&!card.textContent.includes('reader-assets\\'));
}
check('ratio visible',texts.get('operation-hydrolysis-hydrolyze').includes('500:1'));
check('missing pH visible',texts.get('operation-ph-treatment-redisperse').includes('Not reported')&&texts.get('operation-ph-treatment-redisperse').includes('Final pH after basic TBAOH addition is unreported'));
check('model fit visible',texts.get('equation-4').includes('0.14')&&texts.get('equation-4').includes('c < 0.04'));
const host=new Element('main');mountSourceSections(host,reader);
const walk=n=>[n,...n.children.flatMap(c=>typeof c==='string'?[]:walk(c))];
const nodes=walk(host),cards=nodes.filter(n=>n.dataset.evidenceItem),input=nodes.find(n=>n.tag==='input');
check('all cards mounted',cards.length===flat.length);
check('search listener exists',typeof input.listeners.input==='function');
input.value='tbaoh';input.listeners.input();
check('search filters some cards',cards.some(n=>n.hidden)&&cards.some(n=>!n.hidden));
input.value='';input.listeners.input();check('search reset shows all cards',cards.every(n=>!n.hidden));
fs.writeFileSync(path.join(dir,'reader-render-check.json'),JSON.stringify({schema:'mattersyn-private-reader-render-smoke/1',source_id:'ribeiro2004',checked_at:new Date().toISOString(),rendered_items:flat.length,check_count:checks.length,checks_passed:true,checks,source_evidence_sha256:crypto.createHash('sha256').update(fs.readFileSync(site)).digest('hex'),reader_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,'ribeiro2004.json'))).digest('hex'),actual_browser_qa:false},null,2)+'\n');
console.log(JSON.stringify({items:flat.length,checks:checks.length,passed:true}));
