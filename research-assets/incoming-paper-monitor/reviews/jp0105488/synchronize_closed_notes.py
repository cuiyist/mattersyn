"""Synchronize final explanatory wording without changing a closed scope or its evidence."""
from pathlib import Path
import json,sys
B=Path(__file__).resolve().parent;MON=B.parent.parent
sys.path.insert(0,str(MON));import monitor
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=read(B/'milestones.json')
m['extract']['note']='All eleven supplied main pages extracted into 28 records, 82 operations and 186 measurements; 139 reader items cover 251 source units, 329 typed facts and 17 original assets. Final independent audits passed. Announced supporting figures remain unavailable locally.'
write(B/'milestones.json',m)
c=read(B/'checkpoint.json');c['current_work_items']=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in m.items()];write(B/'checkpoint.json',c)
with monitor.locked_ledger(MON/'ledger.json'):
 ledger=monitor.read_ledger(MON/'ledger.json');g=ledger['groups']['10.1021_jp0105488'];r=g['review']
 assert r['status']=='complete' and g['generation']==2 and r['checkpoint']['website_published']
 r['milestones']['extract']['note']=m['extract']['note'];r['checkpoint']['current_work_items']=c['current_work_items']
 monitor.save_ledger(MON/'ledger.json',ledger)
print('Closed-checkpoint wording synchronized; status, scope, evidence and queue order unchanged')
