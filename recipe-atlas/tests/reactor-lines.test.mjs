import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {readReactorLineNote,reactorEnvironmentText,createReactorLineDetails,reactorLineCaption,reactorDisplayRecord,reactorQuantityUnavailable} from '../static/reactor-lines.mjs';
import {quantityValue} from '../static/quantity-value.mjs';
import {matchProtocolCondition} from '../static/protocol-conditions.mjs';

// Invented fixtures only. No production record, source, asset, HTTP or model I/O.
const keys=['vessel_type','atmosphere','schlenk_line','glovebox','heating_method','stirring','addition_method','cooling_method'];
const missing=()=>({value:'not reported',status:'not_reported',source_id:null,locator:null});
const reported=value=>({value,status:'reported',source_id:'fixture-main',locator:'Fixture page 2, step A'});
function line(overrides={}){return {reactor_line_id:null,...Object.fromEntries(keys.map(k=>[k,missing()])),...overrides};}
function operation(metadata=line(),parameters={}){return {id:'fixture-stage',action:'annotate_condition',label:'Fixture stage',stage:'synthesis',description:'Invented stage text.',parameters,inputs:[],outputs:[],evidence:[],endpoint:{value:null,note:''},environment:{value:'Original fixture environment',status:'reported',note:'Original fixture narrative.\nreactor_line='+JSON.stringify(metadata),evidence:[{source_id:'fixture-main',locator:'Fixture page 1, environment'}]}};}
const record=()=>({sources:[{id:'fixture-main',url:'https://example.invalid/fixture-main'}],materials:[],stocks:[],material_states:[],operations:[]});
const quantity=(value,unit='mL')=>({value,minimum:null,maximum:null,unit,status:'reported',evidence:[{source_id:'fixture-main',locator:'Fixture page 3, quantity'}]});
class Element{
 constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.dataset={};this.attributes={};this._text='';this.style={};this.classList={add(){},toggle(){}};}
 set textContent(v){this._text=String(v);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent).join(' ');}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this._text='';this.children=[...children];}
 setAttribute(k,v){this.attributes[k]=String(v);}
 getAttribute(k){return this.attributes[k]??null;}
 addEventListener(){}
}
const flatten=n=>[n,...n.children.flatMap(flatten)];
function dom(run){const previous=globalThis.document;globalThis.document={createElement:tag=>new Element(tag)};try{return run();}finally{globalThis.document=previous;}}

test('reported categories have readable labels, yes/no values and their own source locator links',()=>dom(()=>{
 const metadata=line({reactor_line_id:'fixture-local-line',vessel_type:reported('vial'),atmosphere:reported('Ar'),schlenk_line:reported(false),glovebox:reported(true),heating_method:reported('oven'),stirring:reported(true),addition_method:reported('dropwise'),cooling_method:reported('natural cooling')});
 const op=operation(metadata),before=JSON.stringify(op),details=createReactorLineDetails(op,record());
 for(const value of ['Vessel type','vial','Atmosphere','Ar','Schlenk line','no','Glovebox','yes','fixture-local-line','Original fixture narrative.','Original fixture environment','Fixture page 1, environment'])assert.ok(details.textContent.includes(value),value);
 const links=flatten(details).filter(n=>n.tagName==='A');assert.equal(links.length,9);
 assert.ok(links.every(n=>n.href==='https://example.invalid/fixture-main'));
 assert.equal(links.filter(n=>n.textContent.includes('Fixture page 2, step A')).length,8);
 assert.equal(JSON.stringify(op),before);assert.doesNotMatch(details.textContent,/reactor_line=|"source_id"/);
}));

test('numeric zero, bounds, rates and source basis remain readable with per-quantity evidence',()=>dom(()=>{
 const parameters={vessel_volume:quantity(0),reaction_volume:{...quantity(null),minimum:20,maximum:30,basis:'fixture total charge'},fill_fraction:quantity(50,'%'),heating_rate:quantity(5,'degC/min'),stirring_rate:quantity(200,'rpm'),addition_rate:quantity(2,'mL/min'),pressure:{...quantity(null,'kPa'),maximum:100,maximum_exclusive:true}};
 const details=createReactorLineDetails(operation(line(),parameters),record());
 for(const value of ['0 mL','20–30 mL','fixture total charge','50 %','5 degC/min','200 rpm','2 mL/min','<100 kPa'])assert.ok(details.textContent.includes(value),value);
 assert.equal(flatten(details).filter(n=>n.tagName==='A'&&n.textContent.includes('Fixture page 3, quantity')).length,7);
}));

