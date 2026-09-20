"""Save manually reviewed preview status and a checksum handoff manifest."""
import json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=read(B/'validation.json');assert report['status']=='passed' and report['errors']==[]
report['visualReview']='Passed manual inspection of final orthographic unit-cell/periodic-neighbor and finite-sphere previews. These are generated geometry previews, not source-paper figures. No interactive Site/browser QA performed.'
report['reviewAssets']=[{'path':'review/'+name,'sha256':sha(B/'review'/name)} for name in ['unit-cell-periodic-context.png','finite-sphere.png']]
source=Path('[local path redacted]')
assert sha(source)==read(B/'provenance.json')['source']['source_sha256']
report['sourcePdfHashVerified']=True
dump(B/'validation.json',report)
files=[B/'si-diamond-ideal-reference.cif',B/'si-diamond-ideal-expanded-p1.cif',
 B/'registry-additions.json',B/'proposed-record-structure-assets.json',B/'provenance.json',B/'validation.json',
 B/'viewer-adapter.mjs',*sorted((B/'models').glob('*.json')),*sorted((B/'downloads').glob('*.xyz'))]
dump(B/'asset-manifest.json',{'status':'ready_for_site_owner_review_and_import','sourceDoi':'10.1021/j100108a019',
 'referenceOnly':True,'measuredSampleStructure':False,'trainingEligible':False,
 'checks':report['checks'],'errors':report['errors'],'visualReview':report['visualReview'],
 'files':[{'path':p.relative_to(B).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],
 'noSiteChanges':True,'noArticleDownloads':True,'noExperimentalCifClaim':True,
 'viewerLimit':'Current unit/supercell rendering is compatible. A finite-particle branch must render the nonperiodic model directly, without periodic replication or cell lines.'})
print(json.dumps({'status':'ready','registrySha256':sha(B/'registry-additions.json'),
 'unitModelSha256':sha(B/'models/si-diamond-ideal-unit-cell.json'),
 'finiteModelSha256':sha(B/'models/si-diamond-illustrative-sphere-3nm.json'),'checks':report['checks']}))
