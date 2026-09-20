from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;P=B/'public-review-proposal'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(P/'besson2002.json');units=read(B/'source-audit.json')['units'];mapping=read(P/'source-item-mapping.json');coverage=read(P/'source-item-coverage.json');crop=read(B/'reader-assets/crop-manifest.json')
items={i['id']:i for s in d['reader_sections'] for i in s['items']};R={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};C=[]
def ck(n,v,detail=''):C.append({'check':n,'passed':bool(v),'detail':detail})
def ptr(x,p):
 for k in p.strip('/').split('/') if p else []:x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
ck('130 reader items',len(items)==130);ck('173 source units mapped',set(mapping)=={u['id'] for u in units} and len(mapping)==173)
ck('Current source inventory hash',coverage['source_audit_sha256']==sha(B/'source-audit.json'));ck('Coverage mapping exact',coverage['unit_to_reader_items']==mapping)
for uid,ids in mapping.items():
 ck(uid+'/valid reader targets',bool(ids) and set(ids)<=set(items))
 for i in ids:ck(uid+'/'+i+'/reverse link',uid in items[i]['source_audit_unit_ids'])
facts=[];links=[]
for i in items.values():
 ck(i['id']+'/source provenance',bool(i['evidence']) and all(e['source_id']=='besson2002' and e['document_role']=='main' and 1<=e['pdf_page']<=6 for e in i['evidence']))
 ck(i['id']+'/not automatic training',i['training_eligible'] is False);ck(i['id']+'/unknown physical batch',i['sample_scope']['physical_batch_id'] is None)
 for x in i['canonical_links']:
  try:ptr(R[x['record_id']],x['json_pointer']);ok=True
  except (KeyError,ValueError,IndexError):ok=False
  ck(i['id']+'/'+x['record_id']+x['json_pointer']+'/link resolves',ok);links.append(x)
 for f in i['facts']:
  facts.append(f);rid=f['canonical_record_id'];p=f['json_pointer'];obj=ptr(R[rid],p)
  if p.startswith('/measurements/'):
   q=obj['value'];ck(f['id']+'/exact sample',f['sample_id']==obj['sample_id']);ck(f['id']+'/measurement ID',f['canonical_measurement_id']==obj['id'])
  else:q=obj
  ck(f['id']+'/canonical value exact',f['canonical_quantity']==q);ck(f['id']+'/unit',f['unit']==q.get('unit'));ck(f['id']+'/approximation',f['approximate']==q.get('approximate',False));ck(f['id']+'/training excluded',f['training_eligible'] is False)
  if q.get('maximum_exclusive'):ck(f['id']+'/strict upper bound display','<' in str(f['value']) and q.get('value') is None)
  if q.get('minimum_exclusive'):ck(f['id']+'/strict lower bound display','>' in str(f['value']) and q.get('value') is None)
 for x in i['sample_scope'].get('canonical_sample_links',[]):ck(i['id']+'/'+x['sample_id']+'/sample pointer',ptr(R[x['record_id']],x['json_pointer'])['sample_id']==x['sample_id'])
expected_m={(rid,m['id']) for rid,r in R.items() for m in r['measurements']};actual_m={(f['canonical_record_id'],f['canonical_measurement_id']) for f in facts if 'canonical_measurement_id' in f}
ck('98 exact measurements covered',expected_m==actual_m and len(actual_m)==98)
expected_o={(rid,'/operations/'+str(j)) for rid,r in R.items() for j,o in enumerate(r['operations'])};actual_o={(x['record_id'],x['json_pointer']) for x in links if x['json_pointer'].startswith('/operations/') and x['json_pointer'].count('/')==2}
ck('36 operations covered',expected_o<=actual_o and len(expected_o)==36)
expected_p={(rid,'/operations/'+str(j)+'/parameters/'+k) for rid,r in R.items() for j,o in enumerate(r['operations']) for k in o['parameters']};actual_p={(f['canonical_record_id'],f['json_pointer']) for f in facts if f.get('basis')=='operation_parameter'}
ck('44 operation parameters covered',expected_p==actual_p and len(expected_p)==44)
expected_s=set()
for rid,r in R.items():
 for j,s in enumerate(r['stocks']):
  for k in s['concentrations']:expected_s.add((rid,f'/stocks/{j}/concentrations/{k}'))
  for n,c in enumerate(s['components']):
   for k in c['quantities']:expected_s.add((rid,f'/stocks/{j}/components/{n}/quantities/{k}'))
