// Targeted final presentation refresh; does not repeat scientific audits.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),base=path.dirname(here),site='[local path redacted]',dist=path.join(site,'dist');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const checks=[];const check=(name,ok)=>checks.push({name,passed:!!ok});
const auditPath=path.join(here,'canonical-to-reader-audit.json'),priorHash=sha(auditPath),audit=read(auditPath);
const changed=Object.entries(audit.artifact_sha256).filter(([p,h])=>!p.startsWith('private/')&&sha(path.join(site,p))!==h).map(([p])=>p);
check('Previously audited scientific, source and reader files unchanged',changed.length===0);
const apparatus=read(path.join(base,'apparatus-source-audit.json'));
const modulePath=path.join(dist,'veinot-protocol.mjs'),visualPath=path.join(dist,'protocol-visuals.mjs');
check('Integrated module matches independent apparatus audit',apparatus.status==='passed'&&sha(modulePath)===apparatus.module_sha256&&sha(modulePath)==='1be352aed4c30156e0bf2d7974a2f51bdc1df694a94317f804915c861c6a4ce4');
class Node {
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.style={};this._text='';this.events={};this.className='';this.classList={add(){},toggle(){}};}
 set textContent(t){this._text=String(t);this.children=[];}get textContent(){return this._text+this.children.map(c=>c.textContent??c).join('');}
 append(...c){this.children.push(...c);}replaceChildren(...c){this.children=[];this._text='';this.append(...c);}
 setAttribute(k,v){this[k]=v;}addEventListener(k,fn){this.events[k]=fn;}
}
globalThis.document={createElement:t=>new Node(t)};
const {mountProtocol}=await import(pathToFileURL(visualPath).href);
const r=read(path.join(dist,'data/records/veinot-1997-qdoh.json'));
const idx=r.operations.findIndex(o=>Object.values(o.parameters).some(q=>q.raw_text==='approximately one-third its original volume'));
check('Actual concentration stage and source text resolve',idx>=0&&r.operations[idx].id==='concentrate');
const host=new Node('section');mountProtocol(host,r);host.children[0].children[idx].events.click();
const selected=host.children[1],text=selected.textContent;
check('Selected-stage grid and full-conditions use exact readable fraction',(text.match(/Approximately one-third of original volume/g)||[]).length===2);
check('Recurring decimal absent from rendered stage',!text.includes('0.3333333333333333'));
check('Actual raw and numerical source quantity unchanged',r.operations[idx].parameters.remaining_volume_fraction.raw_text==='approximately one-third its original volume'&&r.operations[idx].parameters.remaining_volume_fraction.value===1/3);
check('Source-specific final apparatus selected',selected.children[0].children[0].className==='protocol-art protocol-art-veinot');
check('Unknown temperature not invented',text.includes('TemperatureNot reported')&&text.includes('PressureNot reported'));
const failures=checks.filter(c=>!c.passed);
const result={status:failures.length?'failed':'passed',checked_utc:new Date().toISOString(),scope:'Only the final integrated apparatus binding and QDOH one-third-volume display were checked. Previously audited scientific/source/reader files were confirmed unchanged; their scientific audits were not repeated.',prior_full_audit_sha256:priorHash,changed_previously_bound_files:changed,checks_passed:checks.length-failures.length,check_count:checks.length,failures,checks,artifact_sha256:{'dist/protocol-visuals.mjs':sha(visualPath),'dist/veinot-protocol.mjs':sha(modulePath),'dist/data/records/veinot-1997-qdoh.json':sha(path.join(dist,'data/records/veinot-1997-qdoh.json')),'private/apparatus-source-audit.json':sha(path.join(base,'apparatus-source-audit.json'))}};
const resultPath=path.join(here,'final-presentation-check.json');fs.writeFileSync(resultPath,JSON.stringify(result,null,2)+'\n');
if(!failures.length){
 audit.presentation_refresh={status:result.status,checked_utc:result.checked_utc,scope:result.scope,checks_passed:result.checks_passed,check_count:result.check_count,report:'final-presentation-check.json',prior_full_audit_sha256:priorHash};
 Object.assign(audit.artifact_sha256,result.artifact_sha256,{'private/reader-assets/final-presentation-check.json':sha(resultPath)});
 fs.writeFileSync(auditPath,JSON.stringify(audit,null,2)+'\n');
 fs.appendFileSync(path.join(here,'canonical-to-reader-audit.md'),'\nFinal presentation refresh: '+result.checked_utc+' — '+result.checks_passed+'/'+result.check_count+' targeted checks passed. Final apparatus bytes match the independent apparatus audit; the source one-third-volume value renders as “Approximately one-third of original volume”. Scientific records and previous reader bindings are unchanged; no scientific audit repeated.\n');
}
console.log(JSON.stringify({status:result.status,checks_passed:result.checks_passed,check_count:result.check_count,failures,full_audit_sha256:sha(auditPath),presentation_report_sha256:sha(resultPath),artifact_sha256:result.artifact_sha256}));if(failures.length)process.exitCode=1;
