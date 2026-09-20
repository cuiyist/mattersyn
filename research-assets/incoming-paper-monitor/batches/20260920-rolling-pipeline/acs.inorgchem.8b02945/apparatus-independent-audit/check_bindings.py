"""Independent, bounded apparatus audit; does not edit the frozen author proposal."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
A=Path(__file__).resolve().parent
F=A.parent
V=F/'visuals/apparatus'
C=F/'canonical-proposal/draft-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ptr(x,p):
 for k in p.split('/')[1:]:x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
freeze=read(V/'package-freeze.json')
assert sha(V/'package-freeze.json')=='88bde7fb75b522799498a7b081b5e76e5ba1e483d38cab475205901bc4094ef7'
for rel,digest in freeze['bound_files'].items():assert sha(V/rel)==digest,rel
assert sha(C/'package-freeze.json')==freeze['canonical_freeze_sha256']
records={p.stem:read(p) for p in (C/'records').glob('*.json')}
bindings=read(V/'canonical-bindings.json')['bindings']
rendered=read(A/'independently-executed-scenes.json')
author=read(V/'rendered-scenes.json')
assert {x['kind']:x for x in rendered}=={x['kind']:x for x in author},'Fresh execution differs from frozen author scenes'
for b in bindings:
 r=records[b['record_id']]; op=ptr(r,b['operation_pointer'])
 assert op['id']==b['operation_id']
 assert sha(Path(b['record_path']))==b['record_sha256']
 for k in ['inputs','optional_inputs','outputs','retained_fraction']:
  assert b[k]==op.get(k,[] if k in ['inputs','optional_inputs','outputs'] else None),(b['scene_id'],k)
for q in read(V/'typed-field-map.json'):
 rid=q['scene_id'].split('--')[0]
 assert ptr(records[rid],q['pointer'])==q['quantity'],q['scene_id']
byid={x['kind']:x for x in rendered}
text=lambda sid:' '.join(x['value'] for x in byid[sid]['rows'])+' '+byid[sid]['description']
checks={
 'no_representative_mass_on_concentration_variant': all(x['value']=='Not reported' for x in byid['friedfeld-2019-conversion-concentration--sonicate-msc']['rows'] if 'mass' in x['label'].lower()),
 'inherited_ode_explicit': 'inherited common-procedure context' in text('friedfeld-2019-conversion-concentration--sonicate-msc'),
 'sampling_not_duration': 'sampling interval, not a reaction duration' in text('friedfeld-2019-conversion-representative--monitor-growth'),
 'nitrogen_coolant_not_reaction_input': 'nitrogen coolant does not' in text('friedfeld-2019-labeled-acid-synthesis--acid-condense'),
 'dryice_acetone_external': 'external cooling bath' in text('friedfeld-2019-labeled-acid-synthesis--acid-cold-hold'),
 'ether_extract_retained': 'Retain the organic extracts' in text('friedfeld-2019-labeled-acid-synthesis--acid-extract'),
 'filtrate_retained': 'retain the organic filtrate' in text('friedfeld-2019-labeled-acid-synthesis--acid-filter-evaporate'),
 'fft_not_saed': 'not relabeled as an SAED' in text('friedfeld-2019-tem--tem-analyze'),
 'tga_atmosphere_not_inherited': 'not transferred to TGA' in text('friedfeld-2019-tga--tga-analyze'),
 'dsc_ambiguous_token_not_operational': 'not converted into an operational heating rate' in text('friedfeld-2019-dsc--dsc-analyze'),
 'scherrer_distinct_from_particle': 'not automatically a TEM particle diameter' in text('friedfeld-2019-scherrer-analysis--scherrer-analysis-analyze'),
 'upstream_recipe_incomplete': 'complete recipe is not reproduced' in text('friedfeld-2019-labeled-msc-cited--substitute-labeled-acid'),
}
assert all(checks.values()),checks
pub=read(V/'public-module-proposal.json')
for f in pub['files']:assert sha(Path(f['path']))==f['sha256']
assert sha(Path(pub['dependency']['path']))==pub['dependency']['sha256']
assert sha(Path(pub['dependency']['path']))==sha(Path(r'[local path redacted]'))
result={
 'schema':'mattersyn-independent-apparatus-audit/1','created_at':datetime.now(timezone.utc).isoformat(),'reviewer':'/root','author':'/root/norberg2004_extract','status':'passed',
 'scope':'Friedfeld 2019 frozen stage-specific apparatus proposal; no canonical or publication approval.',
 'proposal_freeze_sha256':sha(V/'package-freeze.json'),'canonical_freeze_sha256':sha(C/'package-freeze.json'),
 'source_audit_sha256':sha(F/'source-independent-audit/independent-audit-v2.json'),
 'counts':{'bound_files_verified':len(freeze['bound_files']),'operation_instances':58,'canonical_records':19,'unique_source_operations':34,'typed_quantities':115,'condition_options':39,'display_rows':269},
 'independent_execution':read(A/'module-checks.json'),'semantic_checks':checks,
 'visual_inspection':{'reviewer':'/root','actual_viewed_files':[f'visuals/apparatus/contacts/art-contact-{i}.png' for i in range(1,11)]+['visuals/apparatus/previews/friedfeld-2019-conversion-concentration--sonicate-msc.png','visuals/apparatus/previews/friedfeld-2019-conversion-indium-additive--heat-baseline.png'],'coverage':'All 58 individual art scenes in 10 contact sheets, plus full-size condition layouts for concentration-injection and longest indium-temperature comparison. Academic labels, stage distinctions, bath/input separation and product/data symbolism inspected. No clipping found in the inspected native layouts.','mounted_browser_tested':False},
 'scientific_review':'Read all 34 unique scene descriptions and scope notes. Matched representative conversion, labeled-acid preparation and analytical instrumentation to source main pp6–7 already visually read in this turn; current full33-page source reading is owned by the separate passed source audit. Compared all exact canonical operation inputs, outputs and quantities. No source atomic coordinates, synthetic spectra or invented bath/pressure values supplied.',
 'remaining_gates':['Canonical/reader independent audit, including reader-only corrections','Site integration and actual desktop/mobile browser checks','Batch publication and anonymous endpoint verification'],
 'training_or_exact_structure_approval':False,'publication_approval':False,
}
(A/'independent-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'passed','audit_sha256':sha(A/'independent-audit.json'),'counts':result['counts']}))
