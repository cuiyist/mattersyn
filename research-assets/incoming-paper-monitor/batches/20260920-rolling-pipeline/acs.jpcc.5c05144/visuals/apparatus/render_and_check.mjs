import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildSasongko2025Scene,createSasongko2025Art,createSasongko2025ConditionGrid,renderSasongko2025Markup,sasongko2025SceneSelection} from './sasongko2025-protocol.mjs';
const A=path.dirname(fileURLToPath(import.meta.url));
const read=n=>JSON.parse(fs.readFileSync(path.join(A,n),'utf8'));
const records=read('records.json'),typed=read('typed-field-map.json'),bindings=read('canonical-bindings.json').bindings;
const resolve=(x,p)=>p.split('/').slice(1).reduce((a,k)=>a[k.replaceAll('~1','/').replaceAll('~0','~')],x);
const checks=[];function ck(label,yes){checks.push({check:label,passed:!!yes});if(!yes)throw Error(label);}
const before=JSON.stringify(records);fs.mkdirSync(path.join(A,'svg'),{recursive:true});const scenes=[];
class Element{constructor(t){this.tagName=t;this.className='';this.dataset={};this.style={};this.children=[];this.innerHTML='';this.textContent='';}append(...children){this.children.push(...children);}querySelector(){return{style:{}};}}
globalThis.document={createElement:t=>new Element(t)};
for(const r of records)for(const o of r.operations){
 const s=buildSasongko2025Scene(o,r);ck('Mapped '+r.record_id+'/'+o.id,s&&s.kind===r.record_id+'--'+o.id);
 const b=bindings.find(x=>x.scene_id===s.kind);ck('Graph '+s.kind,JSON.stringify(b.inputs)===JSON.stringify(o.inputs)&&JSON.stringify(b.outputs)===JSON.stringify(o.outputs)&&b.retained_fraction===o.retained_fraction);
 ck('SVG '+s.kind,s.svg.includes('viewBox=')&&s.artSvg.includes('role="img"'));
 ck('No invalid numeric '+s.kind,!/NaN|undefined/.test(s.svg));
 const tq=s.rows.flatMap(x=>x.quantity?[x]:x.quantities||[]);const expected=typed.filter(x=>x.scene_id===s.kind);
 ck('All quantitative rows '+s.kind,tq.length===expected.length);
 for(const t of expected){const row=tq.find(x=>x.pointer===t.pointer);ck('Exact quantity '+s.kind+t.pointer,!!row&&JSON.stringify(row.quantity)===JSON.stringify(t.quantity)&&JSON.stringify(row.quantity)===JSON.stringify(resolve(r,t.pointer)));}
 ck('Notes readable '+s.kind,s.rows.every(x=>typeof x.label==='string'&&typeof x.value==='string'));
 ck('No foreign source '+s.kind,buildSasongko2025Scene(o,{...r,lineage:{source_group:'foreign'}})===null);
 ck('Reject unknown operation '+s.kind,buildSasongko2025Scene({...o,id:'unmapped'},r)===null);
 const art=createSasongko2025Art(o,r),grid=createSasongko2025ConditionGrid(o,r);
 ck('Actual DOM art wrapper '+s.kind,art.dataset.scene===s.kind&&art.innerHTML===s.artSvg);
 ck('Actual DOM condition wrapper '+s.kind,grid.children.length===s.rows.length);
 ck('Actual HTML markup '+s.kind,renderSasongko2025Markup(s).includes(s.artSvg));
 ck('Selection mapping '+s.kind,sasongko2025SceneSelection.records[r.record_id].includes(o.id));
 fs.writeFileSync(path.join(A,'svg',s.kind+'.svg'),s.svg);fs.writeFileSync(path.join(A,'svg',s.kind+'--art.svg'),s.artSvg);
 scenes.push({...s,record_id:r.record_id,operation_id:o.id});
}
ck('All21 scenes',scenes.length===21);ck('No canonical input mutation',JSON.stringify(records)===before);
ck('27 paired context rows',scenes.flatMap(s=>s.rows).filter(r=>r.kind==='paired_comparison_context').length===27);
ck('Exactly170 typed field displays',scenes.flatMap(s=>s.rows.flatMap(r=>r.quantity?[r]:r.quantities||[])).length===170);
fs.writeFileSync(path.join(A,'rendered-scenes.json'),JSON.stringify(scenes,null,2)+'\n');
fs.writeFileSync(path.join(A,'module-author-checks.json'),JSON.stringify({status:'passed_author_checks',checks,check_count:checks.length,scenes:21,typed_fields:170,quantitative_rows:scenes.reduce((n,s)=>n+s.rows.filter(r=>r.quantity||r.quantities).length,0),notes:scenes.reduce((n,s)=>n+s.rows.filter(r=>r.kind==='source_scope_note').length,0),browser_executed:false,independent_audit:false},null,2)+'\n');
console.log(JSON.stringify({checks:checks.length,scenes:scenes.length,rows:scenes.reduce((n,s)=>n+s.rows.length,0)}));
