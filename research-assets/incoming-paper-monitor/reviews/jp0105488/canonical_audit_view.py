import json,sys
from pathlib import Path
B=Path(__file__).parent
def compact(x):
    if isinstance(x,list):return [compact(v) for v in x]
    if isinstance(x,dict):
        return {k:compact(v) for k,v in x.items() if k not in ['evidence','sources','context_links','review_scope','collection'] and v not in [None,'',[],{}]}
    return x
for p in sorted((B/'canonical-drafts').glob('*.json')):
    if len(sys.argv)>1 and p.stem not in ['gerion-2001-'+a for a in sys.argv[1:]]:continue
    r=json.loads(p.read_text(encoding='utf8'))
    print('\nRECORD',r['record_id'])
    for k,v in r.items():
        if k in ['sources','schema_version','revision','record_id','context_links','collection']:continue
        print(k+': '+json.dumps(compact(v),ensure_ascii=False,separators=(',',':')))
