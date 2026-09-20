import fs from 'node:fs';
import {averagePositions,HEO_RECORDS,mountHeoAverage} from '../products/heo2003-average-viewer.mjs';
import {selectReflections} from '../../si-reader-proposal/heo2003-reflection-viewer.mjs';
const model=JSON.parse(fs.readFileSync(new URL('../products/heo2003-average-view.json',import.meta.url)));
const si=JSON.parse(fs.readFileSync(new URL('../../si-reader-proposal/heo2003-reflections.json',import.meta.url)));
let count=0;const failed=[];const ck=(label,ok)=>{count++;if(!ok)failed.push(label);};
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b),ids=rows=>rows.map(r=>r.row_id);
const positions=averagePositions(model),periodic=averagePositions(model,2);
ck('680 unit markers /5440 repeated markers',positions.length===680&&periodic.length===5440);
for(const p of periodic){const base=model.fractionalSites.find(s=>s.id===p.site_id);ck('Periodic translation and exact occupancy '+p.site_id+'/'+p.cell,equal([p.x,p.y,p.z],base.cartesian.map((v,i)=>v+p.cell[i]*24.942))&&equal(p.components,base.components)&&p.mixed===base.mixed&&p.occupancy_sum===base.occupancy_sum);}
for(const group of model.groups){const v=averagePositions(model,1,[group.label]);ck('Layer hides only stated group '+group.label,v.length===680-group.positions_per_cell&&v.every(x=>x.source_label!==group.label));}
for(const extent of [-1,0,3,1.5]){let rejected=false;try{averagePositions(model,extent);}catch{rejected=true;}ck('Unsupported extent rejected '+extent,rejected);}
ck('Exactly three eligible record scopes',equal(HEO_RECORDS,['heo-2003-in66-route','heo-2003-single-crystal-acquisition','heo-2003-average-structure']));
for(const record of [{record_id:HEO_RECORDS[0],lineage:{source_group:'other'}},{record_id:'heo-2003-xps-acquisition',lineage:{source_group:'heo2003'}},{record_id:'heo-2003-refinement-comparison',lineage:{source_group:'heo2003'}}])ck('Mount rejects unqualified record '+record.record_id,await mountHeoAverage(null,record)===false);
ck('Default reflection order unchanged',equal(ids(selectReflections(si)),ids(si.rows)));
for(let page=0;page<=14;page++)for(const kind of ['all','negative','zero','unresolved']){
 const expected=si.rows.filter(r=>{
  if(page&&r.cells[0].evidence.pdf_page!==page)return false;
  const obs=r.cells.find(c=>c.evidence.column_key==='Fobs2');
  return kind==='all'||kind==='negative'&&obs.numeric_value!==null&&obs.numeric_value<0||kind==='zero'&&obs.numeric_value===0||kind==='unresolved'&&r.cells.some(c=>c.sign_status==='unresolved_from_retained_scan');
 });ck('Page/type filter and order '+page+'/'+kind,equal(ids(selectReflections(si,{page:String(page),kind})),ids(expected)));
}
for(const row of si.rows){ck('Exact hkl search '+row.row_id,equal(ids(selectReflections(si,{query:'('+row.hkl.join(',')+')'})),[row.row_id]));ck('Exact row-ID search '+row.row_id,equal(ids(selectReflections(si,{query:row.row_id})),[row.row_id]));}
ck('Unknown query empty',selectReflections(si,{query:'not-an-existing-reflection'}).length===0);
ck('Known unresolved hkl remains searchable',selectReflections(si,{query:'9 11 27',kind:'unresolved'})[0]?.row_id==='si-p11-R-r035');
const report={author:'/root/peng1998_reader_assets',auditor:'/root/backlog_eta',checks:count,failed,scope:'Actual exported pure functions and early scope guards executed independently; no DOM/browser behavior claimed.'};
fs.writeFileSync(new URL('./runtime-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