test('unknown categorical and numeric fields stay not reported without invented locators or vessels',()=>dom(()=>{
 const op=operation(),details=createReactorLineDetails(op,record());
 assert.equal((details.textContent.match(/not reported/g)||[]).length,15);
 assert.equal(flatten(details).filter(n=>n.tagName==='A').length,1); // original environment evidence only
 assert.match(reactorLineCaption(op,record(),'Fixture illustration.'),/Conceptual vessel: vessel type is not reported/);
 assert.doesNotMatch(details.textContent,/three-neck flask|oil bath|vacuum/);
}));

test('the tagged note and explicit reactor_line JSON wrapper retain original prose',()=>{
 const op=operation();assert.equal(readReactorLineNote(op.environment.note).prose,'Original fixture narrative.');
 assert.equal(reactorEnvironmentText(op.environment),'Original fixture environment');
 op.environment.value=null;assert.equal(reactorEnvironmentText(op.environment),'Original fixture narrative.');
 op.environment.note='Preserved wrapper prose.\n'+JSON.stringify({reactor_line:line()});
 assert.equal(readReactorLineNote(op.environment.note).valid,true);assert.equal(reactorEnvironmentText(op.environment),'Preserved wrapper prose.');
 op.environment.note='Preserved pretty wrapper prose.\n'+JSON.stringify({reactor_line:line()},null,2);
 assert.equal(readReactorLineNote(op.environment.note).valid,true);assert.equal(reactorEnvironmentText(op.environment),'Preserved pretty wrapper prose.');
 op.environment.value=false;assert.equal(reactorEnvironmentText(op.environment),'false');
});

test('malformed explicit JSON is not leaked and does not invent missing source facts',()=>dom(()=>{
 const op=operation();op.environment.value=null;op.environment.note='Preserved malformed prose.\nreactor_line={broken';
 assert.equal(readReactorLineNote(op.environment.note).valid,false);
 assert.equal(reactorEnvironmentText(op.environment),'Preserved malformed prose.');
 const details=createReactorLineDetails(op,record());assert.match(details.textContent,/structured source metadata is invalid/);
 assert.ok(details.textContent.includes('Fixture page 1, environment'));assert.doesNotMatch(details.textContent,/\{broken|Vessel type/);
 assert.match(reactorLineCaption(op,record(),'Fixture caption.'),/Conceptual vessel:.*could not be verified/);
}));

test('missing locators, invalid category shapes, fabricated absences and extra keys are rejected',()=>{
 const bad=[line({vessel_type:{...reported('vial'),locator:''}}),line({vessel_type:reported(1)}),line({stirring:{...missing(),value:false}}),{...line(),unexpected_field:reported('fixture')},line({atmosphere:{...reported('Ar'),status:'inferred'}})];
 for(const metadata of bad)assert.equal(readReactorLineNote(operation(metadata).environment.note).valid,false);
});

test('unresolved category source identity displays an unavailable notice without claiming the value',()=>dom(()=>{
 const op=operation(line({vessel_type:{...reported('unbound vessel'),source_id:'missing-source'}}));
 const details=createReactorLineDetails(op,record());assert.match(details.textContent,/metadata is invalid/);assert.doesNotMatch(details.textContent,/unbound vessel/);
 assert.match(reactorLineCaption(op,record(),'Fixture caption.'),/Conceptual vessel/);
}));

test('invalid numeric values and absent quantity evidence are not displayed as reported data',()=>dom(()=>{
 const op=operation(line(),{vessel_volume:{...quantity(25),evidence:[]},pressure:{...quantity(Infinity,'kPa')},fill_fraction:{...quantity(7,'%'),status:'not_reported'}});
 const details=createReactorLineDetails(op,record());assert.match(details.textContent,/source binding or value invalid/);assert.match(details.textContent,/inconsistent missing value/);
 assert.doesNotMatch(details.textContent,/25 mL|Infinity|7 %/);
}));

test('old notes, old false-value fallback and unrelated JSON retain their existing behavior',()=>{
 for(const note of ['Old ordinary prose.','{"unrelated":"old JSON"}','Prose mentions reactor_line but contains no explicit marker.']){
  const env={value:null,note};assert.equal(readReactorLineNote(note),null);assert.equal(reactorEnvironmentText(env),note);
  const op={environment:env,parameters:{vessel_volume:quantity(25)}};assert.equal(createReactorLineDetails(op,record()),null);assert.equal(reactorLineCaption(op,record(),'Old caption.'),'Old caption.');
 }
 assert.equal(reactorEnvironmentText({value:false,note:'Old fallback.'}),'Old fallback.');
});

test('textContent rendering escapes markup and refuses executable citation URLs',()=>dom(()=>{
 const op=operation(line({vessel_type:reported('<script>fixture</script>')})),r=record();r.sources[0].url='javascript:fixture';
 const details=createReactorLineDetails(op,r);assert.ok(details.textContent.includes('<script>fixture</script>'));
 assert.equal(flatten(details).filter(n=>n.tagName==='A').length,0);assert.ok(flatten(details).every(n=>n.innerHTML===undefined));
}));

test('a source-bound reported vessel preserves the existing caption without selecting apparatus',()=>{
 const op=operation(line({vessel_type:reported('vial')}));assert.equal(reactorLineCaption(op,record(),'Original reviewed caption.'),'Original reviewed caption.');
});

test('the retained original fact helper demonstrates the hidden-note and raw-JSON gap',()=>{
 const code=readFileSync(new URL('../static/protocol-visuals.mjs',import.meta.url),'utf8');
 const body=/function fact\(f\)\{([^}]+)\}/.exec(code)?.[1];assert.ok(body);
 const originalFact=new Function('f',body),env=operation().environment;
 assert.equal(originalFact(env),'Original fixture environment');
 const noteOnly={...env,value:null};assert.match(originalFact(noteOnly),/reactor_line=/);
 assert.equal(reactorEnvironmentText(noteOnly),'Original fixture narrative.');
});

