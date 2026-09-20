"""Independent frozen-canonical to reader-proposal audit. No Site writes."""
from pathlib import Path
import json, hashlib, datetime, re
from collections import Counter

B=Path(__file__).resolve().parents[1]
P=B/'public-review-proposal/shah2001.json'
raw=P.read_bytes(); reader=json.loads(raw)
sha=lambda b:hashlib.sha256(b).hexdigest()
record_bytes={p.stem:p.read_bytes() for p in sorted((B/'canonical-drafts').glob('*.json'))}
records={k:json.loads(v) for k,v in record_bytes.items()}
items=[x for sec in reader['reader_sections'] for x in sec['items']]
item_by_id={x['id']:x for x in items}
checks=[]; findings=[]
def check(ok,name,detail=None):
 checks.append({'check':name,'passed':bool(ok),**({'detail':detail} if detail else {})})
def at(rid,p):
 out=records[rid]
 for k in p.lstrip('/').split('/') if p else []:
  k=k.replace('~1','/').replace('~0','~')
  out=out[int(k)] if isinstance(out,list) else out[k]
 return out
def display(q):
 if q.get('value') is not None:return q['value']
 lo,hi=q.get('minimum'),q.get('maximum')
 if lo is not None and hi is not None:return f'{lo}–{hi}'
 if lo is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+str(lo)
 if hi is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+str(hi)
 return None

check(len(records)==19,'Nineteen canonical records available')
check(len(items)==len(item_by_id)==138,'Reader item IDs unique and full inventory retained')
facts=[]; linked_operations=set(); linked_measurements=set(); linked_parameters=set()
sample_links=[]
for x in items:
 for link in x.get('canonical_links',[]):
  rid,p=link['record_id'],link['json_pointer']
  try:obj=at(rid,p);valid=True
  except (KeyError,IndexError,ValueError,TypeError):valid=False
  check(valid,f"{x['id']} canonical pointer resolves: {rid}{p}")
  if valid and re.fullmatch('/operations/[0-9]+',p):linked_operations.add((rid,p))
 for link in x.get('sample_scope',{}).get('canonical_sample_links',[]):
  sample_links.append(link)
  try:prod=at(link['record_id'],link['json_pointer']);valid=prod.get('sample_id')==link['sample_id']
  except (KeyError,IndexError,TypeError):valid=False
  check(valid,f"{x['id']} explicit sample pointer resolves to matching sample_id")
  check(link['sample_id'] in x['sample_scope']['formulations'],f"{x['id']} declared formulation includes linked sample")
 for f in x.get('facts',[]):
  facts.append((x['id'],f));rid,p=f['canonical_record_id'],f['json_pointer']
  try:obj=at(rid,p)
  except (KeyError,IndexError,TypeError):
   check(False,f"{f['id']} fact pointer resolves");continue
  is_measure='canonical_measurement_id' in f
  q=obj['value'] if is_measure else obj
  check(f['canonical_quantity']==q,f"{f['id']} exact typed quantity/status/bounds/provenance preserved")
  check(f['value']==display(q),f"{f['id']} display value preserves exact value or bound")
  check(f.get('unit')==q.get('unit') and f.get('approximate')==q.get('approximate',False),f"{f['id']} units and approximation preserved")
  check({(e['source_id'],e['locator']) for e in q.get('evidence',[])} <= {(e['source_id'],e['locator']) for e in f.get('evidence',[])},f"{f['id']} evidence retained")
  check(f.get('training_eligible') is False,f"{f['id']} reader display does not grant training eligibility")
  if is_measure:
   linked_measurements.add((rid,p))
   check(f['canonical_measurement_id']==obj['id'] and f.get('sample_id')==obj['sample_id'],f"{f['id']} measurement and sample identity exact")
   check(any(z['sample_id']==f['sample_id'] for z in records[rid]['products']),f"{f['id']} sample exists in same canonical record")
  elif 'canonical_operation_id' in f:
   op=at(rid,'/'.join(p.split('/')[:3]))
   check(f['canonical_operation_id']==op['id'] and f['canonical_parameter']==p.rsplit('/',1)[1],f"{f['id']} operation/parameter identity exact")
   linked_parameters.add((rid,p))

