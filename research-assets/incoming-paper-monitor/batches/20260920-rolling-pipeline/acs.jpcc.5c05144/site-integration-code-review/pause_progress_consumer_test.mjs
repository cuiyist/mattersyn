import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const O=path.dirname(fileURLToPath(import.meta.url));
const M='[local path redacted]',S=M+'/recipe-atlas';
const source=fs.readFileSync(S+'/dist/progress.mjs','utf8');
const actual=JSON.parse(fs.readFileSync(S+'/dist/data/review-progress.json','utf8'));
const checks=[];const ck=(check,p)=>{checks.push({check,passed:!!p});if(!p)throw Error(check);};
const node=(tag,text)=>({tag,textContent:text??'',children:[],append(...n){this.children.push(...n);},replaceChildren(...n){this.children=n;}});
const ids=[...source.matchAll(/\$\('([^']+)'\)/g)].map(x=>x[1]);
const body=source.slice(0,source.indexOf("let last=''"));
const cases=[['paused-empty','paused_for_joint_review',[],'Work is paused for joint review',true],['unpaused-empty','being_recalibrated',[],'No paper is currently under review.',false],['active','being_recalibrated',[{short_label:'Fixture paper',title:'Fixture title',stage:'Fixture review',summary:'Fixture only',stages:[]}],'Fixture paper: Fixture review.',false]];
for(const [name,status,work,expected,paused]of cases){
 const hosts=Object.fromEntries(ids.map(id=>[id,node('host')]));
 const doc={getElementById:id=>hosts[id]??null,createElement:tag=>node(tag)};
 const render=new Function('document','location',body.replaceAll('import.meta.url',JSON.stringify('https://example.test/site/progress.mjs'))+'\nreturn render;')(doc,{origin:'https://example.test'});
 const data=structuredClone(actual);data.estimate.status=status;data.current_work=work;const before=JSON.stringify(data);render(data);
 ck(name+' correct home brief',hosts['review-progress-brief'].textContent.includes(expected));
 ck(name+' no next batch suggestion',!hosts['review-progress-brief'].textContent.includes('Next batch'));
 ck(name+' retains scientific data',JSON.stringify(data)===before);
 const current=hosts['current-work'];ck(name+' expected current work children',current.children.length===(paused?1:work.length));
 if(paused)ck(name+' explicit request-to-resume text',current.children[0].textContent.includes('until you ask to resume'));
 if(work.length)ck(name+' actual work rendered',current.children[0].children.some(n=>n.textContent==='Fixture review'));
}
const result={status:'passed_actual_consumer_function_checks',scope:'Three synthetic rendering states using the exact current consumer with a minimal DOM. No browser or network claim.',check_count:checks.length,checks};
fs.writeFileSync(O+'/pause-progress-consumer-checks.json',JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,checks:checks.length}));