// Exercise the copied mount function itself with all unrelated artwork/providers
// replaced by inert stubs. No source-specific assets or records are loaded.
function mountWithInertProviders(overrides={}){
 const source=readFileSync(new URL('../static/protocol-visuals.mjs',import.meta.url),'utf8');
 const names=[...source.matchAll(/^import \{([^}]+)\} from .+;$/gm)].flatMap(m=>m[1].split(',').map(n=>n.trim().split(/\s+as\s+/).at(-1)));
 const actual={reactorEnvironmentText,createReactorLineDetails,reactorLineCaption,reactorDisplayRecord,reactorQuantityUnavailable,quantityValue,matchProtocolCondition,...overrides,kind:()=> 'context',mountProtocolReferences:()=>Promise.resolve()};
 const inert=()=>null;
 const code=source.replace(/^import .+;\r?\n/gm,'').replace('export function mountProtocol','function mountProtocol');
 return new Function(...names,code+'\nreturn mountProtocol;')(...names.map(name=>actual[name]||inert));
}
test('the copied protocol mount displays new fields and prose, hides JSON, and qualifies unknown vessel',()=>dom(()=>{
 const r=record();r.operations=[operation(line(),{vessel_volume:quantity(25)})];
 const host=new Element('div');mountWithInertProviders()(host,r);
 for(const value of ['Original fixture environment','Original fixture narrative.','Vessel volume','25 mL','Fixture page 3, quantity','Conceptual vessel: vessel type is not reported'])assert.ok(host.textContent.includes(value),value);
 assert.doesNotMatch(host.textContent,/reactor_line=|"reactor_line_id"|"status"/);
}));
test('the copied protocol mount leaves old environments and captions without reactor rows',()=>dom(()=>{
 const r=record(),op=operation();op.environment.note='Old fixture note.';r.operations=[op];
 const host=new Element('div');mountWithInertProviders()(host,r);
 assert.ok(host.textContent.includes('Original fixture environment'));assert.doesNotMatch(host.textContent,/Reactor details|Conceptual vessel:/);
}));

function renderedText(op,overrides={}){return dom(()=>{
 const r=record();r.operations=[op];const before=JSON.stringify(r),host=new Element('div');
 mountWithInertProviders(overrides)(host,r);assert.equal(JSON.stringify(r),before);return host.textContent;
});}
// The real unchanged matcher exposes the generic Pressure row as well as the
// expanded summary; a null matcher cannot exercise these failure paths.
for(const challenge of [
 {name:'missing own pressure evidence',key:'pressure',q:{...quantity(1009,'kPa'),evidence:[]},forbidden:/1009 kPa/,notice:/source binding or value invalid/},
 {name:'unresolved pressure source',key:'pressure',q:{...quantity(1011,'kPa'),evidence:[{source_id:'missing-source',locator:'Fixture locator'}]},forbidden:/1011 kPa/,notice:/source binding or value invalid/},
 {name:'nonnumeric pressure',key:'pressure',q:quantity('INVENTED_INVALID_PRESSURE','kPa'),forbidden:/INVENTED_INVALID_PRESSURE/,notice:/source binding or value invalid/},
 {name:'contradictory missing pressure scalar',key:'pressure',q:{...quantity(1013,'kPa'),status:'not_reported'},forbidden:/1013 kPa/,notice:/inconsistent missing value/},
 {name:'expanded vessel volume without evidence',key:'vessel_volume',q:{...quantity(1021),evidence:[]},forbidden:/1021 mL/,notice:/source binding or value invalid/}
])test('tagged mount suppresses '+challenge.name+' across generic and expanded displays',()=>{
 assert.equal(matchProtocolCondition([['pressure',challenge.q]],'pressure')?.[1],challenge.q);
 const text=renderedText(operation(line(),{[challenge.key]:challenge.q}));
 assert.match(text,challenge.notice);assert.doesNotMatch(text,challenge.forbidden);
});

