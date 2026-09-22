import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath,pathToFileURL} from 'node:url';
import crypto from 'node:crypto';
const work=path.dirname(fileURLToPath(import.meta.url));
const site=path.resolve(work,'../../recipe-atlas'),dist=path.join(site,'dist');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const api=await import(pathToFileURL(path.join(dist,'reader-particle.mjs')));
const art=await import(pathToFileURL(path.join(dist,'particle-shapes.mjs')));
const meta=read(path.join(dist,'data/reader-presentation.json'));
const interpretations=read(path.join(dist,'data/reader-morphology-interpretations.json')).entries;
let checks=0;const ck=(yes,note)=>{assert.ok(yes,note);checks++;};
const groups=new Map(),shapes={};
for(const [rid,p] of Object.entries(meta.records)){
 const r=read(path.join(dist,'data/records',rid+'.json')),before=JSON.stringify(r);
 const local=api.particleGroups(r,p);
 for(const context of p.productContexts||[])ck([...local.values()].some(g=>g.sampleId===context.sample_id),'Context retained '+rid+'/'+context.sample_id);
 for(const fact of p.allProductFacts||p.productFacts||[])ck([...local.values()].some(g=>g.facts.includes(fact)),'Fact retained '+rid+'/'+fact.sample_id);
 for(const [key,g] of local){groups.set(key,g);const d=api.particleDescriptor(g,interpretations);ck(art.PARTICLE_SHAPES.includes(d.shape),'Supported shape '+key);}
 ck(JSON.stringify(r)===before,'Scientific object unchanged '+rid);
}
for(const [key,g] of groups){const d=api.particleDescriptor(g,interpretations);shapes[d.shape]=(shapes[d.shape]||0)+1;}
const pointer=(data,p)=>p.split('/').slice(1).reduce((v,k)=>v[k.replaceAll('~1','/').replaceAll('~0','~')],data);
for(const [key,item] of Object.entries(interpretations)){
 ck(groups.has(key),'Curated interpretation is reachable '+key);
 ck(key===item.record_id+':'+item.sample_id,'Exact record and sample key '+key);
 ck(hash(path.join(site,item.source_hash_scope))===item.source_sha256,'Source bytes '+key);
 const original=read(path.join(dist,'data/records',item.record_id+'.json'));
 ck(original.products.some(p=>p.sample_id===item.sample_id),'Canonical sample exists '+key);
 for(const e of item.evidence){
  const source=e.data_path?read(path.join(dist,e.data_path)):read(path.join(dist,'data/records',e.record_id+'.json'));
  ck(pointer(source,e.pointer)!==undefined,'Evidence pointer '+key+e.pointer);
  if(e.public_asset)ck(hash(path.join(dist,e.public_asset))===e.asset_sha256,'Evidence figure bytes '+key);
 }
 ck(api.particleDescriptor(groups.get(key),interpretations).inferred===item,'Exact context uses its interpretation '+key);
 const unrelated={...groups.get(key),sampleId:'unrelated-context'};
 ck(!api.particleDescriptor(unrelated,interpretations).inferred,'No inference borrowed by neighbor '+key);
}
const probes=[
 ['Circular wells','neutral'],['not spherical','neutral'],['no rods observed','neutral'],
 ['particles on a substrate, no islands','neutral'],['mostly spherical with some rods','neutral'],
 ['Separate nanocrystals; source uses both spherical and cubic shape descriptions','neutral'],
 ['Nearly spherical nanocrystals; no observable size change upon 800 °C annealing reported','sphere'],
 ['cubic shaped','cube'],['cubic packing','neutral'],['cubic crystal phase','neutral'],
 ['quantum belts','belt'],['Proposed shell-like intermediate; isolation damage','neutral'],
 ['Spherical polycrystalline nanocrystal assemblies','sphere-assembly'],
 ['Ordered wire-like nanocrystal assemblies','wire-assembly'],
 ['truncated octahedron','truncated-octahedron'],['high-aspect-ratio rods','rod'],
];
for(const [phrase,wanted] of probes)ck(api.classifyMorphology(phrase)===wanted,'Classifier boundary: '+phrase);
for(const [rel,digest] of Object.entries(read(path.resolve(work,'../reader-redesign-20260922/scientific-baseline.json'))))ck(hash(path.join(site,rel))===digest,'Canonical/export preservation '+rel);
const molecule=fs.readFileSync(path.join(dist,'chemical-viewer.mjs'),'utf8');
ck(!molecule.includes('.addLabel(')&&!molecule.includes('Label every atom'),'Molecule canvas has no label overlay or label control');
const report={status:'passed',checks,material_hubs:Object.keys(meta.materials).length,method_routes:Object.keys(meta.records).length,specimen_contexts:groups.size,curated_interpretations:Object.keys(interpretations).length,illustrated_contexts:groups.size-(shapes.neutral||0),shape_counts:shapes,scope:'Source/sample grouping, morphology boundaries, evidence pointers and hashes, all canonical/export bytes. Browser appearance is checked separately.'};
fs.writeFileSync(path.join(work,'morphology-validation.json'),JSON.stringify(report,null,2)+'\n');console.log(report);
