// Execute the actual built source-reader module in a controlled DOM.
// Run only after the owning root confirms its build is ready. No Site writes.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
const dist='[local path redacted]';
const ledger=JSON.parse(fs.readFileSync(path.join(dist,'data/paper-reviews/schwartz2003.json'),'utf8'));
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
globalThis.location={search:'?id=schwartz2003',hash:''};
globalThis.fetch=async rel=>{const p=path.resolve(dist,String(rel));if(!p.startsWith(path.resolve(dist)+path.sep))throw Error('Unexpected path');return{ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};};
const consoleErrors=[];const priorError=console.error;console.error=(...args)=>consoleErrors.push(args.map(String).join(' '));
await import(pathToFileURL(path.join(dist,'paper-review.mjs')).href+'?audit='+Date.now());
console.error=priorError;
const checks=[],check=(name,value)=>checks.push({name,passed:!!value});
const cards=nodes.filter(n=>n.dataset.evidenceItem),cardMap=new Map(cards.map(n=>[n.dataset.evidenceItem,n]));
const items=ledger.reader_sections.flatMap(s=>s.items);
check('All 184 source items executed',cards.length===184&&items.length===184);
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
check('Eleven main and six SI original figure cards',figureCards.length===17);
for(const [i,f] of ledger.figures.entries()){
 const text=figureCards[i]?.textContent||'';
 check(f.id+' scope and quantitative context displayed',text.includes(f.sample_scope)&&f.quantitative_context.every(x=>text.includes(x)));
 check(f.id+' caption and locators displayed',text.includes(f.caption_paraphrase)&&f.source_locators.every(x=>text.includes(x)));
}
const allAssets=['figures','tables','equations','source_notes','schemes'].flatMap(k=>ledger[k]||[]);
const imageLinks=nodes.filter(n=>n.dataset.figure),filenames=[...new Set(imageLinks.map(n=>String(n.dataset.figure).split('/').pop()))];
check('All 38 original assets accessible',allAssets.length===38&&filenames.length===38&&allAssets.every(a=>filenames.includes(a.public_asset.split('/').pop())));
for(const a of allAssets)check('Original asset exists '+a.id,fs.existsSync(path.join(dist,a.public_asset)));
check('Fourteen main and four SI pages displayed',document.getElementById('review-summary').textContent.includes('18 pages')&&ledger.documents.length===2&&ledger.documents.find(d=>d.role==='main')?.page_count===14&&ledger.documents.find(d=>d.role==='si')?.page_count===4);
check('SI matched identity explicit',ledger.supporting_information.status==='matched_local_si'&&cardMap.get('si-identity')?.textContent.includes('S1 through S6'));
check('Surface cobalt control remains separate',cardMap.get('surface-control')?.textContent.includes('deliberately')||cardMap.get('surface-control')?.textContent.includes('intentionally'));
check('Nominal and retained dopants distinguished',cardMap.get('dopant-substitution')?.textContent.includes('measured dopant'));
check('Co monitoring conflict explicit',cardMap.get('field-co')?.textContent.includes('15 600')&&cardMap.get('field-co')?.textContent.includes('15 700'));
check('Ni monitoring conflict explicit',cardMap.get('field-ni')?.textContent.includes('15 400')&&cardMap.get('field-ni')?.textContent.includes('15 165'));
check('Curie result remains lower bound',cardMap.get('curie-bound')?.textContent.includes('T_C > 350'));
check('Table2 literature comparison distinct',cardMap.get('table2-comparators')?.textContent.includes('Blank cells'));
const input=nodes.find(n=>n.tagName==='input'&&n.placeholder==='Chemical, condition, sample, technique or interpretation');
if(input?.events.input){input.value='TOPO';input.events.input();check('Source search filters meaningful subset',cards.some(n=>!n.hidden)&&cards.some(n=>n.hidden));input.value='';input.events.input();check('Cleared search restores all items',cards.every(n=>!n.hidden));}else check('Source search wired',false);
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
const {buildSchwartz2003Scene}=await import(pathToFileURL(path.join(dist,'schwartz2003-protocol.mjs')).href+'?audit='+Date.now());
const {buildSchwartz2003Scene:privateScene}=await import(pathToFileURL(path.join(privateBase,'visuals/schwartz2003-protocol.mjs')).href+'?audit='+Date.now());
let operationCount=0;const kinds=new Set();
const allRecordIds=[...new Set(ledger.recipe_inventory.flatMap(r=>r.record_ids||[]))];
for(const rid of allRecordIds){
 const record=JSON.parse(fs.readFileSync(path.join(dist,'data/records',rid+'.json'),'utf8'));
 for(const op of record.operations){
  operationCount++;const scene=buildSchwartz2003Scene(op,record),expected=privateScene(op,record);
  check(rid+'/'+op.id+' source-specific scene',!!scene&&!!expected);
  if(scene&&expected){kinds.add(scene.kind);check(rid+'/'+op.id+' exact private-audited scene',scene.svg===expected.svg);check(rid+'/'+op.id+' apparatus disclosure',/illustrative|explanatory/.test(scene.svg));}
 }
}
check('All 95 operations have source-specific scenes',operationCount===95);
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
  const tree=descend(host),copy=tree.find(x=>x.className==='protocol-copy'),art=tree.find(x=>x.className==='protocol-art protocol-art-schwartz2003');
  check(rid+'/'+op.id+' mounted source-specific artwork',art?.innerHTML===buildSchwartz2003Scene(op,record).svg);
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
   if(q.qualifier&&!/^room temperature\b/i.test(q.qualifier))check(rid+'/'+op.id+'/'+key+' source qualifier visible',dd.includes(q.qualifier));
  }
 }
}
check('All 95 actual mounted stages exercised',mountedOperations===95);
check('All 79 actual condition quantities displayed',mountedQuantities===79);
// Exercise actual mountEvidence route-scoped galleries, including the all-source override.
globalThis.fetch=async rel=>{const url=String(rel),p=url.startsWith('file:')?fileURLToPath(url):path.resolve(dist,url);if(!path.resolve(p).startsWith(path.resolve(dist)+path.sep))throw Error('Unexpected evidence path');return{ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};};
const {mountEvidence}=await import(pathToFileURL(path.join(dist,'material-guide.mjs')).href+'?audit='+Date.now());
const gallerySources=[...ledger.figures,...ledger.tables.filter(t=>t.public_asset)];
for(const [suffix,formula,expectedCount,required,forbidden]of [
 ['zno-route','ZnO',5,['figure-1','figure-2','si-figure-6'],['figure-5','figure-10','si-figure-3']],
 ['co-route','ZnO:Co',15,['figure-5','figure-10','si-figure-2'],['figure-2','si-figure-3','si-figure-6']],
 ['ni-route','ZnO:Ni',8,['figure-6','figure-8','si-figure-3'],['figure-2','figure-5','figure-9','figure-10','si-figure-2','si-figure-4']]
]){
 const rid='schwartz-2003-'+suffix,record=JSON.parse(fs.readFileSync(path.join(dist,'data/records',rid+'.json'),'utf8')),host=new Element('div');
 await mountEvidence(host,record,{materialFormula:formula});
 const tree=descend(host),gallery=tree.find(x=>x.className==='guide-evidence-gallery'),filter=tree.find(x=>x.attributes['aria-label']==='Figure scope');
 check(rid+' figure selector mounted',!!filter&&gallery?.children.length===19);
 filter.value='record';filter.onchange();
 const shown=()=>gallerySources.filter((x,i)=>!gallery.children[i].hidden).map(x=>x.id);
 check(rid+' intended material gallery count',shown().length===expectedCount);
 check(rid+' required applicable figures visible',required.every(id=>shown().includes(id)));
 check(rid+' other-material specific figures excluded',forbidden.every(id=>!shown().includes(id)));
 const allowed=new Set(ledger.material_original_asset_ids[formula]);
 check(rid+' every visible asset explicitly allowed',shown().every(id=>allowed.has(id)));
 check(rid+' contextual sample identity disclosure',host.textContent.includes(ledger.material_asset_scope_note));
 const links=tree.filter(x=>x.tagName==='a').map(x=>String(x.href));
 check(rid+' all declared evidence contexts linked',ledger.route_evidence_contexts[rid].every(id=>links.some(url=>url.endsWith('/records/'+id+'.html'))));
 filter.value='all';filter.onchange();check(rid+' all-source override retains all 19 originals',shown().length===19);
 filter.value='record';filter.onchange();check(rid+' selector restores material context',shown().length===expectedCount);
}
// Existing source without new optional fields retains its original direct/formulation behavior.
const priorLedger=JSON.parse(fs.readFileSync(path.join(dist,'data/paper-reviews/braun2001.json'),'utf8'));
const priorRecord=JSON.parse(fs.readFileSync(path.join(dist,'data/records/braun-2001-system-i.json'),'utf8'));
const priorHost=new Element('div');await mountEvidence(priorHost,priorRecord);
const priorTree=descend(priorHost),priorFilter=priorTree.find(x=>x.attributes['aria-label']==='Figure scope'),priorGallery=priorTree.find(x=>x.className==='guide-evidence-gallery');
priorFilter.value='record';priorFilter.onchange();
const priorFigures=[...priorLedger.figures,...(priorLedger.tables||[]).filter(t=>t.public_asset)],priorLabels=priorLedger.record_formulation_labels[priorRecord.record_id]||[];
check('Prior source retains original relevance logic',priorFigures.every((f,i)=>priorGallery.children[i].hidden===!((f.sample_links||[]).some(x=>(typeof x==='string'?x:x.record_id)===priorRecord.record_id)||(f.formulation_labels||[]).some(x=>priorLabels.includes(x)))));
priorFilter.value='all';priorFilter.onchange();check('Prior source retains all-originals override',priorGallery.children.every(x=>!x.hidden));

const failures=checks.filter(c=>!c.passed);
const result={status:failures.length?'failed':'passed',checked_utc:new Date().toISOString(),scope:'Controlled DOM execution of actual source-reader and apparatus modules, exact original-asset accessibility and source-defined molecular bindings. No browser geometry or publication claim.',reader_items:cards.length,unique_original_assets:filenames.length,operation_count:operationCount,mounted_operations:mountedOperations,mounted_quantities:mountedQuantities,binding_count:bindingCount,checks_passed:checks.length-failures.length,check_count:checks.length,failures,console_errors:consoleErrors,checks,artifact_sha256:Object.fromEntries(['paper-review.mjs','source-evidence.mjs','material-guide.mjs','protocol-visuals.mjs','quantity-value.mjs','schwartz2003-protocol.mjs','data/paper-reviews/schwartz2003.json','assets/chemical-registry/bindings.json','assets/chemical-registry/registry.json'].map(p=>['dist/'+p,digest(path.join(dist,p))]))};
fs.writeFileSync(path.join(here,'reader-runtime-check.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,reader_items:cards.length,unique_original_assets:filenames.length,operations:operationCount,bindings:bindingCount,check_count:checks.length,failures}));
if(failures.length)process.exitCode=1;