test('display views preserve valid and untagged identities and never mutate the source operation',()=>{
 const r=record(),valid=operation(line(),{pressure:quantity(0,'kPa')});r.operations=[valid];
 assert.equal(reactorDisplayRecord(r),r);
 const old=operation(line(),{pressure:{...quantity(1031,'kPa'),evidence:[]}});old.environment.note='Old untagged note.';r.operations=[old];
 assert.equal(reactorDisplayRecord(r),r);assert.match(renderedText(old),/1031 kPa/);
 assert.doesNotMatch(renderedText(old),/Reactor details|Reactor quantity unavailable|Conceptual vessel:/);
 const invalid=operation(line(),{pressure:{...quantity(1033,'kPa'),evidence:[]}});r.operations=[invalid];const before=JSON.stringify(r),view=reactorDisplayRecord(r);
 assert.notEqual(view,r);assert.notEqual(view.operations[0],invalid);assert.equal(JSON.stringify(r),before);
 const q=view.operations[0].parameters.pressure;assert.equal(q.value,null);assert.equal(q.minimum,null);assert.equal(q.maximum,null);
 assert.match(reactorQuantityUnavailable(q),/source binding or value invalid/);assert.doesNotMatch(JSON.stringify(view),/1033/);
});

test('specialized condition providers receive only the safe view through both operation and record',()=>{
 const op=operation(line(),{pressure:{...quantity(1041,'kPa'),evidence:[]},vessel_volume:{...quantity(1043),evidence:[]}});let called=false;
 const text=renderedText(op,{
  buildRusch2026Scene:()=>({caption:'Invented specialized illustration.'}),
  createRusch2026ConditionGrid:(displayOperation,displayRecord)=>{
   called=true;
   for(const q of [displayOperation.parameters.pressure,displayOperation.parameters.vessel_volume,displayRecord.operations[0].parameters.pressure,displayRecord.operations[0].parameters.vessel_volume]){
    assert.equal(q.value,null);assert.equal(quantityValue(q),null);assert.match(reactorQuantityUnavailable(q),/source binding or value invalid/);
   }
   const grid=new Element('dl');grid.append(Object.assign(new Element('dd'),{textContent:reactorQuantityUnavailable(displayOperation.parameters.pressure)}));return grid;
  }
 });
 assert.equal(called,true);assert.match(text,/source binding or value invalid/);assert.doesNotMatch(text,/1041 kPa|1043 mL/);
});

test('actual generic pressure keeps source-bound zero and range while honest unknown stays unknown',()=>{
 for(const [q,expected] of [[quantity(0,'kPa'),/0 kPa/],[{...quantity(null,'kPa'),minimum:20,maximum:30},/20–30 kPa/]]){
  const text=renderedText(operation(line(),{pressure:q}));assert.match(text,expected);assert.match(text,/Fixture page 3, quantity/);assert.doesNotMatch(text,/Reactor quantity unavailable/);
 }
 const text=renderedText(operation(line(),{pressure:{...quantity(null,'kPa'),status:'not_reported',evidence:[]}}));assert.match(text,/not reported/);assert.doesNotMatch(text,/Reactor quantity unavailable|0 kPa/);
});

const attributeMissing=()=>({value:null,status:'not_reported',basis:'Fixture missing basis',evidence:[]});
const attributeReported=value=>({value,status:'reported',basis:'Fixture reported basis',evidence:[{source_id:'fixture-main',locator:'Fixture attributes page 2'}]});
function attributes(overrides={}){return {reactor_line_id:attributeMissing(),...Object.fromEntries(keys.map(k=>[k,attributeMissing()])),...overrides};}
function attributeOperation(metadata=attributes(),parameters={}){
 const op=operation(line(),parameters);op.environment.note='Original fixture narrative.\nReactor attributes: '+JSON.stringify(metadata);return op;
}

