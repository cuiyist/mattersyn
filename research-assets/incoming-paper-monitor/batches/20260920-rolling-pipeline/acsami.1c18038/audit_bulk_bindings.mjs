import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
const L=path.dirname(new URL(import.meta.url).pathname).replace(/^\/(?=[A-Za-z]:)/,'');
const V=path.join(L,'visuals/bulk-structure-proposal');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
let checks=0;const check=(ok,label)=>{checks++;if(!ok)throw Error(label);};
const freeze=read(path.join(V,'package-freeze.json'));
for(const [name,digest] of Object.entries(freeze.own_files))check(sha(path.join(V,name))===digest,'Frozen asset '+name);
const api=await import(pathToFileURL(path.join(V,'lian2021-bulk-viewer.mjs')));
const bindings=read(path.join(V,'product-bindings-proposal.json')).bindings;
check(bindings.length===4,'four explicit contexts');
const records=fs.readdirSync(path.join(L,'canonical-proposal/v1')).filter(f=>f.startsWith('lian-2021-')&&f.endsWith('.json')).map(f=>read(path.join(L,'canonical-proposal/v1',f)));
check(records.length===16,'sixteen canonical records');
for(const r of records){const want=bindings.filter(b=>b.record_id===r.record_id);const got=api.eligibleBulkContexts(r);check(JSON.stringify(got.map(b=>b.sample_id))===JSON.stringify(want.map(b=>b.sample_id)),'context selection '+r.record_id);}
for(const b of bindings){
 const r=read(b.source_record_path), p=r.products[Number(b.product_pointer.split('/').at(-1))];
 check(sha(b.source_record_path)===b.source_record_sha256,'bound canonical');
 check(JSON.stringify(p)===JSON.stringify(b.product_snapshot),'exact source product snapshot');
 check(p.sample_id===b.sample_id,'sample id');
 check(!b.same_physical_batch_verified&&!b.eligible_as_measured_label&&!b.atomic_training_eligible,'no extra sample or training claim');
 for(const mutate of [x=>x.lineage.source_group='different',x=>x.record_id+='-wrong',x=>x.products=[],x=>x.products.forEach(p=>p.sample_id+='-wrong'),x=>x.products.forEach(p=>p.composition.value+='X'),x=>x.products.forEach(p=>p.phase.value='unknown')]){const x=structuredClone(r);mutate(x);check(api.eligibleBulkContexts(x).length===0,'fail-closed identity guards');}
}
for(const phase of ['a','b']){
 const m=read(path.join(V,`lian2021-bulk-${phase}-non-h.json`));
 for(const expanded of [false,true]){const g=api.displayGeometry(m,expanded);check(g.sites.length===(phase==='a'?(expanded?64:32):(expanded?144:36)),'geometry count');check(g.bonds.length===(expanded?0:m.source_bonds.length),'source links only');check(g.sites.every(x=>x.occupancy===null),'occupancy unknown');}
 const m2=structuredClone(m);m2.asymmetric_unit_sites[0].occupancy=1;let threw=false;try{api.displayGeometry(m2);}catch{threw=true;}check(threw,'reject assumed occupancy');
}
const allow=read(path.join(V,'public-asset-proposal.json')).files;check(allow.length===6,'six assets');
for(const x of allow){check(sha(x.source)===x.sha256,'asset hash');check(!x.target.includes('..')&&!path.isAbsolute(x.target)&&/\.(json|cif|css|mjs)$/.test(x.target),'bounded public path');}
const output={status:'passed',author:'/root/peng1998_reader_assets',auditor:'/root',at:new Date().toISOString(),check_count:checks,package_freeze_sha256:sha(path.join(V,'package-freeze.json')),scope:'Frozen-file identity, exact canonical record/sample/formula/phase bindings and negative controls; source-only connectivity; unknown-occupancy rejection; six-file public allowlist. Model math has a separate independent receipt. Actual integrated browser scope remains pending.',browser_passed:false,script_sha256:sha(new URL(import.meta.url))};
fs.writeFileSync(path.join(L,'visuals/bulk-structure-independent-audit/binding-audit.json'),JSON.stringify(output,null,2)+'\n');console.log(JSON.stringify(output));
