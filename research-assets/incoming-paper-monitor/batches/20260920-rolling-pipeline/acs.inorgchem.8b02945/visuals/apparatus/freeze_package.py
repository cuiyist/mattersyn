from pathlib import Path
import json,hashlib,datetime
A=Path(__file__).resolve().parent;F=A.parents[1];C=F/'canonical-proposal/draft-v2'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(A/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(A/'package-freeze.json').exists()
checks=0
def check(v):
 global checks
 assert v;checks+=1
inputs={}
for rel,h in read(C/'package-freeze.json')['bound_files'].items():check(sha(C/rel)==h)
for p in [C/'package-freeze.json',C/'record-manifest.json',F/'source-extraction-revision-2/package-freeze.json',F/'source-extraction-revision-2/source-facts.json',F/'source-extraction-revision-2/source-inventory.json',F/'source-independent-audit/independent-audit-v2.json',F/'intake-identity.json']:
 inputs[str(p)]=sha(p)
for row in read(F/'intake-identity.json')['file_copies']:
 p=Path(row['source_path']);check(sha(p)==row['sha256']);inputs[str(p)]=sha(p)
bindings=read(A/'canonical-bindings.json')['bindings'];records={r['record_id']:r for r in read(A/'records.json')}
for b in bindings:
 p=Path(b['record_path']);check(sha(p)==b['record_sha256']);inputs[str(p)]=sha(p)
 o=records[b['record_id']]['operations'][int(b['operation_pointer'].split('/')[-1])]
 for k in ['inputs','outputs','retained_fraction']:check(b[k]==o[k])
 check(b['optional_inputs']==o.get('optional_inputs',[]));check(b['operation_id']==o['id'])
for x in read(A/'typed-field-map.json'):
 b=next(b for b in bindings if b['scene_id']==x['scene_id']);v=records[b['record_id']]
 for k in x['pointer'].split('/')[1:]:v=v[int(k)]if isinstance(v,list)else v[k]
 check(v==x['quantity'])
check(read(A/'author-validation.json')['checks']==1486)
pre=read(A/'preview-manifest.json')
for scene in pre['scenes']:
 for prefix in ['svg','png','art_svg','art_png']:check(sha(A/scene[prefix+'_path'])==scene[prefix+'_sha256'])
for s in pre['contacts']+pre['art_contacts']:check(sha(A/s['path'])==s['sha256'])
module=(A/'friedfeld2019-protocol.mjs').read_text(encoding='utf-8');check('C:\\Users'not in module and 'C:/Users'not in module);check('__CONFIG__'not in module)
save('author-source-binding-validation.json',dict(status='passed_author_checks_not_independent_approval',checks=checks,source_generation=1,source_bundle=read(F/'intake-identity.json')['bundle_sha256'],bound_inputs=inputs,canonical_records_unchanged=True,source_files_unchanged=True))
targets=['friedfeld-2019-labeled-acid-synthesis--acid-charge','friedfeld-2019-kinetic-analysis--kinetic-analysis-analyze','friedfeld-2019-conversion-representative--heat-baseline','friedfeld-2019-conversion-concentration--sonicate-msc','friedfeld-2019-labeled-acid-synthesis--acid-acidify']
save('author-visual-inspection.json',dict(author='/root/norberg2004_extract',status='actual_static_previews_inspected',scope='All 58 art previews through 10 art contact sheets and all 58 full condition layouts through 15 full contact sheets; targeted final previews reopened after bounded layout corrections. Condition quantities additionally checked from actual executed module objects.',scene_count=58,art_contacts=pre['art_contacts'],full_contacts=pre['contacts'],targeted_final_previews=[x for x in pre['scenes']if x['scene_id']in targets],original_source_pages_actually_viewed=[dict(path=str(F/'source-render'/f'main-{i:02}.png'),sha256=sha(F/'source-render'/f'main-{i:02}.png'),scope='Original experimental apparatus, conversion, isotope synthesis and acquisition sections')for i in [6,7]],resolved_author_findings=['Wrapped the BnMgCl / 2-MeTHF label to remove left-edge clipping.','Moved the nitrogen arrow away from the illustrative thermowell; connected probe cable to the acquisition display.','Wrapped source-transformation labels inside their analysis card.','Kept all condition lists dynamically sized and formatted pH as an endpoint.'],scientific_scope=['Four-neck conversion and separate three-neck acid apparatus','External liquid-nitrogen, dry-ice/acetone and ice-water coolants; no invented numerical LN2 or room temperature','Three separate acid-workup fractions: organic filtrate, crude acid and isolated crystals','MSC precursor versus formed-material symbols and separated InP/In2O3 GPC contexts','Distinct condition alternatives and unreported changed-concentration charge','Thermal atmosphere unknown and local FFT not SAED'],mounted_browser_validation=False,independent_visual_audit=False))
pre['visual_review_status']='actual_author_static_inspection_complete_independent_audit_pending';save('preview-manifest.json',pre)
save('public-module-proposal.json',dict(status='private_proposal_pending_independent_audit',source_id='friedfeld2019',files=[dict(path=str(A/'friedfeld2019-protocol.mjs'),sha256=sha(A/'friedfeld2019-protocol.mjs'),suggested_site_relative_path='friedfeld2019-protocol.mjs')],dependency=dict(path=str(A/'quantity-value.mjs'),sha256=sha(A/'quantity-value.mjs'),import_path='./quantity-value.mjs',reuse_existing_source_neutral_helper=True),private_only=['records.json','canonical-bindings.json','typed-field-map.json','preview/contact files','author scripts and audit metadata'],no_original_source_asset_in_module=True))
(A/'README.md').write_text('''# Friedfeld 2019 apparatus author proposal

58 scene instances correspond exactly to 34 source operations in 19 records. The four conversion series are separately keyed; the 11 observation-only records intentionally have no apparatus scene. All 115 operation/alternative quantitative fields are preserved, with alternatives placed at their relevant stages. There are 269 displayed rows including scoped source notes.

The module exports `buildFriedfeld2019Scene`, `createFriedfeld2019Art`, `createFriedfeld2019ConditionGrid`, `renderFriedfeld2019Markup`, and `friedfeld2019SceneSelection`. Dispatch requires source group `friedfeld2019` plus exact record and operation IDs. The actual functions executed against deep-frozen canonical objects and a minimal DOM. Static SVG/PNG images were inspected. A mounted browser and Site integration were not tested here.

Only the public module listed in public-module-proposal.json is proposed for copying; its source-neutral quantity-value dependency must match. Do not publish the private record bundle or audit/provenance files as website assets. No original source pages, molecular graph, atomic model, synthetic diffraction pattern or spectrum was created by this package.

Source revision 2 has a distinct passed audit. Canonical/reader v2 remains a separately reviewed upstream gate; any later reader-only correction can be accompanied by an explicit unchanged-record receipt. This apparatus authorship does not approve its own science or publication.
''',encoding='utf-8')
files={str(p.relative_to(A)).replace('\\','/'):sha(p)for p in sorted(A.rglob('*'))if p.is_file()and p.name!='package-freeze.json'}
freeze=dict(schema='mattersyn-private-apparatus-freeze/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),author='/root/norberg2004_extract',status='frozen_author_proposal_pending_independent_audit',source_id='friedfeld2019',source_generation=1,canonical_freeze_sha256=sha(C/'package-freeze.json'),source_audit_sha256=sha(F/'source-independent-audit/independent-audit-v2.json'),counts=dict(record_contexts=19,operation_instances=58,distinct_source_operations=34,art_types=34,typed_quantities=115,condition_options=39,display_rows=269),bound_files=files,external_bound_inputs=inputs,approvals=dict(independent_apparatus_audit=False,mounted_browser=False,site_integration=False,training=False,publication=False))
save('package-freeze.json',freeze)
print(json.dumps(dict(package_sha256=sha(A/'package-freeze.json'),module_sha256=sha(A/'friedfeld2019-protocol.mjs'),bound_files=len(files),final_binding_checks=checks)))
