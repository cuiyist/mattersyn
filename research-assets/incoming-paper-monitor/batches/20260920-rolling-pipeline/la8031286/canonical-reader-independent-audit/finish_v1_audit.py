from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
A=Path(__file__).resolve().parent;G=A.parent;C=G/'canonical-proposal/v1';P=G/'public-review-proposal/v1'
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
m=read(A/'mechanical-checks-v1.json');bound={x['path']:x['sha256']for x in m['bound_files']};checks=[]
def ck(label,ok):checks.append({'check':label,'passed':bool(ok)});assert ok,label
src=read(G/'source-facts.json');ops={o['id']:o for p in src['protocols']for o in p['operations']};records={p.stem:read(p)for p in C.glob('pati-2009-*.json')}
expected_dependencies={'prepare-nitrate':[],'prepare-tea':[],'drip':['prepare-nitrate','prepare-tea'],'poststir':['drip'],'filter':['poststir'],'alcohol-wash':['filter'],'ambient-dry':['alcohol-wash'],'acetone-wash':['ambient-dry']}
for solvent in ['ethanol','propanol','butanol']:
 r=records['pati-2009-'+solvent+'-route'];aliases={'selected-alcohol':solvent,'selected-nitrate-stock':solvent+'-nitrate-stock-prepared-state','selected-tea-stock':solvent+'-tea-stock-prepared-state'}
 ck('Exact route steps '+solvent,[o['id']for o in r['operations']]==list(expected_dependencies))
 ck('No foreign alcohol '+solvent,{x['id']for x in r['materials']}&{'ethanol','propanol','butanol'}=={solvent})
 ck('Exactly separate two stocks '+solvent,{x['id']for x in r['stocks']}=={solvent+'-nitrate-stock',solvent+'-tea-stock'})
 for op in r['operations']:
  original=ops[op['id']]
  for k in ['inputs','outputs']:ck('Exact source alias '+solvent+'/'+op['id']+'/'+k,op[k]==[aliases.get(x,x)for x in original[k]])
  ck('Exact chronology '+solvent+'/'+op['id'],op['depends_on']==expected_dependencies[op['id']])
 ck('No diagnostic return '+solvent,all('diagnostic-mixture'not in o['inputs']for o in r['operations']))
for rid,r in records.items():
 if r['record_type']=='literature_protocol':continue
 for o in r['operations']:
  extra={'bet-acquire':['nitrogen-bet'],'tga-acquire':['air'],'packing-acquire':['pipet']}.get(o['id'],[])
  ck('Analytical input contexts '+rid,o['inputs']==ops[o['id']]['inputs']+extra)
  ck('Analytical outputs '+rid,o['outputs']==ops[o['id']]['outputs'])
  ck('No acquisition combines physical samples '+rid,all(x['kind']in['sample_set','analysis_data']for x in r['material_states']))
  if o['stage']=='characterization' and o['id']!='diagnostic':ck('Analytical output classification '+rid,all(x['kind']=='analysis_data'for x in r['material_states']if x['id']in o['outputs']))
