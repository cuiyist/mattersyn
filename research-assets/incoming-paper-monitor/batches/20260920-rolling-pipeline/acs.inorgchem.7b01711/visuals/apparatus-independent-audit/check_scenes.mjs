import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import crypto from 'node:crypto';
const A=path.dirname(fileURLToPath(import.meta.url)),P=path.join(A,'../apparatus'),N=path.join(A,'../..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const mod=await import(pathToFileURL(path.join(P,'morrison2017-protocol.mjs')));
const manifest=read(path.join(N,'canonical-proposal/v2/record-manifest.json'));
const records=manifest.records.map(x=>read(x.path));
const bindings=read(path.join(P,'canonical-bindings.json')).bindings,stored=read(path.join(P,'rendered-scenes.json'));
const checks=[],scopes=[];
function ck(ok,s){checks.push({check:s,passed:!!ok});}
function deepFreeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(deepFreeze);Object.freeze(x);}return x;}
function at(x,p){for(const k of p.split('/').slice(1))x=x[k.replaceAll('~1','/').replaceAll('~0','~')];return x;}
function equal(x,y){return JSON.stringify(x)===JSON.stringify(y);}
function independentFormat(q){
 let number;
 if(q.value!=null)number=String(q.value);
 else if(q.minimum!=null&&q.maximum!=null)number=`${q.minimum}–${q.maximum}`;
 else if(q.maximum!=null)number=(q.maximum_exclusive?'<':'≤')+q.maximum;
 else if(q.minimum!=null)number=(q.minimum_exclusive?'>':'≥')+q.minimum;
 else return q.raw_text||'Not reported';
 if(/^\d+(\.\d+)?\(\d+\)$/.test(q.raw_text||''))number=q.raw_text;
 const units={degC:'°C',angstrom:'Å',degree:'°',deg:'°',count:'',multiple:'×',fold:'×'};
 const unit=Object.hasOwn(units,q.unit)?units[q.unit]:(q.unit||'');
 return (q.approximate?'≈ ':'')+number+(unit?' '+unit:'');
}
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.style={};this.dataset={};this.textContent='';this.svg={style:{}};}
 append(...n){this.children.push(...n);}
 querySelector(s){return s==='svg'?this.svg:null;}
}
globalThis.document={createElement:t=>new Element(t)};
const before=JSON.stringify(records);records.forEach(deepFreeze);
let opCount=0,paramCount=0,obsCount=0,rowCount=0;
for(const r of records){
 const ops=r.operations||[];
 if(ops.length)ck(equal(mod.morrison2017SceneSelection.records[r.record_id],ops.map(o=>o.id)),'exact selection order '+r.record_id);
 for(const [i,o] of ops.entries()){
  opCount++;const s=mod.buildMorrison2017Scene(o,r);ck(s!==null,'scene present '+o.id);if(!s)continue;
  const b=bindings.find(v=>v.record_id===r.record_id&&v.operation_id===o.id),z=stored.find(v=>v.record_id===r.record_id&&v.operation_id===o.id);
  ck(!!b&&!!z,'unique stored mapping '+o.id);ck(b.operation_pointer===`/operations/${i}`,'exact operation pointer '+o.id);
  for(const k of ['inputs','outputs','retained_fraction'])ck(equal(b[k],o[k]),'material flow '+o.id+' '+k);
  ck(equal(b.source_evidence,o.evidence),'operation source locators '+o.id);ck(b.canonical_description===o.description,'exact canonical prose '+o.id);
  ck(equal(s.rows,z.rows),'actual render rows match saved '+o.id);ck(s.description===b.human_prose,'authored prose mapped '+o.id);
  ck(s.svg.trim()===fs.readFileSync(path.join(P,'svg',o.id+'.svg'),'utf8').trim(),'actual SVG matches visually inspected file '+o.id);
  const ps=s.rows.filter(x=>x.kind==='operation_parameter');ck(ps.length===Object.keys(o.parameters).length,'all parameters '+o.id);
  for(const [k,q] of Object.entries(o.parameters)){
   paramCount++;const row=ps.find(x=>x.pointer===`/operations/${i}/parameters/${k}`);ck(!!row,'quantity row exists '+o.id+k);
   if(row){ck(equal(row.quantity,q),'exact parameter object '+o.id+k);ck(row.value===independentFormat(q),'independent quantity format '+o.id+k);}
  }
  for(const row of s.rows.filter(x=>x.kind==='reported_observation_or_acquisition')){
   obsCount++;ck(equal(row.quantity,at(r,row.pointer)),'exact observation pointer '+o.id+row.pointer);ck(row.value===independentFormat(row.quantity),'observation display '+o.id+row.pointer);
  }
  const grid=mod.createMorrison2017ConditionGrid(o,r),art=mod.createMorrison2017Art(o,r);rowCount+=s.rows.length;
  ck(grid.children.length===s.rows.length,'condition factory row count '+o.id);
  s.rows.forEach((row,j)=>{ck(grid.children[j].children[0].textContent===row.label,'visible row label');ck(grid.children[j].children[1].textContent===row.value,'visible row value');});
  ck(art.dataset.scene===s.kind&&art.innerHTML===s.artSvg,'actual art factory '+o.id);
  const markup=mod.renderMorrison2017Markup(s);ck(markup.includes(s.artSvg),'responsive markup art '+o.id);
  ck(!/NaN|undefined/.test(s.svg+s.artSvg+markup),'valid render values '+o.id);
  ck(!/<image|<script|<foreignObject/i.test(s.svg),'no external/synthetic source image '+o.id);
  ck(mod.buildMorrison2017Scene(o,{...r,record_id:'wrong'})===null,'wrong record rejected '+o.id);
  ck(mod.buildMorrison2017Scene(o,{...r,lineage:{source_group:'other'}})===null,'wrong source rejected '+o.id);
  ck(mod.buildMorrison2017Scene({...o,id:'wrong'},r)===null,'wrong operation rejected '+o.id);
  scopes.push({record_id:r.record_id,operation_id:o.id,depends_on:o.depends_on,branch:o.branch,inputs:o.inputs,outputs:o.outputs,retained_fraction:o.retained_fraction,rows:s.rows.map(x=>({label:x.label,value:x.value,kind:x.kind,pointer:x.pointer}))});
 }
}
ck(JSON.stringify(records)===before,'input canonical arrays unchanged');ck(opCount===24&&paramCount===62&&obsCount===8&&rowCount===155,'exact aggregate counts');
const get=id=>scopes.find(x=>x.operation_id===id),txt=id=>JSON.stringify(get(id));
ck(txt('hot-growth').includes('≤15 min')&&txt('hot-growth').includes('70 °C'),'hot bound and temperature');
ck(txt('rt-combine').includes('≈ 40 mM')&&!txt('rt-combine').includes('70 °C\"'),'RT concentration separate');
ck(txt('crystal-mount-measure').includes('100(2) K')&&txt('crystal-mount-measure').includes('≈ 0.6 mm'),'crystal temperature and mounting uncertainty');
ck(txt('nmr-heat').includes('2 h')&&txt('nmr-heat').includes('1 h')&&txt('nmr-heat').includes('not a lower bound'),'NMR source disagreement retained');
ck(txt('qb-wash').includes('dispersion, not dry CdSe'),'dispersion basis');
ck(equal(get('qb-tem').depends_on,['qb-shell'])&&!get('qb-tem').inputs.includes('optical-dispersion'),'TEM branches from growth family');
ck(txt('aliquot-toluene-wash').includes('Not reported for this stage'),'final repeat count not inherited');
const result={status:checks.every(x=>x.passed)?'passed':'findings',checks:checks.length,failures:checks.filter(x=>!x.passed),counts:{operations:opCount,parameters:paramCount,typed_observations:obsCount,display_rows:rowCount},module_sha256:hash(path.join(P,'morrison2017-protocol.mjs')),scope:'Actual module scene/condition/art/markup functions executed against deeply frozen full canonical v2 records using a minimal DOM. This is not a browser test.',scopes};
fs.writeFileSync(path.join(A,'actual-function-checks.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({...result,scopes:undefined}));
