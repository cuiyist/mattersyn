from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;H=HERE.parent.parent
OUT=HERE/'v1';OUT.mkdir(exist_ok=True)
CAN=H/'canonical-proposal/v2';CONFIG=json.loads((HERE/'scene-selection-draft.json').read_bytes())
CONFIG['status']='source_bound_canonical_v2_pending_independent_apparatus_audit'
CONFIG['configs']['epxma-acquire']['extra_rows']=[{'label':'Instrument','value':'EDAX 9100 energy-dispersive system on a Phillips 515 scanning electron microscope'},{'label':'Acquisition settings','value':'Beam energy, current, chamber pressure and acquisition duration are not reported.'}]
CONFIG['configs']['epxma-expose']['extra_rows']=[{'label':'Exposure duration','value':'Not reported'}]
CONFIG['configs']['h2s']['extra_rows']=[{'label':'Gas delivery','value':'Zeolitically dried H₂S; charge, delivery mode and dryer preparation are not specified.'}]
records=[];bound={}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for rid,ids in CONFIG['records'].items():
 p=CAN/'canonical-drafts'/f'{rid}.json';r=json.loads(p.read_bytes())
 assert [o['id'] for o in r['operations']]==ids
 records.append(r);bound[str(p)]=sha(p)
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(OUT/'scene-selection.json').write_text(json.dumps(CONFIG,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
module=(HERE/'module-template.mjs').read_text(encoding='utf8').replace('__SOURCE_CONFIG__',json.dumps(CONFIG,ensure_ascii=False))
(OUT/'heo2003-protocol.mjs').write_text(module,encoding='utf8')
source=Path(r'[local path redacted]')
shutil.copyfile(source,OUT/source.name);bound[str(source)]=sha(source)
(OUT/'canonical-bindings.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'canonical_version':2,'files':bound,'operation_count':14},indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared':str(OUT),'records':len(records),'operations':14}))
