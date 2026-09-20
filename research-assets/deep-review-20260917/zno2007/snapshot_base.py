import json
from pathlib import Path
P=Path(__file__).resolve().parent
target=P/'s1-base-snapshot.json'
if target.exists():raise SystemExit('Snapshot already exists; not overwritten.')
r=json.loads((P/'canonical/fu-2007-zno-s1.json').read_text(encoding='utf-8'))
added={'s1-ftir-c-c','s1-ftir-interface','s1-ftir-nh-oh','zno-slope','reference-slope','zno-r2','reference-r2'}
r['measurements']=[m for m in r['measurements'] if m['id'] not in added]
r['context_links']=[x for x in r['context_links'] if x['relation']!='source_coverage']
r['quality']['conflicts']=[x for x in r['quality']['conflicts'] if '1.8 m_h' not in x]
target.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Frozen original S1 input',len(r['measurements']),'measurements')
