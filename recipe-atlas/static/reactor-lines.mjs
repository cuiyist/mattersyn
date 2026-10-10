import {quantityValue} from './quantity-value.mjs';

const CATEGORIES=['vessel_type','atmosphere','schlenk_line','glovebox','heating_method','stirring','addition_method','cooling_method'];
const NUMBERS=['vessel_volume','fill_fraction','reaction_volume','heating_rate','stirring_rate','addition_rate','pressure'];
const FIELDS=['vessel_type','vessel_volume','fill_fraction','reaction_volume','atmosphere','schlenk_line','glovebox','heating_method','heating_rate','stirring','stirring_rate','addition_method','addition_rate','pressure','cooling_method'];
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const text=x=>typeof x==='string'&&x.trim().length>0;
const exact=(x,keys)=>object(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const label=key=>key.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase());
const node=(tag,value,cls)=>{const n=document.createElement(tag);if(value!==undefined)n.textContent=value;if(cls)n.className=cls;return n;};

// A separate display adapter accepts only the explicit appended attributes
// format. It retains original values, basis and every supplied citation; it
// never rewrites the record or relaxes the canonical reactor_line validator.
function readReactorAttributes(note,marker){
 const canonical=/(^|\n)(?:reactor_line[ \t]*=[ \t]*|(?=[ \t]*\{\s*"reactor_line"\s*:))/.exec(note);
 const prose=note.slice(0,canonical?Math.min(marker.index,canonical.index):marker.index);
 try{
  if(canonical)throw Error();
  const raw=JSON.parse(note.slice(marker.index+marker[0].length));
  const schlenk=Object.hasOwn(raw||{},'Schlenk_line')?'Schlenk_line':'schlenk_line';
  if(!exact(raw,['reactor_line_id',...CATEGORIES.map(k=>k==='schlenk_line'?schlenk:k)]))throw Error();
  const line={};
  for(const key of ['reactor_line_id',...CATEGORIES]){
   const f=raw[key==='schlenk_line'?schlenk:key];
   const direct=Object.hasOwn(f||{},'source_id')||Object.hasOwn(f||{},'source_locator');
   const array=Object.hasOwn(f||{},'evidence');
   if(!exact(f,['value','status','basis',...(direct?['source_id','source_locator']:[]),...(array?['evidence']:[])])||(!direct&&!array)||!text(f.basis))throw Error();
   const supplied=direct&&text(f.source_id)&&text(f.source_locator);
   if(direct&&!supplied&&!(f.source_id===null&&f.source_locator===null))throw Error();
   if(array&&(!Array.isArray(f.evidence)||!f.evidence.every(e=>exact(e,['source_id','locator'])&&text(e.source_id)&&text(e.locator))))throw Error();
   if(direct&&array&&(!supplied||!f.evidence.some(e=>e.source_id===f.source_id&&e.locator===f.source_locator)))throw Error();
   const evidence=array?f.evidence:supplied?[{source_id:f.source_id,locator:f.source_locator}]:[];
   if(f.status==='not_reported'){
    if(!(f.value===null||f.value==='not reported'))throw Error();
   }else if(key==='reactor_line_id'){
    if(f.status!=='author_derived'||!text(f.value)||f.value==='not reported'||!evidence.length)throw Error();
   }else{
    const validValue=['schlenk_line','glovebox','stirring'].includes(key)?typeof f.value==='boolean'||text(f.value):text(f.value);
    if(f.status!=='reported'||!validValue||f.value==='not reported'||!evidence.length)throw Error();
   }
   line[key]={...f,evidence};
  }
  return {prose,line,valid:true,attributes:true};
 }catch{return {prose,line:null,valid:false,attributes:true};}
}

// A separately tagged scoped-missingness dialect preserves reviewed absence
// provenance without converting it to a reported value or inventing a line ID.
// Its shape is intentionally independent of canonical and attributes metadata.
function readScopedReactorLine(note,marker){
 const competing=/(^|\n)(?:Reactor attributes:[ \t]*|reactor_line[ \t]*=[ \t]*|(?=[ \t]*\{\s*"reactor_line"\s*:))/.exec(note);
 const prose=note.slice(0,competing?Math.min(marker.index,competing.index):marker.index);
 try{
  if(competing)throw Error();
  const raw=JSON.parse(note.slice(marker.index+marker[0].length));
  if(!exact(raw,['reactor_line'])||!exact(raw.reactor_line,['reactor_line_id',...CATEGORIES]))throw Error();
  const line=raw.reactor_line;
  for(const key of ['reactor_line_id',...CATEGORIES]){
   const f=line[key];
   if(f?.status==='not_reported'){
    if(!exact(f,['value','status','source_id','locator','absence_scope'])||f.value!=='not reported'||!text(f.absence_scope)||!text(f.source_id)||!text(f.locator))throw Error();
   }else{
    if(key==='reactor_line_id'||!exact(f,['value','status','source_id','locator']))throw Error();
    const validValue=['schlenk_line','glovebox','stirring'].includes(key)?typeof f.value==='boolean'||text(f.value):text(f.value);
    if(f.status!=='reported'||!validValue||f.value==='not reported'||!text(f.source_id)||!text(f.locator))throw Error();
   }
  }
  return {prose,line,valid:true,scoped:true};
 }catch{return {prose,line:null,valid:false,scoped:true};}
}

// Only explicit appended metadata marks a new audited note. Ordinary old notes
// and arbitrary JSON keep their original rendering; stored data is never edited.
export function readReactorLineNote(note){
 if(typeof note!=='string')return null;
 const scoped=/(^|\n)Reactor-line metadata \(structured JSON\):[ \t]*/.exec(note);
 if(scoped)return readScopedReactorLine(note,scoped);
 const attributes=/(^|\n)Reactor attributes:[ \t]*/.exec(note);
 if(attributes)return readReactorAttributes(note,attributes);
 const marker=/(^|\n)(?:reactor_line[ \t]*=[ \t]*|(?=[ \t]*\{\s*"reactor_line"\s*:))/.exec(note);
 if(!marker)return null;
 const prose=note.slice(0,marker.index),raw=note.slice(marker.index+marker[0].length);
 try{
  let line=JSON.parse(raw);
  if(Object.hasOwn(line||{},'reactor_line')){if(!exact(line,['reactor_line']))throw Error();line=line.reactor_line;}
  if(!exact(line,['reactor_line_id',...CATEGORIES])||!(line.reactor_line_id===null||text(line.reactor_line_id)))throw Error();
  for(const key of CATEGORIES){
   const f=line[key];if(!exact(f,['value','status','source_id','locator']))throw Error();
   if(f.status==='not_reported'){
    if(f.value!=='not reported'||f.source_id!==null||f.locator!==null)throw Error();
   }else if(f.status==='reported'){
    const validValue=['schlenk_line','glovebox','stirring'].includes(key)?typeof f.value==='boolean'||text(f.value):text(f.value);
    if(!validValue||f.value==='not reported'||!text(f.source_id)||!text(f.locator))throw Error();
   }else throw Error();
  }
  return {prose,line,valid:true};
 }catch{return {prose,line:null,valid:false};}
}

export function reactorEnvironmentText(environment){
 const note=readReactorLineNote(environment?.note);
 if(!note)return environment?.value||environment?.note||'Not reported';
 return environment?.value!==null&&environment?.value!==undefined&&environment?.value!==''?String(environment.value):note.prose||'Not reported';
}

function source(record,id){return (record?.sources||[]).find(s=>s.id===id);}
function evidenceRow(parent,evidence,record,prefix=''){
 if(!Array.isArray(evidence))return;
 for(const e of evidence||[]){
  if(!text(e?.source_id)||!text(e?.locator))continue;
  const display=prefix+e.source_id+' · '+e.locator,s=source(record,e.source_id),n=node('small');
  // Use only an existing citation URL, never construct a guessed page URL.
  if(typeof s?.url==='string'&&/^https?:\/\//i.test(s.url)){
   const a=node('a',display);a.href=s.url;n.append(a);
  }else n.textContent=display;
  parent.append(n);
 }
}
function sourceBound(line,record,attributes=false,scoped=false){
 if(scoped)return ['reactor_line_id',...CATEGORIES].every(key=>source(record,line[key].source_id));
 if(attributes)return ['reactor_line_id',...CATEGORIES].every(key=>line[key].evidence.every(e=>source(record,e.source_id)));
 return CATEGORIES.every(key=>line[key].status==='not_reported'||source(record,line[key].source_id));
}
function numberText(q){
 const v=quantityValue(q);if(v===null)return 'not reported';
 return `${q.approximate?'≈':''}${v}${q.unit?' '+q.unit:''}${q.qualifier?' · '+q.qualifier:''}${q.basis?' · '+q.basis:''}`;
}
function numericField(q,record,format){
 if(!q)return {value:'not reported',evidence:[]};
 if(q.status==='not_reported'){
  const noValue=[q.value,q.minimum,q.maximum].every(v=>v===null||v===undefined);
  return {value:noValue?'not reported':'Reactor quantity unavailable: inconsistent missing value',evidence:noValue?q.evidence:[],unavailable:!noValue};
 }
 const values=[q.value,q.minimum,q.maximum].filter(v=>v!==null&&v!==undefined);
 const evidence=q.evidence;
 if(q.status!=='reported'||!values.length||values.some(v=>typeof v!=='number'||!Number.isFinite(v))
   ||!text(q.unit)||!Array.isArray(evidence)||!evidence.length
   ||!evidence.every(e=>text(e?.source_id)&&text(e?.locator)&&source(record,e.source_id)))
  return {value:'Reactor quantity unavailable: source binding or value invalid',evidence:[],unavailable:true};
 return {value:format(q),evidence};
}

// A display-only view closes every numeric consumer, including older generic
// rows and source-specific providers. No source record is mutated or exported.
const unavailableQuantities=new WeakMap();
export function reactorQuantityUnavailable(quantity){return object(quantity)?unavailableQuantities.get(quantity):undefined;}
function displayOperation(operation,record){
 if(!readReactorLineNote(operation?.environment?.note))return operation;
 let parameters;
 for(const key of NUMBERS){
  const q=operation.parameters?.[key],field=numericField(q,record,numberText);
  if(!field.unavailable)continue;
  const view={value:null,minimum:null,maximum:null,unit:'',status:q?.status,
   approximate:false,qualifier:field.value,basis:'',raw_text:'',evidence:[],derivation:null};
  unavailableQuantities.set(view,field.value);
  parameters??={...operation.parameters};parameters[key]=view;
 }
 return parameters?{...operation,parameters}:operation;
}
export function reactorDisplayRecord(record){
 const operations=record.operations.map(operation=>displayOperation(operation,record));
 return operations.some((operation,i)=>operation!==record.operations[i])?{...record,operations}:record;
}

export function createReactorLineDetails(operation,record,format=numberText){
 const parsed=readReactorLineNote(operation?.environment?.note);if(!parsed)return null;
 const section=node('section',undefined,'protocol-reactor-details');section.append(node('h4','Reactor details'));
 const env=operation.environment;
 if(env.value!==null&&env.value!==undefined&&env.value!=='')section.append(node('p','Environment: '+String(env.value)));
 if(parsed.prose)section.append(node('p',parsed.prose,'record-note'));
 evidenceRow(section,env.evidence,record);
 if(!parsed.valid||!sourceBound(parsed.line,record,parsed.attributes,parsed.scoped)){
  section.append(node('p','Reactor details unavailable: structured source metadata is invalid.','record-note'));return section;
 }
 const grid=node('dl',undefined,'protocol-condition-grid');
 if(parsed.scoped){
  const f=parsed.line.reactor_line_id,row=node('div'),value=node('dd','not reported');
  value.append(node('small','Absence scope: '+f.absence_scope));evidenceRow(value,[f],record,'Scope citation: ');
  row.append(node('dt','Local reactor line'),value);grid.append(row);
 }else if(parsed.attributes){
  const f=parsed.line.reactor_line_id,row=node('div'),value=node('dd',f.status==='not_reported'?'not reported':f.value);
  value.append(node('small','Basis: '+f.basis));evidenceRow(value,f.evidence,record);
  row.append(node('dt',f.status==='author_derived'?'Local reactor line (author-derived)':'Local reactor line'),value);grid.append(row);
 }else if(parsed.line.reactor_line_id!==null){const row=node('div');row.append(node('dt','Local reactor line'),node('dd',parsed.line.reactor_line_id));grid.append(row);}
 for(const key of FIELDS){
  const row=node('div');let display,evidence;
  if(NUMBERS.includes(key))({value:display,evidence}=numericField(operation.parameters?.[key],record,format));
  else{const f=parsed.line[key];display=f.status==='not_reported'?'not reported':typeof f.value==='boolean'?(f.value?'yes':'no'):f.value;evidence=parsed.attributes?f.evidence:parsed.scoped||f.status==='reported'?[f]:[];}
  const value=node('dd',display);
  if(parsed.attributes&&!NUMBERS.includes(key))value.append(node('small','Basis: '+parsed.line[key].basis));
  const scopedAbsence=parsed.scoped&&!NUMBERS.includes(key)&&parsed.line[key].status==='not_reported';
  if(scopedAbsence)value.append(node('small','Absence scope: '+parsed.line[key].absence_scope));
  evidenceRow(value,evidence,record,scopedAbsence?'Scope citation: ':'');row.append(node('dt',label(key)),value);grid.append(row);
 }
 section.append(grid);return section;
}

export function reactorLineCaption(operation,record,caption){
 const parsed=readReactorLineNote(operation?.environment?.note);if(!parsed)return caption;
 if(!parsed.valid||!sourceBound(parsed.line,record,parsed.attributes,parsed.scoped))return caption+' Conceptual vessel: vessel type could not be verified from the reactor metadata.';
 return parsed.line.vessel_type.status==='not_reported'?caption+' Conceptual vessel: vessel type is not reported; no apparatus identity is inferred.':caption;
}
