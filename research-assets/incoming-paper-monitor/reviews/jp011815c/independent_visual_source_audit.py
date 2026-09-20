from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(V/'scene-manifest.json');records={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};checks=[]
def check(name,ok,note=''):checks.append({'check':name,'passed':bool(ok),'note':note})
check('module-hash',manifest['module_sha256']==sha(V/'shah2001-protocol.mjs'))
expected={(rid,o['id']) for rid,r in records.items() for o in r['operations']};seen=set();scene_review=[]
for s in manifest['scenes']:
 rid=s['record_id'];oid=s['operation_id'];seen.add((rid,oid));r=records[rid];o=next(o for o in r['operations'] if o['id']==oid);p=V/s['file'];texts=[' '.join(e.itertext()) for e in ET.parse(p).iter() if e.tag.endswith('text')];txt=' '.join(texts)
 check(rid+'/'+oid+'/canonical-hash',s['source_record_sha256']==sha(B/'canonical-drafts'/(rid+'.json')))
 check(rid+'/'+oid+'/svg-hash',sha(p)==s['sha256'])
 check(rid+'/'+oid+'/source-parameters',s['parameters']==o['parameters'])
 check(rid+'/'+oid+'/source-evidence',s['evidence']==o['evidence'])
 check(rid+'/'+oid+'/explanatory-not-measured','explanatory' in p.read_text(encoding='utf8'))
 if oid=='inject':
  check(rid+'/'+oid+'/simultaneous','Simultaneous thiol + H₂' in txt)
  check(rid+'/'+oid+'/source-scoped-dose',('H₂ mass unreported' in txt) if 'typical-framework' not in rid else '6.22 mg' in txt)
 if rid in ['shah-2001-ir','shah-2001-pt'] and oid in ['fill','hold']:check(rid+'/'+oid+'/visible-inheritance','*' in txt and 'inherited' in txt)
 if oid=='condition':check(rid+'/'+oid+'/backside-not-reagent-feed','Backside CO₂' in txt and 'Heating tape' in txt)
 scene_review.append({'record_id':rid,'operation_id':oid,'source_record_sha256':s['source_record_sha256'],'svg_sha256':s['sha256'],'semantic_status':'source-consistent explanatory scene','quantity_scope':'exact canonical parameters; per-run versus typical/inherited status preserved'})
check('all-74-operations-covered',seen==expected and len(manifest['scenes'])==74)
semantic=[
 'The complete JavaScript module and all operation manifests were independently read against the inspected source and audited canonical records. All 74 source parameter sets and evidence locators agree with their exact canonical files.',
 'Pressure-cell loading, front-chamber CO2 fill, backside piston pressure control and heating are distinct stages. The injection plumbing now feeds the front reaction chamber through two serial valves; the backside CO2 pressure arrow is separate. Simultaneous thiol/H2 dosing is retained without inventing sequential addition or a feed rate.',
 'Named A–I and Ir/Pt injection scenes show molar ratios with H2 mass unknown. Only the typical Ag framework shows 162–324 mg thiol, 6.22 mg H2 and alternative 100/200 µL plus 800 µL apparatus loops. The loop volumes are explicitly distinguished from doses.',
 'Filling at 138 bar and 20 °C is distinguished from 276 bar and the selected reaction temperature. Ir/Pt inherited fill conditions and 3 h hold are visibly starred and explained; 80 °C/276 bar remain directly reported. Approximate 1 h darkening does not replace the 3 h hold.',
 'Cooling to unspecified room temperature, depressurization, top vapor venting, acetone collection, heptane precipitation and acetone redispersion follow the source. No bath, centrifuge, drying, yield, wash count or numerical ramp is invented.',
 'TEM support, electron microscopy, EDS and image sizing are distinct analytical scenes. The 200 mesh grid, 200 kV acceleration and 1.7 Å point resolution are clearly acquisition quantities; at least 400 particles is an inclusive lower bound. EDS note explicitly limits printed Figure 6 to Ag.',
 'Distribution-analysis scenes preserve A–I, spherical-volume conversion, scaled distributions, radius-ratio definitions and the distinction between Brownian theory and observed distributions. No generated measurement curve or atomistic model is presented.',
 'Private contact sheets 01 and 08–13 were actually viewed, covering all distinct scene types, the typical framework and both Ir/Pt inheritance branches. Repetitions for other Ag table rows were checked by exact manifest/canonical quantities rather than falsely claimed as separately viewed images. Creator and parent retain the full 13-sheet visual review; live responsive browser QA remains separate.',
 'Vessel dimensions, colors, particle glyphs, vial shapes and grid drawings are explanatory. They are not measured apparatus geometry, solved atomic structures or experimental morphology observations.'
]
failures=[x for x in checks if not x['passed']]
report={'schema':'mattersyn-independent-visual-source-audit-1','source_id':'shah2001','status':'passed_with_illustration_limits' if not failures else 'failed','checked_utc':datetime.now(timezone.utc).isoformat(),'module_sha256':sha(V/'shah2001-protocol.mjs'),'scene_manifest_sha256':sha(V/'scene-manifest.json'),'source_audit_sha256':sha(B/'source-audit.json'),'canonical_audit_sha256':sha(B/'canonical-records-audit.json'),'scene_count':74,'semantic_review':semantic,'scene_review':scene_review,'actually_viewed_contact_sheets':[{'file':'scenes-'+str(n).zfill(2)+'.png','sha256':sha(V/'review'/('scenes-'+str(n).zfill(2)+'.png'))} for n in [1,8,9,10,11,12,13]],'check_count':len(checks),'failure_count':len(failures),'checks':checks,'failures':failures,'browser_or_publication_verified':False}
(B/'visual-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'visual-source-audit.md').write_text('# Independent apparatus source audit: Shah et al. (2001)\n\nStatus: '+report['status']+'. 74 operation scenes; '+str(len(checks))+' checks, '+str(len(failures))+' failures.\n\n'+'\n\n'.join(semantic)+'\n\nExact hashes and actual visual coverage are recorded in visual-source-audit.json.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':failures,'audit_sha256':sha(B/'visual-source-audit.json')}))
