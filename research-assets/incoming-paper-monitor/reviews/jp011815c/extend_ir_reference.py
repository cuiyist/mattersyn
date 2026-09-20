from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';R=S/'dist/assets/crystal-references';p=R/'registry.json'
d=json.loads(p.read_text(encoding='utf-8'));e=next(e for e in d['entries']if e['id']=='ir-fcc')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(R/e['cifPath'])==e['cifSha256'] and sha(R/e['modelPath'])==e['modelSha256']
assert e['referenceOnly'] is True and e['trainingEligible'] is False
e['record_ids']=list(dict.fromkeys(e['record_ids']+['shah-2001-ir']))
e['scope']='Bulk FCC Ir reference for comparison only. Stowell2005 reports FCC for its OA/oleylamine specimens. Shah2001 reports crystalline Ir by microscopy without a refined phase assignment or atomic coordinates; this reference does not establish the phase or structure of that specimen.'
e['sample_context_note']='The listed oa-xrd and oa-fig1d contexts belong only to Stowell2005. Shah2001 has no measured-coordinate or phase-refinement link.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'ir-reference-reuse.json').write_text(json.dumps({'status':'local_reference_reused','entry':e,'unchanged_cif_sha256':sha(R/e['cifPath']),'unchanged_model_sha256':sha(R/e['modelPath']),'measured_sample_claim':False,'training_label':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Reused verified local bulk Ir reference; no experimental phase or measured coordinate assignment.')
