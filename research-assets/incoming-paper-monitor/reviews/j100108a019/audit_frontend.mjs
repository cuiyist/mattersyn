// Read-only evaluation of actual frontend source with a minimal DOM.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import {fileURLToPath,pathToFileURL} from 'node:url';
const HERE=path.dirname(fileURLToPath(import.meta.url));
const SITE='[local path redacted]';
const names=['source-evidence.mjs','paper-review.mjs','material-guide.mjs','analysis-protocol.mjs'];
const texts=Object.fromEntries(names.map(n=>[n,fs.readFileSync(path.join(SITE,n),'utf8')]));
const hash=t=>crypto.createHash('sha256').update(t).digest('hex');
const importedReview=path.join(SITE,'data/paper-reviews/littau1993.json');
const reviewPath=fs.existsSync(importedReview)?importedReview:path.join(HERE,'public-review-proposal/littau1993.json');
const review=JSON.parse(fs.readFileSync(reviewPath,'utf8'));
const records=Object.fromEntries(['canonical-drafts','procedure-drafts','context-drafts'].flatMap(folder=>fs.readdirSync(path.join(HERE,folder)).filter(n=>n.endsWith('.json')).map(n=>{const imported=path.join(SITE,'data/records',n);const p=fs.existsSync(imported)?imported:path.join(HERE,folder,n);const r=JSON.parse(fs.readFileSync(p,'utf8'));return [r.record_id,r];})));
class Node {
 constructor(tag='text',text=''){this.tagName=tag.toUpperCase();this.children=[];this._text=text;this.dataset={};this.style={};this.attributes={};this.listeners={};this.hidden=false;this.value='';this.className='';this.parentNode=null;this._html='';}
 append(...children){for(let c of children){if(typeof c==='string')c=new Node('text',c);if(c){if(this.tagName==='SELECT'&&c.tagName==='OPTION'&&!this.children.length)this.value=c.value;c.parentNode=this;this.children.push(c);}}}
 appendChild(c){this.append(c);return c;}
 replaceChildren(...children){this.children=[];this._text='';this._html='';this.append(...children);}
 insertBefore(c,ref){if(!ref||!this.children.includes(ref))return this.append(c);c.parentNode=this;this.children.splice(this.children.indexOf(ref),0,c);}
 set textContent(v){this._text=String(v??'');this.children=[];this._html='';}
 get textContent(){return this._text+(this._html?this._html.replace(/<[^>]*>/g,' '):'')+this.children.map(c=>c.textContent).join(' ');}
 set innerHTML(v){this._html=String(v);this.children=[];this._text='';}
 get innerHTML(){return this._html;}
 setAttribute(k,v){this.attributes[k]=String(v);}
 getAttribute(k){return this.attributes[k];}
 addEventListener(k,fn){this.listeners[k]=fn;}
 removeEventListener(k){delete this.listeners[k];}
 scrollIntoView(){}
 showModal(){this.open=true;}
 close(){this.open=false;}
 querySelectorAll(s){return walk(this).filter(n=>matches(n,s));}
 querySelector(s){return this.querySelectorAll(s)[0]||null;}
}
const walk=n=>[n,...n.children.flatMap(walk)];
const matches=(n,s)=>s.startsWith('.')?n.className.split(' ').includes(s.slice(1)):s.startsWith('#')?n.id===s.slice(1):n.tagName.toLowerCase()===s;
function documentMock(){const body=new Node('body');return {body,title:'',createElement:t=>new Node(t),createTextNode:t=>new Node('text',t),getElementById:id=>walk(body).find(n=>n.id===id)||null,addEventListener(){}};}
function addId(doc,id,tag='div'){const n=new Node(tag);n.id=id;doc.body.append(n);return n;}
function transformed(name){return texts[name].replace(/^import .+;\s*$/gm,'').replace(/^export \{.+;\s*$/gm,'').replace(/export (async )?function /g,(_,a)=>`${a||''}function `).replaceAll('import.meta.url',JSON.stringify(pathToFileURL(path.join(SITE,name)).href));}
const doc=documentMock();
const env={document:doc,URL,console,Set,Map};
vm.createContext(env);
vm.runInContext(transformed('source-evidence.mjs')+'\nglobalThis.sourceItemCard=sourceItemCard;globalThis.mountSourceSections=mountSourceSections;',env);
const results=[];
const check=(name,pass,details={})=>results.push({name,pass,...details});
const human=x=>String(x??'').replaceAll('_',' ');
let missing=[];let exactLinksLost=[];let approxLost=[];
for(const item of review.reader_sections.flatMap(s=>s.items)){
 const card=env.sourceItemCard(item,{compact:true,sourceDoi:review.doi,sourceId:review.paper_id});
 const text=card.textContent;
 const tests=[['title',item.title],['text',item.text],['claim_type',human(item.claim_type)],...item.notes.map(n=>['note',n]),...item.evidence.map(e=>['evidence',e.locator])];
 for(const [field,value]of tests)if(value&&!text.includes(value))missing.push({id:item.id,field,value});
 const list=walk(card).find(n=>n.className==='source-facts');
 for(const [i,f]of item.facts.entries()){
  const row=list?.children[i];const rt=row?.textContent||'';
  for(const [field,value]of [['label',f.label],['status',human(f.status)],['qualifier',human(f.qualifier)],['basis',f.basis]])if(value&&!rt.includes(value))missing.push({id:item.id,fact:i,field,value});
  const values=typeof f.value==='object'&&f.value!==null?Object.values(f.value):[f.value===null?'Not reported':f.value];
  for(const value of values)if(!rt.includes(String(value)))missing.push({id:item.id,fact:i,field:'value',value});
  if(f.unit&&!rt.includes(f.unit))missing.push({id:item.id,fact:i,field:'unit',value:f.unit});
  for(const e of f.evidence||[])if(!rt.includes(e.locator))missing.push({id:item.id,fact:i,field:'evidence',value:e.locator});
  if(f.approximate&&!/≈|approximat/i.test(rt))approxLost.push({id:item.id,fact:i,label:f.label});
 }
 for(const l of item.canonical_links){
  const anchors=walk(card).filter(n=>n.tagName==='A'&&String(n.href).includes(l.record_id));
  const pointerRetained=!l.json_pointer||text.includes(l.json_pointer)||anchors.some(a=>String(a.href).includes(encodeURIComponent(l.json_pointer)));
  if(!anchors.length||!pointerRetained||!text.includes(l.relation))exactLinksLost.push({id:item.id,record_id:l.record_id,json_pointer:l.json_pointer,recordLink:!!anchors.length,pointerRetained,relationRetained:text.includes(l.relation)});
 }
}
check('Every public item title/text/claim/notes/evidence and every fact label/value/unit/status/qualifier/basis/evidence survives',missing.length===0,{missing});
check('Every approximate fact remains explicitly approximate',approxLost.length===0,{missing:approxLost});
check('Every canonical record/pointer/relation link remains recoverable',exactLinksLost.length===0,{missing:exactLinksLost});
const host=addId(doc,'source-host');env.mountSourceSections(host,review);
const cards=walk(host).filter(n=>n.className==='source-evidence-item');
check('All 136 public items mount exactly once',cards.length===136&&new Set(cards.map(c=>c.dataset.evidenceItem)).size===136,{count:cards.length});
const input=walk(host).find(n=>n.tagName==='INPUT');input.value='slightly above';input.listeners.input();
check('Search retains quantum-yield qualifier context',cards.some(c=>!c.hidden&&c.dataset.evidenceItem==='source-observations-10'));
input.value='unmatched-token-littau-93817';input.listeners.input();
check('Unmatched search hides all evidence cards',cards.every(c=>c.hidden));
input.value='';input.listeners.input();
check('Clearing search restores all items',cards.every(c=>!c.hidden));

async function materialScenario(separateIntuition){
 const d=documentMock();const h=addId(d,'evidence-host');if(separateIntuition)addId(d,'record-intuition-content');
 const context={document:d,URL,console,sourceItemCard:env.sourceItemCard,fetch:async url=>({ok:true,json:async()=>String(url).includes('paper-review-index')?{papers:[{id:'littau1993'}]}:review}),
                mountCrystalReferences:async()=>{},mountProtocol:()=>{},chemicalRegistry:async()=>({}),chemicalEntry:()=>null};
 vm.createContext(context);vm.runInContext(transformed('material-guide.mjs')+'\nglobalThis.mountEvidence=mountEvidence;',context);
 await context.mountEvidence(h,records['littau-1993-si-aerosol-6p0']);
 const grid=walk(h).find(n=>n.className==='guide-evidence-gallery');
 const imgs=walk(grid||new Node()).filter(n=>n.tagName==='IMG');
 const aksVisible=imgs.filter(n=>String(n.src).includes('figure-3.png')||String(n.src).includes('figure-4.png'));
 const hiddenByAncestor=n=>{while(n){if(n.hidden)return true;n=n.parentNode;}return false;};
 return {h,d,grid,imgs,aksVisible:aksVisible.filter(n=>!hiddenByAncestor(n)),buttons:walk(h).filter(n=>['BUTTON','INPUT','SELECT'].includes(n.tagName))};
}
for(const separate of [false,true]){
 const s=await materialScenario(separate);
 check('Material gallery survives intuition rendering ('+(separate?'separate host':'fallback host')+')',!!s.grid,{images:s.imgs.length});
 check('6.0 default gallery excludes unrelated AKS41 original images ('+(separate?'separate host':'fallback host')+')',!!s.grid&&s.aksVisible.length===0,{visibleAKS41:s.aksVisible.map(n=>String(n.src))});
 if(separate){
  const control=s.buttons.find(n=>n.tagName==='SELECT'&&n.getAttribute('aria-label')==='Figure scope');
  check('An explicit all-paper-figures control exists',!!control,{controls:s.buttons.map(n=>n.textContent)});
  if(control){control.value='all';control.onchange();check('All-paper selection restores all thirteen original assets',walk(s.grid).filter(n=>n.className==='guide-figure'&&!n.hidden).length===13);control.value='record';control.onchange();}
 }
}

// Exercise the actual source-review module with network and browser surface mocked.
{
 const d=documentMock();for(const id of ['review-body','review-title','review-doi','review-summary','review-download','figure-dialog','figure-close','figure-title','figure-large'])addId(d,id);
 const body=d.getElementById('review-body');const gaps=new Node('section');gaps.id='gaps';body.append(gaps);
 const errors=[];const ctx={document:d,URL,URLSearchParams,location:{search:'?id=littau1993',hash:''},
  console:{error:e=>errors.push(String(e))},fetch:async()=>({ok:true,json:async()=>review}),mountSourceSections:(h,r)=>{
   const old=env.document;env.document=d;env.mountSourceSections(h,r);env.document=old;}};
 vm.createContext(ctx);await vm.runInContext('(async()=>{'+transformed('paper-review.mjs')+'})()',ctx);
 const publicCards=walk(d.body).filter(n=>n.className==='source-evidence-item');
 check('Source-review module runs and mounts all 136 items',!errors.length&&publicCards.length===136,{errors,count:publicCards.length});
 check('Source-review summary preserves main-only/SI-unverified scope',/main review; SI unverified/.test(d.getElementById('review-summary').textContent),{summary:d.getElementById('review-summary').textContent});
 const headings=walk(d.body).filter(n=>n.tagName==='SUMMARY').map(n=>n.textContent);
 check('Main-only source avoids a misleading Main–SI identity heading',!headings.includes('Main–SI identity verification'),{headingPresent:headings.includes('Main–SI identity verification')});
}

// Analysis actions: source-qualified schematics only; no synthetic data plotted.
{
 const d=documentMock();const ctx={document:d,console};vm.createContext(ctx);
 vm.runInContext(transformed('analysis-protocol.mjs')+'\nglobalThis.createAnalysisArt=createAnalysisArt;',ctx);
 const actions=[];
 for(const r of Object.values(records).filter(r=>r.record_type==='procedure'))for(const o of r.operations){
  const art=ctx.createAnalysisArt(o,r);if(art)actions.push({record:r.record_id,operation:o.id,action:o.action,scene:art.dataset.scene,text:art.textContent,svg:art.innerHTML});
 }
 check('Analysis schematics carry explanatory, non-dimensional equipment caveat',actions.every(x=>x.svg.includes('Explanatory schematic; dimensions do not specify actual equipment.')),{scenes:actions.length});
 check('Analysis schematics do not create artificial measured spectra or diffraction traces',actions.filter(x=>['spectroscopy','diffraction'].includes(x.scene)).every(x=>/No spectrum is invented|No simulated pattern/.test(x.text)));
 fs.writeFileSync(path.join(HERE,'frontend-analysis-scene-audit.json'),JSON.stringify(actions.map(({svg,...x})=>x),null,2)+'\n');
}
const current=Object.fromEntries(names.map(n=>[n,hash(fs.readFileSync(path.join(SITE,n),'utf8'))]));
const reviewed=Object.fromEntries(names.map(n=>[n,hash(texts[n])]));
const filesStable=Object.keys(current).every(n=>current[n]===reviewed[n]);
const report={status:results.every(r=>r.pass)&&filesStable?'passed_bounded_mock_DOM_audit':'findings_or_source_changed',
 scope:'Actual frontend source read and evaluated with minimal DOM/network mocks. This tests data retention and control flow, not real browser layout, focus, zoom or rendering.',
 input_review_file:reviewPath,input_review_sha256:hash(fs.readFileSync(reviewPath)),reviewed_frontend_sha256:reviewed,
 files_stable_during_test:filesStable,results,
 manual_diagram_notes:[
  {priority:'verified_closed',topic:'HPLC schematic',finding:'Previously requested two-column distinction is inspected against the current scene text separately.'},
  {priority:'verified_closed',topic:'Powder preparation versus mounting',finding:'Previously requested preparation-versus-optical-fiber distinction is inspected against the current action-specific branch separately.'},
  {priority:'scope',topic:'Reflux illustration',finding:'A generic reflux condenser is physically plausible but apparatus geometry is not supplied. The schematic caveat must remain; do not claim that exact glassware was reported.'}],
 untouched:'No Site files edited by this audit. Public proposal prose/map revisions were restricted to the private generator/proposal as authorized.',
 remaining:'Root real-browser QA, verified asset/record import and final source-to-view checks remain necessary. No training or publication approval.'};
fs.writeFileSync(path.join(HERE,'frontend-render-audit.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(HERE,'frontend-render-audit.md'),'# Littau frontend data-retention audit\n\n'+report.scope+'\n\n'+results.map(r=>'- '+(r.pass?'PASS':'FINDING')+': '+r.name).join('\n')+'\n\n'+report.manual_diagram_notes.map(x=>'- '+x.topic+': '+x.finding).join('\n')+'\n\n'+report.remaining+'\n');
console.log(JSON.stringify({status:report.status,checks:results.length,failed:results.filter(r=>!r.pass).map(r=>({name:r.name,missing_count:r.missing?.length})),filesStable},null,2));
