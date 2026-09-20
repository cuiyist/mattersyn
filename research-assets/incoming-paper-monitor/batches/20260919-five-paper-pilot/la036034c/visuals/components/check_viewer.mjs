// Private author smoke check. No browser/WebGL rendering or Site approval is claimed.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const out=path.dirname(fileURLToPath(import.meta.url));
const html=fs.readFileSync(path.join(out,'viewer.html'),'utf8');
const checks=[];const check=(ok,label)=>checks.push({passed:!!ok,check:label});
const scripts=[...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
for(const [i,s] of scripts.entries()){if(/application\/json/.test(s[1])||/src=/.test(s[1]))continue;new vm.Script(s[2],{filename:`viewer-inline-${i}.js`});check(true,'Parse inline viewer JavaScript '+i);}
const embedded=JSON.parse(scripts.find(s=>/id="data"/.test(s[1]))[2]);
const reg=JSON.parse(fs.readFileSync(path.join(out,'registry-additions.json'),'utf8'));
check(JSON.stringify(embedded.registry)===JSON.stringify(reg),'Embedded registry is exactly the authored registry');
check(embedded.slots.length===61&&embedded.stocks.length===2,'Embedded exact source slots and stocks');
for(const e of reg.entries){
 check(fs.existsSync(path.join(out,e.svgPath)),e.id+' SVG resolves');
 if(e.model3dPath){const model=embedded.models[path.basename(e.model3dPath)];check(!!model&&model.has3D&&model.allowRotation,e.id+' interactive 3D model resolves');check(model.atoms.every((a,i)=>Number.isFinite(a.x)&&a.index===i),e.id+' model passed to viewer has finite zero-based atoms');}
 else check(!e.model3dPath,e.id+' symbolic/2D remains nonrotating');
}
for(const slot of embedded.slots){const target=embedded.bindings.recordBindings[slot.record_id][slot.material_id];check(target===slot.registry_id&&reg.entries.some(e=>e.id===target),slot.record_id+'/'+slot.material_id+' explicit dropdown target');}
for(const stock of embedded.stocks){check(stock.components.every(c=>reg.entries.some(e=>e.id===c.registry_id)),stock.stock_id+' separate component selectors resolve');check(stock.viewer_policy.includes('never create a combined solution conformer'),stock.stock_id+' no solution geometry');}
check(html.includes('mol/L of amine groups')&&html.includes('Not whole-polymer-chain molarity'),'Viewer retains amine-group concentration qualifier');
const result={status:checks.every(c=>c.passed)?'passed':'failed',scope:'Syntax, embedded payload and resource resolution only. Browser layout, mouse interaction and WebGL remain pending.',checks,counts:{checks:checks.length,failures:checks.filter(c=>!c.passed).length},bound_files:{'viewer.html':crypto.createHash('sha256').update(html).digest('hex'),'registry-additions.json':crypto.createHash('sha256').update(fs.readFileSync(path.join(out,'registry-additions.json'))).digest('hex')}};
fs.writeFileSync(path.join(out,'viewer-author-smoke-check.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,...result.counts}));
if(result.status!=='passed')process.exitCode=1;
