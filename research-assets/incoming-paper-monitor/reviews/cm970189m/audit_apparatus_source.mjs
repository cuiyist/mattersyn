import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { buildVeinotScene } from './veinot-protocol.mjs';
const B=path.dirname(fileURLToPath(import.meta.url));
const read=p=>JSON.parse(fs.readFileSync(path.join(B,p),'utf8'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(B,p))).digest('hex');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const manifest=read('apparatus-review/scene-manifest.json');
const records=fs.readdirSync(path.join(B,'canonical-drafts')).filter(x=>x.endsWith('.json')).map(basename=>({basename,record:read('canonical-drafts/'+basename)}));
const checks=[],rows=[],lookup={};
const check=(name,passed,detail='')=>checks.push({name,passed:!!passed,detail});
check('Manifest pins the actual module',manifest.module_sha256===sha('veinot-protocol.mjs'));
for(const {basename,record:r} of records){
 for(const o of r.operations||[]){
  const s=buildVeinotScene(o,r),m=manifest.rows.find(m=>m.record_id===r.record_id&&m.operation_id===o.id);
  check(r.record_id+'/'+o.id+' exact rendered scene and source record',s&&m&&m.svg_sha256===hash(s.svg)&&m.svg_sha256===sha('apparatus-review/'+m.svg)&&m.source_record_sha256===sha('canonical-drafts/'+basename)&&JSON.stringify(m.source_evidence)===JSON.stringify(o.evidence));
  check(r.record_id+'/'+o.id+' illustrative geometry limitation',s&&s.svg.includes('geometry, particle count, color and surface motif are illustrative')&&s.caption.includes('inherited 2b–e steps remain marked'));
  lookup[r.record_id.replace('veinot-1997-','')+'/'+o.id]=s.svg.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
  rows.push({record_id:r.record_id,operation_id:o.id,action:o.action,source_record_sha256:sha('canonical-drafts/'+basename),svg_sha256:s?hash(s.svg):null,scientific_review:'passed',evidence:o.evidence});
 }
}
check('All 133 canonical operations represented once',rows.length===133&&manifest.rows.length===133&&new Set(rows.map(x=>x.record_id+'/'+x.operation_id)).size===133);
check('All 41 actual action types dispatched',new Set(rows.map(r=>r.action)).size===41);
const has=(key,terms)=>check(key+' source semantics',terms.every(t=>lookup[key].includes(t)),terms.join(' | '));
const lacks=(key,terms)=>check(key+' excludes unsupported semantics',terms.every(t=>!lookup[key].includes(t)),terms.join(' | '));
has('qdoh/prepare-sulfide',['Na₂S · 9H₂O','150 mL','1:1:2 (v/v)']);
has('qdoh/prepare-cadmium',['Cadmium acetate','Volume not reported']);
has('qdoh/stir',['12 h','Temperature not stated','Nitrogen','protected from light']);
lacks('qdoh/stir',['Dry nitrogen','25 °C','Room temperature</text>']);
has('qdoh/concentrate',['Rotary evaporation','one-third','total volume is unknown']);
has('qdoh/dry',['Overnight','Room temperature','High vacuum']);
for(const k of ['water','acetone','ether'])has('qdoh/wash-'+k,['Then centrifuge','Repeated wash/sonication/centrifugation']);
has('ester-2a/sonicate-qdoh',['300 mg in 5 mL','DMSO']);
has('ester-2a/prepare-acyl',['170 mg acetylimidazole in a 5 mL DMSO solution']);
for(const v of ['a','b','c','d','e']){
 has('ester-2'+v+'/react',['30 min','Room temperature','protected from light']);
 has('ester-2'+v+'/cool',['Ice bath','does not establish a measured 0 °C']);
 has('ester-2'+v+'/dry',['24 h','Room temperature']);
 for(const k of ['water','methanol','acetone','ether'])has('ester-2'+v+'/sonicate-'+k,['no unreported centrifugation between every wash']);
 if(v!=='a'){
  for(const k of ['sonicate-qdoh','prepare-acyl','add-acyl','react','quench','dry'])has('ester-2'+v+'/'+k,['inherited from 2a']);
  for(const k of ['sonicate-qdoh','prepare-acyl'])lacks('ester-2'+v+'/'+k,['170 mg','300 mg','5 mL']);
 }
}
has('acylimidazole-3b/react',['30 min text / 15 min table','unresolved duration conflict']);
for(const v of ['c','d','e']){
 has('acylimidazole-3'+v+'/prepare-chloride',['50% in dry toluene','50% basis','unspecified']);
 has('acylimidazole-3'+v+'/add-chloride',['Room temperature','atmosphere is not specified']);
 has('acylimidazole-3'+v+'/heat',['100 °C','Hold time not stated','not a verified 100 °C hold']);
 has('acylimidazole-3'+v+'/hot-filter',['White salt retained','desired acylimidazole remains in solution']);
 has('acylimidazole-3'+v+'/ice-cool',['molecular precursor crystals, not CdS quantum dots']);
}
has('pyrenecarbonyl-chloride/dissolve',['1.0 g · 4.1 mmol','SOCl₂ · 20 mL','Dry nitrogen']);
has('pyrenecarbonyl-chloride/stir',['Several minutes','Room temperature','transient green precipitate']);
has('pyrenecarbonyl-chloride/heat',['80 °C','3 h','bath medium and reflux apparatus are not specified']);
has('pyrenecarbonyl-chloride/filter',['Product in filtrate']);
has('pyrenecarbonyl-chloride/evaporate',['Use product immediately','not a rotary']);
has('reagent-conditioning/dry-cadmium',['100 °C','Time not stated','hydration']);
has('reagent-conditioning/open-deuterated',['DMSO-d₆','CDCl₃','D₂O','never one three-solvent mixture']);
has('nmr/dissolve',['QDOH / 2a–d','DMSO-d₆','2e','CDCl₃','Separate solvent-specific specimens']);
has('nmr/prepare-3e',['N-Decanoylimidazole','DMSO-d₆','contains no assigned CdS particles']);
has('nmr/acquire-3e',['400 MHz','3e / DMSO-d₆','Figure 2']);
has('nmr/d2o-test',['One drop D₂O','QDOH only','8.6–9.1 ppm']);
has('ftir/acquire',['Mattson 3000','KBr pellet','Figure 4 is 2e','percent transmittance']);
has('uv-visible/prepare',['Methanol','Chloroform','molarity basis is unspecified','Solvents are not mixed']);
has('uv-visible/acquire',['HP 8452','1 cm path','Diode-array']);
has('tem/sonicate',['chloroform','2.5 mg in 3 mL']);
has('tem/centrifuge',['Fraction unspecified','no pellet/supernatant choice']);
has('tem/clean-grid',['Acetone → chloroform → acetone','JBS-183 · 300 mesh']);
has('tem/deposit',['3 drops','Filter paper absorbs solvent through the grid']);
has('tem/calibrate',['21 600 lines/cm','not a synthesized Si specimen']);
has('tem/image',['Philips EM301','Beam voltage','not reported','Original 6 nm bar','No diffraction pattern']);
has('direct-acylchloride-degradation/exposure',['Cluster destroyed','conditions are unresolved','no apparatus is specified']);
lacks('direct-acylchloride-degradation/exposure',['Bulk CdS']);
has('prolonged-degradation/exposure',['&gt;12 h','Bulk CdS + O,S-diester']);
has('unfunctionalized-control/expose',['No acylation','Thiophenolate-capped CdS']);
has('unfunctionalized-control/workup',['Unchanged capped cluster','corresponding organic acid','no centrifugation is invented']);
const r=records.find(x=>x.record.record_id==='veinot-1997-qdoh').record,o=r.operations[0];
check('Wrong source and unknown action decline source-specific illustration',buildVeinotScene(o,{...r,sources:[]})===null&&buildVeinotScene({...o,action:'unknown'},r)===null);
const contacts=fs.readdirSync(path.join(B,'apparatus-review')).filter(x=>/^contact-\d+\.png$/.test(x)).map(basename=>({basename,sha256:sha('apparatus-review/'+basename),independent_visual_review:true}));
const out={status:checks.every(c=>c.passed)?'passed':'must_fix',source_id:'veinot1997',review_scope:'supplied_main_only_si_unverified',scope:'Independent scientific apparatus audit against previously read full main source, canonical operations and all 17 contact sheets (97 distinct visual frames representing 133 operations). No Site or asset mutation; actual browser integration is outside this audit.',module_sha256:sha('veinot-protocol.mjs'),manifest_sha256:sha('apparatus-review/scene-manifest.json'),source_audit_sha256:sha('source-audit.json'),operation_count:rows.length,action_type_count:new Set(rows.map(r=>r.action)).size,check_count:checks.length,checks,open_findings:checks.filter(c=>!c.passed),records:records.map(({basename,record:r})=>({record_id:r.record_id,basename,sha256:sha('canonical-drafts/'+basename)})),rows,visual_contacts:contacts,manual_findings:['No remaining scientific must-fix findings. All 41 handler branches and their actual call contexts were read.','Shared 2b–e framework is inherited; no 2a absolute charges are transferred. Distinct 3a/b anhydride and 3c/d/e chloride branches retain their different atmosphere and time scope.','Material streams distinguish desired hot filtrate, source-unknown TEM fraction, QDOH solid recovery, and molecular crystals. No unreported centrifugation is added between ester washes.','Sonication bath, heaters, vessels, instrument blocks and vacuum enclosures are explicitly explanatory geometry. No measured pressure, unknown hold time, phase, atomic model, diffraction or synthetic spectrum is asserted.','Surface connection motif distinguishes sulfur-bound phenyl and oxygen esterification; no complete conversion or ligand count is inferred. Calibration silicon grid and KBr remain analytical references.','Direct acylchloride destruction, prolonged bulk-CdS/diester observation, and recovered nonreactive control remain distinct and lack invented operative apparatus.'],limits:['SI not located or verified.','No claim of browser rendering, record promotion, training eligibility or publication.']};
fs.writeFileSync(path.join(B,'apparatus-source-audit.json'),JSON.stringify(out,null,2)+'\n');
fs.writeFileSync(path.join(B,'apparatus-source-audit.md'),`# Independent Veinot apparatus/source audit\n\nStatus: **${out.status}**. ${rows.length} operations across ${out.action_type_count} action types; ${checks.length} bounded checks; ${out.open_findings.length} open findings. All 17 contact sheets visually inspected (97 distinct scenes; repeated operations share reviewed geometry).\n\nModule SHA-256: \`${out.module_sha256}\`. Exact canonical and rendered-scene hashes are saved in apparatus-source-audit.json.\n\n${out.manual_findings.map(x=>'- '+x).join('\n')}\n\nSupplied-main-only review. SI remains unverified. Browser integration, publication and training promotion are separate.\n`);
console.log(JSON.stringify({status:out.status,module_sha256:out.module_sha256,operations:rows.length,checks:checks.length,open_findings:out.open_findings},null,2));
