"""Record completed manual review and produce a private handoff manifest."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=read(B/'validation-report.json');assert report['status']=='passed' and not report['errors']
report['visualReviewStatus']='passed_manual_inspection_of_actual_svg_render_contact_sheets'
report['visualReviewScope']='Both contact sheets inspected: all 19 new SVGs, including SiH3–SiH3 and SiH2Cl2 connectivity, the other neutral molecules, ionic charges/fragments, helium and eight unresolved/support cards. No Site/browser interaction was tested.'
report['visualReviewAssets']=[{'path':p,'sha256':sha(B/p)} for p in report['contactSheets']]
dump(B/'validation-report.json',report)
generation=read(B/'generation-report.json');generation['status']='passed_connectivity_formula_charge_hash_and_svg_review';dump(B/'generation-report.json',generation)
registry=read(B/'registry-additions.json')
provenance={'source':'https://doi.org/10.1021/j100108a019',
 'paperSourceScope':'Reviewed local main article; no additional article retrieval in this asset task.',
 'chemicalReferenceScope':'Eleven explicitly named identities verified through official PubChem API responses, cached under raw/.',
 'modelPurpose':'Illustrative chemical identity references only; no experimental solution, surface or crystal structure.',
 'entries':[{'id':e['id'],'name':e['name'],'formula':e['formula'],'depictionKind':e['depictionKind'],
 'sourceUrls':e['sourceUrls'],'provenance':e['provenance'],'limitations':e['limitations'],'assetHashes':e['assetHashes']} for e in registry['entries']],
 'reused':read(B/'reused-references.json')['entries']}
dump(B/'model-provenance.json',provenance)
files=[]
for folder in ['svg','models','sdf','raw']:
 for p in sorted((B/folder).glob('*')):
  if p.is_file():files.append({'path':p.relative_to(B).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,
   'purpose':{'svg':'public identity depiction','models':'public illustrative model','sdf':'optional illustrative-conformer download','raw':'cached official PubChem provenance'}[folder]})
for name in ['registry-additions.json','bindings-additions.json','reused-references.json','model-provenance.json','missing-identities.json','molecules-3d-additions.json','source-catalog.json','validation-report.json','generation-report.json']:
 p=B/name;files.append({'path':name,'sha256':sha(p),'bytes':p.stat().st_size,'purpose':'handoff metadata'})
dump(B/'asset-manifest.json',{'status':'ready_for_site_owner_review_and_merge','summary':registry['summary'],
 'validation':{'checks':report['checks'],'errors':report['errors'],'visualReviewStatus':report['visualReviewStatus']},'files':files,
 'noSiteChanges':True,'noArticleDownloads':True,'noNewAgents':True})
print(json.dumps({'status':'ready','checks':report['checks'],'files':len(files),'registrySha256':sha(B/'registry-additions.json'),'bindingsSha256':sha(B/'bindings-additions.json')}))
