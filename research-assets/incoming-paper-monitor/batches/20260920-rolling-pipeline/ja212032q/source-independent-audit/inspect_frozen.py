from pathlib import Path
import json,sys
G=Path(__file__).resolve().parent.parent
f=json.loads((G/'source-facts.json').read_text(encoding='utf-8'))
def slim(x):
 if isinstance(x,list):return [slim(v) for v in x]
 if isinstance(x,dict):
  omit=['source_sha256','created_at','independent_audit_status']+(['evidence','conflict_ids','gap_ids'] if 'raw_text' in x else [])
  return {k:slim(v) for k,v in x.items() if k not in omit and v is not None and v!=[]}
 return x
mode=sys.argv[1]
if mode in f:
 rows=f[mode]
 if isinstance(rows,list):
  low=int(sys.argv[2]) if len(sys.argv)>2 else 0
  high=int(sys.argv[3]) if len(sys.argv)>3 else len(rows)
  for i,row in enumerate(rows[low:high],low):print(str(i)+' '+json.dumps(slim(row),ensure_ascii=False))
 else:print(json.dumps(slim(rows),ensure_ascii=False))