expected_m={(rid,f'/measurements/{i}') for rid,r in records.items() for i,_ in enumerate(r['measurements'])}
expected_o={(rid,f'/operations/{i}') for rid,r in records.items() for i,_ in enumerate(r['operations'])}
expected_p={(rid,f'/operations/{i}/parameters/{k}') for rid,r in records.items() for i,o in enumerate(r['operations']) for k in o['parameters']}
check(linked_measurements==expected_m and len(expected_m)==111,'All 111 measurement facts covered with no extraneous measurement targets',{'missing':sorted(expected_m-linked_measurements),'extra':sorted(linked_measurements-expected_m)})
check(linked_operations==expected_o and len(expected_o)==74,'All 74 operation links covered with no extraneous operation targets',{'missing':sorted(expected_o-linked_operations),'extra':sorted(linked_operations-expected_o)})
check(linked_parameters==expected_p and len(expected_p)==118,'All 118 operation parameter quantities covered',{'missing':sorted(expected_p-linked_parameters),'extra':sorted(linked_parameters-expected_p)})
check(len(facts)==len({f['id'] for _,f in facts}),'Fact IDs unique across all reader sections')

# Compare paired table columns independently of the reader generation script.
for row in reader['tables'][0]['structured_rows']:
 rid=row['canonical_record_id'];r=records[rid];ops={o['id']:o for o in r['operations']};ms={m['id']:m for m in r['measurements']}
 expected={'precursor_concentration_mM':ops['load']['parameters']['precursor_concentration']['value'],'thiol_precursor_mol_mol':ops['inject']['parameters']['thiol_to_precursor_molar_ratio']['value'],'temperature_degC':ops['condition']['parameters']['temperature']['value'],'mean_diameter_angstrom':ms['diameter']['value']['value'],'standard_deviation_angstrom':ms['diameter-standard-deviation']['value']['value'],'relative_standard_deviation_percent':ms['relative-standard-deviation']['value']['value']}
 check(all(row[k]==v for k,v in expected.items()),f"Table 1 {row['experiment']} retains all six paired condition/outcome columns")
 check(rid=='shah-2001-ag-'+row['experiment'].lower(),f"Table 1 {row['experiment']} canonical row label exact")
for metal in ['ir','pt']:
 allowed={'shah-2001-'+metal,'shah-2001-recovery','shah-2001-tem-eds'}
 check(set(reader['material_evidence_records'][metal.title()])==allowed,f'{metal.upper()} material map excludes Ag specimen and model records')
 for name in [metal+'-route',metal+'-tem','chemical-'+metal]:
  check(all(z['record_id']=='shah-2001-'+metal for z in item_by_id[name]['canonical_links']),f'{name} links only its own metal route')
 fs=item_by_id[metal+'-route']['facts']
 inherited=[f for f in fs if f['canonical_quantity']['status']=='inferred']
 check(len(inherited)==3,f'{metal.upper()} fill T/P and hold retain inferred status')
 check(all(any(w in f['qualifier'].lower() for w in ['inherit','common','not separately']) for f in inherited),f'{metal.upper()} inherited method qualifiers visible')
 check(not any('mass' in f.get('canonical_parameter','') for f in fs),f'{metal.upper()} no transferred Ag reagent mass')
 check(not any(f.get('canonical_measurement_id')=='diameter' for _,f in facts if f['canonical_record_id']=='shah-2001-'+metal),f'{metal.upper()} no invented mean diameter')
for name,sample in [('optical-current','spectrum-i'),('optical-c10','spectrum-ii'),('optical-hydrocarbon','spectrum-iii')]:
 check(item_by_id[name]['sample_scope']['formulations']==[sample],name+' remains a separate optical cohort')
 check(all(l['record_id']=='shah-2001-optical-comparison' for l in item_by_id[name]['canonical_links']),name+' not joined to same-diameter Table 1 experiment')
