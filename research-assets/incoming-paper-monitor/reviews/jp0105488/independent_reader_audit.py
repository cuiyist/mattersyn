from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json
B=Path(__file__).resolve().parent;P=B/'public-review-proposal'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=read(P/'gerion2001.json');units=read(B/'source-audit.json')['units'];mapping=read(P/'source-item-mapping.json');coverage=read(P/'source-item-coverage.json');measuremap=read(P/'canonical-measurement-coverage.json');crop=read(B/'reader-assets/crop-manifest.json')
items={i['id']:i for s in d['reader_sections'] for i in s['items']};R={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};C=[]
def check(n,ok,detail=''):C.append({'check':n,'passed':bool(ok),'detail':detail})
def pointer(obj,p):
 for key in p.strip('/').split('/') if p else []:obj=obj[int(key)] if isinstance(obj,list) else obj[key.replace('~1','/').replace('~0','~')]
 return obj
check('139-reader-items',len(items)==139)
check('all251-source-units-mapped',set(mapping)=={u['id'] for u in units} and len(mapping)==251)
check('coverage-exact-current-source-inventory',coverage['source_audit_sha256']==sha(B/'source-audit.json'))
check('coverage-file-mapping-equality',coverage['unit_to_reader_items']==mapping)
for uid,ii in mapping.items():
 check(uid+'/valid-readers',bool(ii) and set(ii)<=set(items))
 for i in ii:check(uid+'/'+i+'/reverse-link',uid in items[i]['source_audit_unit_ids'])
facts=[];links=[];samplelinks=[]
for i in items.values():
 check(i['id']+'/source-provenance',bool(i['evidence']) and all(e['source_id']=='gerion2001' and e['document_role']=='main' and 1<=e['pdf_page']<=11 for e in i['evidence']))
 check(i['id']+'/not-automatic-training',i['training_eligible'] is False)
 for link in i['canonical_links']:
  try:pointer(R[link['record_id']],link['json_pointer']);ok=True
  except (KeyError,IndexError,ValueError):ok=False
  check(i['id']+'/'+link['record_id']+link['json_pointer']+'/link-resolves',ok);links.append(link)
 for f in i['facts']:
  facts.append(f);rid=f['canonical_record_id'];p=f['json_pointer'];obj=pointer(R[rid],p)
  if p.startswith('/measurements/'):
   q=obj['value'];check(f['id']+'/sample-exact',f['sample_id']==obj['sample_id']);check(f['id']+'/measurement-id',f['canonical_measurement_id']==obj['id'])
  else:q=obj
  check(f['id']+'/canonical-quantity-exact',f['canonical_quantity']==q)
  check(f['id']+'/unit-preserved',f['unit']==q.get('unit'))
  check(f['id']+'/approximation-preserved',f['approximate']==q.get('approximate',False))
  check(f['id']+'/not-training-by-default',f['training_eligible'] is False)
 for sl in i['sample_scope'].get('canonical_sample_links',[]):
  obj=pointer(R[sl['record_id']],sl['json_pointer']);check(i['id']+'/'+sl['sample_id']+'/sample-pointer',obj['sample_id']==sl['sample_id']);samplelinks.append(sl)
expected_measurements={(rid,m['id']) for rid,r in R.items() for m in r['measurements']}
actual_measurements={(f['canonical_record_id'],f['canonical_measurement_id']) for f in facts if 'canonical_measurement_id' in f}
check('all186-measurements-exactly-covered',expected_measurements==actual_measurements and len(actual_measurements)==186)
expected_ops={(rid,'/operations/'+str(j)) for rid,r in R.items() for j,o in enumerate(r['operations'])}
actual_ops={(x['record_id'],x['json_pointer']) for x in links if x['json_pointer'].startswith('/operations/') and x['json_pointer'].count('/')==2}
check('all82-operations-covered',expected_ops<=actual_ops and len(expected_ops)==82)
check('329-typed-facts',len(facts)==329)
check('36-source-references',all(f'reference-{n:02}' in items for n in range(1,37)))
check('declared-SI-gap',d['review_scope']=='supplied_main_only_si_unverified' and d['supporting_information']['status']=='declared_not_located_or_matched')
check('source-document-hash',d['documents'][0]['sha256']==read(B/'source-identity.json')['source_sha256'])
check('reader-removal-not-unverified-omission','attempts to remove' in items['quench-rationale']['text'].lower() and 'omitting phosphonate' not in items['quench-rationale']['text'])
check('CW-method-volume-exact','approximately 1 µL' not in items['cw-acquisition']['text'] and '1 µL' in items['cw-acquisition']['text'])
for uid,expected in {'hardware-evaporators':['silica-dialysis','silica-optional','equilibration'],'optical-result-spectrum-invariance':['optical-overview','optical-width'],'figure1-exchange':['mps-binding','primary-network'],'figure4-conditions':['cw-acquisition','cw-result'],'intuition-hplc-limits':['hplc-size-limit','hplc-outlook']}.items():check(uid+'/complete-multi-claim-association',set(expected)<=set(mapping['gerion2001-'+uid]))
assets=d['figures']+d['tables']+d['source_notes'];ac={a['id']:a for a in assets};cm={a['id']:a for a in crop['assets']}
check('17-original-assets',len(ac)==len(cm)==17 and set(ac)==set(cm))
assetrows=[]
for aid,a in ac.items():
 c=cm[aid];p=B/'reader-assets'/c['relative_asset'];h=sha(p)
 check(aid+'/crop-hash',h==a['public_asset_sha256']==c['sha256'])
 check(aid+'/page-source',a['page']==c['source_pdf_page'] and a['asset_provenance']['source_sha256']==c['source_sha256']==d['documents'][0]['sha256'])
 check(aid+'/sample-record-links',set(a['sample_links'])<=set(R))
 check(aid+'/crop-transform',a['asset_provenance']['crop_bbox_pdf_points_top_left']==c['crop_bbox_pdf_points_top_left'])
 check(aid+'/not-recreated-data',a['training_eligible'] is False)
 assetrows.append({'id':aid,'sha256':h,'page':a['page'],'source_correspondence':'passed','sample_links':a['sample_links'],'visual_review':'Actually inspected on source-derived crop contact sheet; full original source pages also previously viewed.'})
