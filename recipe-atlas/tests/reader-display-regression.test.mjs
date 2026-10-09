import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {scopeKind} from '../static/reader-structures.mjs';
import {particleGroups,particleDescriptor,mountParticleContext} from '../static/reader-particle.mjs';
import {scopedProductArt,scopedProductArtIds} from '../static/reader-scoped-product-art.mjs';
import {drawFiniteReference} from '../static/finite-crystal-reference.mjs';

// Invented fixtures and public code only. No record/source/model files or HTTP.
const expectedArtIds=['ready-four-qd-core-shell','ready-four-lhd-composition','ready-four-qlhd-composition','ready-four-xie-composition','ready-four-zhu-composition','ready-four-pbs-powder-composition','ready-four-samplec-composition'];
const freeze=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};

test('explicit reference types outrank negative reconstruction prose',()=>{
 for(const [metadata,expected]of [
  [{sourceType:'literature_bulk_reference',description:'Not a sample reconstruction.'},'Bulk reference'],
  [{referenceType:'literature_bulk_reference',name:'Constructed wording in a descriptive title'},'Bulk reference'],
  [{sourceType:'computed_reference',description:'Not a sample reconstruction.'},'Computed reference'],
  [{referenceType:'computed_reference'},'Computed reference'],
  [{sourceType:'constructed_lattice_reference',referenceType:'locally_constructed_ideal_reference'},'Constructed reference'],
  [{referenceType:'locally_constructed_bulk_reference'},'Constructed reference'],
  [{sourceType:'source_table_partial_framework'},'Partial structure reference'],
  [{name:'Constructed ideal reference'},'Constructed reference'],
  [{description:'No reconstructed specimen or interface is supplied.'},'Bulk reference'],
  [{name:'PBE reference calculation'},'Computed reference'],
  [{name:'Partial framework reference'},'Partial structure reference'],
  [{name:'Plain independent cell'},'Bulk reference'],
 ])assert.equal(scopeKind(metadata),expected,JSON.stringify(metadata));
});

