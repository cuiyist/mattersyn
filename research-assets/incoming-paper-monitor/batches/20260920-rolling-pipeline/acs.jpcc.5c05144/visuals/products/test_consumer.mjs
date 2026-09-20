// Executes the actual read-only Site consumer with minimal DOM objects.
// This is a function/dispatch test, not a mounted-browser approval.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const O=path.dirname(fileURLToPath(import.meta.url));
const read=n=>JSON.parse(fs.readFileSync(path.join(O,n),'utf8').replace(/^\ufeff/,''));
const source=path.join(O,'consumer-snapshot/crystal-viewer.mjs');
const text=fs.readFileSync(source,'utf8'),start=text.indexOf('async function productIdentity(host,r){'),end=text.indexOf('\nconst colors=',start);
if(start<0||end<0)throw Error('Exact consumer boundary unavailable');
const original=text.slice(start,end),proposalMode=process.argv.includes('--proposal-links');
let effective=original;
if(proposalMode){const plan=read('original-evidence-consumer-insertion.json');if(crypto.createHash('sha256').update(text).digest('hex')!==plan.baseline_sha256)throw Error('Consumer baseline differs');if(effective.split(plan.anchor).length!==2)throw Error('Insertion boundary differs');effective=effective.replace(plan.anchor,plan.replacement);}
const body=effective.replaceAll('import.meta.url','moduleUrl');
const payload=read('public-product-contexts-proposal.json'),reg=read('registry-additions.json'),binding=read('bindings.json'),entries=new Map(reg.entries.map(e=>[e.id,e]));
const checks=[];const ck=(check,passed)=>{checks.push({check,passed:!!passed});if(!passed)throw Error(check);};
const node=(tag,text,cls)=>({tag,text:text??'',cls,children:[],value:'0',append(...xs){this.children.push(...xs);},replaceChildren(...xs){this.children=xs;},setAttribute(k,v){this[k]=v;}});
const walk=x=>[x,...(x.children||[]).flatMap(walk)];let opened=[];
const fn=new Function('el','fetch','URL','moduleUrl','chemicalRegistry','chemicalImage','openChemical',`let productContextsPromise,productReferencePromise;${body};return productIdentity;`)(node,async()=>({ok:true,json:async()=>payload}),URL,pathToFileURL(source).href,async()=>({entries}),entry=>node('img',entry.id),entry=>opened.push(entry));
for(const[rid,rows]of Object.entries(payload.recordContexts)){
 const host=node('host');await fn(host,{record_id:rid,lineage:{source_group:'sasongko2025'}});
 const select=walk(host).find(x=>x.tag==='select');ck(rid+' selector exists',!!select);ck(rid+' all options',select.children.length===rows.length);
 for(let i=0;i<rows.length;i++){
  select.value=String(i);select.onchange();const row=rows[i],nodes=walk(host),button=nodes.find(n=>n.tag==='button');
  ck(rid+'/'+i+' exact component label',select.children[i].text===row.label+' · '+row.sample_id);
  ck(rid+'/'+i+' exact scoped caption',nodes.some(n=>n.tag==='p'&&n.text===row.caption));
  ck(rid+'/'+i+' exact source phase note',nodes.some(n=>n.tag==='p'&&n.text.includes(row.phase.note)));
  ck(rid+'/'+i+' observed component image',nodes.some(n=>n.tag==='img'&&n.text===row.registry_id));
  ck(rid+'/'+i+' source locators visible',row.phase.evidence.every(e=>nodes.some(n=>n.tag==='small'&&n.text===e.source_id+' · '+e.locator)));
  button.onclick();const chosen=opened.at(-1);ck(rid+'/'+i+' enlarge scoped symbol',chosen.id===row.registry_id&&chosen.caption===row.caption&&!chosen.model3dPath&&!chosen.model2dPath);
  if(proposalMode){const anchors=nodes.filter(x=>x.tag==='a');ck(rid+'/'+i+' original link count',anchors.length===row.original_evidence_links.length);row.original_evidence_links.forEach((l,j)=>{ck('Exact image URL/hash',anchors[j].href.endsWith(l.public_asset+'?sha='+l.sha256));ck('Original label and safe new window',anchors[j].text===l.label+' ↗'&&anchors[j].target==='_blank'&&anchors[j].rel==='noopener noreferrer');});}
 }
}
for(const row of binding.excluded_contexts)ck(row.record_id+'/'+row.sample_id+' excluded',!(payload.recordContexts[row.record_id]||[]).some(x=>x.sample_id===row.sample_id));
const host=node('host');await fn(host,{record_id:'unrelated-record',lineage:{source_group:'other-source'}});ck('No unrelated source dispatch',host.children.length===0);
if(proposalMode){const [rid,rows]=Object.entries(payload.recordContexts)[0],row=rows[0],good=[...row.original_evidence_links];row.original_evidence_links.push({public_asset:'https://external.invalid/source.pdf',sha256:'a'.repeat(64)},{public_asset:'../original.pdf',sha256:'b'.repeat(64)},{public_asset:'assets/figures/sasongko2025/figure-1.png',sha256:'bad'});const h=node('host');await fn(h,{record_id:rid,lineage:{source_group:'sasongko2025'}});ck('Unsafe/unhashed link candidates rejected',walk(h).filter(x=>x.tag==='a').length===good.length);const alien=node('host');await fn(alien,{record_id:rid,lineage:{source_group:'unrelated'}});ck('Original links require exact source group',walk(alien).filter(x=>x.tag==='a').length===0);row.original_evidence_links=good;}
const report={status:'passed_author_consumer_execution',proposal_mode:proposalMode,check_count:checks.length,checks,consumer_path:source,consumer_sha256:crypto.createHash('sha256').update(text).digest('hex'),extracted_function_sha256:crypto.createHash('sha256').update(original).digest('hex'),effective_function_sha256:crypto.createHash('sha256').update(effective).digest('hex'),source_presentation_changes_required:proposalMode,mounted_browser_approval:false,independent_scientific_audit:false};
fs.writeFileSync(path.join(O,proposalMode?'proposed-links-consumer-checks.json':'consumer-execution-checks.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,proposalMode,check_count:checks.length}));
