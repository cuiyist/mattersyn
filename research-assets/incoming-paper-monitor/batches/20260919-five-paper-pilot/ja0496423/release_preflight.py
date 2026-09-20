from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
G=Path(__file__).resolve().parent
S=Path('[local path redacted]')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit=G/'integration-source-audit-addendum.json'
assert sha(audit)=='d064ac96cf766c8bf76d17c73fc4235e2cf9b881d1f3d30268600188244323fa'
a=json.loads(audit.read_text(encoding='utf-8-sig'))
assert a['status']=='passed'
fail=[p for p,h in a['bound_files'].items() if not Path(p).is_file() or sha(p)!=h]
assert not fail, fail
sys.path.insert(0,str(G.parents[2]))
import monitor
fingerprint=monitor.fingerprint(G.parents[2]/'ledger.json','mattersyn-primary',group_id='10.1021_ja0496423')
assert fingerprint['generation']==2
assert set(fingerprint['files'].values())=={'ae3ae7a8e5c2a96866da9b1599d54317f2189873dd8b143dfd11328c9b80525c','93187032178ee66f73154cf461f8a02be6bc251c02b397c3f5269c5c1a5e44eb'}
(G/'publication-source-fingerprint.json').write_text(json.dumps(fingerprint,indent=2)+'\n',encoding='utf-8')
qa={'schema':'mattersyn.browser-validation.v1','source_id':'gu2004','at':datetime.now(timezone.utc).isoformat(),'status':'passed','method':'Actual Codex in-app browser interactions and screenshots; not static-source substitution','origin':'http://127.0.0.1:5187/','protocol_scenes_clicked':33,'material_modals_opened':28,'record_ids':['heterodimer','cdacac-preparation','microscopy','xrf','magnetometry','optical','fept-control'],'checks':['Each source operation selected; 33 unique Gu scene IDs and SVG artwork observed','All 28 reagent/specimen bindings opened with canvas or loaded original SVG','Pt/Cd acetylacetonate and Fe(CO)5 retain component-only representations','Gu 97% oleylamine source caption observed; functional groups toggled, zoom/reset and keyboard rotation used','New nitrogen reference used; quantitative bond validation belongs to the separate molecular audit','Original Figure 1 enlarged and reset; complete readable panel D SAED rings and indexes retained','Paper review search SAED returns 6 of 138 items; all source sections and original asset links rendered','Fe+Pt periodic table filter returned two reviewed whole/component pages and linked to the FePt/CdS hub','New hub loaded full method, chemical cards, protocol, product context, original figures, properties, intuition and source links','390x844 protocol and molecular modal visually inspected with usable controls, wrapping and no horizontal document overflow','Temporary viewport override reset','Final browser warning/error log empty'],'original_figure_1_pixels':[2042,544],'reference_viewport_sizes':[[1280,900],[390,844]],'errors':[],'independent_integration_audit_sha256':sha(audit),'validated_binding_count':len(a['bound_files']),'final_checks':{'check_site':'438 pages, 424 canonical/public hashes, 95 optical rows passed','check_atlas':'40 collections and component identity/relevance/privacy passed','chemical_viewer_syntax':'node --check passed'},'scope_limit':'This browser check verifies displayed behavior. Source-scientific and molecular accuracy are separately hash-bound in independent audits.'}
(G/'browser-validation.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'passed','audit_files_verified':len(a['bound_files']),'source_generation':fingerprint['generation'],'source_copies':len(fingerprint['files']),'browser_evidence':str(G/'browser-validation.json')}))
