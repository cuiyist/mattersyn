from pathlib import Path
import json
A=Path(__file__).resolve().parent;V=A.parent/'v1';H=V.parents[1]
def load(p): return json.loads(Path(p).read_bytes())
def clean(x):
    if isinstance(x,list):return [clean(v) for v in x]
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items() if k not in {'evidence','derivation','canonical_quantity','source_payload'} and v not in [None,'',[],{}]}
    return x
reader=load(V/'public-review-proposal/heo2003.json')
for sec in reader['reader_sections']:
    lines=[]
    for i in sec['items']:
        lines.append(i['id']+' | '+i['title']+' | '+i.get('claim_type',''))
        lines.append(i.get('text',''))
        if i.get('notes'):lines.append('NOTES '+str(i['notes']))
        lines.append('SCOPE '+str(clean(i.get('sample_scope',{}))))
        lines.append('FACTS '+str([clean({k:v for k,v in f.items() if k not in {'id','json_pointer','canonical_record_id','training_eligible'}}) for f in i.get('facts',[])]))
        lines.append('LINKS '+str(i.get('canonical_links',[])))
        lines.append('')
    (A/('reader-'+sec['id']+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
records={p.stem:load(p) for p in (V/'canonical-drafts').glob('*.json')}
ops=[]
for rid,r in records.items():
    ops.append(rid+' | '+r['record_type'])
    ops.append('MATERIALS '+str(clean(r['materials'])))
    ops.append('STOCKS '+str(clean(r['stocks'])))
    for op in r['operations']:ops.append(json.dumps(clean(op),ensure_ascii=False))
    ops.append('OPTIONS '+str(clean(r['condition_options'])))
    ops.append('QUALITY '+str(clean(r['quality'])))
    ops.append('')
(A/'record-operations.txt').write_text('\n'.join(ops),encoding='utf-8')
print({p.name:p.stat().st_size for p in A.glob('*.txt')})
