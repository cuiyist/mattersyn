"""Independent aggregate reconciliation; do not rerun the author's builder."""
from pathlib import Path
from collections import Counter
from decimal import Decimal
from datetime import datetime,timezone
import json,csv,hashlib,copy
O=Path(__file__).resolve().parent;H=O.parent;A=H/'si-complete-candidate-revision-1'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dump=lambda p,x:Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[];bound={};N=['h','k','l','Fcal2','Fobs2','sigma_Fobs2'];FIELDS=N+['marker']
def ck(ok,label):
 checks.append({'passed':bool(ok),'check':label})
 if not ok:raise AssertionError(label)
def bind(p,expected=None):
 p=Path(p);s=sha(p);ck(expected is None or s==expected,'Exact file hash '+p.name);bound[str(p)]=s;return s
def audit_bound(a,p,s):
 hits=[v for k,v in a['bound_files'].items()if Path(k)==Path(p)]
 ck(len(hits)==1 and hits[0]==s,'Scoped audit binds current source input '+Path(p).name)
def pointer(obj,p):
 for k in p.strip('/').split('/'):obj=obj[int(k)]if isinstance(obj,list)else obj[k.replace('~1','/').replace('~0','~')]
 return obj
freeze=read(O/'package-freeze.json');bind(O/'package-freeze.json','85cb4b1d71aa152752ca4882a1143dcd3a341e5992e8807f20841041d9d23989')
ck(freeze['author']=='/root','Distinct aggregate author from independent auditor')
for category in ['inputs','outputs']:
 for x in freeze[category]:bind(x['path'],x['sha256'])
data=read(O/'all-reflections.json');author_report=read(O/'author-validation.json')
ck(data['author']=='/root'and data['source_generation']==2,'Correct author/source generation')
ck(not data['independent_complete_aggregate_audit_passed'],'Frozen author package does not self-certify independent audit')
ck(data['source_sha256']=='3b2e262af1932ed04cfddd596958c92d89c37099ab9dad8c4ce1f11254d4acc6','Original SI identity')
source=Path(data['rows'][0]['cells'][0]['evidence']['source_path']);bind(source,data['source_sha256'])
ck(len(data['chunk_audits'])==7,'Exactly seven immutable source chunks')
all_originals=[];row_registry={};chunk_reports=[];seen_pages=[]
for i,c in enumerate(data['chunk_audits']):
 expected_pages=[2*i+1,2*i+2];ck(c['pages']==expected_pages,'Ordered nonoverlapping two-page audit scope '+str(expected_pages));seen_pages+=c['pages']
 p=Path(c['transcription']['path']);ap=Path(c['audit']['path']);ps=bind(p,c['transcription']['sha256']);aps=bind(ap,c['audit']['sha256']);original=read(p);audit=read(ap)
 ck(original['source_sha256']==data['source_sha256']and Path(original['source_path'])==source,'Same original SI for chunk '+p.name)
 ck(audit['status']==c['audit_status']and audit['status'].startswith('passed'),'Passed scoped audit status retained '+ap.name)
 ck(audit.get('auditor',audit.get('reviewer'))!=original['author'],'Original transcription and numerical reviewer are distinct '+ap.name)
 scope=audit.get('actual_manual_scope',audit.get('exact_scope'));ck(scope['pdf_pages']==expected_pages,'Actual prior manual scope matches chunk '+ap.name)
 ck(scope.get('body_rows',scope.get('rows'))==len(original['rows'])==c['rows'],'Prior numerical audit covers every source row '+ap.name)
 audit_bound(audit,p,ps);audit_bound(audit,source,data['source_sha256'])
 auditref={'path':ap.name,'sha256':aps,'scope':audit['status']}
 for n,row in enumerate(original['rows']):
  ck(row['row_id']not in row_registry,'Unique source row locator '+row['row_id']);row_registry[row['row_id']]={'row':row,'document':original,'path':p,'hash':ps,'index':n,'audit':auditref};all_originals.append(row)
 chunk_reports.append({'pages':expected_pages,'rows':len(original['rows']),'transcription':c['transcription'],'audit':c['audit'],'status':audit['status'],'prior_manual_scope_verified':True,'fresh_manual_reread_in_this_audit':False})
