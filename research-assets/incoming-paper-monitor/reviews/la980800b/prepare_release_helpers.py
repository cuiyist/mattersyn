from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;OLD=B.parent/'la970480g';S=B.parents[3]/'recipe-atlas'
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
render=json.loads((B/'source-render-manifest.json').read_text(encoding='utf-8'))
for p in render['pages']:
 p.update(text_read=True,visually_reviewed=True,text_sha256=hashlib.sha256((B/p['text_file']).read_bytes()).hexdigest(),render_sha256=hashlib.sha256((B/p['render_file']).read_bytes()).hexdigest())
render.update(verified_title='Investigations of Electrochemical Silver Nanocrystal Growth on Hydrogen-Terminated Silicon(100)',verified_doi='10.1021/la980800b',verified_year=1999,reviewer='mattersyn-primary',reviewed_at=datetime.now(timezone.utc).isoformat(),scope='All nine supplied main pages read as text and visually, including figures, table, scheme, equations, notes and references. SI not located or verified. Reading is not publication.')
write(B/'source-manifest.json',render)
t=(OLD/'build_inventory_actual.py').read_text(encoding='utf-8').replace('yao1998','stiger1999').replace('yao','stiger').replace('Yao','Stiger').replace('All seven supplied','All nine supplied').replace("'page_count':7","'page_count':9").replace("'two_stiger_routes':row['synthesis_route_variant_count']==2","'one_stiger_route':row['synthesis_route_variant_count']==1")
start=t.index("'notes':['Two aqueous")
end=t.index(']}\ninv[',start)
t=t[:start]+"'notes':['One Ag/Si pulsed-electrodeposition route with source-scoped pulse options; individual panel contexts are not asserted independent batches.','Two controls and four electrochemical/microscopy procedures remain separate from the synthesis route.','Nine original figures, actual SAED plus a separate indexing schematic, Table1 and three equations are preserved.','Source concentration, charge-unit, caption and kinetic-rate inconsistencies remain explicit. No measured atomic coordinates supplied.']"+t[end+1:]
(B/'build_inventory_actual.py').write_text(t,encoding='utf-8')
t=(OLD/'run_build.py').read_text(encoding='utf-8').replace('yao-protocol.mjs','stiger-protocol.mjs')
(B/'run_build.py').write_text(t,encoding='utf-8')
print('Saved completed root reading evidence and prepared record-derived inventory/build helpers; no Site import or review promotion.')
