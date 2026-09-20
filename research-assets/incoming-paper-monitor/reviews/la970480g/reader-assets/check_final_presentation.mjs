// Final, bounded delta verification. Does not repeat the passed scientific audit.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),base=path.dirname(here),site='[local path redacted]',dist=path.join(site,'dist');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const checkList=[],check=(name,ok,detail='')=>checkList.push({name,passed:!!ok,detail});
const auditPath=path.join(here,'canonical-to-reader-audit.json'),priorAuditSha=sha(auditPath),audit=read(auditPath);
const priorRuntime=read(path.join(here,'reader-runtime-check.json'));
check('Previously passed full audits preserved',audit.check_count===953&&audit.checks_passed===953&&priorRuntime.check_count===525&&priorRuntime.checks_passed===525);
const permittedBindingChanges=new Set(['data/paper-reviews/yao1998.json','dist/data/paper-reviews/yao1998.json','private/public-review-proposal/yao1998.json']);
const changed=Object.entries(audit.artifact_sha256).filter(([p,h])=>sha(p.startsWith('private/')?path.join(base,p.slice(8)):path.join(site,p))!==h).map(([p])=>p);
check('No previously audited science, exports or asset bytes changed',changed.every(p=>permittedBindingChanges.has(p)),changed.join('; '));
const baseline=read(path.join(here,'reader-audit-baseline.json')),patch=read(path.join(base,'public-review-proposal/reader-scope-patch.json'));
const current=read(path.join(site,'data/paper-reviews/yao1998.json')),generated=read(path.join(dist,'data/paper-reviews/yao1998.json'));
const ptr=(v,p)=>p.split('/').slice(1).reduce((a,k)=>a[Array.isArray(a)?Number(k):k],v);
const changes=(a,b,p='')=>{
 if(typeof a!==typeof b||a===null||b===null)return a===b?[]:[p];
 if(typeof a!=='object')return a===b?[]:[p];
 if(Array.isArray(a)!==Array.isArray(b))return[p];
 if(Array.isArray(a))return a.length===b.length?a.flatMap((x,i)=>changes(x,b[i],p+'/'+i)):[p];
 return [...new Set([...Object.keys(a),...Object.keys(b)])].flatMap(k=>(!(k in a)||!(k in b))?[p+'/'+k]:changes(a[k],b[k],p+'/'+k));
};
const allowed=new Set(['/independent_audit']);
for(const p of patch.patches)for(const field of ['scope_kind','link_limit'])allowed.add(p.json_pointer+'/'+field);
for(const cat of ['figures','equations','source_notes'])for(const [i,a] of current[cat].entries())for(const key of ['reviewed','reader_render_verified'])allowed.add('/'+cat+'/'+i+'/'+key);
const deltas={};
for(const [name,now] of [['data/paper-reviews/yao1998.json',current],['dist/data/paper-reviews/yao1998.json',generated]]){
 const dd=changes(baseline[name],now);deltas[name]=dd;
 check(name+' only requested presentation fields changed',dd.every(p=>allowed.has(p)),dd.filter(p=>!allowed.has(p)).join('; '));
}
check('Exactly 68 scope patches supplied',patch.item_count===68&&patch.patches.length===68);
for(const p of patch.patches){
 const old=ptr(baseline['data/paper-reviews/yao1998.json'],p.json_pointer),now=ptr(current,p.json_pointer);
 check(p.item_id+' guarded two-field scope patch',Object.keys(p.set).every(k=>old[k]===p.before[k]&&now[k]===p.set[k]));
}
const assets=[...current.figures,...current.equations,...current.source_notes];
check('All 16 root-verified asset flags finalized',assets.length===16&&assets.every(a=>a.reviewed===true&&a.reader_render_verified===true));
check('SI and publication scope not expanded',current.review_scope==='supplied_main_only_si_unverified'&&current.supporting_information.status==='not_located_or_verified'&&current.publication_status===baseline['data/paper-reviews/yao1998.json'].publication_status);
const clean=structuredClone(generated);delete clean.review_scope_label;
check('Generated ledger still equals authored ledger',JSON.stringify(clean)===JSON.stringify(current));

