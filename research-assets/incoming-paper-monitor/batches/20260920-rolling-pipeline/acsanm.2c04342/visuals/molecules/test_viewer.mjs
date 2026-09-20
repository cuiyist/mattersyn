import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const O=path.dirname(fileURLToPath(import.meta.url));
const read=n=>JSON.parse(fs.readFileSync(path.join(O,n),'utf8').replace(/^\ufeff/,''));
const modulePath='[local path redacted]';
const {chemicalEntry}=await import(pathToFileURL(modulePath));
const registry=read('registry-additions.json'),bindings=read('bindings-proposal.json');
const entries=new Map(registry.entries.map(e=>[e.id,e])),data={registry,bindings,entries},checks=[];
const ck=(check,passed)=>{checks.push({check,passed:!!passed});if(!passed)throw Error(check);};
for(const[rid,m]of Object.entries(bindings.recordBindings))for(const[mid,id]of Object.entries(m)){
 const note=bindings.bindingNotes[rid][mid],entry=entries.get(id);
 ck(`${rid}/${mid} private lookup`,chemicalEntry(data,rid,mid)===entry);
 ck(`${rid}/${mid} no approval`,note.binding_approved===false);
 const copy=structuredClone(bindings);copy.bindingNotes[rid][mid].binding_approved=true;
 copy.bindingNotes[rid][mid].viewOverrides.model3dPath='forbidden-model.json';
 const resolved=chemicalEntry({...data,bindings:copy},rid,mid);
 ck(`${rid}/${mid} scoped caption`,resolved.caption===note.viewOverrides.caption&&resolved.sourceBindingCaption===note.viewOverrides.caption);
 ck(`${rid}/${mid} exact name`,resolved.name===note.viewOverrides.name);
 ck(`${rid}/${mid} no geometry override`,resolved.model3dPath===entry.model3dPath&&resolved.svgPath===entry.svgPath);
 ck(`${rid}/${mid} immutable base`,chemicalEntry(data,rid,mid)===entry);
}
ck('Unknown source excluded',chemicalEntry(data,'not-matuhina','oa')===undefined);
ck('Unknown slot excluded',chemicalEntry(data,Object.keys(bindings.recordBindings)[0],'unmapped')===undefined);
const report={author:'/root/backlog_eta',status:'passed_author_execution_checks',check_count:checks.length,checks,module_path:modulePath,module_sha256:crypto.createHash('sha256').update(fs.readFileSync(modulePath)).digest('hex'),mounted_browser_approval:false,independent_audit:false};
fs.writeFileSync(path.join(O,'viewer-function-checks.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,check_count:checks.length}));