ck(seen_pages==list(range(1,15)),'Prior independent scopes cover all 14 pages exactly once')
ck(len(data['rows'])==len(all_originals)==1209,'All source rows transported with no omission or added rows')
page_counts=Counter();block_counts=Counter();negative=[];zeros=[];unresolved=[];cell_ids=[];raw_format_differences=[]
for agg,orig in zip(data['rows'],all_originals):
 rid=orig['row_id'];reg=row_registry[rid];ck(agg['row_id']==rid,'Printed source row order retained '+rid)
 ck(agg['author_transcription']=={'path':reg['path'].name,'sha256':reg['hash'],'json_pointer':f'/rows/{reg["index"]}'},'Exact source chunk and JSON pointer '+rid)
 ck(pointer(reg['document'],agg['author_transcription']['json_pointer'])==orig,'Source pointer resolves to original row '+rid)
 ck(agg['effective_independent_audit']==reg['audit'],'Row audit link includes exact scope/hash '+rid)
 ck(set(agg)-set(orig)=={'author_transcription','effective_independent_audit'},'Only authorized row transport metadata added '+rid)
 for k in orig:
  if k!='cells':ck(agg[k]==orig[k],'Original row field retained '+rid+' '+k)
 ck(len(agg['cells'])==len(orig['cells'])==7,'All seven fields transported '+rid)
 for ac,oc in zip(agg['cells'],orig['cells']):
  cid=oc['cell_id'];cell_ids.append(cid);ck(ac['cell_id']==cid,'Exact cell identity '+cid)
  ck(ac['effective_audit_reference']==reg['audit']and ac['independent_numerical_audit']==reg['audit']['scope'],'Cell inherits only its bound scoped audit '+cid)
  ck(set(ac)-set(oc)==({'effective_audit_reference'}if'independent_numerical_audit'in oc else{'effective_audit_reference','independent_numerical_audit'}),'No other cell metadata added '+cid)
  for key in oc:
   if key!='independent_numerical_audit':ck(ac[key]==oc[key],'Original source cell field retained '+cid+' '+key)
  key=ac['evidence']['column_key'];ck(key in FIELDS and ac['raw_text']==agg['raw_cells'][key],'Raw source text exact '+cid)
  ck(ac['evidence']['source_sha256']==data['source_sha256'],'Source hash at every cell '+cid)
  if key in N:
   if ac['numeric_value']is None:unresolved.append({'row_id':rid,'field':key,'cell':ac})
   else:ck(Decimal(str(ac['numeric_value']))==Decimal(ac['raw_text']),'Exact resolved decimal '+cid)
  else:ck(ac['raw_text']=='o'and ac['numeric_value']is None,'Uninterpreted marker retained as nonnumeric '+cid)
  ck(ac['unit']is None and ac['unit_status']==('not_applicable_index'if key in N[:3]else'not_applicable_marker'if key=='marker'else'unreported'),'Units and missingness retained '+cid)
 ev=agg['cells'][0]['evidence'];page_counts[ev['pdf_page']]+=1;block_counts[f'{ev["pdf_page"]:02d}{ev["column_block"]}']+=1
 values={c['evidence']['column_key']:c['numeric_value']for c in agg['cells']};v=values['Fobs2']
 if v is not None and v<0:negative.append({'row_id':rid,'value':v})
 if v==0:zeros.append({'row_id':rid,'value':v})
