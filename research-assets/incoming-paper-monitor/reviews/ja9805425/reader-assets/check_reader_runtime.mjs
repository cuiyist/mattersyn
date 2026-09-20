// Execute the actual built source-reader module in a controlled DOM.
// Run only after the owning root confirms its build is ready. No Site writes.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
const dist='[local path redacted]';
const ledger=JSON.parse(fs.readFileSync(path.join(dist,'data/paper-reviews/peng1998.json'),'utf8'));
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
globalThis.location={search:'?id=peng1998',hash:''};
globalThis.fetch=async rel=>{const p=path.resolve(dist,String(rel));if(!p.startsWith(path.resolve(dist)+path.sep))throw Error('Unexpected path');return{ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};};
const consoleErrors=[];const priorError=console.error;console.error=(...args)=>consoleErrors.push(args.map(String).join(' '));
await import(pathToFileURL(path.join(dist,'paper-review.mjs')).href+'?audit='+Date.now());
console.error=priorError;
const checks=[],check=(name,value)=>checks.push({name,passed:!!value});
const cards=nodes.filter(n=>n.dataset.evidenceItem),cardMap=new Map(cards.map(n=>[n.dataset.evidenceItem,n]));
const items=ledger.reader_sections.flatMap(s=>s.items);
check('All 119 source items executed',cards.length===119&&items.length===119);
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
check('Five original figure cards',figureCards.length===5);
for(const [i,f] of ledger.figures.entries()){
 const text=figureCards[i]?.textContent||'';
 check(f.id+' original scope and context visible',text.includes(f.sample_scope)&&f.quantitative_context.every(x=>text.includes(x)));
 check(f.id+' source caption and locator visible',text.includes(f.caption_paraphrase)&&f.source_locators.every(x=>text.includes(x)));
}
const imageLinks=nodes.filter(n=>n.dataset.figure),filenames=[...new Set(imageLinks.map(n=>String(n.dataset.figure).split('/').pop()))];
const expected=['figure-1.png','figure-2.png','figure-3.png','figure-4.png','si-inas-spectra.png','si-cdse-calibration.png','si-inas-calibration.png','equation-gibbs-thomson.png','equation-growth-rate.png','note-21.png','note-22.png'];
check('All eleven distinct original assets accessible',filenames.length===11&&expected.every(f=>filenames.includes(f)));
for(const image of imageLinks){const rel=String(image.dataset.figure);check('Original asset resolves '+rel,fs.existsSync(path.join(dist,rel)));}
check('Both unnumbered equations accessible',filenames.includes('equation-gibbs-thomson.png')&&filenames.includes('equation-growth-rate.png'));
check('Both complete method notes accessible',filenames.includes('note-21.png')&&filenames.includes('note-22.png'));
const body=document.getElementById('review-body').textContent;
check('Matched main and SI scope visible',document.getElementById('review-summary').textContent.includes('matched SI')&&document.getElementById('review-summary').textContent.includes('6 pages'));
check('Characterization item links resolve',ledger.characterization_inventory.reader_item_ids.every(id=>cardMap.has(id)));
check('All calibration rows rendered with separate material titles',items.filter(i=>/^(cdse|inas)-calibration-row/.test(i.id)).length===36&&['cdse','inas'].every(m=>cardMap.get(m+'-calibration-row01')?.textContent.includes(m==='cdse'?'CdSe':'InAs')));
check('Actual high-energy-only analysis visible',cardMap.get('inas-reabsorption')?.textContent.includes('higher-energy half'));
check('TEM cohort limitation visible',cardMap.get('cdse-tem')?.textContent.includes('not identified as the endpoint'));
check('Theoretical status visible',cardMap.get('model-figure4')?.textContent.includes('author theoretical model'));
check('No private pending proposal status visible',!body.includes('Private proposal only')&&!body.includes('Independent canonical-link and source-to-reader audits remain pending for this private proposal.'));
const input=nodes.find(n=>n.tagName==='input'&&n.placeholder==='Chemical, condition, sample, technique or interpretation');
if(input?.events.input){input.value='reabsorption';input.events.input();check('Source search filters evidence meaningfully',cards.some(n=>!n.hidden)&&cards.some(n=>n.hidden));input.value='';input.events.input();check('Cleared search restores all items',cards.every(n=>!n.hidden));}else check('Source search event wired',false);
const digest=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const failures=checks.filter(c=>!c.passed);
const result={status:failures.length?'failed':'passed',checked_utc:new Date().toISOString(),scope:'Controlled local DOM execution of actual reader modules; no browser geometry, apparatus visual acceptance or publication claim.',reader_items:cards.length,original_asset_links:imageLinks.length,unique_original_assets:filenames.length,original_asset_filenames:filenames,checks_passed:checks.length-failures.length,check_count:checks.length,failures,console_errors:consoleErrors,checks,artifact_sha256:Object.fromEntries(['paper-review.mjs','source-evidence.mjs','data/paper-reviews/peng1998.json'].map(p=>['dist/'+p,digest(path.join(dist,p))]))};
fs.writeFileSync(path.join(here,'reader-runtime-check.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,reader_items:cards.length,unique_original_assets:filenames.length,checks_passed:result.checks_passed,check_count:checks.length,failures}));
if(failures.length)process.exitCode=1;