actual_s={(f['canonical_record_id'],f['json_pointer']) for f in facts if f['json_pointer'].startswith('/stocks/')}
ck('15 stock facts covered',expected_s==actual_s and len(expected_s)==15);ck('157 typed facts',len(facts)==157)
ck('All 43 references and notes',all(f'reference-{n:02}' in items for n in range(1,44)) and len(d['referenced_methods'])==43)
ck('Source ID',d['source_group']==d['paper_id']=='besson2002');ck('SI not claimed',d['review_scope']=='supplied_main_only_si_unverified' and d['supporting_information']['status']=='not_located_or_matched')
ck('Source bytes',d['documents'][0]['sha256']=='9f1b5b781e7a36f1ec109eb14ee724bb6c99a8156b4bc6899cfffe8ab613c357')
ck('Six-cycle endpoint scope','six is read from the figure' in items['copolymer-cycles']['text'])
ck('No acid/citrate/copolymer completion','acid identity' in items['water']['text'].lower() and 'not specified' in items['citrate']['text'] and 'unnamed' in items['copolymer-gap']['text'])
ck('No assumed ethanol ratio basis','basis' in items['ethanol-dilution']['text'] and 'unspecified' in items['ethanol-dilution']['text'])
ck('Symbolic H2S pressure retained','P(H₂S) = P(atmosphere)' in items['gas-precipitation']['text'])
ck('Mesoscopic versus atomic distinction','must not be presented as a CdS unit cell' in items['host-vs-crystal']['text'])
ck('Fourier power not SAED','not a selected-area electron diffraction' in items['image-power']['text'])
ck('Correct index notation','[1 1 −2 0]' in items['tem-orientation']['text'] and '(0 1 −1 1)' in items['figure3-panels']['text'])
ck('c discrepancy explicit','6.8 nm' in items['mesostructure-comparison']['text'] and '7.2 nm' in items['mesostructure-comparison']['text'])
ck('PL conflict explicit','conflict' in items['figure4-axes']['text'] and 'not converted' in items['pl-figure-conflict']['text'])
ck('No assumed exact film occupancy','100%' in items['hrtem-empty-pores']['text'] and 'not converted' in items['hrtem-empty-pores']['text'])
ck('Unpublished dependency retained','to be published' in items['reference-37']['text'])
ck('Component evidence scoped','not bare-silica properties' in d['material_evidence_scope_notes']['SiO2'] and 'not bare-CdS atomic' in d['material_evidence_scope_notes']['CdS'])
audited=read(B/'canonical-records-audit.json')['record_hashes']
for rid,h in audited.items():ck(rid+'/frozen canonical bytes',sha(B/'canonical-drafts'/(rid+'.json'))==h)
assets=d['figures']+d['tables']+d['source_notes'];ac={x['id']:x for x in assets};cm={x['id']:x for x in crop['assets']}
ck('Ten original assets',len(ac)==len(cm)==10 and set(ac)==set(cm));rows=[]
for aid,a in ac.items():
 c=cm[aid];h=sha(B/'reader-assets'/c['relative_asset']);ck(aid+'/exact crop',h==a['public_asset_sha256']==c['sha256']);ck(aid+'/source page',a['page']==c['source_pdf_page'] and a['asset_provenance']['source_sha256']==c['source_sha256']==d['documents'][0]['sha256'])
 ck(aid+'/sample links',set(a['sample_links'])<=set(R));ck(aid+'/crop provenance',a['asset_provenance']['crop_bbox_pdf_points_top_left']==c['crop_bbox_pdf_points_top_left']);ck(aid+'/training not automatic',a['training_eligible'] is False)
 rows.append({'id':aid,'sha256':h,'page':a['page'],'sample_links':a['sample_links'],'source_correspondence':'passed','visual_review':'Actually viewed this original PNG individually. Full six-page source independently viewed earlier. Original panel letters, source axes, scales, captions and method continuations retained; no redraw.'})