ck(len(cell_ids)==len(set(cell_ids))==8463,'All 8,463 field identities are unique')
hkls=[tuple(r['hkl'])for r in data['rows']];ck(len(hkls)==len(set(hkls))==1209,'All 1,209 hkl rows are unique without symmetry transformation')
ck(hkls[0]==(1,1,1)and hkls[-1]==(5,27,29),'Printed first and last reflection indices')
order=[(r['cells'][0]['evidence']['pdf_page'],r['cells'][0]['evidence']['column_block'],r['cells'][0]['evidence']['row_in_block'])for r in data['rows']];ck(order==sorted(order),'Original page/block/body-row sequence retained')
expected_pages={1:80,**{p:90 for p in range(2,14)},14:49}
expected_blocks={f'{p:02d}{b}':(40 if p==1 else (25 if b=='L' else 24)if p==14 else 45)for p in range(1,15)for b in ['L','R']}
ck(dict(page_counts)==expected_pages and dict(block_counts)==expected_blocks,'Full page and unequal boundary-block counts match audited source coverage')
ck(len(negative)==137 and len(zeros)==1 and zeros[0]['row_id']=='si-p10-R-r010','All 137 definite negative observations and one printed zero preserved')
ck(data['unresolved_cells']==unresolved and len(unresolved)==2,'Exactly the two original unresolved cells carried into summary')
for u in unresolved:
 c=u['cell'];mag={'si-p11-R-r035':1965.46,'si-p12-L-r012':3757.09}[u['row_id']];ck(c['numeric_value']is None and c['magnitude_value']==mag and c['signed_value_candidates']==[-mag,mag],'Unresolved sign remains null with original candidates '+u['row_id'])
 ck(c['transcription_status']=='source_sign_unresolved'and c['sign_status']=='unresolved_from_retained_scan'and c['raw_text_includes_editorial_annotation']is True,'Passed audit did not erase source uncertainty '+u['row_id'])
computed={'pages':14,'rows':1209,'numeric_positions':7254,'resolved_numeric_values':7252,'unresolved_sign_cells':2,'markers':1209,'definite_negative_Fobs2':137,'zero_Fobs2':1,'unique_hkl':1209,'rows_by_page':{str(k):v for k,v in sorted(page_counts.items())},'rows_by_block':dict(sorted(block_counts.items()))}
ck(data['counts']==computed==author_report['counts'],'Independently recomputed aggregate totals match exported metadata')
with (O/'all-reflections.tsv').open(encoding='utf-8',newline='')as f:
 reader=csv.DictReader(f,delimiter='\t');tsv=list(reader);headers=reader.fieldnames
ck(headers==['row_id','pdf_page','block','row_in_block',*N,'marker','Fcal2_raw','Fobs2_raw','audit_file'],'Explicit typed TSV columns and raw uncertain-sign companion columns')
ck(len(tsv)==1209,'All TSV rows present')
blank_fields=[]
for t,r in zip(tsv,data['rows']):
 ev=r['cells'][0]['evidence'];values={c['evidence']['column_key']:c for c in r['cells']};rid=r['row_id']
 ck(t['row_id']==rid and int(t['pdf_page'])==ev['pdf_page']and t['block']==ev['column_block']and int(t['row_in_block'])==ev['row_in_block'],'TSV source row identity '+rid)
 for k in N:
  c=values[k]
  if c['numeric_value']is None:
   ck(t[k]=='','TSV unknown signed value is blank rather than zero/positive '+rid+k);blank_fields.append({'row_id':rid,'field':k,'raw_companion':t[k+'_raw']})
   ck(t[k+'_raw']=='[sign_unresolved]'+c['visible_digits'],'TSV blank explained by explicit source-sign label '+rid+k)
  else:ck(t[k]!=''and Decimal(t[k])==Decimal(str(c['numeric_value'])),'TSV exact decimal value '+rid+k)
  if t[k]!=c['raw_text']:raw_format_differences.append({'row_id':rid,'field':k,'tsv':t[k],'raw_source':c['raw_text']})
 ck(t['Fcal2_raw']==r['raw_cells']['Fcal2']and t['Fobs2_raw']==r['raw_cells']['Fobs2']and t['marker']==r['raw_cells']['marker'],'TSV raw source fields and marker unchanged '+rid)
 ck(t['audit_file']==r['effective_independent_audit']['path'],'TSV audit filename resolves through full JSON chunk registry '+rid)
