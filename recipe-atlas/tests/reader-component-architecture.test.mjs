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

test('multi-particle architectures cannot be illustrated as an isolated rod, plate or island',()=>{
 const xu='xu2008-hierarchical-nc-assemblies-adma200800215-au-ag-tio2-long';
 const assemblies=[
  'island-free hierarchical porous architecture at faster evaporation',
  'bilayered superlattice walls with smaller islands in pores',
 ];
 for(const value of assemblies)assert.equal(classifyMorphology(value,xu),'assembly',value);
 assert.equal(classifyMorphology('long TiO2 nanorods'),'rod');
 assert.equal(classifyMorphology('hexagonal CoO nanoplates'),'platelet');
 for(const value of ['2D porous architecture of short TiO2 nanorods','two shifted hexagonal layers of short rods','2D short-rod architecture on wafer, Figure 3h feature-size outcome (unquantified)','orthogonally ordered pores with small pores around large ones'])assert.equal(classifyMorphology(value,xu),'rod-assembly',value);
 assert.equal(classifyMorphology('Ag nanocrystals arranged like petals around hexagonal CoO nanoplates',xu),'platelet-dot-assembly');
 assert.equal(classifyMorphology('hexagonally ordered porous Ag–CoO architecture assembled from one-pot hybrid building blocks',xu),'porous-hybrid-film');
 assert.equal(classifyMorphology('binary porous architecture containing square Eu:LaVO4 particles',xu),'square-dot-assembly');
 assert.equal(classifyMorphology('square nanocrystals',xu),'square-projection');
 for(const length of ['long','short'])assert.equal(classifyMorphology(`ternary porous architecture with TiO2 ${length} rods`,xu),'mixed-rod-dot-assembly');
 assert.equal(classifyMorphology('Extended dendritic deposits; no ordered superlattice observed'),'neutral');
 assert.equal(classifyMorphology('Close-packed QD monolayer with dispersed triangular or truncated triangular Ag nanoprisms'),'neutral');
 assert.match(particleShapeSVG('mixed-rod-dot-assembly'),/Schematic porous assembly of rods and round nanocrystals/);
 for(const shape of ['rod-assembly','platelet-dot-assembly','porous-hybrid-film','square-dot-assembly','square-projection'])assert.match(particleShapeSVG(shape),/role="img"/);
 for(const shape of ['platelet-dot-assembly','porous-hybrid-film','square-dot-assembly']){
  const drawing=particleShapeSVG(shape).split('</defs>')[1];
  assert.match(drawing,/fill="url\(#ms-morph-\d+-gold\)"/,`${shape} dots match the gold legend`);
  assert.match(drawing,/fill="url\(#ms-morph-\d+-top\)"/,`${shape} plates match the teal legend`);
 }
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
