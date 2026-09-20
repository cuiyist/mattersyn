"""Bounded presentation refresh; retain the completed independent science audit."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re

OUT=Path(__file__).resolve().parent;B=OUT.parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ptr(d,p):
    for k in p.split('/')[1:]:d=d[int(k)] if isinstance(d,list) else d[k]
    return d
def diff(a,b,p=''):
    if type(a)!=type(b):return [p]
    if isinstance(a,dict):return [q for k in a.keys()|b.keys() for q in ([p+'/'+k] if k not in a or k not in b else diff(a[k],b[k],p+'/'+k))]
    if isinstance(a,list):return [p] if len(a)!=len(b) else [q for i,(x,y) in enumerate(zip(a,b)) for q in diff(x,y,p+'/'+str(i))]
    return [] if a==b else [p]
baseline=read(OUT/'reader-audit-baseline.json');prior=baseline['prior_audit'];before=baseline['ledger']
path=S/'data/paper-reviews/stiger1999.json';actual=read(path);generated=read(S/'dist/data/paper-reviews/stiger1999.json')
patch=read(B/'public-review-proposal/final-reader-delta.json')
checks=[]
def check(name,ok,detail=''):checks.append({'name':name,'passed':bool(ok),'detail':detail})
check('Prior full audit retained without scientific rerun',prior['status'].startswith('passed') and prior['checks_passed']==1319)
for p in patch['patches']:check(p['item_id']+' guarded final field '+p['json_pointer'],ptr(actual,p['json_pointer'])==p['set'])
dd=diff(before,actual)
def allowed(p):
    return any(p==x['json_pointer'] or p.startswith(x['json_pointer']+'/') for x in patch['patches']) or bool(re.fullmatch(r'/(figures|tables|schemes|equations|source_notes)/\d+/(reviewed|reader_render_verified)',p)) or any(p==q or p.startswith(q+'/') for q in ['/independent_audit','/publication_status','/reader_verification','/remaining_gaps'])
check('Only approved reader presentation fields changed',all(allowed(p) for p in dd),repr(dd))
generated.pop('review_scope_label',None)
check('Generated ledger matches authored scientific and reader data',generated==actual)
bound={}
for name,oldsha in prior['artifact_sha256'].items():
    # Canonical records, standalone rendered records, exports, crops and evidence inventories remain immutable for this gate.
    relevant=(name.startswith(('data/records/','dist/data/records/','dist/records/','dist/assets/figures/','dist/data/exports/')) or name in ['dist/data/records.jsonl','private/canonical-records-audit.json','private/source-audit.json'])
    if relevant:
        p=B/name.removeprefix('private/') if name.startswith('private/') else S/name
        bound[name]=sha(p);check(name+' unchanged from accepted science audit',bound[name]==oldsha)
runtime=read(OUT/'reader-runtime-check.json')
check('Reader runtime passes against final files',runtime['status']=='passed' and all(sha(S/p)==h for p,h in runtime['artifact_sha256'].items()))
assets=[a for cat in ['figures','tables','schemes','equations','source_notes'] for a in actual[cat]]
check('All 15 original assets retain tested visibility flags',len(assets)==15 and all(a['reviewed'] and a['reader_render_verified'] for a in assets))
check('Actual SAED remains distinct from index drawing',any(a['id']=='figure-6b-saed' and a['duplicate_detail_crop'] for a in assets) and 'indexing schematic' in actual['figures'][5]['quantitative_context'][-1])
check('SI status unchanged',actual['review_scope']=='supplied_main_only_si_unverified')
failures=[c for c in checks if not c['passed']]
report={'status':'passed' if not failures else 'findings','checked_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Bounded final reader presentation and hash check. The prior 1,319-check scientific / source-to-reader audit remains intact. Browser geometry and deployment are root-owned.',
        'checks_passed':len(checks)-len(failures),'check_count':len(checks),'findings':failures,
        'changed_ledger_paths':dd,'prior_audit_sha256':sha(OUT/'canonical-to-reader-audit.json'),
        'artifact_sha256':{'data/paper-reviews/stiger1999.json':sha(path),'dist/data/paper-reviews/stiger1999.json':sha(S/'dist/data/paper-reviews/stiger1999.json'),
                           'reader-runtime-check.json':sha(OUT/'reader-runtime-check.json')},
        'unchanged_scientific_bindings':bound,'checks':checks}
(OUT/'final-presentation-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k]for k in ['status','checks_passed','check_count','findings']}))
raise SystemExit(bool(failures))
