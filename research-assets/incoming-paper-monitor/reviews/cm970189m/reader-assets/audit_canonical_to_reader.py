"""Bounded Veinot reader audit. --preflight checks private mappings only.

Default requires integrated Site data and a completed independent scientific
audit. Source and Site are read-only; only this private folder receives reports.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import argparse,json,hashlib,re,html,sys
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;B=OUT.parent;SITE=B.parents[3]/'recipe-atlas';SID='veinot1997'
sys.path.insert(0,str(SITE/'scripts'))
from dataset_lib import validate_record,eligibility,training_view,fmt,digest,build_groups
from build_atlas import synthesis_route
from build_paper_reviews import validate as validate_review
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s))).strip()
def ptr(v,p):
 for k in p.split('/')[1:]:v=v[int(k)] if isinstance(v,list) else v[k.replace('~1','/').replace('~0','~')]
 return v
def diff(a,b,p=''):
 if type(a)!=type(b):return [p]
 if isinstance(a,dict):return [q for k in a.keys()|b.keys() for q in ([p+'/'+k] if k not in a or k not in b else diff(a[k],b[k],p+'/'+k))]
 if isinstance(a,list):return [p] if len(a)!=len(b) else [q for i,(x,y) in enumerate(zip(a,b)) for q in diff(x,y,p+'/'+str(i))]
 return [] if a==b else [p]
def reader_ids(rid,m):
 mid=m['id'];c=m['sample_id'].removeprefix('compound-')
 if rid.endswith('-qdoh'):return ['qdoh-isolation']
 if rid.endswith('-unfunctionalized-control') and mid=='no-reaction':return ['unfunctionalized-control']
 if '-nmr-' in mid:return ['nmr-row-'+c]
 if re.match(r'\w+-ir-\d+$',mid):return ['ir-row-'+c]
 if mid.endswith(('-conversion','-reaction-time','-yield')):return ['nmr-row-'+c,'nmr-table']
 if '-solubility-' in mid:return ['solubility-qdoh' if c=='1' else 'solubility-derivatives']
 if mid.endswith(('-absorption','-model-diameter','-tem-diameter')):return ['optical-size-series','tem-diameter-series']
 if mid in ['1-methods-edge','1-methods-shoulder','1-gap','1-bulk-gap','1-shift']:return ['qdoh-absorption-conflict']
 if mid.startswith('1-methods-ir-') or mid in ['1-sh-absence','1-phenol-ir-body']:return ['qdoh-ir']
 if mid in ['1-oh-exchange','1-nmr-integration']:return ['qdoh-nmr-exchange']
 if mid in ['1-thiol-sulfur-20','1-thiol-sulfur-34','1-density','1-caps','1-coverage','1-sphere-area','1-model-d']:return ['cap-gravimetry']
 if mid=='1-molarity':return ['absorption-acquisition']
 if mid=='1-tem-uncertainty':return ['tem-diameter-series']
 if mid=='1-aggregate-body':return ['aggregation']
 if mid=='1-figure6-scale':return ['tem-acquisition']
 if mid=='1-tyndall':return ['qdoh-dispersion']
 raise AssertionError('Unmapped measurement: '+rid+'/'+mid)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--preflight',action='store_true');args=ap.parse_args()
 checks=[];hashes={};joins=[];promotions={}
 def check(n,ok,d=''):checks.append({'name':n,'passed':bool(ok),'detail':d})
 def bind(p):hashes[str(p.relative_to(SITE)) if p.is_relative_to(SITE) else 'private/'+str(p.relative_to(B))]=sha(p)
 proposal=read(B/'public-review-proposal/veinot1997.json');source=read(B/'source-audit.json');coverage=read(B/'public-review-proposal/source-item-coverage.json')
 drafts={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
 records=drafts if args.preflight else {rid:read(SITE/'data/records'/f'{rid}.json') for rid in drafts}
 ledger=proposal if args.preflight else read(SITE/'data/paper-reviews/veinot1997.json')
 items={i['id']:i for s in ledger['reader_sections'] for i in s['items']};olditems={i['id']:i for s in proposal['reader_sections'] for i in s['items']}
 routeids={'veinot-1997-qdoh'}|{'veinot-1997-ester-2'+x for x in 'abcde'}
 check('21records232measurements133operations',len(records)==21 and sum(len(r['measurements']) for r in records.values())==232 and sum(len(r['operations']) for r in records.values())==133)
 check('Actual21record types',Counter(r['record_type'] for r in records.values())==Counter(literature_protocol=6,procedure=11,protocol_variant=1,observation=3))
 audited=None;mr={}
 if not args.preflight:
  audited=read(B/'canonical-records-audit.json');ah={r['record_id']:r for r in audited['records']};manifest=read(SITE/'dist/data/dataset-manifest.json');mr={r['record_id']:r for r in manifest['records']}
  check('Independent scientific audit completed',audited['status'].startswith('passed') and not audited['open_findings'] and not audited['failed_checks'])
 for rid,r in records.items():
  dp=B/'canonical-drafts'/f'{rid}.json';bind(dp);err=validate_record(r);check(rid+' schema and graph',not err,repr(err))
  check(rid+' no unreported phase filled',r['intended_target']['phase']['value'] is None and all(p['phase']['value'] is None for p in r['products']))
  check(rid+' no measured structure invented',not any(a['eligible_as_measured_label'] for a in r['structure_assets']))
  check(rid+' source compound classes not physical batches',r['lineage']['batch_id'] is None and all(p['batch_id'] is None for p in r['products']))
  text='';rows=[]
  if not args.preflight:
   rp=SITE/'data/records'/f'{rid}.json';gp=SITE/'dist/data/records'/f'{rid}.json';hp=SITE/'dist/records'/f'{rid}.html'
   for p in [rp,gp,hp]:bind(p)
   check(rid+' exact audited draft hash',sha(dp)==ah[rid]['sha256'])
   dd=diff(drafts[rid],r);promotions[rid]=dd
   check(rid+' only authorized status promotion',set(dd)<={'/quality/review_status','/quality/review_scope','/quality/requested_tasks','/sources/0/main_status'},repr(dd))
   check(rid+' generated bytes and manifest digest',rp.read_bytes()==gp.read_bytes() and mr[rid]['record_sha256']==digest(r))
   check(rid+' source-reviewed and SI unverified',r['quality']['review_status']=='source_reviewed' and 'SI not located or verified' in r['quality']['review_scope'])
   wanted={'precursor_selection','partial_protocol'} if rid in routeids else set()
   check(rid+' actual eligibility matches scope',{k for k,v in eligibility(r).items() if v['eligible']}==wanted and mr[rid]['eligibility']==eligibility(r))
   raw=hp.read_text(encoding='utf-8');text=plain(raw);rows=[plain(x) for x in re.findall(r'<tr>(.*?)</tr>',raw,re.S)]
   check(rid+' source link, type and SI scope visible','paper-review.html?id='+SID in raw and r['record_type'].replace('_',' ') in text and 'SI not located or verified' in text)
   for o in r['operations']:
    if o['description']:check(rid+'/'+o['id']+' operation prose rendered',plain(o['description']) in text)
   for task in wanted:
    v=training_view(r,task)
    check(rid+'/'+task+' target inputs only',set(v['input'])<= {'composition','method','requested_surface'} and v['input']['composition']=='CdS')
    if r['intended_target']['surface']['value'] is not None:check(rid+'/'+task+' explicit requested surface retained',v['input'].get('requested_surface')==r['intended_target']['surface'])
    if task=='partial_protocol':check(rid+' missing fields retained',v['output']['missing_fields']==r['quality']['missing_fields'] and bool(v['output']['missing_fields']))
    if task=='precursor_selection' and '-ester-' in rid:check(rid+' starting functional dot and acyl reagent retained',{p['role'] for p in v['output']['precursors']}=={'seed','surface_functionalization_reagent'})
  for m in r['measurements']:
   labels=reader_ids(rid,m);qual='unit' not in m['value']
   check(rid+'/'+m['id']+' source-reader semantic join',all(k in items and rid in {c['record_id'] for c in items[k]['canonical_links']} for k in labels))
   check(rid+'/'+m['id']+' product resolves',m['sample_id'] in {p['sample_id'] for p in r['products']})
   if not args.preflight:check(rid+'/'+m['id']+' '+('qualitative fact' if qual else 'quantity')+' rendered',any(m['property'].replace('_',' ') in row and plain(fmt(m['value'])) in row and m['sample_id'] in row for row in rows))
   joins.append({'record_id':rid,'measurement_id':m['id'],'sample_id':m['sample_id'],'property':m['property'],'value_kind':'qualitative_fact' if qual else 'quantity','reader_item_ids':labels,'evidence':m['evidence']})
 check('30 qualitative facts and202quantities',Counter(j['value_kind'] for j in joins)==Counter(qualitative_fact=30,quantity=202))
 organic=['pyrenecarbonyl-chloride']+['acylimidazole-3'+x for x in 'abcde']
 for k in organic:
  r=records['veinot-1997-'+k]
  check(k+' organic target separate from CdS context',r['material']['formula']=='CdS' and r['intended_target']['composition']['value']!='CdS' and all(p['composition']['value']!='CdS' for p in r['products']))
 for x in 'bcde':
  r=records['veinot-1997-ester-2'+x]
  check('2'+x+' missing charges not inherited',all(m['quantities']['mass']['value'] is None for m in r['materials'] if m['id'] in ['qdoh','3'+x]))
  check('2'+x+' no170mg prose inherited',not re.search(r'\b170\s*mg',json.dumps(r['operations'])))
 check('QDOH main temperature missing rather than inherited',any('reaction temperature' in s.lower() for s in records['veinot-1997-qdoh']['quality']['missing_fields']))
 check('All141sourceunits and101readeritems',len(coverage['source_audit_unit_map'])==141 and len(items)==101)
 for u in coverage['source_audit_unit_map']:check('Source unit '+u['source_audit_id'],ptr(source,u['source_audit_pointer'])['id']==u['source_audit_id'] and all(bool(ptr(ledger,p)) for p in u['public_targets']))
 for u in coverage['reader_units']:check('Reader unit '+u['source_item_id'],ptr(ledger,u['target'])['id']==u['source_item_id'])
 for key,i in items.items():
  if not args.preflight:check(key+' reader science unchanged',all(re.fullmatch(r'/canonical_links/\d+/relation',p) for p in diff(olditems[key],i)),repr(diff(olditems[key],i)))
  for p in i['sample_scope'].get('canonical_sample_links',[]):check(key+'/'+p['sample_id']+' exact compound pointer',ptr(records[p['record_id']],p['json_pointer'])['sample_id']==p['sample_id'])
 check('Three complete tables unchanged',[t['structured_rows'] for t in ledger['tables']]==[t['structured_rows'] for t in proposal['tables']] and [len(t['structured_rows']) for t in ledger['tables']]==[11,6,6])
 check('Methods absorption andIR discrepancies visible',all(s in items['qdoh-absorption-conflict']['text'] for s in ['295 nm','305 nm','390 nm']) and all(s in items['qdoh-ir']['text'] for s in ['3302','3301','1734','1730']))
 check('No nonexistent Eq1 supplied',not ledger['equations'] and 'no corresponding numbered equation' in next(c for c in ledger['evidence_conflicts'] if c['id']=='conflict-12')['text'].lower())
 check('Fifteen references include two direct notes',len(ledger['referenced_methods'])==15 and [r['reference_number'] for r in ledger['referenced_methods'] if r['direct_source_note_reviewed']]==[10,15])
 assets=[*ledger['figures'],*ledger['tables'],*ledger['schemes']]
 original={p['relative_asset']:p for p in read(B/'crop-assets/manifest.json')['assets']}
 check('Eleven originalassets6figs3tables1scheme1illustration',len(assets)==11 and [len(ledger[k]) for k in ['figures','tables','schemes']]==[6,3,2])
 for a in assets:
  p=B/'crop-assets'/Path(a['public_asset']).name if args.preflight else SITE/'dist'/a['public_asset'];bind(p)
  check(a['id']+' original hash and scope',sha(p)==a['public_asset_sha256']==original[p.name]['sha256'] and bool(a['sample_scope']) and bool(a['quantitative_context']) and not a['training_eligible'])
 inventory=None;hubinfo=None;totals=None
 if not args.preflight:
  error=validate_review(ledger);check('Actual source ledger validator',not error,repr(error))
  generated=read(SITE/'dist/data/paper-reviews/veinot1997.json');generated.pop('review_scope_label',None);check('Generated source ledger matches',generated==ledger)
  runtime=read(OUT/'reader-runtime-check.json');check('Source renderer runtime',runtime['status']=='passed' and runtime['reader_items']==101 and runtime['unique_original_assets']==11)
  check('Runtime current module/ledger bindings',all(sha(SITE/p)==h for p,h in runtime['artifact_sha256'].items()))
  allr=[read(p) for p in (SITE/'data/records').glob('*.json')];groups=build_groups(allr)
  check('One evaluationgroup andsplit for entire source',len({groups[rid] for rid in records})==len({mr[rid]['split'] for rid in records})==1)
  totals={k:sum(eligibility(r)[k]['eligible'] for r in allr) for k in eligibility(allr[0])}
  check('No added size/exact/success/optical labels',totals==read(SITE/'dist/data/validation-report.json')['eligible_by_task'] and {k:totals[k] for k in ['size_conditioned_recipe','exact_structure_recipe','success_prediction','optical_outcome']}==dict(size_conditioned_recipe=6,exact_structure_recipe=0,success_prediction=0,optical_outcome=95))
  index=read(SITE/'dist/data/materials-index.json');hmeta=next(h for h in index['materials'] if h['formula']=='CdS');hp=SITE/'dist/data/materials'/f'{hmeta["id"]}.json';bind(hp);hub=read(hp)
  check('CdS directhub contains six new routes only',not hub['component_only'] and set(hub['record_ids'])&records.keys()==routeids and set(hub['direct_record_ids'])&records.keys()==routeids)
  evidence={e['record_id'] for e in hub['evidence_records'] if e['record_id'] in records}
  check('All21 typed contributions with source scope',evidence==set(ledger['material_evidence_records']['CdS'])==set(records) and all(e['record_type']==records[e['record_id']]['record_type'] for e in hub['evidence_records'] if e['record_id'] in records))
  check('CdS source review remains mainonly',next(p for p in hub['papers'] if p['doi']=='10.1021/cm970189m')['fullDocumentReview']['scope']=='supplied_main_only_si_unverified')
  ordered=[r['record_id'] for r in hub['records'] if r.get('is_synthesis_route')]
  expected_order=['veinot-1997-qdoh']+['veinot-1997-ester-2'+x for x in 'abcde']
  check('CdS reader route order starts QDOH then2a–e',ordered[:6]==expected_order)
  check('Prior CdSe/CdS component routes remain',set(ordered[6:])=={'dabbousi-1997-cds-overgrowth','nakonechnyi-2017-wz-cdse-cds-seeded-growth','nakonechnyi-2017-zb-cdse-cds-seeded-growth'})
  check('Hub renders data.records order',"for(const r of data.records.filter" in (SITE/'dist/material-hub.mjs').read_text(encoding='utf-8'))
  hubinfo={'id':hub['id'],'new_routes':sorted(routeids),'source_evidence_records':len(evidence),'component_only':hub['component_only']}
  chem=SITE/'dist/assets/chemical-registry';bindings=read(chem/'bindings.json');entries={e['id']:e for e in read(chem/'registry.json')['entries']};entryids=set()
  for rid,r in records.items():
   bb=bindings['recordBindings'][rid];entryids.update(bb.values());check(rid+' complete molecular bindings',set(bb)=={m['id'] for m in r['materials']} and bindings['sourceRecordSha256'][rid]==sha(SITE/'data/records'/f'{rid}.json'))
  for eid in entryids:
   e=entries[eid]
   for k in ['svgPath','model2dPath','model3dPath']:
    if e.get(k):p=chem/e[k];bind(p);check(eid+'/'+k+' actual model bytes',sha(p)==e['assetHashes'][k])
  product_refs=read(chem/'product-bindings.json');pb={rid:eid for rid,eid in product_refs['recordBindings'].items() if rid in records}
  check('Twelve intended product references only',set(pb)==routeids|{'veinot-1997-'+k for k in organic})
  for rid,eid in pb.items():
   e=entries[eid];r=records[rid]
   check(rid+' product identity matches intended composition',e['formula']==r['intended_target']['composition']['value'])
   check(rid+' product depiction is qualified',bool(e['caption']) and bool(e['limitations']))
   if rid in routeids:check(rid+' surface motif has no fabricated3Dsample',e['model3dPath'] is None and e['provenance']['measured_coordinates'] is False)
   for key in ['svgPath','model2dPath','model3dPath']:
    if e.get(key):p=chem/e[key];bind(p);check(rid+'/'+key+' product asset hash',sha(p)==e['assetHashes'][key])
  product_runtime=read(OUT/'product-runtime-check.json')
  check('Product cards and isotope label runtime passed',product_runtime['status']=='passed' and len(product_runtime['product_cards'])==12 and len(product_runtime['isotope_labels'])==3)
  check('Product runtime binds current files',all(sha(SITE/p)==h for p,h in product_runtime['artifact_sha256'].items()))
  inv=read(SITE/'data/inventory-summary.json');s=inv['summary'];rr={r['record_id']:r for r in allr};routes={rid for rid,r in rr.items() if synthesis_route(r)};benchmark={rid for rid in rr if mr[rid]['collection']=='published_benchmark'};lit=set(rr)-benchmark;procs={rid for rid in lit if rr[rid]['record_type']=='procedure'};obs={rid for rid in lit if rr[rid]['record_type']=='observation'};controls=lit-routes-procs-obs
  counts={'canonical_records':len(rr),'synthesis_route_variant_records':len(routes),'contextual_control_variant_records':len(controls),'shared_preparation_workup_characterization_assay_procedures':len(procs),'contextual_observation_records':len(obs),'published_benchmark_rows':len(benchmark),'public_material_hubs':len(index['materials']),'direct_synthesis_target_systems':sum(not h['component_only'] for h in index['materials']),'component_only_hubs':sum(h['component_only'] for h in index['materials']),'total_canonical_source_groups':len({r['lineage']['source_group'] for r in allr})}
  for k,v in counts.items():check('Inventory '+k,s[k]==v,repr(v))
  check('Legacycorpus unchanged',s['local_document_files_indexed']==7373 and s['local_paper_groups_indexed']==4176)
  check('No independentexperiment/fullcorpus count invented',all(s[k] is None for k in ['independent_experiment_count','full_corpus_recipe_count','full_corpus_distinct_synthesized_material_count']))
  inventory={'checked_utc':datetime.now(timezone.utc).isoformat(),'scope':'Actual integrated inventory, not entire-corpus scientific completion.','actual_counts':counts,'eligible_by_task':totals,'source_group':groups[next(iter(records))],'split':mr[next(iter(records))]['split']}
  (OUT/'inventory-audit.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  for p in [SITE/'data/paper-reviews/veinot1997.json',SITE/'dist/data/paper-reviews/veinot1997.json',SITE/'dist/data/dataset-manifest.json',SITE/'dist/data/validation-report.json',SITE/'data/inventory-summary.json',SITE/'dist/data/materials-index.json',chem/'bindings.json',chem/'registry.json',chem/'product-bindings.json',SITE/'dist/paper-review.mjs',SITE/'dist/source-evidence.mjs',SITE/'dist/material-guide.mjs',SITE/'dist/material-hub.mjs',SITE/'dist/crystal-viewer.mjs',SITE/'dist/chemical-viewer.mjs',SITE/'scripts/dataset_lib.py',SITE/'scripts/build_dataset.py',B/'canonical-records-audit.json',OUT/'reader-runtime-check.json',OUT/'product-runtime-check.json']:bind(p)
 for p in [B/'source-audit.json',B/'public-review-proposal/source-item-coverage.json',B/'public-review-proposal/veinot1997.json']:bind(p)
 failures=[c for c in checks if not c['passed']]
 result={'status':('passed_private_mapping_preflight' if args.preflight else 'passed_bounded_canonical_to_reader_audit') if not failures else 'findings','checked_utc':datetime.now(timezone.utc).isoformat(),'mode':'private_preflight' if args.preflight else 'integrated_site_readonly','checks_passed':len(checks)-len(failures),'check_count':len(checks),'findings':failures,'scope':'Private mapping readiness only; no rendered-reader or publication claim.' if args.preflight else 'Exact independently audited records, generated HTML quantitative/qualitative rows, source runtime, source/unit/sample links, CdS hub, original and molecular asset bytes. Browser geometry/apparatus acceptance and publication are separate.','counts':{'records':len(records),'measurements':len(joins),'qualitative_facts':sum(j['value_kind']=='qualitative_fact' for j in joins),'operations':sum(len(r['operations']) for r in records.values()),'reader_items':len(items),'source_units':len(coverage['source_audit_unit_map']),'original_assets':len(assets)},'measurement_reader_links':joins,'authorized_promotion_differences':promotions,'eligible_by_task':totals,'hub':hubinfo,'inventory':inventory,'artifact_sha256':hashes,'checks':checks}
 name='preflight' if args.preflight else 'canonical-to-reader-audit'
 (OUT/(name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (OUT/(name+'.md')).write_text('# Veinot1997 source-to-reader audit\n\n'+result['status']+f' — {result["checks_passed"]}/{len(checks)} checks.\n\n'+result['scope']+'\n\n'+json.dumps(result['counts'],indent=2)+'\n\nFindings: '+json.dumps(failures,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({k:result[k] for k in ['status','checks_passed','check_count','findings','counts']},ensure_ascii=False))
 return bool(failures)
if __name__=='__main__':raise SystemExit(main())
