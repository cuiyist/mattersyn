// Auditor-owned function tests; no Site writes and no mounted-browser claim.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const O=path.dirname(fileURLToPath(import.meta.url)),P=path.join(O,'../molecules');
const mapping=JSON.parse(fs.readFileSync(path.join(P,'canonical-v2-rebind/effective-file-map.json'),'utf8'));
const read=n=>JSON.parse(fs.readFileSync(mapping[n]?.path||path.join(P,n),'utf8'));
const modulePath='[local path redacted]';
const {chemicalEntry,mountStockComponents,mountReagentComponents}=await import(pathToFileURL(modulePath));
const registry=read('registry-additions.json'),bindings=read('bindings-proposal.json'),solutions=read('solution-components-proposal.json');
const entries=new Map(registry.entries.map(e=>[e.id,e])),data={registry,bindings,entries},checks=[];
function ck(label,value){checks.push({check:label,passed:!!value});if(!value)throw Error(label);}
const before=JSON.stringify({registry,bindings});
for(const [rid,map] of Object.entries(bindings.recordBindings))for(const [mid,eid] of Object.entries(map)){
 const original=entries.get(eid),note=bindings.bindingNotes[rid][mid],label=rid+'/'+mid;
 ck(label+' unapproved lookup unchanged',chemicalEntry(data,rid,mid)===original);
 const approved=structuredClone(bindings),copy=approved.bindingNotes[rid][mid];copy.binding_approved=true;
 for(const key of ['formula','svgPath','model2dPath','model3dPath','functionalGroups','provenance','sourceUrls','assetHashes'])copy.viewOverrides[key]='AUDITOR_FORBIDDEN_OVERRIDE';
 const got=chemicalEntry({...data,bindings:approved},rid,mid);
 for(const key of ['name','caption','limitations'])ck(label+' allowed '+key,JSON.stringify(got[key])===JSON.stringify(note.viewOverrides[key]));
 for(const key of ['formula','svgPath','model2dPath','model3dPath','functionalGroups','provenance','sourceUrls','assetHashes'])ck(label+' locked '+key,JSON.stringify(got[key])===JSON.stringify(original[key]));
 ck(label+' separate source caption',got.sourceBindingCaption===note.viewOverrides.caption);
 ck(label+' no entry mutation',JSON.stringify(entries.get(eid))===JSON.stringify(original));
}
ck('Source isolation',chemicalEntry(data,'sommer-2020-not-a-record','zn-nitrate')===undefined);
ck('Slot isolation',chemicalEntry(data,'sommer-2020-mw-route','unmapped')===undefined);

class Node{
 constructor(tag){this.tagName=tag;this.children=[];this.style={};this.attributes={};this.isConnected=true;this.value='0';}
 append(...x){this.children.push(...x);}
 replaceChildren(...x){this.children=[...x];}
 setAttribute(k,v){this.attributes[k]=v;}
}
globalThis.document={createElement:tag=>new Node(tag),createTextNode:text=>({textContent:text})};
globalThis.fetch=async()=>({ok:true,json:async()=>solutions});
function find(n,tag){return[n,...(n.children||[]).flatMap(c=>find(c,tag))].filter(x=>x.tagName===tag);}
const manifest=JSON.parse(fs.readFileSync(path.resolve(P,'../../canonical-proposal/v2/record-manifest.json'),'utf8'));
const records=manifest.records.map(x=>JSON.parse(fs.readFileSync(x.path,'utf8')));
let componentTests=0;
for(const record of records){
 const contexts=solutions.contexts.filter(c=>c.record_id===record.record_id);
 const host=new Node('div');await mountReagentComponents(host,record,data);
 ck(record.record_id+' exact selector count',find(host,'select').length===contexts.length);
 for(let ci=0;ci<contexts.length;ci++){
  const selector=find(host,'select')[ci],section=host.children[ci],ctx=contexts[ci];
  ck(ctx.id+' complete component options',find(selector,'option').length===ctx.components.length);
  for(let j=0;j<ctx.components.length;j++){
   selector.value=String(j);selector.onchange();
   const c=ctx.components[j],entry=entries.get(c.registry_id),imgs=find(section,'img'),texts=find(section,'p');
   ck(ctx.id+'/'+c.material_id+' selected exact image',imgs.length===1&&String(imgs[0].src).includes(entry.svgPath+'?sha='+entry.assetHashes.svgPath));
   ck(ctx.id+'/'+c.material_id+' scoped selected caption',texts.some(x=>x.textContent===c.viewOverrides.caption));
   ck(ctx.id+'/'+c.material_id+' scope note displayed',texts.some(x=>x.textContent===ctx.scope));
   ck(ctx.id+'/'+c.material_id+' correct dimensional control',find(section,'button').some(x=>x.textContent===(entry.model3dPath?'Rotate component reference ↗':'Inspect component representation ↗')));
   componentTests++;
  }
 }
 for(const stock of record.stocks){
  const host2=new Node('div');mountStockComponents(host2,record,stock,data);
  ck(record.record_id+'/'+stock.id+' generic selector complete',find(host2,'option').length===stock.components.length);
 }
}
ck('All23 component transitions',componentTests===23);
ck('Registry and proposal immutable',JSON.stringify({registry,bindings})===before);
const result={schema:'mattersyn-independent-viewer-functions/1',reviewer:'/root/backlog_eta',author:'/root/peng1998_reader_assets',status:'passed',check_count:checks.length,checks,component_transitions:componentTests,module_path:modulePath,module_sha256:crypto.createHash('sha256').update(fs.readFileSync(modulePath)).digest('hex'),scope:'Actual chemicalEntry and stock/component functions executed using a minimal document test double. Not a mounted-browser test or public integration approval.'};
fs.writeFileSync(path.join(O,'viewer-checks-v2.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,checks:checks.length,component_transitions:componentTests}));
