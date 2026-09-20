// Execute the actual built source-reader module in a controlled DOM.
// Run only after the owning root confirms its build is ready. No Site writes.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
const dist='[local path redacted]';
const ledger=JSON.parse(fs.readFileSync(path.join(dist,'data/paper-reviews/braun2001.json'),'utf8'));
const nodes=[],idMap=new Map();
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this.events={};this.value='';this._text='';this.className='';this.hidden=false;this.style={};this.classList={add:(name)=>{this.className+=' '+name;},toggle:(name,on)=>{const a=new Set(this.className.split(/\s+/).filter(Boolean));if(on)a.add(name);else a.delete(name);this.className=[...a].join(' ');}};nodes.push(this);}
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
globalThis.location={search:'?id=braun2001',hash:''};
globalThis.fetch=async rel=>{const p=path.resolve(dist,String(rel));if(!p.startsWith(path.resolve(dist)+path.sep))throw Error('Unexpected path');return{ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};};
const consoleErrors=[];const priorError=console.error;console.error=(...args)=>consoleErrors.push(args.map(String).join(' '));
await import(pathToFileURL(path.join(dist,'paper-review.mjs')).href+'?audit='+Date.now());
console.error=priorError;
const checks=[],check=(name,value)=>checks.push({name,passed:!!value});
const cards=nodes.filter(n=>n.dataset.evidenceItem),cardMap=new Map(cards.map(n=>[n.dataset.evidenceItem,n]));
const items=ledger.reader_sections.flatMap(s=>s.items);
check('All 85 source items executed',cards.length===85&&items.length===85);
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
check('Four original figure cards',figureCards.length===4);
for(const [i,f] of ledger.figures.entries()){
 const text=figureCards[i]?.textContent||'';
 check(f.id+' scope and quantitative context displayed',text.includes(f.sample_scope)&&f.quantitative_context.every(x=>text.includes(x)));
 check(f.id+' caption and locators displayed',text.includes(f.caption_paraphrase)&&f.source_locators.every(x=>text.includes(x)));
}
const allAssets=['figures','tables','equations','source_notes','schemes'].flatMap(k=>ledger[k]||[]);
const imageLinks=nodes.filter(n=>n.dataset.figure),filenames=[...new Set(imageLinks.map(n=>String(n.dataset.figure).split('/').pop()))];
check('All 8 original assets accessible',allAssets.length===8&&filenames.length===8&&allAssets.every(a=>filenames.includes(a.public_asset.split('/').pop())));
for(const a of allAssets)check('Original asset exists '+a.id,fs.existsSync(path.join(dist,a.public_asset)));
check('Four-page main-only review displayed',document.getElementById('review-summary').textContent.includes('4 pages')&&ledger.documents.length===1&&ledger.documents[0].role==='main');
check('SI remains unverified',ledger.supporting_information.status==='not_located_or_matched');
check('SI search limitation explicit',cardMap.get('coverage')?.textContent.includes('no local SI is matched'));
check('Core-size discrepancy explicit',cardMap.get('core-size-conflict')?.textContent.includes('3.5 nm')&&cardMap.get('core-size-conflict')?.textContent.includes('3.2 nm'));
check('Inset label discrepancy explicit',cardMap.get('inset-label-conflict')?.textContent.includes('bleach'));
check('System III stage d correct',cardMap.get('absorption-stages-iii')?.textContent.includes('d: CdS/(HgS)₁/(CdS)₃'));
const input=nodes.find(n=>n.tagName==='input'&&n.placeholder==='Chemical, condition, sample, technique or interpretation');
if(input?.events.input){input.value='mercury';input.events.input();check('Source search filters meaningful subset',cards.some(n=>!n.hidden)&&cards.some(n=>n.hidden));input.value='';input.events.input();check('Cleared search restores all items',cards.every(n=>!n.hidden));}else check('Source search wired',false);
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
check('All expected reagent identity bindings',bindingCount===Object.values(expectedBindings).reduce((a,x)=>a+Object.keys(x).length,0));
const {buildBraun2001Scene}=await import(pathToFileURL(path.join(dist,'braun2001-protocol.mjs')).href+'?audit='+Date.now());
const {buildBraun2001Scene:privateScene}=await import(pathToFileURL(path.join(privateBase,'visuals/braun2001-protocol.mjs')).href+'?audit='+Date.now());
let operationCount=0;const kinds=new Set();
const allRecordIds=[...new Set(ledger.recipe_inventory.flatMap(r=>r.record_ids||[]))];
for(const rid of allRecordIds){
 const record=JSON.parse(fs.readFileSync(path.join(dist,'data/records',rid+'.json'),'utf8'));
 for(const op of record.operations){
  operationCount++;const scene=buildBraun2001Scene(op,record),expected=privateScene(op,record);
  check(rid+'/'+op.id+' source-specific scene',!!scene&&!!expected);
  if(scene&&expected){kinds.add(scene.kind);check(rid+'/'+op.id+' exact private-audited scene',scene.svg===expected.svg);check(rid+'/'+op.id+' apparatus disclosure',scene.svg.includes('explanatory'));}
 }
}
check('All 45 operations have source-specific scenes',operationCount===45);
check('Stage-specific illustrations have multiple scene kinds',kinds.size>3);
const descend=(root)=>[root,...root.children.filter(x=>x instanceof Element).flatMap(descend)];
const {mountProtocol}=await import(pathToFileURL(path.join(dist,'protocol-visuals.mjs')).href+'?audit='+Date.now());
let mountedOperations=0,mountedQuantities=0;
for(const rid of allRecordIds){
 const record=JSON.parse(fs.readFileSync(path.join(dist,'data/records',rid+'.json'),'utf8'));
 if(!record.operations.length)continue;
 const host=new Element('div');mountProtocol(host,record);
 const bar=host.children.find(x=>x.className==='protocol-step-list');
 check(rid+' interactive buttons created',bar?.children.length===record.operations.length);
 for(const [index,op] of record.operations.entries()){
  bar.children[index].events.click();mountedOperations++;
  const tree=descend(host),copy=tree.find(x=>x.className==='protocol-copy'),art=tree.find(x=>x.className==='protocol-art protocol-art-braun2001');
  check(rid+'/'+op.id+' mounted source-specific artwork',art?.innerHTML===buildBraun2001Scene(op,record).svg);
  check(rid+'/'+op.id+' active button and text',bar.children[index].attributes['aria-pressed']==='true'&&copy?.textContent.includes(op.label)&&copy?.textContent.includes(op.description));
  const dl=descend(copy).filter(x=>x.tagName==='dl'),conditionRows=dl.flatMap(x=>x.children);
  for(const [key,q]of Object.entries(op.parameters)){
   const rows=conditionRows.filter(x=>x.children.find(n=>n.tagName==='dt')?.textContent===key.replaceAll('_',' '));
   const dd=rows[0]?.children.find(n=>n.tagName==='dd')?.textContent||'';mountedQuantities++;
   check(rid+'/'+op.id+'/'+key+' exactly one visible condition row',rows.length===1);
   if(q.value!==null&&q.value!==undefined)check(rid+'/'+op.id+'/'+key+' scalar visible',dd.includes(String(q.value)));
   else if(q.minimum!==null&&q.minimum!==undefined&&q.maximum!==null&&q.maximum!==undefined)check(rid+'/'+op.id+'/'+key+' interval visible',dd.includes(String(q.minimum))&&dd.includes(String(q.maximum))&&/[–,[\]()]/.test(dd));
   else if(q.minimum!==null&&q.minimum!==undefined)check(rid+'/'+op.id+'/'+key+' lower bound visible',dd.includes((q.minimum_exclusive?'>':'≥')+q.minimum));
   else if(q.maximum!==null&&q.maximum!==undefined)check(rid+'/'+op.id+'/'+key+' upper bound visible',dd.includes((q.maximum_exclusive?'<':'≤')+q.maximum));
   else check(rid+'/'+op.id+'/'+key+' unknown remains unknown',/not reported/i.test(dd));
   if(q.unit&&q.status!=='not_reported')check(rid+'/'+op.id+'/'+key+' unit visible',dd.includes(({degC:'°C',uL:'µL',uM:'µM',uJ:'µJ',um:'µm'})[q.unit]||q.unit));
   if(q.approximate&&q.value!==null)check(rid+'/'+op.id+'/'+key+' approximation visible',dd.includes('≈'));
   if(q.basis)check(rid+'/'+op.id+'/'+key+' evidence basis visible',dd.includes(q.basis));
  }
 }
}
check('All 45 actual mounted stages exercised',mountedOperations===45);
check('All 95 actual condition quantities displayed',mountedQuantities===95);
const failures=checks.filter(c=>!c.passed);
const result={status:failures.length?'failed':'passed',checked_utc:new Date().toISOString(),scope:'Controlled DOM execution of actual source-reader and apparatus modules, exact original-asset accessibility and source-defined molecular bindings. No browser geometry or publication claim.',reader_items:cards.length,unique_original_assets:filenames.length,operation_count:operationCount,mounted_operations:mountedOperations,mounted_quantities:mountedQuantities,binding_count:bindingCount,checks_passed:checks.length-failures.length,check_count:checks.length,failures,console_errors:consoleErrors,checks,artifact_sha256:Object.fromEntries(['paper-review.mjs','source-evidence.mjs','protocol-visuals.mjs','quantity-value.mjs','braun2001-protocol.mjs','data/paper-reviews/braun2001.json','assets/chemical-registry/bindings.json','assets/chemical-registry/registry.json'].map(p=>['dist/'+p,digest(path.join(dist,p))]))};
fs.writeFileSync(path.join(here,'reader-runtime-check.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,reader_items:cards.length,unique_original_assets:filenames.length,operations:operationCount,bindings:bindingCount,check_count:checks.length,failures}));
if(failures.length)process.exitCode=1;
