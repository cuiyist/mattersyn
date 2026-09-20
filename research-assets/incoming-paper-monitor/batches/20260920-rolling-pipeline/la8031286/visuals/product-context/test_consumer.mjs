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
const original=text.slice(start,end),body=original.replaceAll('import.meta.url','moduleUrl');
const payload=read('product-contexts-additions.json'),reg=read('registry-additions.json'),binding=read('bindings.json'),entries=new Map(reg.entries.map(e=>[e.id,e]));
const checks=[];const ck=(check,passed)=>{checks.push({check,passed:!!passed});if(!passed)throw Error(check);};
const node=(tag,text,cls)=>({tag,text:text??'',cls,children:[],value:'0',append(...xs){this.children.push(...xs);},replaceChildren(...xs){this.children=xs;},setAttribute(k,v){this[k]=v;}});
const walk=x=>[x,...(x.children||[]).flatMap(walk)];let opened=[];
const fn=new Function('el','fetch','URL','moduleUrl','chemicalRegistry','chemicalImage','openChemical',`let productContextsPromise,productReferencePromise;${body};return productIdentity;`)(node,async()=>({ok:true,json:async()=>payload}),URL,pathToFileURL(source).href,async()=>({entries}),entry=>node('img',entry.id),entry=>opened.push(entry));
for(const[rid,rows]of Object.entries(payload.recordContexts)){
 const host=node('host');await fn(host,{record_id:rid,lineage:{source_group:'pati2009'}});
 const select=walk(host).find(x=>x.tag==='select');ck(rid+' selector exists',!!select);ck(rid+' all options',select.children.length===rows.length);
 for(let i=0;i<rows.length;i++){
  select.value=String(i);select.onchange();const row=rows[i],nodes=walk(host),button=nodes.find(n=>n.tag==='button');
  ck(rid+'/'+i+' exact component label',select.children[i].text===row.label+' · '+row.sample_id);
  ck(rid+'/'+i+' exact scoped caption',nodes.some(n=>n.tag==='p'&&n.text===row.caption));
  ck(rid+'/'+i+' exact source phase note',nodes.some(n=>n.tag==='p'&&n.text.includes(row.phase.note)));
  ck(rid+'/'+i+' observed component image',nodes.some(n=>n.tag==='img'&&n.text===row.registry_id));
  ck(rid+'/'+i+' source locators visible',row.phase.evidence.every(e=>nodes.some(n=>n.tag==='small'&&n.text===e.source_id+' · '+e.locator)));
  button.onclick();const chosen=opened.at(-1);ck(rid+'/'+i+' enlarge scoped symbol',chosen.id===row.registry_id&&chosen.caption===row.caption&&!chosen.model3dPath&&!chosen.model2dPath);
 }
}
for(const row of binding.excluded_contexts)ck(row.record_id+'/'+row.sample_id+' excluded',!(payload.recordContexts[row.record_id]||[]).some(x=>x.sample_id===row.sample_id));
const host=node('host');await fn(host,{record_id:'unrelated-record',lineage:{source_group:'other-source'}});ck('No unrelated source dispatch',host.children.length===0);
const report={status:'passed_author_consumer_execution',check_count:checks.length,checks,consumer_path:source,consumer_sha256:crypto.createHash('sha256').update(text).digest('hex'),extracted_function_sha256:crypto.createHash('sha256').update(original).digest('hex'),source_presentation_changes_required:false,mounted_browser_approval:false,independent_scientific_audit:false};
fs.writeFileSync(path.join(O,'consumer-execution-checks.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,check_count:checks.length}));
