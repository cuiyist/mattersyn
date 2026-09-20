import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const a=path.dirname(fileURLToPath(import.meta.url)),m=path.join(a,'../molecules');
const source='[local path redacted]';
const read=n=>JSON.parse(fs.readFileSync(path.join(m,n),'utf8'));
const registry=read('registry-additions.json'),bindings=read('bindings-proposal.json'),slots=read('material-slot-map.json').slots;
const entries=new Map(registry.entries.map(e=>[e.id,e]));
const baseline=JSON.stringify({registry,bindings});let checks=0,drawn=[];
function eq(x,y){assert.deepEqual(x,y);checks++;}
class Node {
 constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.style={};this.open=true;this.clientWidth=600;this.clientHeight=450;this.attrs={};}
 append(...x){this.children.push(...x);}
 replaceChildren(...x){this.children=x;}
 setAttribute(k,v){this.attrs[k]=v;}
 addEventListener(){}
 showModal(){this.open=true;}
 close(){this.open=false;}
 querySelector(tag){return this.children.find(x=>x.tag===tag)||this.children.flatMap(x=>x.children||[]).find(x=>x.tag===tag);}
}
const body=new Node('body');globalThis.document={body,createElement:t=>new Node(t),createTextNode:t=>new Node('#text',t)};
function text(n){return [n.textContent,...n.children.map(text)].join('\n');}
globalThis.fetch=async url=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(m,'models',path.basename(new URL(url).pathname)),'utf8'))});
globalThis.$3Dmol={createViewer:()=>({clear(){},addModel(){return {addAtoms(x){drawn=x;}}},addLabel(){},setStyle(){},resize(){},zoomTo(){},zoom(){},render(){},rotate(){}})};
globalThis.window={$3Dmol:globalThis.$3Dmol};
const {chemicalEntry,chemicalImage,openChemical}=await import(pathToFileURL(source));
for(const s of slots){
 const eid=s.registry_id,e=entries.get(eid),rid=s.record_id,mid=s.material_id;
 eq(chemicalEntry({entries,bindings},rid,mid),e);
 const approved=structuredClone(bindings);approved.bindingNotes[rid][mid].binding_approved=true;
 const note=approved.bindingNotes[rid][mid];note.viewOverrides.model3dPath='wrong-model.json';note.viewOverrides.formula='wrong';note.viewOverrides.atoms=[{invented:true}];
 const scoped=chemicalEntry({entries,bindings:approved},rid,mid);
 for(const k of ['name','caption','limitations'])eq(scoped[k],s.viewOverrides[k]);
 eq(scoped.sourceBindingCaption,s.viewOverrides.caption);
 for(const k of Object.keys(e).filter(k=>!['name','caption','limitations'].includes(k)))eq(scoped[k],e[k]);
 eq(scoped.atoms,undefined);
 const img=chemicalImage(scoped);eq(new URL(img.src).searchParams.get('sha'),e.assetHashes.svgPath);
 drawn=[];await openChemical(scoped);
 const dialog=body.children[0],visible=text(dialog);
 eq(visible.includes(s.viewOverrides.caption),true);
 for(const limitation of s.viewOverrides.limitations)eq(visible.includes(limitation),true);
 if(e.model3dPath){
   const model=read(e.model3dPath);eq(visible.includes(model.caption),true);eq(drawn.length,model.atoms.length);
   for(let i=0;i<drawn.length;i++)eq([drawn[i].elem,drawn[i].x,drawn[i].y,drawn[i].z],[model.atoms[i].element,model.atoms[i].x,model.atoms[i].y,model.atoms[i].z]);
 }else eq(drawn.length,0);
}
eq(JSON.stringify({registry,bindings}),baseline);
eq(chemicalEntry({entries,bindings},'unrelated-record','tpa-cl'),undefined);
eq(chemicalEntry({entries,bindings},slots[0].record_id,'not-a-slot'),undefined);
const report={status:'passed',author:'/root/peng1998_reader_assets',checks,scope:'Independent execution of actual Site chemicalEntry, chemicalImage and openChemical with a minimal DOM/3D renderer stub: all 45 slots, inactive saved override gates, in-memory approved captions, override whitelist, image hash URLs, exact atom delivery and reference/source-caption coexistence. Not a browser or 3D rendering quality test.',module_path:source,module_sha256:crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),saved_input_mutations:false,browser_approval:false};
fs.writeFileSync(path.join(a,'viewer-checks.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:'passed',checks}));
