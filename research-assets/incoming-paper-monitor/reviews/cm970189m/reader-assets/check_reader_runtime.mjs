// Controlled read-only DOM execution; this is not browser geometry/interaction QA.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
const dist='[local path redacted]';
const ledger=JSON.parse(fs.readFileSync(path.join(dist,'data/paper-reviews/veinot1997.json'),'utf8'));
const nodes=[],idMap=new Map();
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this.value='';this._text='';this.className='';this.hidden=false;nodes.push(this);}
 set id(value){this._id=value;idMap.set(value,this);} get id(){return this._id||'';}
 set textContent(value){this._text=String(value);this.children=[];}get textContent(){return this._text+this.children.map(x=>typeof x==='string'?x:x.textContent).join('');}
 append(...children){for(const c of children){this.children.push(c);if(typeof c==='object')c.parentNode=this;}}
 insertBefore(child,target){const i=this.children.indexOf(target);if(i<0)this.append(child);else {this.children.splice(i,0,child);child.parentNode=this;}}
 replaceChildren(...children){this._text='';this.children=[];this.append(...children);}
 setAttribute(name,value){this.attributes[name]=String(value);}
 addEventListener(){} scrollIntoView(){} showModal(){} close(){}
}
globalThis.document={createElement:tag=>new Element(tag),createTextNode:text=>({textContent:String(text)}),getElementById:id=>idMap.get(id)||null,addEventListener(){},title:''};
for(const id of ['review-title','review-doi','review-summary','review-download','review-body','gaps','figure-dialog','figure-close','figure-title','figure-large']){const e=new Element('div');e.id=id;}
document.getElementById('review-body').append(document.getElementById('gaps'));
globalThis.location={search:'?id=veinot1997',hash:''};
globalThis.fetch=async rel=>{const p=path.resolve(dist,String(rel));if(!p.startsWith(path.resolve(dist)+path.sep))throw Error('Unexpected path');return {ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};};
await import(pathToFileURL(path.join(dist,'paper-review.mjs')).href+'?audit='+Date.now());
const checks=[];
const check=(name,value)=>checks.push({name,passed:!!value});
const cards=nodes.filter(n=>n.dataset.evidenceItem);
const cardMap=new Map(cards.map(n=>[n.dataset.evidenceItem,n]));
const sources=ledger.reader_sections.flatMap(s=>s.items);
check('101 reader cards executed without render interruption',cards.length===101&&sources.length===101);
for(const item of sources){
 const card=cardMap.get(item.id),text=card?.textContent||'';
 check(item.id+' semantic source text',text.includes(item.text));
 check(item.id+' title and claim type',text.includes(item.title)&&text.includes(item.claim_type.replaceAll('_',' ')));
 check(item.id+' notes and source locators',item.notes.every(x=>text.includes(x))&&item.evidence.every(x=>text.includes(x.locator)));
 check(item.id+' typed source facts',item.facts.every(f=>text.includes(f.label)&&text.includes(String(f.value))&&(!f.unit||text.includes(f.unit))&&(!f.basis||text.includes(f.basis))));
 check(item.id+' canonical links',item.canonical_links.every(x=>text.includes(x.record_id.replaceAll('_',' '))));
}
const figCards=nodes.filter(n=>n.className==='review-figure');
check('6 original figure cards',figCards.length===6);
for(const [i,f] of ledger.figures.entries()){
 const text=figCards[i]?.textContent||'';
 check(f.id+' quantitative context and sample scope visible',text.includes(f.sample_scope)&&f.quantitative_context.every(x=>text.includes(x)));
}
const assetlinks=nodes.filter(n=>n.dataset.figure);
const filenames=[...new Set(assetlinks.map(n=>String(n.dataset.figure).split('/').pop()))];
check('11 unique original assets accessible',filenames.length===11);
const allText=document.getElementById('review-body').textContent;
check('Table3 model and TEM columns render separately',allText.includes('tight binding diameter A: 24')&&allText.includes('TEM diameter A: 30.4'));
check('Original compound illustration reader link visible',cardMap.get('compound-identities').textContent.includes('Original compound-family illustration')&&filenames.includes('compound-family-illustration.png'));
check('No main-SI completion mislabel',document.getElementById('review-summary').textContent.includes('SI unverified'));
check('Characterization links resolve source cards',ledger.characterization_inventory.reader_item_ids.every(id=>cardMap.has(id)));
check('No pending canonical-audit relation rendered',!allText.includes('pending independent canonical audit')&&!allText.includes('joins pending independent audit'));
const failures=checks.filter(x=>!x.passed);
const digest=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const result={status:failures.length?'failed':'passed',checked_utc:new Date().toISOString(),scope:'Controlled local DOM execution of actual source reader modules; excludes browser geometry, interactions and apparatus visual acceptance.',reader_items:cards.length,original_asset_links:assetlinks.length,unique_original_assets:filenames.length,original_asset_filenames:filenames,checks_passed:checks.length-failures.length,check_count:checks.length,failures,checks,artifact_sha256:{'dist/paper-review.mjs':digest(path.join(dist,'paper-review.mjs')),'dist/source-evidence.mjs':digest(path.join(dist,'source-evidence.mjs')),'dist/data/paper-reviews/veinot1997.json':digest(path.join(dist,'data/paper-reviews/veinot1997.json'))}};
fs.writeFileSync(path.join(here,'reader-runtime-check.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,reader_items:cards.length,original_asset_links:assetlinks.length,unique_original_assets:filenames.length,checks_passed:result.checks_passed,check_count:result.check_count,failures}));
if(failures.length)process.exitCode=1;
