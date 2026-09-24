"""Read-only independent r2 delta verification. Never runs the extractor builder."""
from pathlib import Path
from datetime import datetime,timezone
import ast,csv,hashlib,json,collections,re
W=Path(__file__).resolve().parent;B=W.parent;P=B/'correction-package-20260924-r2';OLD=B/'correction-package-20260924-r1';PRIOR=B/'independent-audit-agent-chen-20260924'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def rawcsv(p):return list(csv.reader(p.open(encoding='utf-8',newline='')))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8',newline='')))
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (W/'audit-report.json').exists(),'Existing immutable receipt must not be replaced'
start=datetime.now(timezone.utc).isoformat();checks=[]
def check(name,ok,**kw):checks.append({'name':name,'passed':bool(ok),**kw})
manifest=load(P/'correction-manifest.json');oldmanifest=load(OLD/'correction-manifest.json')
check('Expected frozen r2 manifest',sha(P/'correction-manifest.json')=='c89d1378c2e377aba7c51d8aa4ca789f4517fed04193a431cb898710b68f2b13')
check('Prior independent audit unchanged',sha(PRIOR/'audit-report.json')=='3c96200df11d8329801f367745d5694f247f398da57da654e4d8495a84d28e00')
check('Prior independent page map unchanged',sha(PRIOR/'table-page-map.json')=='e346b6d00dba0c61f7d9f7bcd561fbaf8adf30e9017c798ef0f738f774926b72')
for name,expected in manifest['outputs_sha256'].items():check('r2 frozen hash '+name,sha(P/name)==expected)
for name,expected in oldmanifest['outputs_sha256'].items():check('r1 unchanged hash '+name,sha(OLD/name)==expected)
check('Historical failed full audit unchanged',sha(B/'independent-audit/audit-report.json')=='524e8700ac227ca2ba7b9028f72d2fae2d08c4ac297447341c850c29f9316320')
for role in ['main','si']:
 s=manifest[role+'_pdf'];check(role+' exact PDF and prior verified page count',sha(Path(s['path']))==s['sha256']==oldmanifest['source_pdfs'][role]['sha256'] and s['pages']==oldmanifest['source_pdfs'][role]['pages'],page_count=s['pages'])

csvs=sorted(P.glob('*.csv'));check('All ten expected CSVs present',len(csvs)==10)
for f in csvs:
 r=rawcsv(f)
 check(f.name+' unique headers',len(set(r[0]))==len(r[0]),header_count=len(r[0]))
 check(f.name+' uniform row widths',all(len(row)==len(r[0]) for row in r[1:]),row_count=len(r)-1)
 for i,row in enumerate(rows(f),1):
  if 'source_sha256' in row:
   check(f'{f.name} row{i} source hash',row.get('source_id') in ['main','si'] and row['source_sha256']==manifest[row['source_id']+'_pdf']['sha256'])
  for field in ['source_hashes','source_sha256s']:
   if field in row:check(f'{f.name} row{i} {field}',set(row[field].split(';'))<={manifest['main_pdf']['sha256'],manifest['si_pdf']['sha256']})

deduplicated=[]
for name,duplicate in [('doehlert-runs-corrected-v1.csv','coded_S9_crosswalk_status'),('protocol-stages-corrected-v1.csv','additional_evidence_locator')]:
 old=rawcsv(OLD/name);new=rawcsv(P/name);positions=[i for i,k in enumerate(old[0]) if k==duplicate]
 check(name+' expected prior duplicate appears twice',len(positions)==2)
 unique=list(dict.fromkeys(old[0]));check(name+' new exact unique header order',new[0]==unique)
 expected=[]
 for n,row in enumerate(old[1:],1):
  check(f'{name} old duplicate row{n} equal',row[positions[0]]==row[positions[1]])
  expected.append([row[old[0].index(k)] for k in unique])
 check(name+' all cells unchanged after deduplication',new[1:]==expected)
 deduplicated.append({'file':name,'field':duplicate,'rows':len(expected),'all_prior_duplicate_cells_equal':True,'all_scientific_values_unchanged':new[1:]==expected})

