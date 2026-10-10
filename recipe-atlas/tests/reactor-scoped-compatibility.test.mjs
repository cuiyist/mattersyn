import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readReactorLineNote,reactorEnvironmentText,createReactorLineDetails,reactorLineCaption,reactorDisplayRecord,reactorQuantityUnavailable} from '../static/reactor-lines.mjs';

// Synthetic fixtures only. No actual paper, source, network, model or asset I/O.
const keys=['vessel_type','atmosphere','schlenk_line','glovebox','heating_method','stirring','addition_method','cooling_method'];
const marker='Reactor-line metadata (structured JSON): ';
const absent=()=>({value:'not reported',status:'not_reported',source_id:'fixture-main',locator:'Fixture reviewed scope locator',absence_scope:'Fixture bounded review scope; physical continuity is not established.'});
const reported=value=>({value,status:'reported',source_id:'fixture-main',locator:'Fixture reported locator'});
const line=()=>({reactor_line_id:absent(),...Object.fromEntries(keys.map(k=>[k,absent()]))});
const note=x=>'Preserved fixture prose.\n'+marker+JSON.stringify({reactor_line:x});
const operation=(x=line())=>({id:'fixture-operation',parameters:{},environment:{value:null,note:note(x),evidence:[]}});
const record=()=>({sources:[{id:'fixture-main',url:'https://example.invalid/fixture-main'}],operations:[]});
class Element{constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this._text='';}set textContent(x){this._text=String(x);this.children=[];}get textContent(){return this._text+this.children.map(c=>c.textContent).join(' ');}append(...children){this.children.push(...children);}}
const flatten=n=>[n,...n.children.flatMap(flatten)];
function dom(fn){const old=globalThis.document;globalThis.document={createElement:t=>new Element(t)};try{return fn();}finally{globalThis.document=old;}}
function row(details,label){return flatten(details).find(n=>n.tagName==='DIV'&&n.children[0]?.textContent===label);}

test('scoped dialect retains unknown ID and all absence scopes/citations without inventing basis or facts',()=>dom(()=>{
 const op=operation(),before=JSON.stringify(op),p=readReactorLineNote(op.environment.note),d=createReactorLineDetails(op,record());
 assert.equal(p.valid,true);assert.equal(p.scoped,true);assert.equal(p.attributes,undefined);assert.deepEqual(p.line,line());
 assert.equal(flatten(d).filter(n=>n.tagName==='DT').length,16);assert.equal(flatten(d).filter(n=>n.tagName==='A').length,9);
 assert.equal((d.textContent.match(/Absence scope:/g)||[]).length,9);assert.equal((d.textContent.match(/Scope citation:/g)||[]).length,9);
 assert.equal((d.textContent.match(/not reported/g)||[]).length,16);
 assert.match(row(d,'Local reactor line').textContent,/not reported.*Absence scope:.*Scope citation:/);
 assert.doesNotMatch(d.textContent,/Basis:|author-derived|Reactor-line metadata|"source_id"/);
 assert.equal(reactorEnvironmentText(op.environment),'Preserved fixture prose.');assert.equal(JSON.stringify(op),before);
 assert.match(reactorLineCaption(op,record(),'Fixture caption.'),/vessel type is not reported; no apparatus identity is inferred/);
}));

test('reported scoped facts preserve false/true, original prose and own source evidence distinctly from absence',()=>dom(()=>{
 const x=line();x.vessel_type=reported('fixture stated vessel');x.schlenk_line=reported(false);x.glovebox=reported(true);x.stirring=reported(false);
 const op=operation(x);op.environment.value='Original fixture environment';const d=createReactorLineDetails(op,record());
 for(const [name,value] of [['Schlenk line','no'],['Glovebox','yes'],['Stirring','no']])assert.match(row(d,name).textContent,new RegExp(name+' '+value));
 assert.match(row(d,'Vessel type').textContent,/Fixture reported locator/);assert.doesNotMatch(row(d,'Vessel type').textContent,/Scope citation:|Absence scope:/);
 assert.match(d.textContent,/Original fixture environment/);assert.equal(reactorEnvironmentText(op.environment),'Original fixture environment');
 assert.equal(reactorLineCaption(op,record(),'Fixture caption.'),'Fixture caption.');
}));

test('scoped unknowns and ID require exact fields, explicit absence scope, paired nonempty provenance and unknown value',()=>{
 const challenges=[x=>delete x.reactor_line_id,x=>x.extra=absent(),x=>x.Schlenk_line=absent(),x=>x.vessel_type.extra='unexpected',x=>delete x.vessel_type.absence_scope,x=>x.vessel_type.absence_scope='',x=>x.vessel_type.source_id=null,x=>x.vessel_type.locator=null,x=>x.vessel_type.locator=' ',x=>x.vessel_type.value=null,x=>x.vessel_type.value=false,x=>x.vessel_type.status='inferred',x=>x.reactor_line_id='invented-continuity',x=>x.reactor_line_id=null,x=>x.reactor_line_id=reported('invented-continuity'),x=>x.reactor_line_id={...reported('invented-continuity'),status:'author_derived'},x=>x.reactor_line_id.absence_scope='',x=>x.reactor_line_id.evidence=[]];
 for(const change of challenges){const x=line();change(x);assert.equal(readReactorLineNote(note(x)).valid,false);}
});

test('scoped reported categories reject unknown extras, false absences and incomplete or misplaced provenance',()=>{
 for(const f of [{...reported('fixture'),absence_scope:'Not reported scope'}, {...reported('fixture'),source_id:''},{...reported('fixture'),locator:''},{...reported('fixture'),value:42},{...reported('fixture'),value:'not reported'},{...reported('fixture'),basis:'invented'},{...reported('fixture'),evidence:[]}]){
  const x=line();x.vessel_type=f;assert.equal(readReactorLineNote(note(x)).valid,false);
 }
 for(const value of [false,true]){const x=line();x.stirring=reported(value);assert.equal(readReactorLineNote(note(x)).valid,true);}
});