ck('Air only in TGA',[(rid,o['id'])for rid,r in records.items()for o in r['operations']if 'air' in str(o['environment']['value']).lower()]==[('pati-2009-tga','tga-acquire')])
ck('No calcination atmosphere',records['pati-2009-calcination']['operations'][0]['environment']['value'] is None)
ck('No DLS value used as condition',not records['pati-2009-dls']['operations'][0]['parameters'])
ck('No SAED hkl or crystallite size used as acquisition condition',not records['pati-2009-tem']['operations'][0]['parameters'])
ck('Only known reader token failure',m['failures']==[{'category':'actual_reader_consumer','detail':['Explicit recognized review_scope is required']}])
scopes=[
'Read all 243 reader cards including overview prose, 31 printed references, four expressions, ten source conflicts and eight missingness entries; exact typed fields checked separately.',
'Read all 19 record boundaries, all 35 operation instances, 45 material slots, six two-component stocks and 156 record-local contexts.',
'Three alcohol variants remain distinct with identical inherited source procedure, source-specific alcohol names and no fabricated replicates.',
'0.1 M nitrate and 0.4 M TEA stocks have no invented preparation mass or volume. The two 100 mL quantities remain transfers and are not total preparation volumes.',
'Source TEA formula conflict, nitrate hydrate-associated water and anhydrous ethanol-only qualifier remain explicit; no molecule graph approval in this audit.',
'Burette/Erlenmeyer source apparatus and 3–4 mL/min addition retained; post-precipitation 1 h is not replaced with calculated dripping time.',
'Precipitate is retained, separate 10 mL filtrate diagnostic is not returned; alcohol wash precedes 24 h ambient drying then acetone wash; subsequent drying unknown.',
'Calcination is separate 200 °C/3 h with 10 °C/min ramp; its atmosphere is unknown. Air applies only to TGA, and DSC settings do not inherit TGA conditions.',
'As-prepared whole powder composition/phase remain unknown despite local CeO2 microscopy. Calcined source assignments remain composition CeO2/cubic with no exact coordinate or batch label.',
'TEM 3±1 nm crystallites, 5 nm bars, SAED indices and 0.267 nm observed versus 0.271 nm reference remain distinct from aggregates and source-calculated BET diameters.',
'DLS 72±20/50±18/14±8 nm values preserve conflicting radius/diameter terminology without factor-of-two conversion; dispersion preparation is unknown.',
'XRD, TEM, DLS, BET, TGA, DSC, XPS and packing contexts remain separate; analytical state arrays explicitly represent separate specimens and analysis data.',
'BET 78/80/84 m²/g and calculated 10/9.8/9.3 nm retain solvent correspondence; packing 0.6 g/cm³ is separate from cited bulk 7.65 g/cm³.',
'XPS surface fractions, short <15 versus ~15/15 min wording and long >5 h conditions retained; no exact-zero bulk CeIV or inferred complementary 55% claim.',
'All 20 XPS cells and 36 raw grid cells, atypical printed spin labels, 884.5 versus 884.8 eV and unrepaired CeIII area formula are retained; fitting parameters do not resolve conflicting specimen labels.',
'Proposed hydroxo/TEA species and cited mechanism temperatures remain interpretations/cited context, not measured isolated products or conditions for the current route.',
'Reopened and visually reread original main pages 2 and 3 for workup, SAED/TEM, as-prepared/calcined XRD, BET, TGA/DSC and XPS source scopes. Earlier passed eight-page source audit remains separately bound.',
'Only selected scientific crops are referenced for public use. All 20 exact crop hashes retained; no raw full text/full source pages/source binaries enter the reader.',
'Current canonical schema/eligibility and actual build_paper_reviews.validate invoked in a private fixture. Scientific transport passes; actual reader consumer identifies the single unsupported scope token.'
]
for path in [A/'check_proposal.py',A/'prepare_independent_views.py',A/'canonical-reading-view.json',A/'reader-prose-view.txt',A/'mechanical-checks-v1.json',Path(__file__),G/'source-render/main-02.png',G/'source-render/main-03.png']:
 bound[str(path)]=sha(path)
finding={'id':'PATI-CAN-01','severity':'required_correction','path':'public-review-proposal/v1/pati2009.json','pointer':'/review_scope','current':'complete_supplied_main_and_matched_si','required':'supplied_main_and_matched_si','reason':'The current actual Site reader scope consumer rejects the former token. This is a vocabulary correction only; complete supplied main/SI review scope and all scientific fields are unchanged.','status':'open'}
out={'schema':'mattersyn-independent-canonical-reader-audit/1','source_id':'pati2009','author':'/root/backlog_eta','auditor':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'open_findings','passed':False,'proposal_freeze_sha256':sha(C/'package-manifest.json'),'source_audit_sha256':sha(G/'source-independent-audit/independent-audit-v1.json'),'check_count':m['check_count']+len(checks),'transport_check_count':m['check_count'],'scientific_graph_checks':checks,'counts':m['counts'],'manual_scope':scopes,'open_findings':[finding],'bound_files':dict(sorted(bound.items())),'site_changed':False,'molecule_apparatus_browser_publication_approval':False,'training_or_atomic_approval':False}
save(A/'independent-audit-v1.json',out);save(A/'independent-audit.json',out)
(A/'independent-audit-v1.md').write_text('# Pati canonical/reader audit — preserved v1\n\nScientific and typed transport checks pass across 19 records, 35 operation instances, 58 facts, 218 units, 20 numerical table cells, 1,101 reader fields and 20 selected crops. All 243 prose cards read.\n\nOne required correction: `/review_scope` uses an unsupported consumer token. Replace it with `supplied_main_and_matched_si` in a preserved revision; do not change the scientific fields or canonical records. No other finding. Molecule, apparatus, browser and publication gates remain separate.\n','utf8')
print(json.dumps({'status':out['status'],'checks':out['check_count'],'sha256':sha(A/'independent-audit-v1.json')}))
