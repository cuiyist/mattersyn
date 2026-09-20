import json,sys
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).parent
sys.path.insert(0,str(OUT.parents[2]/'recipe-atlas/scripts'))
from dataset_lib import validate_record,eligibility,build_groups
records=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((OUT/'canonical').glob('*.json'))]
results=[{'record_id':r['record_id'],'errors':validate_record(r),'eligibility':eligibility(r)} for r in records]
result={'results':results,'errors_count':sum(len(x['errors']) for x in results),'source_groups':build_groups(records),'validation':'Schema1.0.0 and current readonly dataset_lib semantic validator; no Site build invoked.'}
(OUT/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
