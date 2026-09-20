from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent; OLD=B.parent/'la980800b';S=B.parents[3]/'recipe-atlas'
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=json.loads((B/'source-render-manifest.json').read_text(encoding='utf-8'))
for d in manifest['documents']:
 for p in d['pages']:
  p.update(text_read=True,visually_reviewed=True,text_sha256=hashlib.sha256((B/p['text_file']).read_bytes()).hexdigest(),render_sha256=hashlib.sha256((B/p['render_file']).read_bytes()).hexdigest())
manifest.update(verified_doi='10.1021/ja9805425',reviewer='mattersyn-primary',reviewed_at=datetime.now(timezone.utc).isoformat(),scope='All two main and four SI PDF pages text and visually inspected. SI DOI cover plus three scientific pages matched by DOI, journal/page headers, Peng attribution and described content. Reading is distinct from extraction audit or publication.')
write(B/'source-manifest.json',manifest)
t=(OLD/'build_inventory_actual.py').read_text(encoding='utf-8').replace('stiger1999','peng1998').replace('stiger','peng').replace('Stiger','Peng')
t=t.replace("'review_status':'full_supplied_main_review_si_unverified'","'review_status':'full_supplied_main_and_matched_si_review'")
t=t.replace("'review_scope':'All nine supplied main pages text and visually reviewed with independent audits. Matching SI not located or verified; deployment tracked separately.'","'review_scope':'All two main and four matched SI PDF pages text and visually reviewed with independent audits; deployment tracked separately.'")
t=t.replace("'documents':[{'role':'main','page_count':9,'all_text_read':True,'all_visually_reviewed':True}]","'documents':[{'role':'main','page_count':2,'all_text_read':True,'all_visually_reviewed':True},{'role':'supporting_information','page_count':4,'all_text_read':True,'all_visually_reviewed':True}]")
t=t.replace("'si_status':'not_located_or_verified'","'si_status':'matched_and_reviewed'")
a=t.index("'notes':['One Ag/Si");b=t.index(']}\ninv[',a)
t=t[:a]+"'notes':['Two hot-injection routes for CdSe and InAs; sequential feed additions are correlated stages of each run.','Four preparation/analysis procedures and six observation/calibration/model records remain separate from synthesis route counts.','All 36 optical/TEM calibration rows are source evidence, not independent recipe outcomes.','Original figures, both SI tables, two equations and two procedural notes are preserved; no measured phase or atomic coordinates supplied.']"+t[b+1:]
t=t.replace("'one_peng_route':row['synthesis_route_variant_count']==1","'two_peng_routes':row['synthesis_route_variant_count']==2")
(B/'build_inventory_actual.py').write_text(t,encoding='utf-8')
t=(OLD/'run_build.py').read_text(encoding='utf-8').replace('stiger-protocol.mjs','peng1998-protocol.mjs')
(B/'run_build.py').write_text(t,encoding='utf-8')
c={'paper':'10.1021/ja9805425','title':'Kinetics of II-VI and III-V Colloidal Semiconductor Nanocrystal Growth: “Focusing” of Size Distributions','source_id':'peng1998','year':1998,'source_generation':2,'review_scope':'supplied_main_and_matched_si','si_status':'Matched SI: exact DOI cover plus Peng/JACS 120/5343 headers; three scientific pages and one cover fully inspected.','main_pages_text_reviewed':[1,2],'main_pages_visually_reviewed':[1,2],'si_pages_text_reviewed':[1,2,3,4],'si_pages_visually_reviewed':[1,2,3,4],'canonical_records_created':12,'operation_count':28,'measurement_entries':159,'website_published':False,'checkpoint_at':datetime.now(timezone.utc).isoformat(),'current_work_items':[{'label':'Read','status':'complete','scope':'Two main pages and all four matched SI PDF pages, including both calibration tables and InAs spectra.'},{'label':'Extract','status':'partial','scope':'Twelve schema-valid private drafts; independent scientific audit is checking source facts and sample joins.'},{'label':'Audit','status':'partial','scope':'Independent full-source inventory complete; canonical, molecular, apparatus, original-asset and reader audits in progress.'},{'label':'Integrate','status':'pending','scope':'Root only; awaiting audited proposals before Site import.'},{'label':'Publish','status':'pending','scope':'Existing public Site version 18 remains live.'}],'next_action':'Finish independent audits of 12 canonical drafts,28 operations,159 measurements; reconcile findings, import private reader and molecular/apparatus proposals into existing Site, build, test and publish. Keep calibration rows and 8.5 nm TEM separate from kinetic batch outcomes.'}
write(B/'checkpoint.json',c)
stages={k:{'status':status,'evidence':[str(B/p) for p in evidence],'note':note}for k,status,evidence,note in [
 ('read','complete',['source-manifest.json','source-identity.json','source-audit.json'],'All six supplied PDF pages read and visually reviewed; matched main/SI.'),
 ('extract','partial',['records-validation.json','build_records.py'],'Twelve schema-valid private canonical drafts; full source-reader mapping and canonical audit pending.'),
 ('audit','partial',['source-audit.json','independent-page-coverage.json'],'Independent source inventory complete; other scoped audits pending.'),
 ('integrate','pending',[],'Root import and reader validation pending.'),('publish','pending',[],'Not published; existing version 18 remains live.') ]}
write(B/'milestones.json',stages)
print('Saved root six-page reading evidence and exact current checkpoint; prepared build helpers.')