ck('Figure 1 distinct host cohorts',ac['figure-1']['sample_links']==['besson-2002-ctab-cds-loading','besson-2002-copolymer-cds-loading','besson-2002-uv-visible'])
for n,r in [(2,'xrd'),(3,'hrtem'),(4,'pl-silicon')]:ck(f'Figure {n}/source-specific analytical record',ac[f'figure-{n}']['sample_links']==['besson-2002-'+r])
ck('Figure4 conflict evidence class',ac['figure-4']['evidence_class']=='experimental_with_source_assignment_conflict')
ck('Fourier definition binds HRTEM only',ac['power-spectrum-definition']['sample_links']==['besson-2002-hrtem'])
for refs in d['material_evidence_records'].values():ck('Material links resolve',set(refs)<=set(R))
manual=[
'All 130 reader prose items, all 43 bibliographic entries/notes, all 173 unit-to-item mappings, source/claim/sample metadata and ten asset descriptions were independently compared with the full six-page source and canonical records. The ten actual PNG crops were individually inspected in this audit.',
'Host synthesis preserves TEOS/water/ethanol ratio, initial-water pH, sol aging, CTAB templating, unspecified-basis dilution, spin speed and air calcination. Unreported acid, doses, durations and ramps remain blank. The unnamed copolymer host is not silently assigned the CTAB recipe.',
'Cadmium nitrate starting concentration, separate citrate-stock concentration, one-equivalent initial ammonia and further pH adjustment are distinct. Final bath concentration and Cd complex identity are unresolved. Liquid adsorption, rinse, evacuation and slow gas admission are separate stages; the symbolic atmospheric endpoint does not become an exact pressure or H2S amount.',
'Two host series retain different optically inferred diameters and cycle scopes. Nine CTAB cycles are stated in prose; six is a figure endpoint contextually associated with copolymer saturation. Repetition is not independent physical batch replication. The zero-cycle marker is not a measured zero-size particle.',
'All four figures retain complete panels, axes, labels and captions. Figure 2 display multipliers 0.5 and 5 are retained. Figure 3 scale bars remain distinct from particle size; panel d is image Fourier power, not SAED. The [1 1 −2 0] projection and third-index negative spot labels were checked against the original image.',
'P6₃/mmc, a≈6 nm and c≈6.8 nm refer to mesoscopic pore/particle ordering; local 111 blende fringes are a separate atomic CdS claim. No atomic CIF, common orientation or refined phase fraction is invented. XRD saturated c=7.2 nm versus HRTEM c≈6.8 nm remains unresolved.',
'The 3.5 nm comparator/pore model and 3.6 nm optical endpoint remain separate. Derived 13% CdS volume, 15% pore volume and rounded ~85% filling are preserved alongside residual empty pores. Reference 38 is an incomplete reverse-micelle comparator citation, not an invented complete synthesis route.',
'Silicon-supported photoluminescence remains separate from Pyrex preparation. Body-assigned first-H2S and next-Cd states are not silently joined to conflicting Figure 4 upper/lower curves. 640/450 nm are emission claims, not chosen excitation wavelengths. Vacancy/passivation/wall-interaction mechanisms are author interpretations, without resolved surface species or quantitative yields.',
'Historical materials, cited recipes, hypotheses and potential sulfide/selenide extensions remain context. Main text is completely inspected; no local SI matched and no claim that SI cannot exist. Original source spelling/abbreviation quirks and unpublished reference 37 remain visible. Publication/browser verification is parent-owned.'
]
fail=[c for c in C if not c['passed']]
report={'status':'passed' if not fail else 'failed','source_id':'besson2002','audited_utc':datetime.now(timezone.utc).isoformat(),'reader_sha256':sha(P/'besson2002.json'),'source_inventory_sha256':sha(B/'source-audit.json'),'source_identity_sha256':sha(B/'source-identity.json'),'source_item_mapping_sha256':sha(P/'source-item-mapping.json'),'source_item_coverage_sha256':sha(P/'source-item-coverage.json'),'canonical_measurement_coverage_sha256':sha(P/'canonical-measurement-coverage.json'),'crop_manifest_sha256':sha(B/'reader-assets/crop-manifest.json'),'record_hashes':audited,'item_count':130,'source_unit_count':173,'measurements':98,'operations':36,'typed_facts':157,'asset_count':10,'manual_source_review':manual,'resolved_findings':['Canonical pre-H2S cadmium-adsorbed composition no longer misidentified as CdS.','Six-cycle copolymer endpoint is inferred from the figure, distinct from author-derived saturation diameter.'],'check_count':len(C),'failure_count':len(fail),'checks':C,'failures':fail,'assets':rows,'limits':['Source and scientific correspondence audit only. Parent owns integrated page rendering, interactions, exports and publication.','No matched SI or cited external full text reviewed; absence remains explicit.'],'browser_verified':False,'site_mutated':False}
(B/'reader-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'reader-source-audit.md').write_text('# Besson 2002 independent reader audit\n\n'+report['status']+f': 130 items, 173 source units, 98 measurements, 36 operations, 157 typed facts and ten original assets; {len(C)} checks, {len(fail)} failures.\n\n'+'\n\n'.join(manual)+'\n\nExact hashes are in reader-source-audit.json. No Site mutation or browser verification performed.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'reader_sha256':report['reader_sha256'],'check_count':len(C),'failures':fail},ensure_ascii=False))