test('explicit attribute notes render both Schlenk spellings and all three provenance shapes without mutation',()=>dom(()=>{
 for(const alias of ['schlenk_line','Schlenk_line'])for(const shape of ['direct','array','both']){
  const metadata=attributes({vessel_type:attributeReported('fixture vessel'),schlenk_line:attributeReported(false)});
  if(alias==='Schlenk_line'){metadata.Schlenk_line=metadata.schlenk_line;delete metadata.schlenk_line;}
  const f=metadata.vessel_type;
  if(shape!=='array'){f.source_id='fixture-main';f.source_locator='Fixture attributes page 2';}
  if(shape==='direct')delete f.evidence;
  const op=attributeOperation(metadata),before=JSON.stringify(op),parsed=readReactorLineNote(op.environment.note);
  assert.equal(parsed.valid,true);assert.equal(parsed.attributes,true);assert.equal(parsed.line.vessel_type.value,'fixture vessel');
  assert.equal(parsed.line.vessel_type.basis,f.basis);assert.equal(parsed.line.schlenk_line.value,false);
  const details=createReactorLineDetails(op,record());assert.match(details.textContent,/Schlenk line no/);
  assert.match(details.textContent,/Basis: Fixture reported basis/);assert.match(details.textContent,/Fixture attributes page 2/);
  assert.doesNotMatch(details.textContent,/Reactor attributes:|"source_id"|"status"/);
  assert.equal(JSON.stringify(op),before);assert.equal(reactorLineCaption(op,record(),'Fixture caption.'),'Fixture caption.');
 }
}));

test('attribute details preserve every citation and basis, including missing fields and a labelled derived ID',()=>dom(()=>{
 const a={source_id:'fixture-main',locator:'Fixture first locator'},b={source_id:'fixture-si',locator:'Fixture second locator'};
 const metadata=attributes({
  reactor_line_id:{value:'fixture-local',status:'author_derived',basis:'Fixture local bookkeeping',evidence:[a]},
  vessel_type:{...attributeReported('fixture vessel'),source_id:a.source_id,source_locator:a.locator,evidence:[a,b]},
  glovebox:{value:'not reported',status:'not_reported',basis:'Fixture absence reviewed',evidence:[b]},
  atmosphere:{value:null,status:'not_reported',basis:'Fixture null retained',source_id:b.source_id,source_locator:b.locator}
 });
 const r=record();r.sources.push({id:'fixture-si',url:'https://example.invalid/fixture-si'});
 const op=attributeOperation(metadata),before=JSON.stringify(op),details=createReactorLineDetails(op,r);
 assert.match(details.textContent,/Local reactor line \(author-derived\) fixture-local/);
 for(const basis of ['Fixture local bookkeeping','Fixture absence reviewed','Fixture null retained'])assert.ok(details.textContent.includes('Basis: '+basis));
 assert.equal(flatten(details).filter(n=>n.tagName==='A').length,6); // original environment + all five attribute citations
 assert.equal(flatten(details).filter(n=>n.tagName==='A'&&n.href.endsWith('/fixture-si')).length,3);
 assert.equal(readReactorLineNote(op.environment.note).line.atmosphere.value,null);
 assert.equal(JSON.stringify(op),before);assert.doesNotMatch(details.textContent,/glovebox yes|Atmosphere Ar/);
}));

test('missing attribute values remain missing and no local identifier or vessel is inferred',()=>dom(()=>{
 const metadata=attributes(),op=attributeOperation(metadata),details=createReactorLineDetails(op,record());
 assert.equal((details.textContent.match(/not reported/g)||[]).length,16);
 assert.equal(flatten(details).filter(n=>n.tagName==='A').length,1);
 assert.doesNotMatch(details.textContent,/author-derived|three-neck flask|vacuum/);
 assert.match(reactorLineCaption(op,record(),'Fixture caption.'),/vessel type is not reported/);
}));

test('attribute parser rejects conflicting values, unknown shapes, incomplete provenance and derived categorical facts',()=>{
 const bad=[
  {...attributes(),unknown:attributeMissing()},
  attributes({Schlenk_line:attributeMissing()}),
  attributes({stirring:{...attributeMissing(),value:false}}),
  attributes({vessel_type:{...attributeReported('fixture'),status:'author_derived'}}),
  attributes({reactor_line_id:{...attributeReported('fixture-id'),status:'reported'}}),
  attributes({vessel_type:{...attributeReported('fixture'),basis:''}}),
  attributes({vessel_type:{...attributeReported('fixture'),basis:null}}),
  attributes({vessel_type:{...attributeReported('fixture'),value:7}}),
  attributes({vessel_type:{...attributeReported('fixture'),value:'not reported'}}),
  attributes({vessel_type:{...attributeReported('fixture'),evidence:[]}}),
  attributes({vessel_type:{...attributeReported('fixture'),extra:'unknown'}}),
  attributes({vessel_type:{...attributeReported('fixture'),source_id:'fixture-main'}}),
  attributes({vessel_type:{...attributeReported('fixture'),source_id:'fixture-main',source_locator:'Conflicting locator'}}),
  attributes({vessel_type:{...attributeReported('fixture'),source_id:null,source_locator:null}}),
  attributes({vessel_type:{...attributeReported('fixture'),evidence:[{source_id:'fixture-main',locator:'',extra:'unknown'}]}}),
  attributes({vessel_type:{...attributeReported('fixture'),evidence:[{source_id:'fixture-main',locator:'Fixture locator',extra:'unknown'}]}})
 ];
 for(const metadata of bad)assert.equal(readReactorLineNote(attributeOperation(metadata).environment.note).valid,false);
});