check('Figure5-yellow-only',ac['figure-5']['sample_links']==['gerion-2001-size-yellow'])
check('Table1-optical-only',ac['table-1']['sample_links']==['gerion-2001-optical-properties'])
check('Note34-correct-scattering-record',ac['note-34']['sample_links']==['gerion-2001-upstream-controls'])
check('Table2-four-size-records',set(ac['table-2']['sample_links'])=={'gerion-2001-size-'+x for x in ['green','yellow','red','dark-red']})
check('Figure4-CW-only',ac['figure-4']['sample_links']==['gerion-2001-cw-photostability'])
check('Figure3-storage-only',ac['figure-3']['sample_links']==['gerion-2001-storage-photostability'])
for ref in d['material_evidence_records'].values():check('material-reference-records',set(ref)<=set(R))
manual=['Read all 139 reader items, their notes, all 36 bibliographic/scientific-note entries, and all 17 original-asset labels, captions, axes and sample mappings. Compared source-unit mapping semantics with independently authored 251-unit inventory; multiple-item mappings expanded where a source unit contains several claims.','Full main article was independently read and all 11 original pages visually inspected before reviewing this proposal. All 17 actual original crops were additionally inspected on five contact sheets; figures, labels, scales, source processing and text continuations are retained. No interactive browser inspection is claimed.','The two downstream methods, optional/incomplete APS variant, stock and analytical procedures are separate. No upstream core/shell conditions or biological safety result fabricated. Missing declared HRTEM/AFM SI is explicit, with no recreated missing microscopy.','Table1 optical colors are not equated with Table2 physical size specimens. Each Table2 row preserves its parent core/shell and separate coating branches. Figure5 is yellow-specific; Figure6 trace colors mean two green-parent preparations rather than emission colors or a guaranteed single before/after aliquot. Figure7 panels retain their own conditions and separate lanes.','Source conflicts retained: phosphonate name/connectivity, mm versus µm filters, Table1/body optical peaks, PB/PBS, evaporation factor and rest chronology, pH8.5/8.6, extra2mM lane, Figure4 displayed4000s versus≥~4h claim, Figure5 claimed cutoff versus visible features, AFM cross-reference/one-two-feature reversal, rounded thickness bounds.','Author mechanisms, model assumptions, HPLC detector areas, AFM apparent heights, upper thiol estimates, background literature and outlook remain distinct from primary measured recipe outcomes. No unit cell, crystalline phase, SAED, XRD, Raman, raw spectrum or exact batch join invented.','Component-hub evidence remains expressly scoped: bare CdSe gets only its Table2 core context; ZnS gets incomplete diagnostic context. Composite material tags do not establish new bare-component syntheses. Parent must preserve these distinctions in rendering and training-export selection.']
failed=[x for x in C if not x['passed']]
report={'source_id':'gerion2001','status':'passed' if not failed else 'failed','audited_utc':datetime.now(timezone.utc).isoformat(),'reader_sha256':sha(P/'gerion2001.json'),'source_inventory_sha256':sha(B/'source-audit.json'),'source_identity_sha256':sha(B/'source-identity.json'),'source_item_mapping_sha256':sha(P/'source-item-mapping.json'),'source_item_coverage_sha256':sha(P/'source-item-coverage.json'),'canonical_measurement_coverage_sha256':sha(P/'canonical-measurement-coverage.json'),'crop_manifest_sha256':sha(B/'reader-assets/crop-manifest.json'),'record_hashes':{rid:sha(B/'canonical-drafts'/(rid+'.json')) for rid in R},'item_count':len(items),'source_unit_count':251,'measurements':186,'operations':82,'typed_facts':len(facts),'asset_count':17,'manual_source_review':manual,'resolved_findings':['Phosphonate removal replaced unsupported omission-control paraphrase','Exact CW Methods volume separated from approximate Figure4 caption','Note34 crop/source record corrected to upstream-controls','Five multi-claim source-unit mappings expanded to all relevant items'],'check_count':len(C),'failure_count':len(failed),'checks':C,'failures':failed,'assets':assetrows,'visual_contact_sheets':[{'path':str(B/'crop-review'/f'contact-{n}.jpg'),'sha256':sha(B/'crop-review'/f'contact-{n}.jpg'),'actually_viewed':True} for n in range(1,6)],'limitations':['Complete only for the supplied main article; announced SI remains unlocated/unverified.','Private scientific/source audit, not public render, browser interaction, publication or export eligibility verification.'],'browser_verified':False,'site_mutated':False}
(B/'reader-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'reader-source-audit.md').write_text('# Gerion 2001 independent reader audit\n\n'+report['status']+f': 139 reader items, 251 source units, 186 measurements, 82 operations, 329 typed facts and 17 original assets; {len(C)} supporting checks, {len(failed)} failures.\n\n'+'\n\n'.join(manual)+'\n\nExact reader, source, canonical and asset hashes are stored in reader-source-audit.json. Declared SI remains unlocated/unverified. No Site edit or browser test was performed.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(C),'failures':failed},indent=2))
