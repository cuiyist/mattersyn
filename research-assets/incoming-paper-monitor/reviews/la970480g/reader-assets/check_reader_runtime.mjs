// Controlled DOM execution of the actual source reader. No browser or Site writes.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
const dist='[local path redacted]';
const ledger=JSON.parse(fs.readFileSync(path.join(dist,'data/paper-reviews/yao1998.json'),'utf8'));
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
globalThis.location={search:'?id=yao1998',hash:''};
globalThis.fetch=async rel=>{const p=path.resolve(dist,String(rel));if(!p.startsWith(path.resolve(dist)+path.sep))throw Error('Unexpected path');return{ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};};
await import(pathToFileURL(path.join(dist,'paper-review.mjs')).href+'?audit='+Date.now());
const checks=[],check=(name,value)=>checks.push({name,passed:!!value});
const cards=nodes.filter(n=>n.dataset.evidenceItem),cardMap=new Map(cards.map(n=>[n.dataset.evidenceItem,n]));
const items=ledger.reader_sections.flatMap(s=>s.items);
check('All 100 source items executed',cards.length===100&&items.length===100);
for(const item of items){
 const card=cardMap.get(item.id),text=card?.textContent||'';
 check(item.id+' source prose',text.includes(item.text));
 check(item.id+' title and claim class',text.includes(item.title)&&text.includes(item.claim_type.replaceAll('_',' ')));
 check(item.id+' notes and locators',item.notes.every(x=>text.includes(x))&&item.evidence.every(x=>text.includes(x.locator)));
 check(item.id+' fact values, units and basis',item.facts.every(f=>text.includes(f.label)&&text.includes(String(f.value))&&(!f.unit||text.includes(f.unit))&&(!f.basis||text.includes(f.basis.replaceAll('_',' ')))));
 check(item.id+' source record links',item.canonical_links.every(x=>text.includes(x.record_id.replaceAll('_',' '))));
 for(const a of item.original_assets||[])check(item.id+' original source link '+a.id,card.children.some(n=>n.tagName==='a'&&String(n.href).endsWith(a.public_asset)));
}
const figureCards=nodes.filter(n=>n.className==='review-figure');
check('Nine original figure cards',figureCards.length===9);
for(const [i,f] of ledger.figures.entries()){
 const text=figureCards[i]?.textContent||'';
 check(f.id+' original scope and quantitative context visible',text.includes(f.sample_scope)&&f.quantitative_context.every(x=>text.includes(x)));
}
const imageLinks=nodes.filter(n=>n.dataset.figure),filenames=[...new Set(imageLinks.map(n=>String(n.dataset.figure).split('/').pop()))];
check('Sixteen distinct original assets accessible',filenames.length===16);
check('All three numbered equations accessible',[1,2,3].every(n=>filenames.includes('equation-0'+n+'.png')));
check('No invented XRD plot',!filenames.some(f=>/^figure.*xrd/i.test(f))&&filenames.includes('xrd-assignment-excerpt.png'));
const body=document.getElementById('review-body').textContent;
check('Undefined SD unit and potential conflict visible',cardMap.get('regional-histograms').textContent.includes('unit and mathematical definition')&&cardMap.get('donnan-values').textContent.includes('−26 meV'));
check('Local symbol identities visible',cardMap.get('long-time-profile').textContent.includes('filled symbols for sample b')&&cardMap.get('early-time-profile').textContent.includes('filled circles and a solid line for a'));
check('No SI completion mislabel',document.getElementById('review-summary').textContent.includes('SI unverified'));
check('Characterization item links resolve',ledger.characterization_inventory.reader_item_ids.every(id=>cardMap.has(id)));
check('No stale pending-canonical relation',!body.includes('pending independent canonical audit'));
const input=nodes.find(n=>n.tagName==='input'&&n.placeholder==='Chemical, condition, sample, technique or interpretation');
if(input?.events.input){input.value='Donnan';input.events.input();check('Source search filters meaningfully',cards.some(n=>!n.hidden)&&cards.some(n=>n.hidden));input.value='';input.events.input();check('Cleared search restores all items',cards.every(n=>!n.hidden));}else check('Source search event wired',false);
const digest=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const failures=checks.filter(c=>!c.passed);
const result={status:failures.length?'failed':'passed',checked_utc:new Date().toISOString(),scope:'Controlled local DOM execution of actual reader modules; no browser geometry, apparatus acceptance or publication claim.',reader_items:cards.length,original_asset_links:imageLinks.length,unique_original_assets:filenames.length,original_asset_filenames:filenames,checks_passed:checks.length-failures.length,check_count:checks.length,failures,checks,artifact_sha256:Object.fromEntries(['paper-review.mjs','source-evidence.mjs','data/paper-reviews/yao1998.json'].map(p=>['dist/'+p,digest(path.join(dist,p))]))};
fs.writeFileSync(path.join(here,'reader-runtime-check.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,reader_items:cards.length,unique_original_assets:filenames.length,checks_passed:result.checks_passed,check_count:checks.length,failures}));
if(failures.length)process.exitCode=1;
