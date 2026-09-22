from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
P=Path(__file__).resolve().parent;D=P.parents[2]/'recipe-atlas/dist'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cp=D/'assets/chemical-registry/solution-components.json';contexts=json.loads(cp.read_text('utf8'))['contexts']
pairs=[('ghosh-2012-optimized-shell-route','s-od-stock','ghosh2012-s-od-stock'),
 ('ghosh-2012-optimized-shell-route','cd-oleate-stock','ghosh2012-cd-oleate-stock'),
 ('ghosh-2012-core-standard-route','top-se-injection','ghosh2012-top-se-injection'),
 ('morrison-2017-monolayer-shell','cdptc-thf-shell','morrison2017-cdptc-thf-shell'),
 ('lian-2021-nc-a-route','stock-nc-feed','lian2021-stock-nc-feed')]
mapping={};checks=[];bound={str(cp):sha(cp)}
for rid,sid,cid in pairs:
 rp=D/'data/records'/(rid+'.json');r=json.loads(rp.read_text('utf8'));bound[str(rp)]=sha(rp)
 stocks=[(i,s) for i,s in enumerate(r['stocks']) if s['id']==sid]
 ctxs=[(i,c) for i,c in enumerate(contexts) if c['record_id']==rid and c['id']==cid]
 assert len(stocks)==len(ctxs)==1
 si,s=stocks[0];ci,c=ctxs[0]
 assert c['binding_approved'] is True
 assert [x['material_id'] for x in s['components']]==[x['material_id'] for x in c['components']]
 assert all(x['material_id'] in {m['id'] for m in r['materials']} for x in c['components'])
 assert s['evidence'] and {e['source_id'] for e in s['evidence']}=={r['lineage']['source_group']}
 mapping.setdefault(rid,{})[sid]=cid
 checks.append({'record_id':rid,'stock_id':sid,'context_id':cid,'stock_pointer':'/stocks/'+str(si),
   'context_pointer':'/contexts/'+str(ci),'component_ids':[x['material_id'] for x in s['components']],
   'source_evidence':s['evidence'],'canonical_scope':s['scope'],'component_context_scope':c['scope'],
   'canonical_concentrations':s['concentrations'],
   'checks':['Unique same-record stock/context identity','Identical ordered component IDs','All components resolve in the same canonical record','Existing component binding approved','Source group agrees','Manual concentration/charge/whole-formulation and aliquot scope compared; no amount moved or newly computed']})
result={'schema_version':'1.0','scope':'Explicit existing canonical stock -> existing approved component context. No quantity, formulation or scientific metadata change.','stockBindings':mapping}
(P/'stock-context-bindings.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
receipt={'status':'passed_mapping_crosscheck','reviewer':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),'scope':'Five existing identities crosschecked against their passed canonical source locators, components and amounts; not a new full-paper or chemical-model audit.',
 'bindings':checks,'bound_files':bound,'mapping_sha256':sha(P/'stock-context-bindings.json'),
 'manual_numeric_scope':['Ghosh sulfur/octadecane and Cd-oleate/OA/octadecane each 0.2 mol/L; batch and per-layer volumes remain unknown. Cd:OA changing ratios remain formulation context, not molecule stoichiometry.',
 'Ghosh core injection is TOP-Se 4 mmol + oleylamine 3 mL + ODE 1 mL; no extra charge or final volume inferred.',
 'Morrison shell feed is 2 mL of 10 mM Cd(PTC)2 in THF; 2 mL remains solution volume, not neat THF; core amount unknown.',
 'Lian whole feed uses tetrapropylammonium chloride 1 mmol, SbCl3 0.5 mmol and DMF charge 2000 µL; later 500 µL aliquot stays distinct and no exact aliquot solute amount inferred.']}
(P/'stock-context-binding-checks.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'mapping_sha256':receipt['mapping_sha256'],'checks_sha256':sha(P/'stock-context-binding-checks.json'),'bindings':len(checks)}))
