"""Independent audit of private public-reader proposal. Does not audit actual Site rendering."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;P=B/'public-review-proposal'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ptr(obj,p):
 for t in p.lstrip('/').split('/')if p else []:obj=obj[int(t)] if isinstance(obj,list)else obj[t.replace('~1','/').replace('~0','~')]
 return obj
a=read(P/'stiger1999.json');cover=read(P/'source-item-coverage.json');source=read(B/'source-audit.json');draft=read(B/'characterization-draft.json')
records={p.stem:read(p)for p in (B/'canonical-drafts').glob('*.json')};items={i['id']:i for s in a['reader_sections']for i in s['items']};facts={}
for i in items.values():
 for f in i.get('facts',[]):facts.setdefault(f['id'],[]).append((i,f))
checks=[]
def ck(n,b):checks.append({'name':n,'passed':bool(b)})
ck('202 exact source-unit inventory; 144 reader items',cover['source_audit_sha256']==sha(B/'source-audit.json') and len(cover['source_audit_unit_map'])==202 and len(items)==144)
ck('No missing or duplicate source units',{x['source_unit_id']for x in cover['source_audit_unit_map']}=={x['id']for x in source['units']})
for x in cover['source_audit_unit_map']:
 u=ptr(source,x['source_audit_json_pointer']);dest=[ptr(a,p)for p in x['reader_json_pointers']]
 ck(x['source_unit_id']+' valid source/destination and explicit disposition',u['id']==x['source_unit_id'] and x['category']==u['category'] and [d['id']for d in dest]==x['reader_item_ids'] and bool(x['disposition']) and x['evidence']==u['evidence'])
ck('All143 independently reviewed characterization rows represented',set(facts)=={r['id']for r in draft['measurement_rows']})
for row in draft['measurement_rows']:
 okay=True
 for i,f in facts[row['id']]:
  q=row.get('quantity');expected=(str(q['lower_bound'])+'–'+str(q['upper_bound'])if q and 'lower_bound'in q else q.get('value')if q else row['fact'])
  okay=okay and f['value']==expected and f['basis']==row['basis'] and f['unit']==(q.get('unit')if q else None) and f['approximate']==(q.get('approximate',False)if q else False) and bool(f['evidence'])
  if q and q.get('raw_text'):okay=okay and q['raw_text']in f['qualifier']
  scope=i['sample_scope'];samples=['shared-'+'-and-'.join(row['sample_id'])]if isinstance(row['sample_id'],list)else[row['sample_id']]
  # Source scopes can group multiple observations; all row formulations must remain visible.
  okay=okay and set(samples).issubset(scope['formulations'])
 ck(row['id']+' reader preserves numeric/fact value, basis, qualifiers and cohort',okay)
for i in items.values():
 for link in i.get('canonical_links',[])+i['sample_scope'].get('canonical_sample_links',[]):
  r=records[link['record_id']];target=ptr(r,link['json_pointer'])
  if 'sample_id'in link:assert target['sample_id']==link['sample_id'],(i['id'],link)
 ck(i['id']+' readable evidence and bounded scope',bool(i['text'])and bool(i['evidence'])and bool(i['sample_scope']['link_limit'])and not i['training_eligible'])
assets=a['figures']+a['tables']+a['schemes']+a['equations']+a['source_notes']
assets=[x for x in assets if x.get('public_asset')]
ck('All15 original crop assets represented',len(assets)==15)
for asset in assets:
 p=B/'crop-assets'/Path(asset['public_asset']).name
 ck(asset['id']+' exact source crop, scope and no rendered-publication claim',p.exists()and sha(p)==asset['public_asset_sha256']and bool(asset['sample_scope'])and not asset['reader_render_verified']and not asset['training_eligible'])
ck('Source page identity and unverified SI explicit',a['review_scope']=='supplied_main_only_si_unverified'and a['counts']['supplied_main_pages']==9 and a['counts']['matched_si_pages']==0)
ck('Only one synthesis route, not every context a recipe',len(a['recipe_inventory'])==8 and sum(x['record_type']=='literature_protocol'for x in a['recipe_inventory'])==1)
ck('No training/publication promotion',not a['source_review_promoted']and not a['training_eligible']and a['publication_status']=='private_proposal_not_published')
serialized=json.dumps(a,ensure_ascii=False)
ck('No private absolute filesystem paths or staged payload','C:\\'not in serialized and 'C:/'not in serialized and 'staged_detail'not in serialized)
for id,term in [('source-specific-electrolytes','1.5 mM'),('conflict-09','mC/cm²'),('conflict-18','ms⁻¹'),('height-charge-model','hemisphere'),('source-note43','measured in-house'),('saed-indexing','reference relative intensities'),('transferred-particles','pulse duration is not stated'),('histogram-prose-conflict','2.2 nm'),('induction-time-limits','longer than 30 ms'),('afm-instrument','which lever dimension')]:
 ck(id+' key source distinction retained',term in items[id]['text'])
ck('Direct reference43 and43other unopened cited contexts',items['reference-43']['claim_type']=='direct_source_note'and sum(i['claim_type']=='cited_reference_context'for i in items.values())==43)
f2=next(x for x in a['figures']if x['id']=='figure-2');f6=next(x for x in a['figures']if x['id']=='figure-6')
ck('Figure2 scan styles explicit',all(t in json.dumps(f2).lower()for t in ['solid','dotted','short']))
ck('Figure6 original caption naming conflict explicit','transmission electron diffraction'in json.dumps(f6).lower())
out={'status':'passed'if all(c['passed']for c in checks)else'must_fix','source_id':'stiger1999','scope':'Independent scientific reader-proposal audit against fully read supplied main and 202-unit source inventory; all144 reader item texts,143 typed factual rows and15 figure/table/scheme/equation/detail metadata inspected. This is source-to-proposal acceptance, not actual source-to-browser verification.','reader_proposal_sha256':sha(P/'stiger1999.json'),'coverage_sha256':sha(P/'source-item-coverage.json'),'source_audit_sha256':sha(B/'source-audit.json'),'canonical_audit_sha256':sha(B/'canonical-records-audit.json'),'check_count':len(checks),'checks':checks,'findings':[{'id':'R01','title':'Retain Figure2 scan styles and Figure6 caption naming conflict in accessible metadata','status':'resolved'if all(c['passed']for c in checks[-2:])else'open','detail':'Original pixels retain these details; explicit metadata improves source-unit coverage and avoids classifying TEM panel a as diffraction.'}],'limits':['Nine main pages inspected. Matching SI not located or verified; no external cited article claimed fully read.','One synthesis route, four analytical procedures, two deliberate controls and one contextual observation record are distinct.','Data-model and reference contexts are not experimental outcomes or independently identified physical batches.','All source units have explicit destinations; literal wording is paraphrased and original figure/equation pixels retained, not a public full-text dump.','Root still must verify actual frontend rendering, gallery filtering, quantitative qualifiers and reader-to-canonical links before source-to-view completion.']}
(B/'reader-source-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(B/'reader-source-audit.md').write_text('# Independent reader/source audit\n\n'+out['status'].upper()+': '+str(len(checks))+' checks, 144 reader items, 202 source units, 143 typed characterization rows, 15 original assets.\n\n'+'\n'.join('- '+s for s in out['limits'])+'\n',encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(checks),'failed':[c for c in checks if not c['passed']]},indent=2))