// Execute only the changed scope cards and the affected temperature display.
class Node {
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.style={};this._text='';this.events={};this.className='';this.classList={add(){},toggle(){}};}
 set textContent(t){this._text=String(t);this.children=[];}get textContent(){return this._text+this.children.map(c=>c.textContent??c).join('');}
 append(...c){this.children.push(...c);}replaceChildren(...c){this.children=[];this._text='';this.append(...c);}
 setAttribute(k,v){this[k]=v;}addEventListener(k,fn){this.events[k]=fn;}
}
globalThis.document={createElement:t=>new Node(t),createTextNode:text=>({textContent:String(text)})};
const {sourceItemCard}=await import(pathToFileURL(path.join(dist,'source-evidence.mjs')).href);
const itemMap=new Map(current.reader_sections.flatMap(s=>s.items).map(i=>[i.id,i]));
for(const p of patch.patches){const card=sourceItemCard(itemMap.get(p.item_id),{compact:true,sourceDoi:current.doi,sourceId:current.paper_id});check(p.item_id+' precise scope text renders',card.textContent.includes(p.set.scope_kind.replaceAll('_',' '))&&card.textContent.includes(p.set.link_limit));}
const {mountProtocol}=await import(pathToFileURL(path.join(dist,'protocol-visuals.mjs')).href);
const r=read(path.join(dist,'data/records/yao-1998-sample-a.json'));
const idx=r.operations.findIndex(o=>o.id==='stand'),temp=r.operations[idx]?.parameters.temperature;
check('Actual standing temperature remains numerically unknown',idx>=0&&temp.value===null&&temp.minimum===null&&temp.maximum===null&&temp.unit==='degC'&&temp.qualifier==='room temperature');
const host=new Node('section');mountProtocol(host,r);host.children[0].children[idx].events.click();
const text=host.children[1].textContent;
check('Room-temperature phrase visible in both stage grid and full conditions',(text.match(/Room temperature \(numeric value not reported\)/g)||[]).length===2);
check('No numeric 25 °C or 298 K invented',!text.includes('25 °C')&&!text.includes('298 K'));
const unknown=r.operations.findIndex(o=>!Object.keys(o.parameters).some(k=>k.toLowerCase().includes('temperature')));
check('An unqualified unknown-temperature operation exists',unknown>=0);
if(unknown>=0){host.children[0].children[unknown].events.click();const t=host.children[1].textContent;check('Unqualified unknown temperature stays unknown',!t.includes('Room temperature (numeric value not reported)')&&/temperatureNot reported/i.test(t));}
check('Source-specific Yao artwork still selected',host.children[1].children[0].children[0].className==='protocol-art protocol-art-yao');
const failures=checkList.filter(c=>!c.passed);
const artifact_sha256=Object.fromEntries([...permittedBindingChanges].map(p=>[p,sha(p.startsWith('private/')?path.join(base,p.slice(8)):path.join(site,p))]));
for(const p of ['dist/protocol-visuals.mjs','dist/yao-protocol.mjs','dist/source-evidence.mjs','dist/data/records/yao-1998-sample-a.json'])artifact_sha256[p]=sha(path.join(site,p));
artifact_sha256['private/public-review-proposal/reader-scope-patch.json']=sha(path.join(base,'public-review-proposal/reader-scope-patch.json'));
const result={status:failures.length?'failed':'passed',checked_utc:new Date().toISOString(),scope:'Only 68 reader-scope label/limitation pairs, 16 finalized asset flags, independent-audit description and the exact room-temperature display branch were checked. Prior 953 scientific/export and 525 full reader-runtime checks were not repeated; unchanged record, export and original-asset bytes were verified against their audit bindings. Publication is separate.',prior_full_audit_sha256:priorAuditSha,prior_full_checks:{canonical_reader:953,reader_runtime:525},changed_previously_bound_files:changed,ledger_delta_paths:deltas,checks_passed:checkList.length-failures.length,check_count:checkList.length,failures,checks:checkList,artifact_sha256};
const out=path.join(here,'final-presentation-check.json');fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
if(!failures.length){
 audit.presentation_refresh={status:'passed',checked_utc:result.checked_utc,scope:result.scope,checks_passed:result.checks_passed,check_count:result.check_count,report:'final-presentation-check.json',prior_full_audit_sha256:priorAuditSha};
 Object.assign(audit.artifact_sha256,artifact_sha256,{'private/reader-assets/final-presentation-check.json':sha(out)});
 fs.writeFileSync(auditPath,JSON.stringify(audit,null,2)+'\n');
 fs.appendFileSync(path.join(here,'canonical-to-reader-audit.md'),'\nFinal presentation-only refresh: '+result.checked_utc+' — '+result.checks_passed+'/'+result.check_count+' targeted checks passed. Prior 953/953 and 525/525 evidence retained; scientific records, JSONL exports and original-asset bytes unchanged. Publication remains separate.\n');
}
console.log(JSON.stringify({status:result.status,checks_passed:result.checks_passed,check_count:result.check_count,failures,final_audit_sha256:sha(auditPath),presentation_sha256:sha(out),ledger_sha256:artifact_sha256['data/paper-reviews/yao1998.json'],generated_ledger_sha256:artifact_sha256['dist/data/paper-reviews/yao1998.json']}));
if(failures.length)process.exitCode=1;
