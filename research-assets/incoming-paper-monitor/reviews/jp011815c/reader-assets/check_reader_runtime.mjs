// Execute the actual built source-reader module in a controlled DOM.
// Run only after the owning root confirms its build is ready. No Site writes.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
const dist='[local path redacted]';
const ledger=JSON.parse(fs.readFileSync(path.join(dist,'data/paper-reviews/shah2001.json'),'utf8'));
const nodes=[],idMap=new Map();
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this.events={};this.value='';this._text='';this.className='';this.hidden=false;nodes.push(this);}
 set id(value){this._id=value;idMap.set(value,this);}get id(){return this._id||'';}
 set textContent(value){this._text=String(value);this.children=[];}get textContent(){return this._text+this.children.map(x=>typeof x==='string'?x:x.textContent).join('');}
 append(...children){for(const c of children){this.children.push(c);if(typeof c==='object')c.parentNode=this;}}
 insertBefore(child,target){const i=this.children.indexOf(target);if(i<0)this.append(child);else{this.children.splice(i,0,child);child.parentNode=this;}}
 replaceChildren(...children){this._text='';this.children=[];this.append(...children);}
 setAttribute(name,value){this.attributes[name]=String(value);}
 addEventListener(name,fn){this.events[name]=fn;}scrollIntoView(){}showModal(){}close(){}
}
globalThis.document={createElement:tag=>new Element(tag),createTextNode:text=>({textContent:String(text)}),getElementById:id=>idMap.get(id)||null,addEventListener(){},title:''};
for(const id of ['review-title','review-doi','review-summary','review-download','review-body','gaps','figure-dialog','figure-close','figure-title','figure-large']){const e=new Element('div');e.id=id;}
document.getElementById('review-body').append(document.getElementById('gaps'));
globalThis.location={search:'?id=shah2001',hash:''};
globalThis.fetch=async rel=>{const p=path.resolve(dist,String(rel));if(!p.startsWith(path.resolve(dist)+path.sep))throw Error('Unexpected path');return{ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};};
const consoleErrors=[];const priorError=console.error;console.error=(...args)=>consoleErrors.push(args.map(String).join(' '));
await import(pathToFileURL(path.join(dist,'paper-review.mjs')).href+'?audit='+Date.now());
console.error=priorError;
const checks=[],check=(name,value)=>checks.push({name,passed:!!value});
const cards=nodes.filter(n=>n.dataset.evidenceItem),cardMap=new Map(cards.map(n=>[n.dataset.evidenceItem,n]));
const items=ledger.reader_sections.flatMap(s=>s.items);
check('All 138 source items executed',cards.length===138&&items.length===138);
check('Actual reader initialization has no console errors',consoleErrors.length===0);
for(const item of items){
 const card=cardMap.get(item.id),text=card?.textContent||'';
 check(item.id+' source prose',text.includes(item.text));
 check(item.id+' title and claim class',text.includes(item.title)&&text.includes(item.claim_type.replaceAll('_',' ')));
 check(item.id+' notes and exact locators',item.notes.every(x=>text.includes(x))&&item.evidence.every(x=>text.includes(x.locator)));
 for(const f of item.facts){
  check(item.id+' fact '+f.id+' value/unit/basis',text.includes(f.label)&&text.includes(String(f.value))&&(!f.unit||text.includes(f.unit))&&(!f.basis||text.includes(f.basis.replaceAll('_',' '))));
  check(item.id+' fact '+f.id+' qualifiers',!f.qualifier||text.includes(f.qualifier.replaceAll('_',' ')));
 }
 check(item.id+' linked records',item.canonical_links.every(x=>text.includes(x.record_id.replaceAll('_',' '))));
 check(item.id+' sample boundary',!item.sample_scope?.link_limit||text.includes(item.sample_scope.link_limit));
 for(const a of item.original_assets||[])check(item.id+' original source link '+a.id,card.children.some(n=>n.tagName==='a'&&String(n.href).endsWith(a.public_asset)));
}
const figureCards=nodes.filter(n=>n.className==='review-figure');
check('Eleven original figure cards',figureCards.length===11);
for(const [i,f] of ledger.figures.entries()){
 const text=figureCards[i]?.textContent||'';
 check(f.id+' scope and quantitative context displayed',text.includes(f.sample_scope)&&f.quantitative_context.every(x=>text.includes(x)));
 check(f.id+' caption and locators displayed',text.includes(f.caption_paraphrase)&&f.source_locators.every(x=>text.includes(x)));
}
const allAssets=['figures','tables','equations','source_notes','schemes'].flatMap(k=>ledger[k]||[]);
const imageLinks=nodes.filter(n=>n.dataset.figure),filenames=[...new Set(imageLinks.map(n=>String(n.dataset.figure).split('/').pop()))];
check('All 21 original assets accessible',allAssets.length===21&&filenames.length===21&&allAssets.every(a=>filenames.includes(a.public_asset.split('/').pop())));
for(const a of allAssets)check('Original asset exists '+a.id,fs.existsSync(path.join(dist,a.public_asset)));
check('Eight-page main-only review displayed',document.getElementById('review-summary').textContent.includes('8 pages')&&ledger.documents.length===1&&ledger.documents[0].role==='main');
check('SI remains unverified',ledger.supporting_information.status==='not_located_or_matched');
check('All nine table rows rendered',Array.from('abcdefghi').every(c=>cardMap.get('table1-'+c)?.textContent.includes('Ag experiment '+c.toUpperCase())));
check('Pt precursor ambiguity visible',cardMap.get('chemical-pt')?.textContent.includes('unresolved identity'));
check('Optical 59 Å not joined to Table F',cardMap.get('optical-current')?.textContent.includes('not explicitly identified as experiment F'));
check('Five-point Figure 4 discrepancy visible',cardMap.get('ag-temperature-trend')?.textContent.includes('five points'));
check('Experimental versus model scope visible',cardMap.get('cumulative-distribution')?.textContent.includes('author interpretation'));
const input=nodes.find(n=>n.tagName==='input'&&n.placeholder==='Chemical, condition, sample, technique or interpretation');
if(input?.events.input){input.value='polycrystalline';input.events.input();check('Source search filters meaningful subset',cards.some(n=>!n.hidden)&&cards.some(n=>n.hidden));input.value='';input.events.input();check('Cleared search restores all items',cards.every(n=>!n.hidden));}else check('Source search wired',false);
const digest=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const privateBase=path.dirname(here);
const bindings=JSON.parse(fs.readFileSync(path.join(dist,'assets/chemical-registry/bindings.json'),'utf8')).recordBindings;
const expectedBindings=JSON.parse(fs.readFileSync(path.join(privateBase,'visuals/bindings-additions.json'),'utf8')).recordBindings;
const registry=JSON.parse(fs.readFileSync(path.join(dist,'assets/chemical-registry/registry.json'),'utf8')).entries;
const entryMap=new Map(registry.map(e=>[e.id,e]));
let bindingCount=0;
for(const [rid,map] of Object.entries(expectedBindings))for(const [mid,chemical]of Object.entries(map)){
 bindingCount++;check(rid+'/'+mid+' exact identity binding',bindings[rid]?.[mid]===chemical);
 const entry=entryMap.get(chemical);check(chemical+' registry entry exists',!!entry);
 for(const k of ['svgPath','model2dPath','model3dPath'])if(entry?.[k])check(chemical+'/'+k+' asset resolves',fs.existsSync(path.join(dist,'assets/chemical-registry',entry[k])));
}
check('99 reagent identity bindings',bindingCount===99);
const {buildShah2001Scene}=await import(pathToFileURL(path.join(dist,'shah2001-protocol.mjs')).href+'?audit='+Date.now());
const scenes=JSON.parse(fs.readFileSync(path.join(privateBase,'visuals/scene-manifest.json'),'utf8')).scenes;
let operationCount=0;
for(const rid of Object.keys(expectedBindings)){
 const record=JSON.parse(fs.readFileSync(path.join(dist,'data/records',rid+'.json'),'utf8'));
 for(const op of record.operations){
  operationCount++;const s=buildShah2001Scene(op,record),expected=scenes.find(x=>x.record_id===rid&&x.operation_id===op.id);
  check(rid+'/'+op.id+' supported pressure-cell/analysis scene',!!s&&!!expected);
  if(s&&expected)check(rid+'/'+op.id+' exact audited scene markup',crypto.createHash('sha256').update(s.svg).digest('hex')===expected.sha256);
 }
}
// Some observation/procedure records can have no material bindings, but their operations still require coverage.
const allRecordIds=ledger.recipe_inventory.flatMap(r=>r.record_ids||[]);
for(const rid of allRecordIds.filter(rid=>!Object.hasOwn(expectedBindings,rid))){
 const record=JSON.parse(fs.readFileSync(path.join(dist,'data/records',rid+'.json'),'utf8'));
 for(const op of record.operations){operationCount++;const s=buildShah2001Scene(op,record),expected=scenes.find(x=>x.record_id===rid&&x.operation_id===op.id);check(rid+'/'+op.id+' supported scene',!!s&&!!expected);if(s&&expected)check(rid+'/'+op.id+' audited scene markup',crypto.createHash('sha256').update(s.svg).digest('hex')===expected.sha256);}
}
check('74 operations use source-specific scenes',operationCount===74&&scenes.length===74);
const failures=checks.filter(c=>!c.passed);
const result={status:failures.length?'failed':'passed',checked_utc:new Date().toISOString(),scope:'Controlled DOM execution of actual source-reader and apparatus modules, exact original-asset accessibility and 99 molecular bindings. No browser geometry or publication claim.',reader_items:cards.length,unique_original_assets:filenames.length,operation_count:operationCount,binding_count:bindingCount,checks_passed:checks.length-failures.length,check_count:checks.length,failures,console_errors:consoleErrors,checks,artifact_sha256:Object.fromEntries(['paper-review.mjs','source-evidence.mjs','shah2001-protocol.mjs','data/paper-reviews/shah2001.json','assets/chemical-registry/bindings.json','assets/chemical-registry/registry.json'].map(p=>['dist/'+p,digest(path.join(dist,p))]))};
fs.writeFileSync(path.join(here,'reader-runtime-check.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,reader_items:cards.length,unique_original_assets:filenames.length,operations:operationCount,bindings:bindingCount,check_count:checks.length,failures}));
if(failures.length)process.exitCode=1;