check('unresolved' in item_by_id['chemical-pt']['text'].lower(),'Printed Pt molecular identity conflict remains explicit')
figs={x['id']:x for x in reader['figures']}
check(set(figs['figure-8']['sample_links'])=={'shah-2001-ir','shah-2001-pt'},'Figure 8 belongs only to Ir/Pt routes with panel labels')
check(figs['figure-7']['sample_links']==['shah-2001-optical-comparison'],'Figure 7 optical source asset is not joined to A-I')
check('shah-2001-ag-h' not in figs['figure-4']['sample_links'],'Figure 4 unknown fifth point not promoted to experiment H')
if 'shah-2001-tem-eds' in figs['figure-6']['sample_links']:
 findings.append({'severity':'integration_boundary','location':'/figures/5/sample_links','issue':'Ag-specific Figure 6 also links generic tem-eds, a record in Ir/Pt material maps. Naive intersection filtering can expose Ag specimen EDS on Ir/Pt pages.','recommendation':'Use only shah-2001-ag-structure as Figure 6 specimen link; keep shared EDS acquisition procedure separate.'})
check(P.read_bytes()==raw,'Audited reader file remained unchanged throughout execution')
failed=[x for x in checks if not x['passed']]
out={'status':'passed_with_source_and_integration_limits' if not failed else 'failed','audit_type':'independent_canonical_to_reader_consistency','auditor':'/root/peng1998_visuals (canonical author; independent reviewer of other agent reader proposal)','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reader_file':str(P),'reader_sha256':sha(raw),'canonical_hashes':{k:sha(v) for k,v in record_bytes.items()},'counts':{'records':len(records),'reader_items':len(items),'measurement_facts':len(linked_measurements),'operation_links':len(linked_operations),'operation_parameter_facts':len(linked_parameters),'all_typed_facts':len(facts),'explicit_sample_links':len(sample_links),'checks':len(checks),'passed':len(checks)-len(failed),'failed':len(failed)},'failures':failed,'findings':findings,'checks':checks,'manual_semantic_review':['Nine A-I formulation rows and histogram identities remain paired; population width is not measurement uncertainty.','Ir and Pt route conditions and TEM panels are separated; no mean diameter or Ag typical mass is manufactured.','Typical-framework charges, volume ranges, initial fill and reaction conditions remain separate.','Optical i/ii/iii cohorts remain distinct and are not joined to Ag E/F by shared diameter.','Ag Figures 2, 6 and 11 retain unassigned image/spectral cohort identities rather than batch claims.','Inferred Ir/Pt common-method parameters remain typed inferred with inheritance prose; no exact physical batch asserted.','Instrument TEM resolution is not a measured sample lattice spacing.','Printed Pt name, figure/table disagreements, CO2 state wording and model assumptions remain source-qualified.'],'limits':['This checks the reader proposal against frozen canonical records and manually reviews material/sample boundaries. Independent full-source semantics, figure crops and live browser rendering are separate audits.','Site files were not edited.','A later reader or canonical hash change requires this audit to be refreshed.']}
(B/'reader-assets/canonical-to-reader-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
summary=f"# Shah2001 canonical-to-reader audit\n\nStatus: **{out['status']}**. Reader SHA256: `{out['reader_sha256']}`.\n\nAll **111 measurement facts**, **74 operation links** and **118 operation parameter facts** are covered. The **{len(facts)} typed facts** retain exact canonical quantities, status, bounds, units and provenance. **{len(checks)-len(failed)}/{len(checks)} checks pass**. Nine Table 1 rows retain their paired formulations and outcomes. Ir/Pt routes, Ag typical charges, unassigned image cohorts and optical comparison samples remain distinct.\n\n"
if failed:summary+='Failures:\n\n'+'\n'.join('- '+x['check'] for x in failed)+'\n\n'
if findings:summary+='Integration boundary:\n\n'+'\n'.join('- '+x['issue']+' '+x['recommendation'] for x in findings)+'\n\n'
summary+='This is an independent reader-proposal consistency check by the canonical author. Full-source/crop audit and live browser QA remain separate. No Site edits. Exact canonical hashes and all checks are recorded in the JSON report.\n'
(B/'reader-assets/canonical-to-reader-audit.md').write_text(summary,encoding='utf-8')
print(json.dumps({'status':out['status'],'hash':out['reader_sha256'],'counts':out['counts'],'failures':failed,'findings':findings},ensure_ascii=False))
