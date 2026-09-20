import json,hashlib,math,re
from decimal import Decimal
from collections import Counter
from pathlib import Path
O=Path(__file__).resolve().parent;L=O.parent.parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def check(n,b):
    checks.append({'check':n,'passed':bool(b)})
    assert b,n
source=load(L/'source-tables.json');cells={c['id']:c for t in source['tables'] for r in t['rows'] for c in r['cells']}
def walk(x):
    if isinstance(x,dict):
        if x.get('id') in cells and 'raw_text' in x:yield x
        else:
            for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
seen=[]
for phase in ['a','b']:
    m=load(O/f'lian2021-bulk-{phase}-non-h.json')
    for c in walk(m):check(c['id']+' exact raw/typed object',c==cells[c['id']]);seen.append(c['id'])
    expected={'a':{'C':48,'N':4,'Sb':2,'Cl':10},'b':{'C':96,'N':8,'Sb':8,'Cl':32}}[phase]
    check(phase+' nominal non-H Z consistency',m['counts']['geometric_elements']==expected)
    check(phase+' no H inferred',all(s['element']!='H' for s in m['asymmetric_unit_sites']))
    check(phase+' all unapproved flags',all(v is False for v in m['eligibility'].values()))
    text=(O/f'lian2021-bulk-{phase}-non-h-partial.cif').read_text(encoding='utf-8')
    site_lines={line.split()[0]:line.split() for line in text.splitlines() if re.match(r'^(?:Sb|Cl|N|C)[0-9A-Z]+ (?:Sb|Cl|N|C) ',line)}
    adp_lines={line.split()[0]:line.split() for line in text.splitlines() if re.match(r'^(?:Sb|Cl|N|C)[0-9A-Z]+ [-0-9]',line)}
    for site in m['asymmetric_unit_sites']:
        row=site_lines[site['id']];check(phase+site['id']+' CIF unknown occupancy',row[-1]=='?')
        for i,c in enumerate(site['source_coordinate_row']['cells']):
            s=re.fullmatch(r'([+-]?\d+(?:\.\d+)?)(?:\((\d+)\))?',row[i+2]);check(c['id']+' CIF value',float(s[1])==c['value'])
            if s[2]:
                digits=len(s[1].split('.')[1]) if '.' in s[1] else 0
                su=float(Decimal(s[2])*(Decimal(10)**(-digits)))
                check(c['id']+' CIF standard uncertainty',su==c['uncertainty'])
        for i,c in enumerate(site['source_adp_row']['cells']):
            token=adp_lines[site['id']][i+1];s=re.fullmatch(r'([+-]?\d+(?:\.\d+)?)(?:\((\d+)\))?',token)
            check(c['id']+' CIF ADP value',float(s[1])==c['value'])
            digits=len(s[1].split('.')[1]) if '.' in s[1] else 0
            su=float(Decimal(s[2])*(Decimal(10)**(-digits))) if s[2] else None
            check(c['id']+' CIF ADP standard uncertainty',su==c['uncertainty'])
check('all 891 table cells transported exactly',set(seen)==set(cells) and len(cells)==891 and len(seen)==891)
for path,h in load(O/'input-bindings.json')['bound_files'].items():check('frozen input unchanged '+path,sha(path)==h)
for b in load(O/'product-bindings-proposal.json')['bindings']:
    r=load(b['source_record_path']);p=r
    for k in b['product_pointer'].strip('/').split('/'):p=p[int(k)] if isinstance(p,list) else p[k]
    check(b['sample_id']+' snapshot exact',p==b['product_snapshot'])
    check(b['sample_id']+' tasks remain empty',r['quality']['requested_tasks']==[] if 'requested_tasks' in r.get('quality',{}) else r.get('requested_tasks',[])==[])
for f in load(O/'public-asset-proposal.json')['files']:check(f['target']+' allowlist hash',sha(f['source'])==f['sha256'])
report={'status':'passed','scope':'author exact table/CIF transport, source/canonical preservation and binding checks','check_count':len(checks),'source_table_cell_count':len(cells),'checks':checks}
(O/'transport-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'passed','checks':len(checks),'table_cells':len(cells)}))
