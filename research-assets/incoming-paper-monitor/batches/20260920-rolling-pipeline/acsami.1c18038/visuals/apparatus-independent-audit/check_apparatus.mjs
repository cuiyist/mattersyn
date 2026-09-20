import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath,pathToFileURL} from 'node:url';
const a=path.dirname(fileURLToPath(import.meta.url)),m=path.resolve(a,'../apparatus'),l=path.resolve(a,'../..');
const bound={},checks=[];
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const read=p=>{p=path.resolve(p);bound[p.replaceAll('\\','/')]=sha(p);return JSON.parse(fs.readFileSync(p,'utf8'));};
const eq=(label,x,y)=>{assert.deepEqual(x,y,label);checks.push(label);};
const pointer=(x,p)=>p.slice(1).split('/').reduce((o,k)=>o[k.replaceAll('~1','/').replaceAll('~0','~')],x);
const freeze=read(path.join(m,'package-freeze.json'));
eq('Expected author freeze',sha(path.join(m,'package-freeze.json')),'fe99285425cfe7de6526f75f47808f0b5d980739d41dfce85f20c0facdcc3957');
for(const [p,h] of Object.entries({...freeze.bound_files,...freeze.bound_inputs})){eq('Frozen bytes '+p,sha(p),h);bound[p.replaceAll('\\','/')]=h;}
const manifest=read(path.join(l,'canonical-proposal/v1/record-manifest.json'));
const records=manifest.records.map(x=>{eq('Canonical '+x.record_id,sha(x.path),x.sha256);return read(x.path);});
const compact=read(path.join(m,'records.json'));eq('Compact unchanged records',compact,records.filter(r=>r.operations.length));
const bindings=read(path.join(m,'canonical-bindings.json')).bindings,rendered=read(path.join(m,'rendered-scenes.json'));
const previews=read(path.join(m,'preview-manifest.json')).scenes;
const {buildLian2021Scene,createLian2021Art,createLian2021ConditionGrid,renderLian2021Markup,lian2021SceneSelection}=await import(pathToFileURL(path.join(m,'lian2021-protocol.mjs')));
function frozen(x){if(x&&typeof x==='object'){Object.freeze(x);Object.values(x).forEach(frozen);}return x;}
records.forEach(frozen);const before=JSON.stringify(records);
class Node{constructor(tag){this.tag=tag;this.style={};this.dataset={};this.children=[];}append(...x){this.children.push(...x);}querySelector(){return {style:{}};}}
globalThis.document={createElement:t=>new Node(t)};
const expected={
 'a-dissolve-filter':['2 mmol','1 mmol','800 µL'],'a-evaporate':['4 days'],
 'b-dissolve-filter':['1 mmol','1 mmol','800 µL'],'b-evaporate':['4 days'],
 'nc-dissolve-filter':['1 mmol','0.5 mmol','2000 µL'],'nc-inject':['500 µL','5 mL','500 µL'],
 'nc-centrifuge':['7000 rpm','3 min'],'film-blend':['20 min','1/0','1/3','1/2','2/3','0/1'],'film-cast':[],
 'spin-feed':['2 mmol','1 mmol','1000 µL'],'spin-deposit':['200 µL','2000 rpm','40 s','80 °C','30 min'],
 'bulk-xray':[],'bulk-xps-tga':[],'bulk-optics':[],'bulk-plqe':['365 nm'],'nc-tem':['300 kV'],'nc-optics':[],
 'nc-plqe':['365 nm','365 nm'],'film-pl':[],'beta-irradiate':['0.4 MeV','16 kW','400 Gy/s'],
 'dft-relax':['400 eV','<0.01 eV/Å','4x4x4','2x4x4']
};
const allPairs=records.flatMap(r=>r.operations.map(o=>[r.record_id,o.id]));
eq('21 operations',allPairs.length,21);eq('All binding pairs',bindings.map(b=>[b.record_id,b.operation_id]),allPairs);
eq('Only operation records dispatched',lian2021SceneSelection.records,Object.fromEntries(records.filter(r=>r.operations.length).map(r=>[r.record_id,r.operations.map(o=>o.id)])));
let parameterCount=0,contextCount=0,rowCount=0;const scenes=[];
for(const r of records){
 for(const [i,o] of r.operations.entries()){
   const s=buildLian2021Scene(o,r),b=bindings.find(x=>x.record_id===r.record_id&&x.operation_id===o.id);
   eq('Exact operation pointer '+o.id,b.operation_pointer,'/operations/'+i);
   for(const k of ['inputs','outputs','retained_fraction'])eq('Bound '+k+' '+o.id,b[k],o[k]);
   eq('Bound description '+o.id,b.canonical_description,o.description);eq('Bound evidence '+o.id,b.source_evidence,o.evidence);
   eq('No approval '+o.id,b.binding_approved,false);eq('Reader prose '+o.id,b.human_prose,s.description);
   eq('Saved scene equals actual execution '+o.id,rendered.find(x=>x.operation_id===o.id),{record_id:r.record_id,operation_id:o.id,...s});
   eq('Actual typed display '+o.id,s.rows.filter(x=>x.quantity).map(x=>x.value),expected[o.id]);
   const pars=s.rows.filter(x=>x.kind==='operation_parameter');eq('Exact parameter keys '+o.id,pars.map(x=>x.pointer),Object.keys(o.parameters).map(k=>'/operations/'+i+'/parameters/'+k));
   for(const row of s.rows.filter(x=>x.quantity)){eq('Exact quantity '+o.id+row.pointer,row.quantity,pointer(r,row.pointer));}
   for(const c of b.measurement_rows){const row=s.rows.find(x=>x.pointer===c.pointer);eq('Explicit same-record context '+o.id+c.pointer,r.measurements.find(x=>x.id===c.measurement_id).value,row.quantity);eq('Context classification '+o.id+c.pointer,row.kind,'source_context');}
   parameterCount+=pars.length;contextCount+=b.measurement_rows.length;rowCount+=s.rows.length;
   const art=createLian2021Art(o,r),grid=createLian2021ConditionGrid(o,r),markup=renderLian2021Markup(s);
   eq('Art exact '+o.id,art.innerHTML,s.artSvg);eq('Art selection '+o.id,art.dataset.scene,s.kind);
   eq('Condition rows exact '+o.id,grid.children.map(x=>x.children.map(t=>t.textContent)),s.rows.map(x=>[x.label,x.value]));
   eq('Markup contains description '+o.id,markup.includes(s.description.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')),true);
   const preview=previews.find(x=>x.operation_id===o.id);eq('SVG preview actual '+o.id,fs.readFileSync(path.join(m,preview.svg_path),'utf8').trim(),s.svg.trim());
   eq('Preview SVG hash '+o.id,sha(path.join(m,preview.svg_path)),preview.svg_sha256);eq('Preview PNG hash '+o.id,sha(path.join(m,preview.png_path)),preview.png_sha256);
   eq('No foreign source '+o.id,buildLian2021Scene(o,{...r,lineage:{...r.lineage,source_group:'other'}}),null);
   eq('No other record '+o.id,buildLian2021Scene(o,{...r,record_id:'unrelated'}),null);
   eq('No unknown operation '+o.id,buildLian2021Scene({...o,id:'missing'},r),null);
   scenes.push({record_id:r.record_id,operation_id:o.id,rows:s.rows,description:s.description});
 }
}
eq('All inputs unchanged',JSON.stringify(records),before);eq('34 parameter rows',parameterCount,34);eq('7 explicit contexts',contextCount,7);eq('122 display rows',rowCount,122);
const scene=id=>scenes.find(x=>x.operation_id===id),text=id=>JSON.stringify(scene(id));
eq('NC no temperature inference',text('nc-inject').includes('no nanocrystal growth temperature'),true);
eq('Spin supported film',text('spin-deposit').includes('no peeling'),true);
eq('Cast peeled-film retention',text('film-cast').includes('Peeled composite film; glass is the separated support'),true);
eq('Nitrogen only TGA',text('bulk-xps-tga').includes('Nitrogen is assigned only to TGA'),true);
eq('Dried powder PLQE',text('nc-plqe').includes('does not establish the same result for a dispersed colloid'),true);
eq('No beta blend join',text('beta-irradiate').includes('exact blend ratio is not identified'),true);
eq('Meshes stay source context',scene('dft-relax').rows.filter(x=>x.kind==='source_context').map(x=>[x.label,x.value]),[['Compound A k-point mesh','4x4x4'],['Compound B k-point mesh','2x4x4']]);
eq('Only module public',freeze.public_allowlist.map(x=>x.path),['lian2021-protocol.mjs']);
eq('Module no private paths',/C:[/\\]|complete-source-payloads|firstPagePreviewPrivate/.test(fs.readFileSync(path.join(m,'lian2021-protocol.mjs'),'utf8')),false);
for(const p of ['main-06.png','main-07.png'])bound[path.join(l,'source-render',p).replaceAll('\\','/')]=sha(path.join(l,'source-render',p));
bound[path.join(l,'reader-assets/scheme-1.png').replaceAll('\\','/')]=sha(path.join(l,'reader-assets/scheme-1.png'));
const result={status:'passed',auditor:'/root/peng1998_reader_assets',generated_at:new Date().toISOString(),checks:checks.length,check_labels:checks,operations:21,parameter_rows:parameterCount,context_rows:contextCount,display_rows:rowCount,scope:'Actual source-specific module and art/condition factories executed on deep-frozen audited canonical records using a minimal DOM. Original source6/7 and Scheme1 separately read; no mounted-browser claim.',scenes,bound_files:bound};
fs.writeFileSync(path.join(a,'mechanical-checks.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:'passed',checks:checks.length}));
