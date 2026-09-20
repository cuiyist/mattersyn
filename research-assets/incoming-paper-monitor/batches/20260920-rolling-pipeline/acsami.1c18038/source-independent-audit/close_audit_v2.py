from pathlib import Path
import json,hashlib,copy,datetime,math
A=Path(__file__).resolve().parent;P=A.parent;OLD=P/'source-extraction-revision-1'
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(ok,topic):
 checks.append({'check':topic,'passed':bool(ok)})
 if not ok:raise AssertionError(topic)
v1=read(A/'independent-audit-v1.json');mc=read(A/'mechanical-checks-v2.json');freeze=read(P/'package-freeze.json');oldfreeze=read(OLD/'package-freeze.json')
ck(sha(P/'package-freeze.json')=='2eca0b5181f3b60156227095e51833af870c7a3ea7e0590c4d3e782931555ae7','expected final freeze')
ck(mc['counts']['failed']==0,'all final source/transport/crop checks pass')
ck(sha(OLD/'package-freeze.json')==v1['proposal_freeze_sha256'],'original freeze preserved')
for ps,h in oldfreeze['bound_files'].items():
 p=Path(ps); archived=OLD/p.relative_to(P) if p.is_relative_to(P) else None
 retained=archived if archived and archived.exists() else p
 ck(sha(retained)==h,'old frozen bytes preserved '+str(retained))
old=read(OLD/'source-facts.json');new=read(P/'source-facts.json');expected=copy.deepcopy(old)
expected['protocols'][5]['operations'][1]['action']='Acquire XPS; acquire TGA under N2'
ck(expected==new,'source-facts exactly one permitted wording leaf; all other science identical')
oldi=read(OLD/'source-inventory.json');newi=read(P/'source-inventory.json');expecti=copy.deepcopy(oldi)
expecti['protocols'][5]['operations'][1]['action']='Acquire XPS; acquire TGA under N2'
for i,u in enumerate(expecti['inventory_units']):
 oid=u['id'];u['id']=u['type']+':'+oid;u['source_object_id']=oid
 ck(newi['inventory_units'][i]==u,f'unit{i} exact namespace-only change')
ck(expecti==newi,'inventory exactly one wording leaf plus334 namespace/source-object metadata leaves')
for name in ['source-tables.json','original-assets-manifest.json','complete-source-payloads.json','page-coverage.json','pairing-review.json','source-consistency-diagnostics.json']:
 ck(sha(OLD/name)==sha(P/name),'unchanged '+name)
# Independent arithmetic verifies author diagnostics without promoting their site association.
tables={x['id']:x for x in new['tables']}
for d in read(P/'source-consistency-diagnostics.json')['diagnostics']:
 t=tables[d['table']]
 if 'derived_mean_angstrom' in d:
  values=[r['cells'][0]['value'] for r in t['rows'] if r['atoms'][0]==d['site'] and r['atoms'][1].startswith('Cl')]
  avg=sum(values)/len(values);delta=sum(((v-avg)/avg)**2 for v in values)/len(values)
  ck(len(values)==d['bond_count'],'diagnostic bond count '+d['table']+d['site'])
  ck(math.isclose(avg,d['derived_mean_angstrom'],rel_tol=1e-12),'diagnostic mean '+d['table']+d['site'])
  ck(math.isclose(delta,d['derived_delta_d'],rel_tol=1e-12),'diagnostic distortion '+d['table']+d['site'])
 else:
  values=[r['cells'][0]['value'] for r in t['rows'] if r['atoms'][1]==d['site'] and r['atoms'][0].startswith('Cl') and r['atoms'][2].startswith('Cl') and abs(r['cells'][0]['value']-90)<45]
  ck(len(values)==d['near90_angle_count'],'diagnostic angle count '+d['table']+d['site'])
  value=sum((x-90)**2 for x in values)/(7 if len(values)==8 else 4)
  ck(math.isclose(value,d['derived_sigma2_deg2'],rel_tol=1e-12),'diagnostic variance '+d['table']+d['site'])
