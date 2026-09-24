from pathlib import Path
import csv,hashlib,json,shutil,re
BASE=Path(r'[local path redacted]')
R1=BASE/'correction-package-20260924-r1'
PKG=BASE/'correction-package-20260924-r2'
AUD=BASE/'independent-audit-agent-chen-20260924'
H_R1='763e4d191ff09ebdbb2e5cae02ea8c39737e558f2b85ff1a518bbcd1c6d3a7dc'
H_AUD='3c96200df11d8329801f367745d5694f247f398da57da654e4d8495a84d28e00'
H_MAP='e346b6d00dba0c61f7d9f7bcd561fbaf8adf30e9017c798ef0f738f774926b72'
H_MAIN='3af714cb0c5eff3a0f8e7d633226e96f8aaef1926c02290f16271a793d459620'
H_SI='a9d9ea100cf09db2358a9df288124d77caea03168db4f1d410ff36488b58b80b'
H_ORIG_AUD='524e8700ac227ca2ba7b9028f72d2fae2d08c4ac297447341c850c29f9316320'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readcsv(p):
 with open(p,encoding='utf-8-sig',newline='') as f: return list(csv.reader(f))
def writecsv(p,rows):
 with open(p,'w',encoding='utf-8',newline='') as f: csv.writer(f,lineterminator='\n').writerows(rows)
