import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
root=Path('[local path redacted]')
out=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'recipe-atlas/scripts'))
from dataset_lib import validate_record,eligibility
records=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((out/'canonical').glob('*.json'))]
byid={r['record_id']:r for r in records};ids=set(byid);report=[]
for r in records:
 errors=validate_record(r)
 if r['lineage']['parent_record_id'] and r['lineage']['parent_record_id'] not in ids:errors.append('Parent record is outside package: '+r['lineage']['parent_record_id'])
 report.append({'record_id':r['record_id'],'errors':errors,'eligibility':eligibility(r),'counts':{k:len(r[k]) for k in ['materials','stocks','operations','products','measurements']}})
c=json.loads((out/'coverage.json').read_text(encoding='utf-8'))
checks={'nine_pages_read_and_visually_reviewed':sum(d['page_count'] for d in c['documents'])==9 and all(p['text_read'] and p['visual_review'] for d in c['documents'] for p in d['pages']),
'all_five_figures_reviewed':len(c['figures'])==5 and all(f['reviewed'] and f['original_crop_asset']['visually_reviewed'] for f in c['figures']),
'every_inventory_record_resolves':all(rid in ids for item in c['recipe_inventory'] for rid in item['record_ids']),
'all_figure_sample_links_resolve':all(any(r['record_id']==link['record_id'] and all(s in {p['sample_id'] for p in r['products']} for s in link['sample_ids']) for r in records) for f in c['figures'] for link in f['sample_links']),
'source_hashes_match':all(hashlib.sha256(Path(d['source_path']).read_bytes()).hexdigest()==d['sha256'] for d in c['documents']),
'crop_hashes_match':all(hashlib.sha256(Path(f['original_crop_asset']['asset']).read_bytes()).hexdigest()==f['original_crop_asset']['sha256'] for f in c['figures'])}
# Values below were independently checked against complete rendered SI pp. 1–3.
expected={
 'stowell-2005-ir-oa-oleylamine-290c':{'ir-precursor':{'mass':(.19,'g')},'diol':{'mass':(.195,'g')},'dioctyl-ether':{'reactor_volume':(7.5,'mL'),'feed_volume':(1,'mL')},'oa':{'volume':(.08,'µL')},'oam':{'volume':(.085,'µL')}},
 'stowell-2005-ir-top-290c':{'ir-precursor':{'mass':(.38,'g')},'diol':{'mass':(.39,'g')},'top':{'reactor_volume':(10,'mL'),'feed_volume':(2,'mL')}},
 'stowell-2005-ir-toab-270c':{'ir-precursor':{'mass':(.2,'g')},'diol':{'mass':(.2,'g')},'dioctyl-ether':{'volume':(7,'mL')},'toab':{'mass':(.76,'g')}},
 'stowell-2005-ir-topb-270c':{'ir-precursor':{'mass':(.2,'g')},'diol':{'mass':(.2,'g')},'dioctyl-ether':{'volume':(7,'mL')},'topb':{'mass':(.76,'g')}}}
critical=[]
for rid,materials in expected.items():
 mats={m['id']:m for m in byid[rid]['materials']}
 for mid,fields in materials.items():
  for field,(value,unit) in fields.items():
   q=mats[mid]['quantities'][field];critical.append({'record':rid,'material':mid,'field':field,'value':value,'unit':unit,'matches':q['value']==value and q['unit']==unit})
checks['critical_source_charge_values_match']=all(x['matches'] for x in critical)
checks['both_equations_reviewed_with_original_crops']=len(c['equations'])==2 and all(e['reviewed'] and e['formula_text'] and e['assumptions'] and e['original_crop_asset']['visually_reviewed'] for e in c['equations'])
checks['equation_crop_hashes_match']=all(hashlib.sha256(Path(e['original_crop_asset']['asset']).read_bytes()).hexdigest()==e['original_crop_asset']['sha256'] for e in c['equations'])
oa_product=next(p for p in byid['stowell-2005-ir-oa-oleylamine-290c']['products'] if p['sample_id']=='oa-method-product')
checks['oa_surface_label_uses_ligand_identity']=oa_product['source_sample_label']=='OA/oleylamine-capped Ir method product' and oa_product['surface']['value']=='Oleic-acid/oleylamine-capped'
checks['assays_and_shared_procedures_excluded_from_synthesis_tasks']=all(not any(v['eligible'] for v in eligibility(r).values()) for r in records if r['record_type']=='procedure')
checks['no_exact_structure_labels']=all(not eligibility(r)['exact_structure_recipe']['eligible'] for r in records)
result={'record_count':len(records),'validation_error_count':sum(len(x['errors']) for x in report),'coverage_checks':checks,'critical_quantity_checks':critical,'records':report}
(out/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'record_count':len(records),'validation_error_count':result['validation_error_count'],'coverage_checks':checks,'critical_charge_checks':len(critical),'measurements':sum(len(r['measurements']) for r in records)},indent=2))
assert result['validation_error_count']==0 and all(checks.values())
