// Bounded read-only audit of the two new integration paths, not a browser test.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import {fileURLToPath,pathToFileURL} from 'node:url';
const HERE=path.dirname(fileURLToPath(import.meta.url));
const SITE='[local path redacted]';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(path.join(SITE,p),'utf8'));
const files=['material-hub.mjs','finite-crystal-reference.mjs','crystal-viewer.mjs','assets/crystal-references/registry.json','data/paper-reviews/littau1993.json','data/materials/si-siox-3a1c19.json','data/materials/si-243a7b.json'];
const snapshots=Object.fromEntries(files.map(p=>[p,fs.readFileSync(path.join(SITE,p),'utf8')]));
const results=[];
const check=(name,pass,detail={})=>results.push({name,pass,...detail});
// Reuse the already-reviewed minimal DOM without copying application logic.
const prior=fs.readFileSync(path.join(HERE,'audit_frontend.mjs'),'utf8');
const mockDefinitions=prior.slice(prior.indexOf('class Node {'),prior.indexOf('function transformed(name)'));
function context(extra={}){const c={URL,URLSearchParams,console,...extra};vm.createContext(c);vm.runInContext(mockDefinitions+'\nglobalThis.Node=Node;globalThis.walk=walk;globalThis.addId=addId;globalThis.document=documentMock();document.querySelector=s=>document.body.querySelector(s);',c);return c;}
function source(name){return snapshots[name].replace(/^import .+;\s*$/gm,'').replace(/export (async )?function /g,(_,a)=>(a||'')+'function ').replaceAll('import.meta.url',JSON.stringify(pathToFileURL(path.join(SITE,name)).href));}
const index=read('data/materials-index.json');
for(const formula of ['Si/SiOx','Si']){
 const item=index.materials.find(x=>x.formula===formula),data=read('data/materials/'+item.id+'.json'),errors=[],requested=[];
 const c=context({location:{search:'?id='+item.id},console:{error:x=>errors.push(String(x))},mountMaterialGuide:async()=>{},fetch:async url=>{requested.push(String(url));return {ok:true,json:async()=>read(String(url))};}});
 for(const id of ['material-formula','material-name','material-elements','material-scope-note','material-dataset','material-methods','material-illustrated-guide','material-structures','material-properties','material-papers','more-papers','paper-contribution-count'])c.addId(c.document,id);
 await vm.runInContext('(async()=>{'+source('material-hub.mjs')+'})()',c);
 const h=[c.document.getElementById('material-structures'),c.document.getElementById('material-properties')];
 const cards=h.flatMap(x=>c.walk(x).filter(n=>n.tagName==='ARTICLE'));
 let missing=[],measurementCount=0;
 for(const r of data.evidence_records.map(x=>read('data/records/'+x.record_id+'.json'))){
  const text=cards.filter(x=>x.children.some(n=>n.tagName==='H3'&&n.textContent===r.title)).map(x=>x.textContent).join(' ');
  for(const m of r.measurements){measurementCount++;for(const [field,value]of [['formula',r.material.formula],['conditions',m.conditions],['basis',m.value.basis],['qualifier',m.value.qualifier],...m.evidence.map(e=>['evidence',e.locator])])if(value&&!text.includes(value))missing.push({record:r.record_id,measurement:m.measurement_id||m.id,field,value});}
 }
 check(formula+' hub preserves conditions, basis, qualifier, formula and source locators for all evidence-record measurements',!errors.length&&!missing.length,{measurementCount,errors,missing});
 check(formula+' has thirteen evidence records and only three synthesis routes',data.evidence_records.length===13&&new Set(data.evidence_records.map(x=>x.record_id)).size===13&&data.records.length===3&&data.records.every(x=>x.is_synthesis_route)&&c.document.getElementById('material-methods').children.length===3);
 check(formula+' preserves source and specimen scope notes in both characterization sections',h.every(x=>data.evidence_scope_notes.every(note=>x.textContent.includes(note))));
}
const registry=read('assets/crystal-references/registry.json');
const ref=registry.entries.find(x=>x.id==='littau-1993-si-diamond-ideal-reference');
check('Constructed Si reference binds only the two formulations with diamond-Si evidence',JSON.stringify([...ref.record_ids].sort())===JSON.stringify(['littau-1993-si-aerosol-2p0','littau-1993-si-aerosol-6p0']));
const model=read('assets/crystal-references/'+ref.finiteModelPath);
check('Finite particle explicitly remains unmeasured, nonperiodic, untrainable illustrative geometry',model.periodic===false&&model.cell===null&&model.cellVectors===null&&model.measured_sample_structure===false&&model.training_eligible===false&&model.representation==='finite_illustrative_particle');
const assetList=[{path:ref.cifPath,sha256:ref.sha256||ref.cifSha256},{path:ref.modelPath,sha256:ref.modelSha256},{path:ref.finiteModelPath,sha256:ref.finiteModelSha256},...ref.additionalDownloads];
const assetChecks=assetList.map(a=>({path:a.path,expected:a.sha256,actual:hash(fs.readFileSync(path.join(SITE,'assets/crystal-references',a.path)))}));
check('All five reference assets match registry SHA-256 values',assetChecks.length===5&&assetChecks.every(x=>x.actual===x.expected),{assets:assetChecks});
const finite=context();vm.runInContext(source('finite-crystal-reference.mjs')+'\nglobalThis.finiteReferenceAtoms=finiteReferenceAtoms;globalThis.drawFiniteReference=drawFiniteReference;',finite);
const calls=[],viewer={clear(){calls.push(['clear']);},addModel(){return {addAtoms:a=>calls.push(['atoms',a])};},setStyle(){calls.push(['style']);},zoomTo(){calls.push(['zoom']);},rotate(){calls.push(['rotate']);},render(){calls.push(['render']);}};
const caption=finite.drawFiniteReference(viewer,model),atoms=calls.find(x=>x[0]==='atoms')[1];
check('Finite renderer adds 705 atoms once without periodic cell lines or tiling and retains reference-only flags',atoms.length===705&&calls.filter(x=>x[0]==='atoms').length===1&&atoms.every(a=>a.properties.reference_only===true&&a.properties.measured_sample===false)&&caption===model.caption);
let rejected=0;for(const patch of [{periodic:true},{measured_sample_structure:true},{training_eligible:true}])try{finite.finiteReferenceAtoms({...model,...patch});}catch{rejected++;}
check('Finite renderer rejects periodic, measured-sample or training-eligible inputs',rejected===3);
const off=context({window:{},fetch:async()=>({json:async()=>registry})});vm.runInContext(source('crystal-viewer.mjs')+'\nglobalThis.mountCrystalReferences=mountCrystalReferences;',off);
const host=new off.Node('div');await off.mountCrystalReferences(host,{record_id:'littau-1993-si-aerosol-6p0'});
const anchorText=off.walk(host).filter(n=>n.tagName==='A').map(n=>n.textContent);
check('Reference files remain downloadable when the optional 3D viewer is unavailable',ref.additionalDownloads.every(x=>anchorText.some(t=>t.includes(x.label)))&&anchorText.some(t=>t.includes(ref.sourceLinkLabel)),{anchorText});
const stable=files.every(p=>hash(snapshots[p])===hash(fs.readFileSync(path.join(SITE,p))));
const report={status:results.every(x=>x.pass)&&stable?'passed_bounded_supplement':'findings_or_source_changed',scope:'Imported silicon hub evidence joins and reference-crystal data/control guards. Read-only actual source evaluation with minimal DOM; no repeated PDF review, Site mutation, training promotion or publication decision.',results,files_stable_during_test:stable,reviewed_sha256:Object.fromEntries(files.map(p=>[p,hash(snapshots[p])])),remaining:'Actual browser geometry, image layout and controls are covered by root browser QA. Main-only review scope and unresolved matching SI remain unchanged.'};
fs.writeFileSync(path.join(HERE,'frontend-evidence-crystal-audit.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(HERE,'frontend-evidence-crystal-audit.md'),'# Littau evidence and crystal integration audit\n\n'+report.scope+'\n\n'+results.map(x=>'- '+(x.pass?'PASS':'FINDING')+': '+x.name).join('\n')+'\n\n'+report.remaining+'\n');
console.log(JSON.stringify({status:report.status,checks:results.length,failed:results.filter(x=>!x.pass),stable},null,2));
