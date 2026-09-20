"""Assemble immutable, separately audited Heo SI chunks without changing data."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import copy, hashlib, json, sys

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'si-complete-candidate'
SI_SHA = '3b2e262af1932ed04cfddd596958c92d89c37099ab9dad8c4ce1f11254d4acc6'
NUMERIC = ['h', 'k', 'l', 'Fcal2', 'Fobs2', 'sigma_Fobs2']
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def dump(path, data): path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def bind(path): return {'path':str(path), 'sha256':sha(path)}

if (OUT / 'package-freeze.json').exists():
    archive = ROOT / 'si-complete-candidate-revision-1'
    if '--revise-after-archive' not in sys.argv or not all(
        (archive/p.name).is_file() and sha(archive/p.name)==sha(p)
        for p in OUT.iterdir() if p.is_file() and p.name in
        {'all-reflections.json','all-reflections.tsv','author-validation.json','package-freeze.json'}
    ): raise SystemExit('Existing freeze must be preserved and explicitly revised before rerun.')
OUT.mkdir(exist_ok=True)
progress = read(ROOT / 'si-numerical-progress-index.json')
snapshots=OUT/'input-snapshots'; snapshots.mkdir(exist_ok=True)
snapshot=snapshots/'si-numerical-progress-before-aggregate.json'
snapshot.write_bytes((ROOT/'si-numerical-progress-index.json').read_bytes())
chunks = copy.deepcopy(progress['chunks'])
chunks.append({'pages':[13,14], 'transcription':bind(ROOT/'si-pages13-14-transcription.json'),
               'audit':bind(ROOT/'si-pages-13-14-independent-audit.json')})
all_rows = []
checks = []
inputs = [bind(ROOT/'main-tables.json'), bind(ROOT/'source-scientific-audit.json'),
          bind(ROOT/'pairing-review.json'), bind(ROOT/'screening-audit.json'),
          bind(snapshot)]
chunk_summary = []
def check(name, value, detail=None):
    checks.append({'check':name,'passed':bool(value),'detail':detail})
    if not value: raise ValueError(name + ': ' + str(detail))

for chunk in chunks:
    path = Path(chunk['transcription']['path']); auditpath = Path(chunk['audit']['path'])
    check('transcription hash '+path.name, sha(path)==chunk['transcription']['sha256'])
    check('audit hash '+auditpath.name, sha(auditpath)==chunk['audit']['sha256'])
    doc = read(path); audit = read(auditpath)
    check('same SI generation '+path.name, doc['source_sha256']==SI_SHA)
    check('passed independent audit '+path.name, audit['status'].startswith('passed'), audit['status'])
    inputs += [bind(path), bind(auditpath)]
    auditref = {'path':auditpath.name,'sha256':sha(auditpath),'scope':audit['status']}
    for index, original in enumerate(doc['rows']):
        row = copy.deepcopy(original)
        row['author_transcription'] = {'path':path.name,'sha256':sha(path),'json_pointer':f'/rows/{index}'}
        row['effective_independent_audit'] = auditref
        for cell in row['cells']:
            cell['independent_numerical_audit'] = audit['status']
            cell['effective_audit_reference'] = auditref
        # Assert that every raw, numeric, uncertain-sign and provenance field is
        # unchanged; only the review status and explicit transport links differ.
        restored=copy.deepcopy(row)
        restored.pop('author_transcription'); restored.pop('effective_independent_audit')
        for a,b in zip(restored['cells'], original['cells']):
            a.pop('effective_audit_reference')
            if 'independent_numerical_audit' in b:
                a['independent_numerical_audit']=b['independent_numerical_audit']
            else: a.pop('independent_numerical_audit',None)
        check('lossless row '+row['row_id'], restored==original)
        check('all six numeric fields '+row['row_id'], set(NUMERIC).issubset(row['raw_cells']))
        all_rows.append(row)
    chunk_summary.append({'pages':chunk['pages'],'rows':len(doc['rows']),
                          'transcription':bind(path),'audit':bind(auditpath),
                          'audit_status':audit['status']})

row_ids=[r['row_id'] for r in all_rows]
hkls=[tuple(r['hkl']) for r in all_rows]
page_rows=Counter(); block_rows=Counter(); negatives=0; zeros=0; uncertain=[]
for row in all_rows:
    ev=row['cells'][0]['evidence']; page=ev['pdf_page']; block=ev['column_block']
    page_rows[page]+=1; block_rows[f'{page:02d}{block}']+=1
    values={c['evidence']['column_key']:c for c in row['cells']}
    for key in NUMERIC:
        c=values[key]
        if c['numeric_value'] is None:
            uncertain.append({'row_id':row['row_id'],'field':key,'cell':copy.deepcopy(c)})
    obs=values['Fobs2']['numeric_value']
    negatives+=int(obs is not None and obs<0); zeros+=int(obs==0)
    check('positive sigma '+row['row_id'], values['sigma_Fobs2']['numeric_value']>0)
check('all pages present', sorted(page_rows)==list(range(1,15)),dict(page_rows))
check('unique row locators', len(set(row_ids))==len(row_ids))
check('unique hkl indices without transforming',len(set(hkls))==len(hkls))
check('first printed hkl', hkls[0]==(1,1,1))
check('last printed hkl', hkls[-1]==(5,27,29))
check('only two retained uncertain signs',len(uncertain)==2)
check('uncertain cells identities', {(x['row_id'],x['field']) for x in uncertain}==
      {('si-p11-R-r035','Fobs2'),('si-p12-L-r012','Fcal2')})
tables=read(ROOT/'main-tables.json')
table1=tables['tables'][0]
# Exact source table cell, not an independently inferred count of experiments.
matching=[]
def walk(obj,path=''):
    if isinstance(obj,dict):
        if isinstance(obj.get('raw_cells'),list) and any('unique reflections' in str(x) for x in obj['raw_cells']):
            matching.append({'pointer':path,'row':obj})
        for k,v in obj.items():walk(v,path+'/'+str(k))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):walk(v,path+'/'+str(i))
walk(tables)
check('one unique-reflections source row',len(matching)==1,matching)
check('1209 matches selected Fd-3m table model',len(all_rows)==1209 and '1209' in str(matching[0]['row']['raw_cells']),matching)
counts={'pages':14,'rows':len(all_rows),'numeric_positions':len(all_rows)*6,
        'resolved_numeric_values':len(all_rows)*6-len(uncertain), 'unresolved_sign_cells':len(uncertain),
        'markers':len(all_rows),'definite_negative_Fobs2':negatives,'zero_Fobs2':zeros,
        'unique_hkl':len(set(hkls)),'rows_by_page':dict(sorted(page_rows.items())),
        'rows_by_block':dict(sorted(block_rows.items()))}
doc={'schema':'mattersyn-complete-si-reflection-candidate/1','source_id':'heo2003',
     'author':'/root','created_at':datetime.now(timezone.utc).isoformat(),
     'status':'all_chunks_independently_audited_aggregate_audit_pending',
     'source_generation':2,'source_sha256':SI_SHA,
     'title_as_printed':'Observed and Calculated Structure Factors Squared with Esds for In66-X',
     'coverage':'All 14 SI pages and all printed body rows; two sign cells remain unresolved.',
     'independent_complete_aggregate_audit_passed':False,
     'counts':counts,'chunk_audits':chunk_summary,
     'transport_policy':'Raw data and evidence are identical to immutable author chunks. Only inherited pre-audit status fields are replaced with hash-bound passed scoped audits, with explicit original chunk pointers.',
     'unresolved_cells':uncertain,'rows':all_rows,
     'scientific_limits':['Two signed numeric values remain null with their original magnitudes and candidates; no sign is selected.',
         'Negative observations are retained. No clipping, averaging, symmetry expansion or filtering is applied.',
         'Trailing o-like marks have no source-defined header and remain uninterpreted.',
         '1209 distinct rows agree with the main Table1 unique-reflection count for Fd-3m; 2335 measured reflections and 2032 for the alternative Fd-3 model are separate source counts.',
         'The 754 above-threshold reflections are not recounted by converting the printed F-squared fields to a guessed threshold.',
         'This is measured/calculated diffraction evidence, not atomic coordinates, a recipe variant, an ordered microstate or an exact structure-recipe training pair.']}
dump(OUT/'all-reflections.json',doc)
header=['row_id','pdf_page','block','row_in_block',*NUMERIC,'marker','Fcal2_raw','Fobs2_raw','audit_file']
lines=['\t'.join(header)]
for row in all_rows:
    ev=row['cells'][0]['evidence']; values={c['evidence']['column_key']:c for c in row['cells']}
    vals=[row['row_id'],ev['pdf_page'],ev['column_block'],ev['row_in_block']]
    vals += ['' if values[k]['numeric_value'] is None else values[k]['numeric_value'] for k in NUMERIC]
    vals += [row['raw_cells']['marker'],row['raw_cells']['Fcal2'],row['raw_cells']['Fobs2'],row['effective_independent_audit']['path']]
    lines.append('\t'.join(map(str,vals)))
(OUT/'all-reflections.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
report={'schema':'mattersyn-si-aggregate-author-check/1','author':'/root','status':'passed_mechanical_reconciliation_independent_audit_pending',
        'counts':counts,'source_table_reconciliation':matching,'checks':checks,
        'unresolved_sign_cells':[{'row_id':x['row_id'],'field':x['field'],'numeric_value':None} for x in uncertain]}
dump(OUT/'author-validation.json',report)
inputs.append(bind(Path(__file__)))
freeze={'schema':'mattersyn-si-aggregate-freeze/1','author':'/root','created_at':datetime.now(timezone.utc).isoformat(),
        'status':'pending_independent_aggregate_audit','inputs':inputs,
        'outputs':[bind(OUT/'all-reflections.json'),bind(OUT/'all-reflections.tsv'),bind(OUT/'author-validation.json')]}
dump(OUT/'package-freeze.json',freeze)
print(json.dumps({'counts':counts,'checks':len(checks),'freeze_sha256':sha(OUT/'package-freeze.json')},indent=2))