d=copy.deepcopy(v1);d['created_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['status']='passed';d['proposal_revision']=2;d['proposal_freeze_sha256']=sha(P/'package-freeze.json');d['counts']['mechanical_checks']=mc['counts']['checks'];d['counts']['mechanical_failures']=0;d['counts']['bounded_revision_checks']=len(checks)
d['manual_scopes'][-1]['assessment']='All167 inventory entries now have unique type-prefixed unit IDs; unchanged source_object_id and JSON pointers preserve exact links. No task/exact-pair/publication gate approved.'
d['manual_scopes'].append({'id':'L22','topic':'Derived consistency diagnostics','assessment':'Independently recomputed all6 bond/angle diagnostic groups. These remain labeled arithmetic diagnostics, not source values or proven B-site assignments. A angle variance5.355928... is close to, not literally identical to, printed5.35; source rounding/uncertainty is not resolved by recomputation.'})
d['counts']['manual_scientific_scopes']=len(d['manual_scopes'])
for f in d['findings']:
 if f['id']=='LIAN-SOURCE-02':f.update(status='resolved_revision_2',resolution='Exactly one source-facts action leaf and its inventory mirror now explicitly assign N2 only to TGA. All source values and other object fields unchanged.')
 if f['id']=='LIAN-SOURCE-03':f.update(status='resolved_revision_2',resolution='All167 inventory IDs are type-prefixed; source_object_id and original JSON pointers retain the unchanged scientific identities. Exact335-leaf inventory delta verified.')
d['open_findings']=[];d['revision_delta']={'old_audit_path':str(A/'independent-audit-v1.json'),'old_audit_sha256':sha(A/'independent-audit-v1.json'),'old_freeze_sha256':v1['proposal_freeze_sha256'],'final_freeze_sha256':d['proposal_freeze_sha256'],'source_facts_changed_leaves':1,'source_inventory_changed_or_added_leaves':335,'scientific_quantities_changed':0,'original_crops_changed':0,'checks':checks}
bound=dict(mc['bound_files'])
for name in ['independent-audit-v1.json','independent-audit-v1.md','independent-reading-v1.json','independent-reading-v1.md','independent-reading-addendum.md','independent-table-tokens-v1.json','mechanical-checks-v1.json','mechanical-checks-v2.json','check_extraction.py','close_audit_v2.py']:
 bound[str(A/name)]=sha(A/name)
d['bound_files']=bound
for ps,h in bound.items():ck(sha(Path(ps))==h,'final input unchanged '+ps)
d['counts']['final_bound_files']=len(bound);d['counts']['bounded_revision_checks']=len(checks)
out=A/'independent-audit-v2.json';assert not out.exists();out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8');(A/'independent-audit.json').write_bytes(out.read_bytes())
md='''# Lian 2021 independent source audit — passed, revision 2

All 8 main-paper and 26 supporting-information pages were independently read and visually inspected before comparing the author's extraction. The reviewed package covers 57 facts / 134 quantities, 15 materials, 5 stocks, 9 protocol groups / 21 operations, 14 sample contexts, and 167 unique source units.

All nine crystallographic tables were checked: 311 rows, 891 cells, including 885 numeric cells with their signs, uncertainties and scales. All 53 selected source crops were visually inspected and matched independent fresh PDFium renders pixel-for-pixel. The 21 figures, one scheme, six equations and 30 reference entries retain their source and specimen scopes. Final mechanical checks: 8,962 passed.

The corrections are resolved: PS molecular weight retains its approximate value without an unprinted unit; nitrogen is explicitly scoped to TGA; source-unit IDs are unique across material/sample namespaces. Revision 1 is preserved. The final revision changes one source-facts wording leaf and the corresponding inventory wording plus identity metadata; scientific quantities and source crops are unchanged.

The declared crystal ZIP and MP4 remain locally absent. The PDF's non-hydrogen bulk coordinates and displacement parameters are retained as partial source data, not a qualified original CIF or a nanocrystal structure–recipe pair. Four source conflicts and ten missing-information categories remain explicit. This source audit does not approve canonical records, molecular/apparatus viewers, training tasks, website integration or publication.

Exact hashes, the initial findings, independent reading history and final delta checks are in independent-audit-v2.json (identical current alias: independent-audit.json).
'''
(A/'independent-audit-v2.md').write_text(md,'utf8');(A/'independent-audit.md').write_text(md,'utf8')
print(json.dumps({'path':str(out),'sha256':sha(out),'freeze_sha256':d['proposal_freeze_sha256'],'bound_files':len(bound),'checks':d['counts']['mechanical_checks'],'delta_and_final_hash_checks':len(checks)}))