test('every supplied attribute citation must bind to a known source, even for missing or derived fields',()=>dom(()=>{
 for(const key of ['vessel_type','glovebox','reactor_line_id']){
  const f=key==='vessel_type'?attributeReported('UNBOUND_FIXTURE_VALUE'):key==='reactor_line_id'?{...attributeMissing(),status:'author_derived',value:'UNBOUND_FIXTURE_ID'}:attributeMissing();
  f.evidence=[{source_id:'missing-source',locator:'Fixture unknown source'}];
  const op=attributeOperation(attributes({[key]:f})),details=createReactorLineDetails(op,record());
  assert.match(details.textContent,/structured source metadata is invalid/);assert.doesNotMatch(details.textContent,/UNBOUND_FIXTURE|Fixture unknown source/);
  assert.match(reactorLineCaption(op,record(),'Fixture caption.'),/could not be verified/);
 }
}));

test('malformed attributes and competing explicit metadata do not leak JSON into the environment',()=>dom(()=>{
 for(const note of ['Preserved prose.\nReactor attributes: {broken','Preserved prose.\nreactor_line='+JSON.stringify(line())+'\nReactor attributes: '+JSON.stringify(attributes())]){
  const op=attributeOperation();op.environment.value=null;op.environment.note=note;
  assert.equal(readReactorLineNote(note).valid,false);assert.equal(reactorEnvironmentText(op.environment),'Preserved prose.');
  const details=createReactorLineDetails(op,record());assert.match(details.textContent,/metadata is invalid/);
  assert.doesNotMatch(details.textContent,/\{broken|"reactor_line_id"|Reactor attributes:|reactor_line=/);
 }
 assert.equal(readReactorLineNote('Old prose mentions Reactor attributes: without an appended line.'),null);
}));

test('actual protocol mount handles attribute notes and preserves existing numeric safeguards',()=>{
 const op=attributeOperation(attributes({atmosphere:attributeReported('fixture atmosphere')}),{pressure:{...quantity(1051,'kPa'),evidence:[]},reaction_volume:quantity(0)});
 const text=renderedText(op);
 for(const value of ['Original fixture environment','Original fixture narrative.','fixture atmosphere','Fixture attributes page 2','0 mL'])assert.ok(text.includes(value),value);
 assert.match(text,/source binding or value invalid/);assert.doesNotMatch(text,/1051 kPa|Reactor attributes:|"basis"/);
});

test('condition grid CSS overrides global flex rows with full-width wrapping labels, values and citations',()=>{
 const css=readFileSync(new URL('../static/styles.css',import.meta.url),'utf8');
 assert.match(css,/\.protocol-condition-grid>div\{display:block;min-width:0\}/);
 assert.match(css,/\.protocol-condition-grid dt,\.protocol-condition-grid dd\{[^}]*width:100%;[^}]*text-align:left;[^}]*overflow-wrap:anywhere;[^}]*word-break:normal/);
 assert.match(css,/\.protocol-condition-grid dd>small\{display:block;/);
});

test('author-derived local ID requires its own nonempty source-located evidence in either provenance shape',()=>dom(()=>{
 for(const provenance of [{evidence:[]},{source_id:null,source_locator:null}]){
  const metadata=attributes({reactor_line_id:{value:'UNBOUND_DERIVED_FIXTURE_ID',status:'author_derived',basis:'Fixture local bookkeeping',...provenance}});
  const op=attributeOperation(metadata),before=JSON.stringify(op),parsed=readReactorLineNote(op.environment.note);
  assert.equal(parsed.valid,false);
  const details=createReactorLineDetails(op,record());assert.match(details.textContent,/structured source metadata is invalid/);
  assert.doesNotMatch(details.textContent,/UNBOUND_DERIVED_FIXTURE_ID|author-derived/);
  assert.match(reactorLineCaption(op,record(),'Fixture caption.'),/could not be verified/);
  assert.doesNotMatch(renderedText(op),/UNBOUND_DERIVED_FIXTURE_ID/);
  assert.equal(JSON.stringify(op),before);
 }
}));