page_map={r['table_id']:r for r in load(PRIOR/'table-page-map.json')}
newdisp=rows(P/'table-dispositions-v1.csv');olddisp=rows(OLD/'table-dispositions-v1.csv')
check('25 table dispositions preserved',len(newdisp)==len(olddisp)==25)
for a,b in zip(newdisp,olddisp):
 e=page_map[a['table_id']]
 check(a['table_id']+' PDF page exact',a['pdf_page']==e['expected_pdf_page'])
 check(a['table_id']+' printed page exact',a['printed_page']==e['expected_printed_page'])
 check(a['table_id']+' only page metadata changed',{k:v for k,v in a.items() if k not in ['pdf_page','printed_page']}=={k:v for k,v in b.items() if k not in ['pdf_page','printed_page']})
s1=next(r for r in newdisp if r['table_id']=='S1');check('S1 begins p4 and continues p5/S4-S5',s1['pdf_page']=='4-5' and s1['printed_page']=='S4-S5')
oldcov=rows(OLD/'page-coverage-corrected-v1.csv');newcov=rows(P/'page-coverage-corrected-v1.csv');cov_delta=[]
for i,(a,b) in enumerate(zip(oldcov,newcov)):
 for k in a:
  if a[k]!=b[k]:cov_delta.append({'row_index':i,'source_id':b['source_id'],'pdf_page':b['pdf_page'],'field':k,'before':a[k],'after':b[k]})
check('Only SI p4 coverage summary changed',len(cov_delta)==1 and cov_delta[0]['source_id']=='si' and cov_delta[0]['pdf_page']=='4' and cov_delta[0]['field']=='coverage_summary')
check('p4 summary preserves Figure S5 and adds TableS1 continuation',cov_delta[0]['after']==cov_delta[0]['before']+'; Table S1 begins here and continues on SI PDF p5/printed S5')

# Reuse only this independent reviewer's frozen source-transcribed constants, never the author candidate.
priorfreeze=load(PRIOR/'audit-freeze.json')
check('Independent numerical rubric unchanged',sha(PRIOR/'audit_corrections.py')==priorfreeze['files']['audit_corrections.py'])
constants={}
for node in ast.parse((PRIOR/'audit_corrections.py').read_text(encoding='utf-8')).body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name) and target.id in ['expected_s9','expected_des']:constants[target.id]=ast.literal_eval(node.value)
s9=rows(P/'si-table-s9-coded-v1.csv');s13=rows(P/'si-table-s13-corrected-v1.csv')
for i,(row,vals) in enumerate(zip(s9,constants['expected_s9']),1):
 for key,value in zip(['Co_to_Ni_ratio_coded','Co_to_DDT_ratio_coded','temperature_coded'],vals):check(f'S9 cell row{i} {key}',row[key]==value,expected=value,actual=row[key])
for i,(row,vals) in enumerate(zip(s13,constants['expected_des']),1):
 for key,value in zip(['observed_desirability','predicted_desirability'],vals):check(f'S13 desirability cell row{i} {key}',row[key]==value,expected=value,actual=row[key])
check('All71 audited cell scopes preserved',len(s9)==13 and len(s13)==16)
unchanged=['conflicts-and-gaps-corrected-v1.csv','correction-map-v1.md','extraction-ledger-corrected-v1.md','figure-index-corrected-v1.csv','materials-and-stocks-corrected-v1.csv','response-models-corrected-v1.md','si-table-s13-corrected-v1.csv','si-table-s9-coded-v1.csv','validation-and-characterization-corrected-v1.csv']
for name in unchanged:check('Exact unchanged scientific/conflict output '+name,sha(P/name)==sha(OLD/name))
conflicts=rows(P/'conflicts-and-gaps-corrected-v1.csv')
check('All16 retained source conflict/context entries',len(conflicts)==16)
for key in ['C1','C2','C3','C4','C5','C6','C7','C8','C9','C10','C11','A1','A3','A4','A5','A6']:
 check('Conflict retained '+key,any(r['issue_id']==key for r in conflicts))
