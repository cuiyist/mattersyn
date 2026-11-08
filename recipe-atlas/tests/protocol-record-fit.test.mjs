import {test} from 'node:test';
import assert from 'node:assert/strict';
import {fitRecordGeometry,protocolArtHeight,protocolPresentationPolicy,PROTOCOL_SCENE_CAPTION,compactDrawingFacts,wireDrawingCallouts,nativeArtMetric,createProtocolArtFrame,createRecordFitController} from '../static/protocol-record-fit.mjs';
import {reportedDrawingFacts,reportedDrawingViewport,createReportedDrawing} from '../static/reported-scene-drawing.mjs';
import {reportedProtocolSceneDescriptor} from '../static/reported-protocol-scenes.mjs';
const spec=x=>({kind:'solution',vesselKind:'plain',added:[],substrates:[],environment:'',gasLine:false,heating:false,stirring:false,...x});
const q=(value,unit='degC')=>({value,unit,status:'reported'});
const op=(parameters={},extra={})=>({id:'step',action:'inject',label:'Inject reported stock',parameters,inputs:[],environment:{status:'not_reported'},...extra});
const record={materials:[],stocks:[],material_states:[],products:[],method:'Other'};
class E{
 constructor(tag){this.tagName=tag;this.children=[];this.style={};this.dataset={};this.attributes={};this._text='';}
 set textContent(value){this._text=String(value);this.children=[];}get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 append(...children){this.children.push(...children);}replaceChildren(...children){this._text='';this.children=[...children];}setAttribute(key,value){this.attributes[key]=value;}
 querySelectorAll(){return this.children.flatMap(child=>[child,...child.querySelectorAll()]);}
}
function dom(fn){const old=globalThis.document;globalThis.document={createElement:tag=>new E(tag),createElementNS:(_,tag)=>new E(tag),createTextNode:text=>{const e=new E('#text');e.textContent=text;return e;}};try{return fn();}finally{globalThis.document=old;}}
test('desktop/phone caps select the full drawing frame, independently of status',()=>{assert.equal(protocolArtHeight(1440),400);assert.equal(protocolArtHeight(390),320);for(const review_status of ['source_extracted','source_reviewed'])assert.deepEqual(protocolPresentationPolicy({quality:{review_status}}),{caption:PROTOCOL_SCENE_CAPTION,enlarge:true});assert.equal(protocolPresentationPolicy({}, {protectedPerPaper:true,protectedCaption:'Exact protected caption.'}).caption,'Exact protected caption.');assert.equal(protocolPresentationPolicy({}, {hasDrawing:false}).enlarge,false);});
test('one common record scale fits every native geometry and fixed-font overhead',()=>{const rows=[{width:300,height:290,overhead:95},{width:180,height:323,overhead:120},{width:80,height:170,overhead:25}];for(const maxHeight of [320,400]){const fit=fitRecordGeometry(rows,{width:280,maxHeight});assert.ok(fit.scale>0);assert.ok(fit.metrics.every(m=>Math.abs((m.renderedHeight-m.overhead)/m.height-fit.scale)<1e-12));assert.ok(fit.metrics.every(m=>m.renderedHeight<=maxHeight&&m.width*fit.scale<=280));}});
test('invalid geometry and impossible fixed annotations fail before applying a transform',()=>{for(const m of [{width:0,height:10},{width:10,height:NaN},{width:10,height:10,overhead:320}])assert.throws(()=>fitRecordGeometry([m],{width:280,maxHeight:320}));});
test('all fourteen fixed kinds and six vessel variants fit the same record plan',()=>{const kinds=['solution','inject','cool','degas','reflux','chamber','closed-reactor','furnace','centrifuge','filter','workup-tube','dry-tube','mill-jar','mortar-pestle'],vessels=['plain','flask','three-neck-flask','tube','vial','beaker'];const rows=kinds.flatMap(kind=>vessels.map(vesselKind=>({...reportedDrawingViewport(spec({kind,vesselKind})),overhead:100})));const fit=fitRecordGeometry(rows,{width:280,maxHeight:320});assert.equal(rows.length,84);assert.ok(fit.metrics.every(m=>m.renderedHeight<=320));});
test('native artwork metric preserves negative appendages and frame rebases their origin',()=>dom(()=>{const metric=nativeArtMetric({left:30,top:40,right:130,bottom:140,width:100,height:100},[{left:10,top:15,right:150,bottom:170,width:140,height:155}]);assert.deepEqual(metric,{width:140,height:155,baseWidth:100,originX:20,originY:25});const art=new E('div'),frame=createProtocolArtFrame(art,{metric,scale:.5,width:280,maxHeight:320});assert.equal(art.style.left,'20px');assert.equal(art.style.top,'25px');assert.equal(frame.style.height,'77.5px');assert.equal(frame.dataset.nativeArtWidth,'140');assert.equal(frame.children[0].style.transform,'scale(0.5)');}));
test('normal own names and full values are never shortened merely because they are long',()=>{const s=spec({added:['Very long reported chemical identity with an oxidation state'],addedLabels:['Very long reported chemical identity with an oxidation state']}),conditions=[{key:'temperature',value:'180 °C · ramp target',drawingValue:'180 °C'}],f=reportedDrawingFacts(s,conditions),out=compactDrawingFacts(f,s,conditions,{compact:true});assert.equal(out.facts.added[0].label,s.added[0]);assert.deepEqual(out.fullFacts,[]);});
test('measured compact fallback keeps a reported short feed name instead of replacing it by elemental formula',()=>{const s=spec({added:['TOPSe'],addedFormulas:['Se']}),f=reportedDrawingFacts(s,[]);assert.equal(compactDrawingFacts(f,s,[],{fallback:true}).facts.added[0].label,'TOPSe');});
test('compact source details and meaningful quantity qualifiers have exact accessible full-fact targets',()=>dom(()=>{const s=spec({kind:'chamber',added:['Ga']}),conditions=[{key:'Ga_flux',value:'1 ML/s · own exact source qualifier'},{key:'substrate_temperature',value:'180 °C · ramp target',drawingValue:'180 °C'}],f=reportedDrawingFacts(s,conditions),result=compactDrawingFacts(f,s,conditions,{fallback:true}),host=new E('div');const source=new E('span');source.textContent=result.facts.sources[0].lines[0];const temp=new E('span');temp.textContent='180 °C ↗';host.append(source,temp);wireDrawingCallouts(host,result.fullFacts,'record step');const links=host.querySelectorAll().filter(x=>x.tagName==='a');assert.equal(links.length,2);assert.ok(links.every(x=>x.href.startsWith('#protocol-fact-record-step-')));assert.ok(result.fullFacts.some(x=>x.value==='180 °C · ramp target'));assert.ok(result.fullFacts.some(x=>x.value.includes('own exact source qualifier')));}));
test('only own reported reaction/mixture temperatures above25C imply hot addition',()=>{for(const action of ['inject','add'])for(const [value,expected]of [[25,false],[25.1,true],[80,true]]){const d=reportedProtocolSceneDescriptor(op({temperature:q(value)},{action}),record);assert.equal(d.heating,expected);}assert.equal(reportedProtocolSceneDescriptor(op({temperature:q(299,'K')}),record).heating,true);assert.equal(reportedProtocolSceneDescriptor(op({temperature:{...q(null),maximum:200}}),record).heating,false);});
test('source/feed/stock-only temperatures cannot invent a heated reaction vessel',()=>{for(const key of ['stock_temperature','source_temperature','feed_temperature','precursor_temperature','injection_solution_temperature'])assert.equal(reportedProtocolSceneDescriptor(op({[key]:q(180)}),record).heating,false,key);assert.equal(reportedProtocolSceneDescriptor(op({reaction_temperature:q(180)}),record).heating,true);});
test('heating removed, cooling and workup never borrow a warm temperature plate',()=>{for(const action of ['cool','wash','dry'])assert.equal(reportedProtocolSceneDescriptor(op({temperature:q(80)},{action}),record).heating,false);assert.equal(reportedProtocolSceneDescriptor(op({temperature:q(80)},{label:'Inject after heating was removed'}),record).heating,false);});
test('recipe chemical-charge prose is not accepted as a vessel',()=>{const d=reportedProtocolSceneDescriptor(op(),{...record,products:[{notes:['Reactor: 3.2 g of trioctylphosphine (TOP) (Main PDF p.2).']}]});assert.equal(d.vessel,null);const positive=reportedProtocolSceneDescriptor(op(),{...record,products:[{notes:['Reactor: three-neck flask (Main PDF p.2).']}]});assert.equal(positive.vessel.value,'three-neck flask');});
test('a native image load invalidates the placeholder plan and disconnect prevents later remount work',()=>{
 const previous=globalThis.document,events={},image={complete:false,addEventListener:(name,fn)=>{events[name]=fn;}};
 let loaded=false,changed=0;
 const frame={getBoundingClientRect:()=>({width:280}),querySelectorAll:()=>[]};
 const host={isConnected:true,append(){},querySelector:()=>frame};
 globalThis.document={createElement:()=>({dataset:{},style:{},replaceChildren(){},remove(){}})};
 try{
  const controller=createRecordFitController({host,operations:[{id:'image'}],createArt:()=>({getBoundingClientRect:()=>({left:0,top:0,right:100,bottom:loaded?200:100,width:100,height:loaded?200:100}),querySelectorAll:selector=>selector==='img'?[image]:[]}),onChange:()=>{changed++;}});
  assert.equal(controller.refresh(frame),true);assert.equal(controller.options('image').metric.height,100);
  image.complete=true;loaded=true;events.load();assert.equal(changed,1);assert.equal(controller.options('image').metric.height,200);
  controller.disconnect();events.load();assert.equal(changed,1);
 }finally{globalThis.document=previous;}
});

test('a short width-limited furnace reserves the measured apparatus-panel padding',()=>{
 const fit=fitRecordGeometry([{id:'only-furnace',width:300,height:217,overhead:24,horizontalOverhead:16}],{width:310,maxHeight:320});
 assert.ok(Math.abs(fit.scale-(294/300*.995))<1e-12);
 assert.ok(300*fit.scale<=294);assert.ok(fit.metrics[0].renderedHeight<320);
 // The former outer-frame-only plan would put its right edge beyond the panel.
 assert.ok(300*(310/300*.995)>294);
});
test('measured inner widths constrain the one scale shared across a mixed record',()=>{
 const fit=fitRecordGeometry([{width:300,height:217,overhead:24,horizontalOverhead:16},{width:180,height:260,overhead:20,horizontalOverhead:24}],{width:310,maxHeight:320});
 assert.ok(fit.metrics.every(m=>m.width*fit.scale<=310-m.horizontalOverhead));
 for(const horizontalOverhead of [-1,NaN,310])assert.throws(()=>fitRecordGeometry([{width:300,height:217,horizontalOverhead}],{width:310,maxHeight:320}));
});