test('seven fixed inline drawings are accessible and contain no external or executable content',()=>{
 assert.deepEqual([...scopedProductArtIds].sort(),[...expectedArtIds].sort());
 for(const id of expectedArtIds){const svg=scopedProductArt(id);assert.match(svg,/^<svg\b/);assert.match(svg,/role="img"/);assert.match(svg,/<title>[^<]+<\/title>/);assert.match(svg,/<desc>[^<]+<\/desc>/);assert.match(svg,/<(?:rect|circle|path|ellipse)\b/);assert.doesNotMatch(svg.replace('xmlns="http://www.w3.org/2000/svg"',''),/<(?:script|foreignObject|image|use|a)\b|\son\w+\s*=|\bhref\s*=|javascript:|https?:\/\//i);assert.match(svg,/no measured coordinates|not reconstructed|not assigned|not reported/i);}
 assert.equal(scopedProductArt('unregistered-fixture'),null);assert.equal(scopedProductArt('__proto__'),null);assert.equal(scopedProductArt('constructor'),null);
});

test('an illustration joins only the exact record and specimen key without inventing morphology',()=>{
 const r=freeze({record_id:'fixture-a',products:[{sample_id:'prepared',source_sample_label:'Prepared fixture',composition:{value:'Fixture composition',status:'reported'},morphology:{value:null,status:'not_reported'}}]});
 const p=freeze({productContexts:[{record_id:'fixture-b',sample_id:'prepared',label:'Other record'}]});
 const entry=freeze({shape:'composition-schematic',display_kind:'composition_schematic',inline_art_id:expectedArtIds[1],rationale:'Synthetic composition only'});
 const interpretations=freeze({'fixture-a:prepared':entry});const before=JSON.stringify({r,p,interpretations}),groups=particleGroups(r,p);
 assert.equal(particleDescriptor(groups.get('fixture-a:prepared'),interpretations).inferred,entry);
 assert.equal(particleDescriptor(groups.get('fixture-a:prepared'),interpretations).morphology,'');
 assert.equal(particleDescriptor(groups.get('fixture-b:prepared'),interpretations).inferred,undefined);
 assert.equal(particleDescriptor(groups.get('fixture-b:prepared'),interpretations).shape,'neutral');
 assert.equal(JSON.stringify({r,p,interpretations}),before);
});

class Element{
 constructor(tag,text,cls){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this.style={};this.className=cls||'';this.isConnected=true;this._text=text||'';this._html='';}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(...nodes){this.children=[...nodes];this._text='';}
 setAttribute(k,v){this.attributes[k]=String(v);}
 set textContent(v){this._text=String(v);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent??'').join(' ');}
 set innerHTML(v){assert.match(v,/^<svg\b/);this._html=v;}
 get innerHTML(){return this._html;}
}
const el=(...a)=>new Element(...a),flatten=n=>[n,...n.children.flatMap(flatten)];

// Execute the actual private drawReference body against an immutable invented
// periodic/finite model and deterministic camera stub. This makes Reset/Home
// regressions observable without exposing a new production rendering API.
const rendererCode=readFileSync(new URL('../static/reader-structures.mjs',import.meta.url),'utf8');
const drawStart=rendererCode.indexOf('async function drawReference('),drawEnd=rendererCode.indexOf('export function finiteReferencesForRecord');
assert.ok(drawStart>=0&&drawEnd>drawStart);
const drawReference=new Function('el','badge','link','disclosure','siteURL','colors','referenceCellVectors','drawFiniteReference','elementLegend','button','scopeKind','return ('+rendererCode.slice(drawStart,drawEnd)+');')(
 el,t=>el('span',t),t=>el('a',t),(t,n)=>{const d=el('details',t);d.append(n);return d;},x=>x,{},()=>[[1,0,0],[0,1,0],[0,0,1]],drawFiniteReference,()=>el('div','Fixture legend','element-legend'),(label,callback)=>{const b=el('button',label);b.onclick=callback;return b;},scopeKind);
async function cameraFixture(t,finite=false){
 let viewer;const prior={window:globalThis.window,$3Dmol:globalThis.$3Dmol,ResizeObserver:globalThis.ResizeObserver,fetch:globalThis.fetch};
 t.after(()=>Object.assign(globalThis,prior));
 const createViewer=()=>viewer={x:0,y:0,z:1,atoms:[],clear(){this.atoms=[];},getView(){return [0,0,0,this.z,this.x,this.y,0,1];},setView(v){this.z=v[3];this.x=v[4];this.y=v[5];},addModel(){return {addAtoms:a=>{this.atoms=a;}};},setStyle(){},addLine(){},zoomTo(){this.z=1;},rotate(n,axis){this[axis]+=n;},zoom(n){this.z*=n;},render(){},resize(){}};
 globalThis.window={$3Dmol:{createViewer}};globalThis.$3Dmol=window.$3Dmol;globalThis.ResizeObserver=class{observe(){}disconnect(){}};
 const model=freeze(finite?{periodic:false,representation:'finite_illustrative_particle',measured_sample_structure:false,training_eligible:false,atoms:[{serial:0,element:'X',x:0,y:0,z:0,bonds:[],bondOrder:[],properties:{}}],caption:'Invented finite fixture.'}:{cell:{a:1,b:1,c:1,alpha:90,beta:90,gamma:90},atoms:[{element:'X',x:0,y:0,z:0,occupancy:1}]});
 const ref=freeze({id:'invented',name:'Invented software fixture',sourceType:'literature_bulk_reference',modelPath:'invented.json',finiteModelPath:'invented-finite.json',cifPath:'invented.cif',sourceUrl:'https://example.invalid/invented'}),before=JSON.stringify({model,ref});
 globalThis.fetch=async()=>({json:async()=>model});const host=el('article');await drawReference(host,ref,finite);const view=flatten(host).find(n=>n.className==='crystal-reference-view');
 return {viewer,host,key:key=>view.onkeydown({key,preventDefault(){}}),click:label=>{const b=flatten(host).find(n=>n.tagName==='button'&&n.textContent===label);assert.ok(b,label);b.onclick();},initial:viewer.getView(),stable:()=>assert.equal(JSON.stringify({model,ref}),before)};
}

test('periodic Reset and repeated Home restore the initial camera after rotation/zoom',async t=>{
 const c=await cameraFixture(t);c.key('ArrowRight');c.click('+');assert.notDeepEqual(c.viewer.getView(),c.initial);c.click('Reset');assert.deepEqual(c.viewer.getView(),c.initial);
 for(let i=0;i<3;i++)c.click('Reset');assert.deepEqual(c.viewer.getView(),c.initial);c.key('ArrowLeft');c.key('Home');c.key('Home');assert.deepEqual(c.viewer.getView(),c.initial);c.stable();
});

test('Home and Reset retain repeated-cell extent without duplicating controls or legends',async t=>{
 const c=await cameraFixture(t),nodes=flatten(c.host).length;c.click('2 × 2 × 2 cells');assert.equal(c.viewer.atoms.length,8);const repeated=c.viewer.getView();c.key('ArrowUp');c.key('+');c.key('Home');c.click('Reset');assert.deepEqual(c.viewer.getView(),repeated);assert.equal(c.viewer.atoms.length,8);
 c.click('Unit cell');assert.equal(c.viewer.atoms.length,1);assert.deepEqual(c.viewer.getView(),c.initial);assert.equal(flatten(c.host).length,nodes);assert.equal(flatten(c.host).filter(n=>n.className==='element-legend').length,1);c.stable();
});

test('finite references reset without tiling or mutating model/reference objects',async t=>{
 const c=await cameraFixture(t,true);c.key('ArrowLeft');c.key('-');c.key('Home');assert.deepEqual(c.viewer.getView(),c.initial);c.click('+');c.click('Reset');assert.deepEqual(c.viewer.getView(),c.initial);assert.equal(c.viewer.atoms.length,1);c.stable();
});

test('the shared legend static-position rule covers structure panels outside Reader',()=>{
 const css=readFileSync(new URL('../static/reader.css',import.meta.url),'utf8');
 assert.match(css,/\.reader-structure-panel \.element-legend,\.reader-main \.element-legend,\.reader-molecule-dialog \.element-legend\{position:static;inset:auto;transform:none;margin:8px 0;max-width:100%\}/);
 // Actual pixel containment in Reader/Data remains browser QA, not a CSS assertion.
});

test('a conceptual composition drawing is labelled honestly and source text remains text',async t=>{
 const prior={document:globalThis.document,fetch:globalThis.fetch};t.after(()=>Object.assign(globalThis,prior));globalThis.document={createElement:tag=>el(tag),createTextNode:text=>el('#text',text)};
 const entry=freeze({record_id:'fixture-product',sample_id:'prepared',shape:'composition-schematic',display_kind:'composition_schematic',inline_art_id:expectedArtIds[1],label:'Conceptual fixture product',rationale:'Invented composition only; morphology is not reported.',evidence:[],limitations:['No inferred physical shape.']});
 globalThis.fetch=async url=>{assert.match(String(url),/reader-morphology-interpretations\.json$/);return {ok:true,json:async()=>({entries:{'fixture-product:prepared':entry}})};};
 const r=freeze({record_id:'fixture-product',products:[{sample_id:'prepared',source_sample_label:'Prepared fixture',recipe_link:'explicit',composition:{value:'<img src=x onerror=fixture()>',status:'reported'},morphology:{value:null,status:'not_reported'}}]}),p=freeze({presentation_status:'pending',primary_product:{default_sample_id:'prepared'}}),before=JSON.stringify({r,p});
 const host=el('section');const mounted=await mountParticleContext(host,r,p);assert.equal(mounted.choose.value,'fixture-product:prepared');assert.match(host.textContent,/Conceptual product/);assert.doesNotMatch(host.textContent,/Inferred morphology|has not yet been assigned/);assert.match(host.textContent,/morphology is not reported/);assert.match(host.textContent,/<img src=x onerror=fixture\(\)>/);assert.equal(flatten(host).filter(n=>n.tagName==='img').length,0);assert.equal(flatten(host).filter(n=>n.innerHTML.startsWith('<svg')).length,1);assert.equal(JSON.stringify({r,p}),before);
});
