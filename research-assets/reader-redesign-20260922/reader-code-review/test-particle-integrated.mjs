import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const here=path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Z]:)/i,'$1'));
const root='[local path redacted]';
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
// Pure grouping/descriptor checks only; DOM and actual browser remain root QA.
const actual=process.argv[2]==='actual';
const original=fs.readFileSync(actual?root+'/reader-particle.mjs':path.join(here,'reader-particle-proposal.mjs'),'utf8');
const module=await import('data:text/javascript;base64,'+Buffer.from(original.replace(/^import .*reader-utils\.mjs';$/m,'' )).toString('base64'));
const p=read('data/reader-presentation.json');let checks=0;const check=(ok,label)=>{assert.ok(ok,label);checks++;};
for(const [rid,meta] of Object.entries(p.records)){
 const r=read('data/records/'+rid+'.json'),before=JSON.stringify(r),groups=module.particleGroups(r,meta);
 for(const c of meta.productContexts||[])check([...groups.values()].some(g=>g.sampleId===c.sample_id),'Context retained '+rid+'/'+c.sample_id);
 for(const f of meta.allProductFacts||meta.productFacts||[])check([...groups.values()].some(g=>g.facts.includes(f)),'Fact retained '+rid+'/'+f.sample_id);
 check(JSON.stringify(r)===before,'Canonical object unchanged '+rid);
}
for(const rid of ['braun-2001-system-i','braun-2001-system-ii','braun-2001-system-iii']){
 const r=read('data/records/'+rid+'.json'),g=module.particleGroups(r,p.records[rid]).get(rid+':a-cds-core'),d=module.particleDescriptor(g);
 check(d.composition==='CdS','Initial core must retain its CdS identity');check(!d.composition.includes('HgS'),'No downstream HgS layer borrowed');check(!d.caption.includes('Core'),'No invented core/shell label');
}
{
 const rid='banerjee-2003-growth',r=read('data/records/'+rid+'.json'),d=module.particleDescriptor(module.particleGroups(r,p.records[rid]).get(rid+':washings'));
 check(d.composition==='CdTe','Washings remain CdTe without MWNT host');
}
{
 const rid='sommer-2020-acs-route',r=read('data/records/'+rid+'.json'),groups=module.particleGroups(r,p.records[rid]);
 check(groups.size===7,'All seven ACS contexts retained despite null composition');
 for(const g of groups.values()){const d=module.particleDescriptor(g);check(d.composition==='Composition not assigned','No nominal ZnAl2O4 product assignment');check(d.shape==='neutral','Unknown morphology has neutral placeholder');}
}
{
 const r=read('data/records/evans-2010-species9-crystallization.json'),groups=module.particleGroups(r,{}),d=module.particleDescriptor([...groups.values()][0]);
 check(!['CdSe','PbSe','CdSe/PbSe'].includes(d.composition),'Molecular species cannot inherit paper-level quantum-dot label');
}
const result={status:'passed',checks,scope:'Actual 123 route contexts/facts plus known core/washings/unknown-composition/molecular cases. Pure functions, no browser or geometry validation.'};
fs.writeFileSync(path.join(here,actual?'particle-integrated-tests.json':'particle-proposal-tests.json'),JSON.stringify(result,null,2)+'\n');console.log(result);
