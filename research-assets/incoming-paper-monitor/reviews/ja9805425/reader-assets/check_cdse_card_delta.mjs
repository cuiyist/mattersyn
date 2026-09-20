// Bounded execution of the actual changed CdSe method-card module. No Site writes.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import{pathToFileURL,fileURLToPath}from'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));const dist='[local path redacted]';
const nodes=[],ids=new Map();
class E{
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.events={};this._text='';nodes.push(this);}
 set id(v){this._id=v;ids.set(v,this);}get id(){return this._id;}
 set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(x=>typeof x==='string'?x:x.textContent).join('');}
 append(...cs){this.children.push(...cs);}replaceChildren(...cs){this._text='';this.children=[];this.append(...cs);}addEventListener(n,f){this.events[n]=f;}
}
globalThis.document={body:{dataset:{material:'CdSe'}},createElement:t=>new E(t),getElementById:id=>ids.get(id),querySelector:s=>ids.get(s.replace(/^#/,'')),title:''};
for(const id of['methods','material-papers','more-papers','paper-contribution-count']){const n=new E('div');n.id=id;}
globalThis.location={search:''};
globalThis.fetch=async rel=>{const p=path.resolve(dist,String(rel));if(!p.startsWith(path.resolve(dist)+path.sep))throw Error('Unexpected file');return{ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};};
const errors=[];const old=console.error;console.error=(...a)=>errors.push(a.map(String).join(' '));
await import(pathToFileURL(path.join(dist,'material-hub.mjs')).href+'?delta='+Date.now());console.error=old;
const index=JSON.parse(fs.readFileSync(path.join(dist,'data/materials-index.json'),'utf8'));
const entry=index.materials.find(m=>m.formula==='CdSe');const hub=JSON.parse(fs.readFileSync(path.join(dist,'data/materials',entry.id+'.json'),'utf8'));
const represented=new Set(['murray-1993-cdse-method-1','murray-1993-cdse-method-2','peng-2000-cdse-typical','peng-2000-cdse-high-aspect-ratio','nakonechnyi-2017-zb-cdse-core','nakonechnyi-2017-zb-cdse-cds-seeded-growth']);
const expected=hub.records.filter(r=>r.is_synthesis_route&&r.collection==='reviewed_literature'&&!represented.has(r.record_id));
const cards=nodes.filter(n=>n.className==='method-card');const links=cards.map(n=>String(n.href));
const checks=[
 {name:'No runtime errors',passed:errors.length===0},
 {name:'Every additional reviewed synthesis route renders once',passed:cards.length===expected.length&&expected.every(r=>links.filter(h=>h===r.page_url).length===1)},
 {name:'New Peng1998 CdSe route is visible',passed:links.includes('records/peng-1998-cdse-focusing.html')},
 {name:'Pre-existing represented routes are not duplicated',passed:[...represented].every(r=>!links.includes('records/'+r+'.html'))},
 {name:'No supporting procedure or unreviewed record promoted',passed:links.every(h=>expected.some(r=>r.page_url===h))},
 {name:'Actual card contains academic title and method',passed:expected.every(r=>cards.find(c=>String(c.href)===r.page_url)?.textContent.includes(r.title)&&cards.find(c=>String(c.href)===r.page_url)?.textContent.includes(r.method.toUpperCase()))}
];
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const result={status:checks.every(c=>c.passed)?'passed':'failed',checked_utc:new Date().toISOString(),scope:'Controlled execution of actual changed CdSe card code; root browser QA is separate.',actual_card_urls:links,expected_record_ids:expected.map(r=>r.record_id),errors,checks,artifact_sha256:Object.fromEntries(['material-hub.mjs','cdse.html','data/materials/'+entry.id+'.json'].map(p=>['dist/'+p,sha(path.join(dist,p))]))};
fs.writeFileSync(path.join(here,'cdse-card-delta.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,checks:checks.length,cards:links.length,failures:checks.filter(c=>!c.passed)}));if(result.status!=='passed')process.exitCode=1;