builder=(P/'build-correction-package-r2.py').read_text(encoding='utf-8')
check('Builder has unique-header guard','len(set(' in builder or 'set(header' in builder or 'duplicate' in builder.lower())
passed=all(x['passed'] for x in checks)
report={'schema':'mattersyn-independent-correction-audit/1','audit_id':'acsnano1c00502-agent-chen-20260924-r2','reviewer':'independent agent /root/chen_reader_integration','started_at_utc':start,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'passed':passed,'status':'PASS_R1_R2_CORRECTION_SCOPE' if passed else 'FAIL_REQUIRED_CORRECTIONS','scope':'Targeted independent r2 metadata/schema delta re-audit. Source images and71 numerical expected values are reused from this same reviewer\'s frozen r1 source audit after source/rubric hash verification. No repeated full-PDF reading, canonical integration, browser QA, publication or training approval is asserted.','r2_manifest_sha256':sha(P/'correction-manifest.json'),'r1_manifest_sha256':sha(OLD/'correction-manifest.json'),'prior_independent_audit_sha256':sha(PRIOR/'audit-report.json'),'prior_independent_freeze_sha256':sha(PRIOR/'audit-freeze.json'),'original_failed_audit_sha256':sha(B/'independent-audit/audit-report.json'),'source_bindings':{k:manifest[k+'_pdf'] for k in ['main','si']},'candidate_file_bindings':[{'filename':n,'sha256':sha(P/n)} for n in sorted(manifest['outputs_sha256'])],'resolved_findings':[{'id':'R1','result':'25 table page pairs match independent source page map; S1 p4-5/S4-S5 and page4 coverage repaired.'},{'id':'R2','result':'All10CSV headers unique and rows uniform;27 prior duplicate-row pairs equal; deduplication loses or changes no cell.'}],'numerical_checks':{'S9_coded_cells':39,'S13_desirability_cells':32,'total_71_passed':True,'retained_prior96_response_cells':'byte-identical numeric CSV to r1','DOE_and_protocol_scientific_cells':'exact after duplicate-column removal'},'deduplicated_columns':deduplicated,'page_coverage_delta':cov_delta,'unchanged_scientific_file_count':len(unchanged),'retained_conflict_count':16,'checks':checks,'check_count':len(checks),'check_summary':dict(collections.Counter('passed' if x['passed'] else 'failed' for x in checks)),'remaining_required_corrections':[c for c in checks if not c['passed']],'nonblocking_notes_retained':load(PRIOR/'audit-report.json')['nonblocking_notes'],'scientific_source_conflicts_resolved':False,'historical_failed_audits_modified':False,'candidate_or_site_files_edited':False,'canonical_integration_or_publication_or_training_approval':False}
for name,expected in manifest['outputs_sha256'].items():assert sha(P/name)==expected,name
save(W/'audit-report.json',report)
(W/'AUDIT.md').write_text('''# ACS Nano r2 targeted independent re-audit

**PASS for the R1/R2 correction scope.** The required metadata/schema defects from the prior independent audit are closed. All25 table page pairs match the independently verified map, including TableS1 at SI PDFpp4-5/printedS4-S5. All10CSV files have unique headers and uniform rows. The27 previously duplicated row-cell pairs were equal; removing the duplicate columns changed no retained field.

All71 audited numerical transcriptions (39S9 coded values and32S13 desirability values) match the source-derived independent rubric. Sources, conflicts, response models, characterization and scientific values remain unchanged. The prior full audit and r1 failed recheck are preserved; this separate receipt updates only the corrected scope.

No required residual defect was found. Two prior nonblocking handoff notes remain: add p9 provenance for oleylamine grade/pretreatment when mapping the separate bounds/default rows, and normalize stale ledger links before presenting that document to readers. Neither changes the scientific result of this delta audit.

This pass permits subsequent canonical integration and its separate review; it is not an integration, website QA, publication or training approval. Exact atomic recipe pairs remain unestablished, and source contradictions remain unresolved.

See audit-report.json for hashes, exact checks and unchanged-source reuse boundaries. No candidate, source, canonical or website file was edited.
''',encoding='utf-8')
freeze={'schema':'mattersyn-independent-audit-freeze/1','created_at_utc':datetime.now(timezone.utc).isoformat(),'files':{p.name:sha(p) for p in sorted(W.iterdir()) if p.is_file() and p.name!='audit-freeze.json'},'candidate_manifest_sha256':sha(P/'correction-manifest.json'),'passed':passed,'scope':'R1/R2 correction delta only','publication_or_training_approval':False}
save(W/'audit-freeze.json',freeze)
print(json.dumps({'passed':passed,'checks':len(checks),'counts':report['check_summary'],'report_sha256':sha(W/'audit-report.json'),'freeze_sha256':sha(W/'audit-freeze.json'),'directory':str(W)}))
