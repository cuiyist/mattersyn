// Bounded check of actual material-hub measurement-prefix expression; no Site writes.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
const O=path.dirname(fileURLToPath(import.meta.url)),B=path.dirname(O),S='[local path redacted]';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const reportPath=path.join(O,'integrated-presentation-audit.json'),baselineHash=sha(reportPath),report=read(reportPath),modulePath=path.join(S,'dist/material-hub.mjs');
const code=fs.readFileSync(modulePath,'utf8'),line=code.split('\n').find(x=>x.includes('for(const m of measurements)'));
const match=line?.match(/card\.append\(node\('p',(.+?)\+' · '\+\(sample\?\.source_sample_label/);
if(!match)throw Error('Could not isolate actual material-hub measurement composition expression');
const expression=match[1],checks=[],ck=(name,value,detail='')=>checks.push({name,passed:!!value,detail});
ck('Measurement composition expression has no record-formula fallback',!expression.includes('r.material.formula')&&expression.includes('sample?.composition?.value')&&expression.includes('Sample composition not assigned'));
const rows=[];let assigned=0,unassigned=0,differentFromParent=0;
for(const file of fs.readdirSync(path.join(B,'canonical-drafts')).filter(x=>x.endsWith('.json'))){
 const record=read(path.join(S,'data/records',file));
 for(const m of record.measurements){
  const sample=record.products.find(p=>p.sample_id===m.sample_id),expected=sample&&typeof sample.composition?.value==='string'&&sample.composition.value.length?sample.composition.value:'Sample composition not assigned';
  const actual=vm.runInNewContext(expression,{sample,r:record},{timeout:100});
  ck(record.record_id+'/'+m.id+' sample-specific composition prefix',actual===expected);
  if(expected==='Sample composition not assigned')unassigned++;else assigned++;
  if(expected!==record.material.formula)differentFromParent++;
  rows.push({record_id:record.record_id,measurement_id:m.id,sample_id:m.sample_id,parent_formula:record.material.formula,expected_prefix:expected,actual_prefix:actual});
 }
}
ck('Both assigned and unassigned sample contexts exercised',assigned>0&&unassigned>0);
ck('At least one sample differs from parent formula',differentFromParent>0);
const unchangedData=[];
for(const [relative,hash] of Object.entries(report.artifact_sha256)){
 if(!/^(data\/records\/|dist\/data\/records\/|data\/paper-reviews\/|dist\/data\/paper-reviews\/|dist\/data\/records\.jsonl$|dist\/data\/materials\/)/.test(relative))continue;
 const current=sha(path.join(S,relative));ck(relative+' unchanged from integrated baseline',current===hash);unchangedData.push({path:relative,baseline_sha256:hash,current_sha256:current});
}
const findings=checks.filter(x=>!x.passed),result={status:findings.length?'findings':'passed',checked_utc:new Date().toISOString(),scope:'Bounded material-hub display delta only. Evaluates the actual new prefix expression against every Gerion measurement and checks unchanged source/data hashes; no source reread or browser-geometry claim.',baseline_integrated_report_sha256:baselineHash,module_sha256:sha(modulePath),expression,counts:{measurements:rows.length,assigned,unassigned,different_from_parent:differentFromParent,unchanged_data_files:unchangedData.length},check_count:checks.length,checks_passed:checks.length-findings.length,findings,checks,rows,unchanged_data:unchangedData};
fs.writeFileSync(path.join(O,'material-hub-composition-delta-check.json'),JSON.stringify(result,null,2)+'\n');
if(!findings.length){
 report.artifact_sha256['dist/material-hub.mjs']=result.module_sha256;
 report.checks.push(...checks);report.check_count=report.checks.length;report.checks_passed=report.checks.filter(x=>x.passed).length;
 report.presentation_delta_checks??=[];report.presentation_delta_checks.push({file:'material-hub-composition-delta-check.json',sha256:sha(path.join(O,'material-hub-composition-delta-check.json')),status:result.status,checked_utc:result.checked_utc,check_count:result.check_count});
 report.checked_utc=result.checked_utc;
 fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
 fs.writeFileSync(path.join(O,'integrated-presentation-audit.md'),'# Gerion 2001 integrated presentation check\n\n'+report.status+`; ${report.checks_passed}/${report.check_count} checks.\n\n`+report.scope+'\n\nBounded follow-up: actual material-hub measurement labels use sample composition, or an explicit unassigned label. Canonical and reader data are unchanged. See material-hub-composition-delta-check.json.\n');
}
console.log(JSON.stringify({status:result.status,counts:result.counts,check_count:result.check_count,findings,integrated_checks:report.check_count}));
if(findings.length)process.exitCode=1;