test('every supplied scoped category and ID source must bind, including unknown citations',()=>dom(()=>{
 for(const key of ['reactor_line_id',...keys]){
  const x=line();x[key].source_id='unbound-fixture';const op=operation(x),d=createReactorLineDetails(op,record());
  assert.equal(readReactorLineNote(op.environment.note).valid,true);assert.match(d.textContent,/metadata is invalid/);
  assert.equal(flatten(d).filter(n=>n.tagName==='DT').length,0);assert.doesNotMatch(d.textContent,/unbound-fixture|Fixture reviewed scope locator/);
  assert.match(reactorLineCaption(op,record(),'Fixture caption.'),/could not be verified/);
 }
 const x=line();x.vessel_type={...reported('UNBOUND_VALUE'),source_id:'unbound-fixture'};assert.doesNotMatch(createReactorLineDetails(operation(x),record()).textContent,/UNBOUND_VALUE/);
}));

test('malformed explicit scoped payloads suppress raw JSON while preserving prose and failure notice',()=>dom(()=>{
 for(const payload of ['{broken','null','[]',JSON.stringify(line()),JSON.stringify({reactor_line:line(),extra:1}),JSON.stringify({reactor_line:{...line(),__unexpected__:1}})]){
  const op=operation();op.environment.note='Preserved fixture prose.\n'+marker+payload;
  assert.equal(readReactorLineNote(op.environment.note).valid,false);assert.equal(reactorEnvironmentText(op.environment),'Preserved fixture prose.');
  const d=createReactorLineDetails(op,record());assert.match(d.textContent,/metadata is invalid/);assert.doesNotMatch(d.textContent,/\{broken|"reactor_line"|"status"|Reactor-line metadata/);
 }
}));

test('ambiguous markers are rejected in either order and before the earliest marker no raw metadata leaks',()=>dom(()=>{
 const canonical={reactor_line_id:null,...Object.fromEntries(keys.map(k=>[k,{value:'not reported',status:'not_reported',source_id:null,locator:null}]))};
 const attr={reactor_line_id:{value:null,status:'not_reported',basis:'Fixture basis',evidence:[]},...Object.fromEntries(keys.map(k=>[k,{value:null,status:'not_reported',basis:'Fixture basis',evidence:[]}]))};
 const scoped=marker+JSON.stringify({reactor_line:line()});
 for(const other of ['reactor_line='+JSON.stringify(canonical),JSON.stringify({reactor_line:canonical}),'Reactor attributes: '+JSON.stringify(attr),scoped])for(const pair of [[scoped,other],[other,scoped]]){
  const op=operation();op.environment.note='Preserved fixture prose.\n'+pair.join('\n');
  assert.equal(readReactorLineNote(op.environment.note).valid,false);assert.equal(reactorEnvironmentText(op.environment),'Preserved fixture prose.');
  const d=createReactorLineDetails(op,record());assert.match(d.textContent,/metadata is invalid/);assert.doesNotMatch(d.textContent,/"reactor_line_id"|Reactor attributes:|reactor_line=|Reactor-line metadata/);
 }
}));

test('the new dialect does not widen canonical or attributes schemas or capture ordinary inline mentions',()=>{
 assert.equal(readReactorLineNote('Fixture prose mentions '+marker+'inline.'),null);
 assert.equal(readReactorLineNote('reactor_line='+JSON.stringify(line())).valid,false);
 assert.equal(readReactorLineNote(JSON.stringify({reactor_line:line()})).valid,false);
 assert.equal(readReactorLineNote('Reactor attributes: '+JSON.stringify(line())).valid,false);
 const op=operation();op.environment.note=marker+JSON.stringify({reactor_line:line()});assert.equal(reactorEnvironmentText(op.environment),'Not reported');
});

test('scoped absence text and locators remain text-only and executable URLs never become links',()=>dom(()=>{
 const x=line();x.glovebox.absence_scope='<img src=x onerror=fixture>';x.glovebox.locator='<script>fixture locator</script>';
 const r=record();r.sources[0].url='javascript:fixture';const d=createReactorLineDetails(operation(x),r);
 assert.match(d.textContent,/<img src=x onerror=fixture>/);assert.match(d.textContent,/<script>fixture locator<\/script>/);
 assert.equal(flatten(d).filter(n=>n.tagName==='A').length,0);assert.ok(flatten(d).every(n=>n.innerHTML===undefined));
}));

test('scoped dialect retains numeric evidence/zero safeguards and never mutates record or unknown provenance',()=>dom(()=>{
 const evidence=[{source_id:'fixture-main',locator:'Fixture quantity locator'}];
 const op=operation();op.parameters={reaction_volume:{value:0,unit:'mL',status:'reported',evidence},pressure:{value:1234,unit:'kPa',status:'reported',evidence:[]}};
 const r=record();r.operations=[op];const before=JSON.stringify(r),safe=reactorDisplayRecord(r),d=createReactorLineDetails(op,r);
 assert.match(d.textContent,/0 mL/);assert.match(d.textContent,/Fixture quantity locator/);assert.match(d.textContent,/source binding or value invalid/);assert.doesNotMatch(d.textContent,/1234 kPa/);
 assert.equal(safe.operations[0].parameters.pressure.value,null);assert.match(reactorQuantityUnavailable(safe.operations[0].parameters.pressure),/source binding or value invalid/);
 assert.equal(JSON.stringify(r),before);
}));