ck({(x['row_id'],x['field'])for x in blank_fields}=={('si-p11-R-r035','Fobs2'),('si-p12-L-r012','Fcal2')},'Exactly two TSV blanks, both explicitly qualified')
# The original main Table 1 crop was actually reopened and read in this audit.
tables=read(H/'main-tables.json');t1=tables['tables'][0];modelrows={r['row_id']:r for r in t1['model_rows']};asset=H/'reader-assets/main-table-1.png';bind(asset);bind(tables['source']['path'],tables['source']['sha256'])
ck(t1['source']['pdf_page']==4 and t1['source']['printed_page']==1123,'Original main Table1 locator')
for rid,vals in [('measured-reflections',['2335','2335']),('unique-reflections',['1209','2032']),('strong-reflections',['754','1207'])]:ck(modelrows[rid]['raw_cells'][1:]==vals,'Original Table1 distinct model counts '+rid)
ck(modelrows['unique-reflections']['model_values']['Fd3̄m']['value']==1209 and modelrows['unique-reflections']['model_values']['Fd3̄']['value']==2032,'1209 is Fd-3m count, 2032 belongs to alternative Fd-3')
ck('Fo > 4σ(Fo)'in modelrows['strong-reflections']['raw_cells'][0],'754 is source amplitude-threshold count, not an invented F-squared filter')
matches=author_report['source_table_reconciliation'];ck(len(matches)==1 and pointer(tables,matches[0]['pointer'])==matches[0]['row']==modelrows['unique-reflections'],'Author count pointer identifies actual original unique-reflection row')
ck(any('754'in s and 'not recounted'in s for s in data['scientific_limits'])and any('not atomic coordinates'in s for s in data['scientific_limits']),'No guessed threshold or exact structure claims')
# Narrow packaging correction: immutable progress snapshot replaces mutable journal dependency.
bind(A/'package-freeze.json','7e1d02750cb39f06b363362d4a3cb3d2212bfb7eb373bb43739d1310b9b1294c');oldfreeze=read(A/'package-freeze.json')
for x in oldfreeze['outputs']:bind(A/Path(x['path']).name,x['sha256'])
oldinputs={Path(x['path']).name:x for x in oldfreeze['inputs']};bind(A/'reconcile_si.py',oldinputs['reconcile_si.py']['sha256']);bind(A/'si-numerical-progress-index.json',oldinputs['si-numerical-progress-index.json']['sha256'])
snapshot=O/'input-snapshots/si-numerical-progress-before-aggregate.json';bind(snapshot,oldinputs['si-numerical-progress-index.json']['sha256'])
ck(snapshot.read_bytes()==(A/'si-numerical-progress-index.json').read_bytes(),'Immutable snapshot exactly preserves initially bound progress payload')
ck(all(Path(x['path'])!=H/'si-numerical-progress-index.json'for x in freeze['inputs'])and any(Path(x['path'])==snapshot for x in freeze['inputs']),'Mutable progress journal removed from final freeze dependencies')
olddata=read(A/'all-reflections.json');newcopy=copy.deepcopy(data);newcopy['created_at']=olddata['created_at'];ck(newcopy==olddata,'Only aggregate creation timestamp changed; every data/provenance field unchanged across packaging revision')
ck((A/'all-reflections.tsv').read_bytes()==(O/'all-reflections.tsv').read_bytes(),'TSV bytes unchanged across packaging correction')
ck((A/'author-validation.json').read_bytes()==(O/'author-validation.json').read_bytes(),'Original mechanical reconciliation report unchanged')
bind(Path(__file__))
for p,s in bound.items():ck(sha(p)==s,'Unchanged at independent audit close '+Path(p).name)
source_counts={'source_asset':str(asset),'asset_sha256':sha(asset),'pdf_page':4,'printed_page':1123,'measured_reflections_both_models':2335,'Fd-3m_227_unique_reflections':1209,'Fd-3_203_unique_reflections':2032,'Fd-3m_Fo_gt_4sigmaFo':754,'Fd-3_Fo_gt_4sigmaFo':1207,'interpretation':'Count correspondence supports reconciliation of the selected model; no F-squared threshold transformation, symmetry inference or exact atomic-coordinate pairing was performed.'}
correction={'id':'mutable-progress-freeze-input','reported_by':'/root','status':'resolved_and_independently_verified','initial_freeze_sha256':sha(A/'package-freeze.json'),'final_freeze_sha256':sha(O/'package-freeze.json'),'immutable_snapshot':{'path':str(snapshot),'sha256':sha(snapshot)},'scope':'Root replaced mutable progress-journal dependency with byte-identical immutable snapshot and preserved the initial package. Only created_at changed in aggregate JSON; TSV and row data/provenance are unchanged.'}
out={'schema':'mattersyn-independent-si-aggregate-audit/1','source_id':'heo2003','auditor':'/root/norberg2004_extract','aggregate_author':'/root','audited_at':datetime.now(timezone.utc).isoformat(),'status':'passed_aggregate_reconciliation_with_two_preserved_source_sign_uncertainties','package_freeze_sha256':sha(O/'package-freeze.json'),'counts':computed,'scope':{'kind':'aggregate reconciliation of seven previously independently read source chunks','fresh_manual_source_inspection':['Original main Table1 crop: both model columns, measured/unique/threshold rows and source locator'],'fresh_manual_reread_of_all_SI_cells':False,'prior_chunk_scope_and_hash_checks':chunk_reports,'every_aggregate_row_and_cell_compared_to_original_chunk':True,'original_source_unchanged':True},'main_table_count_reconciliation':source_counts,'transport':{'all_1209_rows_and_8463_cells_losslessly_preserved':True,'allowed_changes':'Only explicit author-chunk/audit references added and inherited independent_numerical_audit status replaced with the corresponding exact hash-bound scoped audit. Original raw text, typed values, units, missingness, uncertainty, sample labels, notes and source provenance retained.','numeric_TSV_checked':True,'TSV_two_nulls':blank_fields,'TSV_raw_format_differences':raw_format_differences,'TSV_companion_scope':'TSV is the typed flat view. JSON retains every original raw field, unit/missingness state and full hash/pointer provenance. TSV row_id/audit_file join the JSON registry; it is not a standalone atomic-structure export.'},'negative_observations':negative,'zero_observations':zeros,'preserved_source_uncertainties':[{'row_id':u['row_id'],'field':u['field'],'visible_digits':u['cell']['visible_digits'],'numeric_value':None,'signed_value_candidates':u['cell']['signed_value_candidates']}for u in unresolved],'resolved_packaging_findings':[correction],'open_required_corrections':[],'mechanical_checks':checks,'mechanical_check_count':len(checks),'bound_files':bound,'limits':['This audit reconciles already audited source chunks; it does not claim a fresh visual rereading of all SI cells.','Two source signs remain unreadable. Their magnitudes/candidates are retained and neither signed value is approved.','The SI header/main-paper identity caveat and source-defined units/marker limits remain in the original chunk/pairing records.','No exact ordered structure, atomic-coordinate CIF, recipe variant, exact structure–recipe training pair, website approval or publication is asserted.'],'training_eligible':False,'published':False,'source_or_author_files_modified':False}
dump(O/'independent-audit.json',out)
(O/'independent-audit.md').write_text(f'''# Heo SI aggregate independent audit

Passed aggregate reconciliation with **two preserved source-sign uncertainties**. All seven scoped audit/source hashes were checked; all **1,209 rows and 8,463 fields** were independently compared with their original immutable chunks. Raw text, 7,254 numeric positions, 7,252 resolved values, units/missingness, uncertainty metadata, sample labels and provenance are retained. Only bound audit/transport metadata changes. There are 137 definite negative Fobs² observations, one printed zero and 1,209 uninterpreted markers.

The two signed values remain null in JSON and blank in the typed TSV, whose adjacent raw fields explicitly say `[sign_unresolved]`. Their magnitudes and ± candidates remain unchanged. TSV row IDs and audit names link to the full JSON provenance; JSON is the complete raw/source record.

The original main Table 1 was reopened. Its **1,209 unique reflections belong to Fd-3m/227**; **2,032 belong to Fd-3/203**. Both columns report **2,335 measured reflections**. The selected-model **754** count uses **Fo > 4σ(Fo)** and was not recomputed from squared fields. These are reflection-count distinctions, not additional recipes or exact atomic structures.

One packaging issue was resolved: the mutable progress-journal dependency was replaced by a byte-identical immutable snapshot. The initial package is preserved; the revised JSON differs only in creation time, and TSV bytes/data/provenance are unchanged. No required correction remains.

This is an aggregate audit using prior independent numerical readings, **not a fresh visual rereading of every SI cell**. It does not approve either unresolved sign, an ordered/exact structure–recipe pair, training eligibility or publication. The {len(checks):,} independent mechanical checks and exact bound files are recorded in the JSON.

Final package freeze SHA256: `{sha(O/'package-freeze.json')}`.
''',encoding='utf-8')
print(json.dumps({'status':out['status'],'checks':len(checks),'bound_files':len(bound),'raw_format_difference_count':len(raw_format_differences),'audit_sha256':sha(O/'independent-audit.json')}))