// Invented fixtures for the explicit attributes locator alias; no production I/O.
test('direct attribute citations accept either single locator spelling and retain source values without mutation',()=>dom(()=>{
 for(const locatorKey of ['locator','source_locator']){
  const citation={value:'fixture alias vessel',status:'reported',basis:'Fixture alias basis',source_id:'fixture-main',[locatorKey]:'Fixture alias page 4'};
  const metadata=attributes({vessel_type:citation,atmosphere:{value:'not reported',status:'not_reported',basis:'Fixture missing atmosphere',source_id:null,[locatorKey]:null}});
  const op=attributeOperation(metadata),before=JSON.stringify(op),parsed=readReactorLineNote(op.environment.note);
  assert.equal(parsed.valid,true);assert.equal(parsed.attributes,true);
  assert.equal(parsed.line.vessel_type[locatorKey],citation[locatorKey]);
  assert.equal(parsed.line.vessel_type.value,citation.value);assert.equal(parsed.line.vessel_type.basis,citation.basis);
  assert.deepEqual(parsed.line.vessel_type.evidence,[{source_id:'fixture-main',locator:'Fixture alias page 4'}]);
  const details=createReactorLineDetails(op,record());
  for(const value of ['fixture alias vessel','Fixture alias basis','Fixture alias page 4','not reported'])assert.ok(details.textContent.includes(value),value);
  assert.doesNotMatch(details.textContent,/metadata is invalid|Reactor attributes:|"source_id"/);
  assert.equal(JSON.stringify(op),before);
 }
}));

test('direct attribute citations reject both or neither locator aliases, orphan aliases and extra or conflicting fields',()=>{
 const citation={value:'fixture alias vessel',status:'reported',basis:'Fixture alias basis',source_id:'fixture-main',locator:'Fixture alias page 4'};
 const {locator,...withoutLocator}=citation,{source_id,...withoutSource}=citation;
 const invalid=[
  {...citation,source_locator:locator},
  {...citation,source_locator:'Conflicting fixture locator'},
  withoutLocator,withoutSource,
  {...citation,extra:'unexpected'},
  {...citation,locator:''},
  {...citation,source_id:null},
  {...citation,evidence:[{source_id:'fixture-main',locator:'Different fixture locator'}]}
 ];
 for(const field of invalid)assert.equal(readReactorLineNote(attributeOperation(attributes({vessel_type:field})).environment.note).valid,false);
});

test('either attribute locator alias still requires a known source at display time and leaves the source operation intact',()=>dom(()=>{
 for(const locatorKey of ['locator','source_locator']){
  const field={value:'UNBOUND_ALIAS_FIXTURE_VESSEL',status:'reported',basis:'Fixture alias basis',source_id:'missing-source',[locatorKey]:'Fixture alias page 4'};
  const op=attributeOperation(attributes({vessel_type:field})),before=JSON.stringify(op);
  assert.equal(readReactorLineNote(op.environment.note).valid,true);
  const details=createReactorLineDetails(op,record());
  assert.match(details.textContent,/metadata is invalid/);assert.doesNotMatch(details.textContent,/UNBOUND_ALIAS_FIXTURE_VESSEL/);
  assert.equal(JSON.stringify(op),before);
 }
}));


// Invented rich scoped metadata fixtures; no production records or source I/O.
const scopedAbsent=()=>({value:'not reported',status:'not_reported',source_id:'fixture-main',locator:'Fixture scoped page 5',absence_scope:'Not stated in the fixture passage.'});
const scopedMetadata=(overrides={})=>({reactor_line:{reactor_line_id:scopedAbsent(),...Object.fromEntries(keys.map(k=>[k,scopedAbsent()])),...overrides}});
const scopedOperation=metadata=>({...operation(),environment:{value:null,evidence:[],note:'Fixture scoped prose.\nReactor-line metadata (structured JSON): '+JSON.stringify(metadata)}});
const scopedLocal=()=>({value:'fixture-local-tube',status:'local_metadata',source_id:'fixture-main',locator:'Fixture scoped page 5',assignment:'Author-assigned fixture bookkeeping, not a source laboratory identifier.',continuity_status:'source_supported',continuity_basis:'Fixture passage names the same tube for these two stages.'});
const scopedVerbatim=()=>({value:'other (verbatim)',status:'reported',source_id:'fixture-main',locator:'Fixture scoped page 6',qualifier:'Qualitative condition only; no apparatus or pressure inferred.',verbatim:'fixture reduced pressure'});

