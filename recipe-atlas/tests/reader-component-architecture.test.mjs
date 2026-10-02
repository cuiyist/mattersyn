import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {componentScopeLabel} from '../static/reader-utils.mjs';
import {classifyMorphology} from '../static/reader-particle.mjs';
import {PARTICLE_SHAPES,particleShapeInfo,particleShapeSVG} from '../static/particle-shapes.mjs';

test('phase-mixture component badge does not claim a heterostructure',()=>{
 const label=componentScopeLabel({component_only:true,component_architectures:['phase_mixture']});
 assert.equal(label,'Component within a source-reported phase mixture');
 assert.doesNotMatch(label,/heterostructure/i);
});
test('core-shell component keeps its heterostructure label',()=>{
 assert.equal(componentScopeLabel({component_only:true,component_architectures:['core_shell']}),'Component within a core/shell heterostructure');
});
test('composite component receives a composite label',()=>{
 assert.equal(componentScopeLabel({component_only:true,component_architectures:['composite']}),'Component within a composite product');
});
test('non-component material has no component badge',()=>{
 assert.equal(componentScopeLabel({component_only:false,component_architectures:['phase_mixture']}),'');
});

test('unspecified architecture never gains a heterostructure badge',()=>{
 assert.doesNotMatch(componentScopeLabel({component_only:true}),/heterostructure/i);
 assert.doesNotMatch(componentScopeLabel({component_only:true,component_architectures:['unresolved']}),/heterostructure/i);
});

test('source-described disks get an illustrative planar shape but negated or conflicting morphology does not',()=>{
 assert.equal(classifyMorphology('Disklike; equilateral hexagon shape is predominant'),'platelet');
 assert.equal(classifyMorphology('CuS nanodisks'),'platelet');
 assert.equal(classifyMorphology('Cubic-shaped dispersed particles'),'cube');
 for(const value of ['No nanodisks observed','Nanodisks were not observed','Nanodisks and spheres','Unknown disklike morphology'])assert.equal(classifyMorphology(value),'neutral',value);
});

test('lamellar-stack artwork is explicitly qualitative and carries no measured scale',()=>{
 assert.ok(PARTICLE_SHAPES.includes('lamellar-stack'));
 assert.match(particleShapeInfo('lamellar-stack').ariaLabel,/number and arrangement are illustrative/);
 const svg=particleShapeSVG('lamellar-stack');
 assert.match(svg,/role="img"/);
 assert.match(svg,/Schematic irregular lamellae/);
 assert.doesNotMatch(svg,/(?:\d+\s?(?:nm|Å)|scale bar)/i);
});

test('source-bound Yuan CPT dot projections render as flat 2D illustrations for all quantified routes',()=>{
 const entries=JSON.parse(readFileSync(new URL('../static/data/reader-morphology-interpretations.json',import.meta.url),'utf8')).entries;
 assert.ok(PARTICLE_SHAPES.includes('dot-projection'));
 assert.match(particleShapeInfo('dot-projection').ariaLabel,/2D TEM projection.*3D shape and size are not inferred/);
 const svg=particleShapeSVG('dot-projection');
 assert.match(svg,/<circle cx="200" cy="155" r="82"/);
 assert.doesNotMatch(svg,/Morphology illustration unavailable|\d+\s?(?:nm|Å)|scale bar/i);
 for(const [ratio,panel] of [[0,'a'],[25,'b'],[50,'c'],[75,'d']]){
  const id=`yuan2026-agbis2-cpt-${ratio}`,entry=entries[`${id}:${id}-sample`];
  assert.ok(entry,`${ratio}% CPT interpretation`);
  assert.equal(entry.shape,'dot-projection');
  assert.equal(entry.status,'curator_interpretation');
  assert.equal(entry.recipe_link,'explicit');
  assert.ok(entry.evidence.some(e=>e.record_id===id&&e.figure_id==='figure-2-tem-gisaxs'&&e.panel===panel));
  assert.ok(entry.limitations.some(note=>/no physical 3D envelope/i.test(note)));
 }
});

test('Liu specimen drawings are bound to four distinct observed source panels',()=>{
 const root=new URL('../',import.meta.url);
 const recordId='liu2008-ag-pvp-nanorods-nanohexapods-cg701128b-route';
 const recordPath=new URL(`data/records/${recordId}.json`,root);
 const record=JSON.parse(readFileSync(recordPath,'utf8'));
 const recordHash=createHash('sha256').update(readFileSync(recordPath)).digest('hex');
 const entries=JSON.parse(readFileSync(new URL('static/data/reader-morphology-interpretations.json',root),'utf8')).entries;
 const cases=[
  ['l-agnh','hexapod','liu2008-main-figure-1','a'],
  ['h-zigzag-rods','bent-rod','liu2008-main-figure-3','a'],
  ['l-multipods','multipod','liu2008-main-figure-5','a'],
  ['h-ag2s-nanotube','nanotube','liu2008-si-figure-s2','b'],
 ];
 for(const [suffix,shape,figure,panel] of cases){
  const sampleId=`liu2008-ag-pvp-nanorods-nanohexapods-cg701128b-${suffix}`;
  const entry=entries[`${recordId}:${sampleId}`];
  assert.ok(entry,`${suffix} source-bound interpretation`);
  assert.ok(PARTICLE_SHAPES.includes(shape));
  assert.equal(entry.shape,shape);
  assert.equal(entry.source_sha256,recordHash);
  assert.equal(entry.sample_id,sampleId);
  assert.equal(entry.measured_atomic_coordinates,false);
  assert.ok(record.products.some(product=>product.sample_id===sampleId));
  const evidence=entry.evidence.find(item=>item.figure_id===figure&&item.panel===panel);
  assert.ok(evidence,`${suffix} panel binding`);
  const bytes=readFileSync(new URL(`static/${evidence.public_asset}`,root));
  assert.equal(createHash('sha256').update(bytes).digest('hex'),evidence.asset_sha256);
  assert.match(particleShapeSVG(shape),/role="img"/);
  assert.ok(entry.limitations.length>=2);
 }
 assert.match(entries[`${recordId}:liu2008-ag-pvp-nanorods-nanohexapods-cg701128b-h-ag2s-nanotube`].limitations.join(' '),/not the same physical particle/);
 assert.match(entries[`${recordId}:liu2008-ag-pvp-nanorods-nanohexapods-cg701128b-l-multipods`].limitations.join(' '),/electron-beam damage/);
});
