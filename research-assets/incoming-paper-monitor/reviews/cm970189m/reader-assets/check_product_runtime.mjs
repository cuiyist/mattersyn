// Read-only module execution for product cards and isotope text, not 3D geometry QA.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),dist='[local path redacted]';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),digest=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
class Node {
 constructor(tag){this.tagName=tag;this.children=[];this.style={};this.dataset={};this._text='';this.className='';this.clientWidth=600;this.clientHeight=400;this.open=false;}
 set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(c=>c.textContent??c).join('');}
 append(...a){this.children.push(...a);}replaceChildren(...a){this._text='';this.children=[];this.append(...a);}
 setAttribute(k,v){this[k]=v;}addEventListener(){}showModal(){this.open=true;}close(){this.open=false;}
}
globalThis.document={body:new Node('body'),createElement:t=>new Node(t),createTextNode:t=>({textContent:String(t)})};
const labels=[];const fakeViewer={addModel:()=>({addAtoms(){}}),addLabel:t=>labels.push(t),setStyle(){},resize(){},zoomTo(){},zoom(){},render(){},rotate(){},clear(){}};
globalThis.window={$3Dmol:{createViewer:()=>fakeViewer}};globalThis.$3Dmol=window.$3Dmol;
globalThis.fetch=async url=>{const u=new URL(url);if(u.protocol!=='file:')throw Error('Network not allowed in audit');const p=fileURLToPath(u);if(!path.resolve(p).startsWith(path.resolve(dist)+path.sep))throw Error('Outside dist');return {ok:fs.existsSync(p),json:async()=>read(p)};};
const {mountCrystalReferences}=await import(pathToFileURL(path.join(dist,'crystal-viewer.mjs')).href);
const {chemicalRegistry,openChemical}=await import(pathToFileURL(path.join(dist,'chemical-viewer.mjs')).href);
const bindingPath=path.join(dist,'assets/chemical-registry/product-bindings.json');const refs=read(bindingPath);
const registry=await chemicalRegistry(),checks=[],cards=[];const check=(name,ok)=>checks.push({name,passed:!!ok});
for(const [rid,eid] of Object.entries(refs.recordBindings)){
 if(!rid.startsWith('veinot-1997-'))continue;
 const record=read(path.join(dist,'data/records',rid+'.json')),entry=registry.entries.get(eid),host=new Node('section');
 await mountCrystalReferences(host,record);
 const body=host.textContent,found=host.children.filter(n=>n.className==='crystal-reference-card');
 check(rid+' one correctly typed product card',found.length===1&&body.includes(entry.model3dPath?'Product molecular structure':'Surface functionalization'));
 check(rid+' source limitation displayed',body.includes(entry.caption));
 check(rid+' correct model/illustration control',body.includes(entry.model3dPath?'Rotate molecular reference':'Enlarge surface representation'));
 const button=found[0]?.children.find(n=>n.tagName==='button');check(rid+' wired product control',typeof button?.onclick==='function');
 if(rid.includes('-ester-')||rid.endsWith('-qdoh'))check(rid+' no experimental phase/CIF implied',body.includes('does not assign a CdS polymorph')&&body.includes('No sample CIF'));
 cards.push({record_id:rid,entry_id:eid,model_kind:entry.model3dPath?'illustrative_molecular_conformer':'surface_connectivity_illustration'});
}
check('Twelve product reference cards',cards.length===12);
const isotopeChecks=[];
for(const [eid,count] of [['dimethyl-sulfoxide-d6',6],['chloroform-d',1],['deuterium-oxide',2]]){
 labels.length=0;const e=registry.entries.get(eid);await openChemical(e);
 check(eid+' isotope labels executed',labels.length===count&&labels.every(x=>x==='²H'));
 isotopeChecks.push({entry_id:eid,labels:[...labels]});
}
const failures=checks.filter(c=>!c.passed);const result={status:failures.length?'failed':'passed',checked_utc:new Date().toISOString(),scope:'Actual product-card and chemical-viewer module execution in controlled local DOM. Fake 3D API records labels only; no physical geometry, mouse interaction or screenshot acceptance claim.',product_cards:cards,isotope_labels:isotopeChecks,checks_passed:checks.length-failures.length,check_count:checks.length,failures,checks,artifact_sha256:Object.fromEntries(['crystal-viewer.mjs','chemical-viewer.mjs','material-guide.mjs','assets/chemical-registry/product-bindings.json','assets/chemical-registry/registry.json','assets/chemical-registry/bindings.json'].map(p=>['dist/'+p,digest(path.join(dist,p))]))};
fs.writeFileSync(path.join(here,'product-runtime-check.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,product_cards:cards.length,isotope_entries:isotopeChecks.length,checks_passed:result.checks_passed,check_count:checks.length,failures}));if(failures.length)process.exitCode=1;
