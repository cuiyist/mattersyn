import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {buildDabbousiScene} from './dabbousi-protocol.mjs';

// Private, read-only source-to-scene checks. Only the two private audit outputs are written.
const base=path.dirname(fileURLToPath(import.meta.url));
const site='[local path redacted]';
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const read=p=>fs.readFileSync(p);
const json=p=>JSON.parse(read(p));
const checks=[], scenes=[], records=[];
function check(name,ok,detail=''){checks.push({name,passed:Boolean(ok),detail});}
const manifest=json(path.join(base,'apparatus-review/manifest.json'));
const files=fs.readdirSync(path.join(base,'canonical-drafts')).filter(f=>f.endsWith('.json')).sort();
for(const f of files){
  const p=path.join(base,'canonical-drafts',f),raw=read(p),r=JSON.parse(raw);
  records.push({record_id:r.record_id,sha256:sha(raw),operation_count:r.operations.length});
  for(const o of r.operations){
    const s=buildDabbousiScene(o,r), id=r.record_id+'/'+o.id;
    const m=manifest.files.find(v=>v.recordId===r.record_id&&v.operationId===o.id);
    check(id+' / dispatch',s?.kind===o.action);
    if(!s)continue;
    check(id+' / source guard',buildDabbousiScene(o,{...r,sources:[{doi:'10.0000/unrelated'}]})===null);
    check(id+' / current artifact',m?.sourceRecordSha256===sha(raw)&&m?.sha256===sha(s.svg));
    scenes.push({record_id:r.record_id,operation_id:o.id,action:o.action,svg_sha256:sha(s.svg),source_evidence:o.evidence,visual_review:'passed in independently inspected final contact sheets',text:s.svg.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim(),caption:s.caption});
  }
}
const scene=(id,op)=>scenes.find(s=>s.record_id==='dabbousi-1997-'+id&&s.operation_id===op)?.text||'';
check('60 canonical operation scenes',scenes.length===60);
check('35 distinct action classes',new Set(scenes.map(s=>s.action)).size===35);
check('CdS explicit 180 C and approximately 1 mL/min',/180 °C/.test(scene('cds-overgrowth','dose'))&&/≈1 mL\/min/.test(scene('cds-overgrowth','dose'))&&!/5–10 min/.test(scene('cds-overgrowth','dose')));
check('ZnS paired temperature and 5–10 min',/5–10 min/.test(scene('zns-overgrowth','dose'))&&/Source-paired T/.test(scene('zns-overgrowth','dose')));
check('CdS shared-step inheritance visible',/inherited/.test(scene('cds-overgrowth','heat-seeds')));
check('CdS equal storage cosolvents without invented amounts',/Equal amounts/.test(scene('cds-overgrowth','storage-solvent'))&&/Basis unstated/.test(scene('cds-overgrowth','storage-solvent'))&&!/5 mL/.test(scene('cds-overgrowth','storage-solvent')));
check('ZnS butanol is storage aid rather than quench',/1-Butanol · 5 mL/.test(scene('zns-overgrowth','storage-solvent'))&&/no quench/.test(scene('zns-overgrowth','storage-solvent')));
check('Seed stock distinct from injected charge',/0.1 mol/.test(scene('cdse-seed-preparation','stock'))&&/100 mL/.test(scene('cdse-seed-preparation','stock'))&&/unreported injected seed charge/.test(scene('cdse-seed-preparation','stock')));
check('Seed injection and growth temperatures distinct',/340–360 °C/.test(scene('cdse-seed-preparation','inject'))&&/290–300 °C/.test(scene('cdse-seed-preparation','grow')));
check('Solvent pumping has no numerical temperature',/No heater, numerical pressure, temperature/.test(scene('zns-overgrowth','pump-solvent'))&&!/60 °C|190 °C/.test(scene('zns-overgrowth','pump-solvent')));
check('Solution and film SAXS voltages distinct',/40 kV/.test(scene('saxs-solution','saxs'))&&/60 kV/.test(scene('saxs-pvb-film','saxs')));
check('WDS dry film, not wet solution thickness',/Cast and dry/.test(scene('wds-preparation','cast'))&&/Final film · 1 µm/.test(scene('wds-preparation','cast')));
check('TEM evaporation and unspecified WDS coating preserved',/Carbon evaporation/.test(scene('tem-preparation','coat'))&&/no evaporation is inferred/.test(scene('wds-preparation','carbon')));
check('XPS experimental Mg excitation and analyzer source',/1253.6 eV/.test(scene('xps-preparation','xps'))&&/Hemispherical/.test(scene('xps-preparation','xps'))&&/Al option is not applied simultaneously/.test(scene('xps-preparation','xps')));
check('Optical geometry limitation preserved',/front-face collection/.test(scene('optical-characterization','measure'))&&/not optical geometry/.test(scene('optical-characterization','measure')));
check('Air exposure is not a forced serial synthesis',/not one mandatory serial sequence/.test(scene('air-exposure','expose')));
const refDir=path.join(site,'dist/assets/crystal-references');
const registry=json(path.join(refDir,'registry.json'));
const ref=registry.entries.find(e=>e.id==='cdse-wurtzite-cod-9016056');
const modelBytes=read(path.join(refDir,ref.modelPath)),model=JSON.parse(modelBytes),cifBytes=read(path.join(refDir,ref.cifPath));
check('Bulk crystal reference hash matches registry',sha(modelBytes)===ref.modelSha256&&sha(cifBytes)===ref.cifSha256);
check('Pure bulk CdSe only: four atoms, no Zn/S/interface',model.atoms.length===4&&model.atoms.every(a=>a.element==='Cd'||a.element==='Se'));
check('Bulk crystal model excluded from experimental training',model.reference_only===true&&model.training_eligible===false&&model.measured_sample_structure===false&&ref.referenceOnly===true&&ref.trainingEligible===false);
check('Bulk reference explicitly disclaims reconstructed experimental interface',/does not reconstruct/.test(ref.scope)&&/No ZnS, CdS or ZnSe shell atoms/.test(ref.scope));
const moduleSha=sha(read(path.join(base,'dabbousi-protocol.mjs')));
check('Audited stable module matches author manifest',moduleSha===manifest.moduleSha256);
const contacts=manifest.visualReview.assets.map(a=>({file:a.file,sha256:sha(read(path.join(base,'apparatus-review',a.file))),visually_inspected:true,assessment:'All six panels readable; no unsupported quantitative geometry or apparatus noticed.'}));
check('Ten contact sheets still match the visually inspected manifest',contacts.length===10&&contacts.every(a=>manifest.visualReview.assets.find(m=>m.file===a.file)?.sha256===a.sha256));
const scientific_review=[
  {topic:'Shell branch and precursor handling',source_locator:'Main PDF p. 2 / printed p. 9464, Materials and Syntheses; p. 13 / printed p. 9475, note 22',result:'ZnEt2 vs CdMe2 filtration, TOPSe stock vs injected charge, TOP/TOPO roles, same-basic-procedure inheritance, six ZnS temperature pairs and explicit CdS dosing differences remain separate.'},
  {topic:'Thermal and workup states',source_locator:'Main PDF p. 2 / printed p. 9464, Syntheses',result:'Conditioning under vacuum, hexane removal, N2 shell growth, 90 C hold, storage, methanol precipitation and redispersion alternatives have distinct scenes. No unsupported heater, bath medium, vacuum number, storage temperature, centrifuge setting or quench is supplied.'},
  {topic:'Characterization preparation and instruments',source_locator:'Main PDF pp. 2–3 / printed pp. 9464–9465, characterization methods',result:'WDS dry-film thickness and unspecified carbon coating are distinct from TEM carbon evaporation. Pyridine film preparations, polymer/solvent alternatives, solution vs film SAXS settings, XPS excitation/analyzer and front-face PL limitation are retained.'},
  {topic:'Air exposure',source_locator:'Main PDF pp. 5–6 / printed pp. 9467–9468, Figures 5–7 and discussion',result:'Bare/coated groups are comparison states. The drawing does not impose one mandatory serial synthesis or humidity/temperature control.'},
  {topic:'Bulk reference boundary',source_locator:'Main PDF p. 10 / printed p. 9472, Figure 13 and WAXS models; external COD9016056 retained as a separately identified reference',result:'The external bulk CdSe cell has a=4.299 Angstrom, deliberately distinct from the paper model value 4.29. It has only Cd/Se atoms, carries explicit reference-only flags, and is not a measured core/shell structure or reconstructed interface.'}
];
const errors=checks.filter(c=>!c.passed);
const out={schema_version:'1.0',source_id:'dabbousi1997',source_doi:'10.1021/jp971091y',scope:'Independent bounded source-to-apparatus and reused bulk-reference audit; supplied main only, SI not verified. No source-to-view, training or publication promotion.',status:errors.length?'must_fix':'passed',module_sha256:moduleSha,source_sha256:'dac183303049a3275d4f1874c66ac0ceece9895bc175f7f7e9727ef7c9cd8f9d',records,scene_count:scenes.length,action_count:new Set(scenes.map(s=>s.action)).size,check_count:checks.length,checks,open_findings:errors,scientific_review,contact_sheets:contacts,scenes,bulk_reference:{id:ref.id,cif_sha256:sha(cifBytes),model_sha256:sha(modelBytes),atoms:model.atoms.map(a=>a.element),cell:model.cell,registry_scope:ref.scope},limitations:['This verifies explanatory static SVGs and source semantics, not a fabricated apparatus specification. Vessel geometry, particle counts and layer proportions are illustrative.','Complete numerical operation conditions are rendered alongside the diagrams by the common reader UI; browser integration and controls remain root QA responsibilities.','The passed source and canonical audits remain separately scoped; this artifact does not establish matched-SI review or change training eligibility.']};
fs.writeFileSync(path.join(base,'apparatus-source-audit.json'),JSON.stringify(out,null,2)+'\n');
fs.writeFileSync(path.join(base,'apparatus-source-audit.md'),`# Independent Dabbousi apparatus/source audit\n\nStatus: **${out.status}**. ${scenes.length} operation scenes across ${records.length} records; ${out.action_count} action types. ${checks.length} bounded checks, ${errors.length} open must-fix findings. All ten final contact sheets were independently visually inspected.\n\nModule SHA-256: \`${moduleSha}\`.\n\n${scientific_review.map(x=>`- **${x.topic}.** ${x.result} Source: ${x.source_locator}.`).join('\n')}\n\nThe independent bulk CdSe reference contains two Cd and two Se atoms, is explicitly reference-only, and cannot be used as a measured shell/interface or experimental training target. Registry, model and CIF hashes were checked.\n\n${out.limitations.map(x=>'- '+x).join('\n')}\n\nExact record/scene hashes, checks, source locators and contact-sheet hashes are in apparatus-source-audit.json. Reusable private check: audit_apparatus_source.mjs. No Site files were changed.\n`);
console.log(JSON.stringify({status:out.status,records:records.length,scenes:scenes.length,actions:out.action_count,checks:checks.length,errors,module_sha256:moduleSha},null,2));
if(errors.length)process.exitCode=1;
