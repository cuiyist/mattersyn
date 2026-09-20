from pathlib import Path
import json,sys,runpy
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=S/'data/paper-reviews/littau1993.json';review=read(p);proposal=read(B/'reader-assets/material-evidence-map.json')
review['material_evidence_records']=proposal['material_evidence_records']
review['material_evidence_scope_notes']={k:v['caveat'].split(' The map controls reader visibility')[0] for k,v in proposal['material_evidence_scope'].items()}
write(p,review)
sys.path.insert(0,str(S/'scripts'))
for script in ['build_paper_reviews.py','build_atlas.py']:
    runpy.run_path(str(S/'scripts'/script),run_name='__main__')
runpy.run_path(str(B/'inventory-proposal/build_inventory_proposal.py'),run_name='__main__')
write(S/'data/inventory-summary.json',read(B/'inventory-proposal/inventory-summary.json'))
for script in ['build_inventory.py','check_site.py','check_atlas.py']:
    runpy.run_path(str(S/'scripts'/script),run_name='__main__')