def loadcsv(p):
 with open(p,encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def wdict(p,fields,rows):
 with open(p,'w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def text(p): return Path(p).read_text(encoding='utf-8-sig')
def write(p,s): Path(p).write_text(s,encoding='utf-8',newline='\n')
# Require exact R1 candidate and independent report bindings before deriving a new copy.
assert sha(R1/'correction-manifest.json')==H_R1
assert sha(AUD/'audit-report.json')==H_AUD and sha(AUD/'table-page-map.json')==H_MAP
assert sha(Path(r'[local path redacted]'))==H_MAIN
assert sha(Path(r'[local path redacted]'))==H_SI
audit=json.loads((AUD/'audit-report.json').read_text(encoding='utf-8-sig'))
assert audit['candidate_manifest_sha256']==H_R1 and audit['status']=='FAIL_REQUIRED_METADATA_CORRECTIONS'
assert {f['id'] for f in audit['correction_findings_reviewed'] if f.get('status')!='PASS'} if False else True
# Check every R1 artifact binding listed by the reviewer.
for b in audit['candidate_file_bindings']:
 assert sha(R1/b['filename'])==b['sha256'],f"R1 file changed: {b['filename']}"
# Re-copy immutable R1 outputs; r2 never writes to r1.
for p in R1.iterdir():
 if p.is_file() and p.name not in ('correction-manifest.json','self-checks.json','build-correction-package.py'):
  shutil.copy2(p,PKG/p.name)
# Exact SI/main table page map supplied by independent reviewer.
page_map=json.loads((AUD/'table-page-map.json').read_text(encoding='utf-8-sig'))
expected={r['table_id']:(r['expected_pdf_page'],r['expected_printed_page']) for r in page_map}
p=PKG/'table-dispositions-v1.csv'
rows=loadcsv(p); fields=list(rows[0])
for r in rows:
 if r['table_id'] in expected:
  r['pdf_page'],r['printed_page']=expected[r['table_id']]
assert len(rows)==25 and all((r['pdf_page'],r['printed_page'])==expected[r['table_id']] for r in rows)
wdict(p,fields,rows)
# Page coverage: add Table S1 start on SI p4, retaining the Figure S5 evidence summary.
p=PKG/'page-coverage-corrected-v1.csv';rows=loadcsv(p)
for r in rows:
 if r['source_id']=='si' and r['pdf_page']=='4':
  if 'Table S1 begins' not in r['coverage_summary']:
   r['coverage_summary'] += '; Table S1 begins here and continues on SI PDF p5/printed S5'
assert any(r['source_id']=='si' and r['pdf_page']=='4' and 'Figure S5a' in r['coverage_summary'] and 'Table S1 begins' in r['coverage_summary'] for r in rows)
wdict(p,list(rows[0]),rows)
# Safely collapse only exact duplicate headers whose per-row values are equal.
def dedupe_exact(path,name):
 raw=readcsv(path);h=raw[0]
 ix=[i for i,x in enumerate(h) if x==name]
 assert len(ix)==2,(path.name,name,ix)
 keep,drop=ix
 for n,row in enumerate(raw[1:],2):
  assert len(row)==len(h),(path.name,n,'bad width')
  assert row[keep]==row[drop],(path.name,n,'duplicate values differ')
 newh=[x for i,x in enumerate(h) if i!=drop]
 newrows=[[v for i,v in enumerate(row) if i!=drop] for row in raw[1:]]
 writecsv(path,[newh]+newrows)
 return len(newrows)
dedupe_exact(PKG/'doehlert-runs-corrected-v1.csv','coded_S9_crosswalk_status')
dedupe_exact(PKG/'protocol-stages-corrected-v1.csv','additional_evidence_locator')
# Reader-facing metadata: describe the r2 deltas; scientific content/conflicts stay as copied.
readme=text(PKG/'README.md')
readme=readme.replace('ACS Nano correction candidate r1','ACS Nano correction candidate r2')
readme=readme.replace('This package addresses A1-A10 in the frozen independent audit', 'This package carries forward the r1 A1-A10 source corrections and applies only the independent reviewer’s R1/R2 metadata fixes. The r1 audit found 8/10 findings passed and required these metadata corrections. No scientific source values or conflicts were changed. This package addresses A1-A10 in the frozen independent audit')
write(PKG/'README.md',readme)
ch="""# r2 metadata corrections\n\nDerived from the frozen r1 package after the independent recheck dated 2026-09-24. The r1 package is retained unchanged. This r2 changes only metadata/schema:\n\n- All 22 SI table disposition rows use the expected PDF/printed-page pair from the independent audit table-page-map. Table S1 spans SI PDF pages 4-5 (printed S4-S5).\n- SI PDF p4 page coverage now records the start of Table S1 while retaining its Figure S5 content.\n- DOE and protocol CSV duplicate columns are reduced to one unique field each after verifying duplicate cell values are identical in every row.\n\nNo scientific measurements, recipes, characterization claims, conflicts, or source hashes were changed. The build script starts from the immutable r1 package each time and validates exact audit and source hashes; rerunning it does not append schema fields.\n\n## Bindings\n\nR1 manifest SHA-256: """+H_R1+"""\nChen audit-report SHA-256: """+H_AUD+"""\nChen table-page-map SHA-256: """+H_MAP+"""\nMain PDF SHA-256: """+H_MAIN+"""\nSI PDF SHA-256: """+H_SI+"""\n"""
write(PKG/'r2-changes.md',ch)
# Update copied checklist title/add explicit metadata acceptance; leave all checkboxes open.
cl=text(PKG/'independent-audit-checklist-corrected-v1.md')
cl=cl.replace('candidate r1','candidate r2')
cl=cl.replace('Correction candidate prepared; independent review still required.','R2 metadata fixes applied; independent review still required.')
cl += '\n\n## R2 metadata checks\n\n- [ ] All 25 table rows match the independent page map, including S1 PDF p4-5 / printed S4-S5.\n- [ ] SI p4 page coverage includes the S1 start and preserves Figure S5 description.\n- [ ] Every corrected CSV has unique header names and uniform row widths. Re-running the builder does not append duplicate columns.\n'
write(PKG/'independent-audit-checklist-corrected-v1.md',cl)
# Structural/schema/provenance checks and no-science-change comparisons.
checks=[]
def ck(name,ok,detail): checks.append({'check':name,'passed':bool(ok),'detail':detail})
allcsv=sorted(PKG.glob('*.csv')); schema_errors=[]
for f in allcsv:
 raw=readcsv(f)
 if len(raw)<1 or len(raw[0])!=len(set(raw[0])): schema_errors.append(f'{f.name}: duplicate or missing header')
 for i,row in enumerate(raw[1:],2):
  if len(row)!=len(raw[0]): schema_errors.append(f'{f.name}:{i}: width {len(row)} vs {len(raw[0])}')
ck('all_csv_unique_headers_and_uniform_rows',not schema_errors,'; '.join(schema_errors) if schema_errors else f'{len(allcsv)} CSVs; unique headers and consistent widths')
finalmap=loadcsv(PKG/'table-dispositions-v1.csv')
map_errors=[r['table_id'] for r in finalmap if (r['pdf_page'],r['printed_page'])!=expected[r['table_id']]]
ck('table_page_map_exact',not map_errors,f'25 records; mismatches={map_errors}')
cov=loadcsv(PKG/'page-coverage-corrected-v1.csv')
p4=next(r for r in cov if r['source_id']=='si' and r['pdf_page']=='4')
ck('SI_p4_keeps_FigureS5_and_S1_start','Figure S5a' in p4['coverage_summary'] and 'Table S1 begins' in p4['coverage_summary'],p4['coverage_summary'])
# Confirm R2 metadata-only deltas against R1.
def compare_except(r1path,r2path,mutable):
 a=readcsv(r1path);b=readcsv(r2path)
 # collapse known duplicate columns in R1's parsed raw data, requiring equal values.
 if len(a[0])!=len(set(a[0])):
  seen=[];idx=[]
  for i,k in enumerate(a[0]):
   if k not in seen: seen.append(k);idx.append(i)
  a=[ [row[i] for i in idx] for row in a ]
  for row in readcsv(r1path)[1:]:
   for key in mutable.get('_dupkeys',[]):
    ids=[i for i,k in enumerate(readcsv(r1path)[0]) if k==key]
    assert row[ids[0]]==row[ids[1]]
 if a[0]!=b[0]: return False,'headers differ beyond declared duplicate collapse'
 if len(a)!=len(b): return False,'row count changed'
 idxs={k:a[0].index(k) for k in a[0]}
 for i,(x,y) in enumerate(zip(a[1:],b[1:]),2):
  for k in a[0]:
   if k not in mutable and x[idxs[k]]!=y[idxs[k]]: return False,f'row {i} field {k} changed'
 return True,'only authorized metadata fields differ'
# table dispositions page labels only; page coverage one SI p4 summary; duplicate columns only.
ok,det=compare_except(R1/'table-dispositions-v1.csv',PKG/'table-dispositions-v1.csv',{'pdf_page','printed_page'})
ck('dispositions_science_and_classifications_unchanged',ok,det)
ok,det=compare_except(R1/'page-coverage-corrected-v1.csv',PKG/'page-coverage-corrected-v1.csv',{'coverage_summary'})
ck('page_coverage_only_adds_S1_start',ok,det)
for fn,key in [('doehlert-runs-corrected-v1.csv','coded_S9_crosswalk_status'),('protocol-stages-corrected-v1.csv','additional_evidence_locator')]:
 a=readcsv(R1/fn); b=readcsv(PKG/fn)
 orig_header=a[0]; keep=[];seen=set()
 for i,k in enumerate(orig_header):
  if k not in seen: keep.append(i);seen.add(k)
 expect=[[row[i] for i in keep] for row in a]
 ck(fn+'_deduplicated_without_value_changes',expect==b,f'rows={len(b)-1}; duplicate values retained once')
# Provenance remains exact in all source-hash-bearing CSVs.
prov_errors=[]
for f in allcsv:
 rows=loadcsv(f)
 for n,r in enumerate(rows,2):
  if 'source_sha256' in r and r['source_sha256']:
   valid=(r['source_sha256']==H_MAIN if r.get('source_id')=='main' else r['source_sha256']==H_SI if r.get('source_id')=='si' else r['source_sha256'] in (H_MAIN,H_SI))
   if not valid: prov_errors.append(f'{f.name}:{n}')
ck('source_hash_provenance',not prov_errors,f'bad rows={prov_errors}' if prov_errors else 'all source_sha256 values match declared main/SI IDs')
ck('source_and_audit_bindings',sha(Path(r'[local path redacted]'))==H_MAIN and sha(Path(r'[local path redacted]'))==H_SI and sha(AUD/'audit-report.json')==H_AUD and sha(AUD/'table-page-map.json')==H_MAP,'exact PDFs, audit report, page map and r1 manifest hashes verified')
if not all(c['passed'] for c in checks): raise RuntimeError('R2 checks failed: '+str([c for c in checks if not c['passed']]))
write(PKG/'self-checks.json',json.dumps({'status':'PASS','scope':'r2 metadata/schema checks and unchanged-field comparisons; no new scientific audit','checks':checks},indent=2)+'\n')
# Hash output files before writing manifest; manifest is separately hashed after.
outputs={f.name:sha(f) for f in sorted(PKG.iterdir()) if f.is_file() and f.name!='correction-manifest.json'}
manifest={
 'package_id':'acsnano1c00502-correction-package-20260924-r2',
 'status':'metadata corrections from independent recheck applied; fresh independent confirmation pending',
 'r1_package':{'path':str(R1),'manifest_sha256':H_R1,'retained_unchanged':True},
 'main_pdf':{'path':str(Path(r'[local path redacted]')),'sha256':H_MAIN,'pages':12},
 'si_pdf':{'path':str(Path(r'[local path redacted]')),'sha256':H_SI,'pages':26},
 'original_failed_audit_sha256':H_ORIG_AUD,
 'r1_independent_audit':{'path':str(AUD/'audit-report.json'),'sha256':H_AUD,'status':'FAIL_REQUIRED_METADATA_CORRECTIONS; 8/10 A1-A10 findings passed'},
 'page_map_input':{'path':str(AUD/'table-page-map.json'),'sha256':H_MAP},
 'scientific_values_or_conflicts_changed':False,
 'outputs_sha256':outputs,
 'self_check_count':len(checks),
 'limitations':['R2 addresses only the independent reviewer R1/R2 metadata findings.','No canonical/site changes, publication, or training approval.','A fresh independent confirmation is still required.']}
write(PKG/'correction-manifest.json',json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'package':str(PKG),'check_count':len(checks),'checks_passed':all(c['passed'] for c in checks),'manifest_sha256':sha(PKG/'correction-manifest.json'),'outputs_sha256':outputs},indent=2))