test('rich scoped metadata renders local identity and verbatim qualifiers without changing source values',()=>dom(()=>{
 const op=scopedOperation(scopedMetadata({reactor_line_id:scopedLocal(),atmosphere:scopedVerbatim(),stirring:{...reported(true),qualifier:'Fixture mixing statement.'}}));
 const before=JSON.stringify(op),parsed=readReactorLineNote(op.environment.note);
 assert.equal(parsed.valid,true);assert.equal(parsed.scopedRich,true);
 assert.equal(parsed.line.reactor_line_id.status,'local_metadata');assert.equal(parsed.line.atmosphere.value,'other (verbatim)');
 const details=createReactorLineDetails(op,record());
 for(const value of ['Local reactor line (local metadata)','fixture-local-tube','Author-assigned fixture bookkeeping','Fixture passage names the same tube','source_supported','other (verbatim)','fixture reduced pressure','Qualitative condition only','Fixture mixing statement.','Fixture scoped page 5','Fixture scoped page 6'])assert.ok(details.textContent.includes(value),value);
 assert.doesNotMatch(details.textContent,/metadata is invalid|author-derived|"reactor_line"/);
 assert.equal(flatten(details).filter(n=>n.tagName==='DT').length,16);
 assert.equal(JSON.stringify(op),before);
}));

test('original scoped missingness and reported fields retain their original dialect and validation',()=>dom(()=>{
 const good=scopedOperation(scopedMetadata({vessel_type:reported('fixture flask')})),before=JSON.stringify(good);
 const parsed=readReactorLineNote(good.environment.note);assert.equal(parsed.valid,true);assert.equal(parsed.scoped,true);assert.equal(parsed.scopedRich,undefined);
 assert.doesNotMatch(createReactorLineDetails(good,record()).textContent,/metadata is invalid/);assert.equal(JSON.stringify(good),before);
 const bad=scopedOperation(scopedMetadata({vessel_type:{...scopedAbsent(),extra:'unexpected'}}));assert.equal(readReactorLineNote(bad.environment.note).valid,false);
}));

test('rich scoped dialect rejects missing, extra, inconsistent and ambiguous metadata',()=>{
 const invalid=[
  {reactor_line_id:{...scopedLocal(),extra:'unexpected'}},
  {reactor_line_id:{...scopedLocal(),continuity_status:'inferred'}},
  {reactor_line_id:{...scopedLocal(),assignment:''}},
  {reactor_line_id:{...scopedLocal(),status:'reported'}},
  {atmosphere:{...scopedVerbatim(),source_locator:'Duplicate citation spelling'}},
  {atmosphere:{...scopedVerbatim(),verbatim:''}},
  {atmosphere:{...scopedVerbatim(),qualifier:''}},
  {atmosphere:{...scopedVerbatim(),value:'a different value'}},
  {atmosphere:{...scopedVerbatim(),status:'author_derived'}},
  {atmosphere:{...scopedVerbatim(),locator:null}},
  {vessel_type:{...scopedAbsent(),value:'a reported-looking vessel'}},
  {vessel_type:{...scopedAbsent(),extra:'unexpected'}}
 ];
 const {verbatim,...missingVerbatim}=scopedVerbatim();invalid.push({atmosphere:missingVerbatim});
 const {continuity_basis,...missingBasis}=scopedLocal();invalid.push({reactor_line_id:missingBasis});
 for(const change of invalid)assert.equal(readReactorLineNote(scopedOperation(scopedMetadata(change)).environment.note).valid,false);
 const missing=scopedMetadata({atmosphere:scopedVerbatim()});delete missing.reactor_line.cooling_method;assert.equal(readReactorLineNote(scopedOperation(missing).environment.note).valid,false);
 for(const prefix of ['reactor_line='+JSON.stringify(line())+'\n','Reactor attributes: '+JSON.stringify(attributes())+'\n'])assert.equal(readReactorLineNote(prefix+scopedOperation(scopedMetadata({atmosphere:scopedVerbatim()})).environment.note).valid,false);
});

test('rich scoped details bind every citation and preserve original objects including unresolved sources',()=>dom(()=>{
 for(const key of ['reactor_line_id','atmosphere','cooling_method']){
  const metadata=scopedMetadata({reactor_line_id:scopedLocal(),atmosphere:scopedVerbatim()});metadata.reactor_line[key].source_id='unknown-fixture-source';
  const op=scopedOperation(metadata),before=JSON.stringify(op);assert.equal(readReactorLineNote(op.environment.note).valid,true);
  const details=createReactorLineDetails(op,record());assert.match(details.textContent,/metadata is invalid/);assert.doesNotMatch(details.textContent,/fixture-local-tube|fixture reduced pressure/);assert.equal(JSON.stringify(op),before);
 }
}));
