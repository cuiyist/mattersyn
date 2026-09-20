"""Private handoff validation; this is not an independent source audit."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
from PIL import Image

O=Path(__file__).resolve().parent;B=O.parent
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=read(O/'peng1998.json');crops=read(B/'reader-assets/crop-manifest.json')
coverage=read(O/'source-item-coverage.json');measurements=read(O/'canonical-measurement-coverage.json')
drafts={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
checks=[]
def check(name,condition):
 checks.append({'check':name,'passed':bool(condition)})
 if not condition:raise AssertionError(name)
def pointer(data,p):
 for part in p.split('/')[1:]:data=data[int(part)] if isinstance(data,list) else data[part.replace('~1','/').replace('~0','~')]
 return data
items={i['id']:i for s in review['reader_sections'] for i in s['items']}
check('All 119 reader item IDs unique',len(items)==119==sum(len(s['items']) for s in review['reader_sections']))
check('All 160 source units mapped',coverage['mapped_unit_count']==160 and not coverage['unmapped_units'])
check('All 159 canonical measurements mapped',measurements['measurement_count']==159)
for uid,targets in coverage['unit_to_reader_items'].items():
 check('Source coverage '+uid,all(t in items and uid in items[t]['source_audit_unit_ids'] for t in targets))
for k,item in items.items():
 check('Evidence and provenance '+k,bool(item['evidence']) and bool(item['source_locators']))
 check('Not promoted to training '+k,item['training_eligible'] is False)
 for l in item['canonical_links']:
  check('Canonical pointer '+k+' '+l['record_id']+l['json_pointer'],l['record_id'] in drafts and pointer(drafts[l['record_id']],l['json_pointer']) is not None)
 for join in item['sample_scope'].get('canonical_sample_links',[]):
  check('Sample join '+k+' '+join['record_id']+'::'+join['sample_id'],pointer(drafts[join['record_id']],join['json_pointer'])['sample_id']==join['sample_id'])
 for f in item['facts']:
  if not f.get('canonical_record_id'):continue
  m=pointer(drafts[f['canonical_record_id']],f['json_pointer'])
  check('Measurement value/unit '+f['id'],m['id']==f['canonical_measurement_id'] and m['sample_id']==f['sample_id'] and m['value'].get('value')==f['value'] and m['value'].get('unit')==f.get('unit'))
for rid,h in measurements['draft_sha256'].items():check('Draft fingerprint '+rid,sha(B/'canonical-drafts'/f'{rid}.json')==h)
assets=[a for key in ['figures','tables','schemes','equations','source_notes'] for a in review[key]]
check('11 distinct original source assets',len(assets)==11 and len({a['public_asset'] for a in assets})==11)
for a in assets:
 c=next(c for c in crops['assets'] if c['id']==a['id']);p=B/'reader-assets'/c['relative_asset']
 check('Crop SHA '+a['id'],sha(p)==c['sha256']==a['public_asset_sha256'])
 check('Crop image dimensions '+a['id'],list(Image.open(p).size)==c['pixel_dimensions'])
 check('Source hash '+a['id'],c['source_sha256']==next(s['sha256'] for s in crops['sources'] if s['role']==c['source_role']))
 check('Await independent/browser gates '+a['id'],a['reviewed'] is False and a['reader_render_verified'] is False)
 c['visual_reviewed']=True
 c['visual_review_note']='Reader/assets preparer inspected this exact cropped image with view_image, including all edges, captions, original axes and labels. Independent crop/source audit and browser rendering remain pending.'
check('Figure 3 is only linked to unassigned TEM observation',next(a for a in assets if a['id']=='figure-3')['sample_links']==['peng-1998-cdse-tem'])
check('Figure 4 remains theory',next(a for a in assets if a['id']=='figure-4')['evidence_class']=='source_theoretical_model')
check('SI scientific pages and cover distinct',review['counts']['matched_si_pages']==4 and review['counts']['si_scientific_pages']==3)
(B/'reader-assets/crop-manifest.json').write_text(json.dumps(crops,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report={'scope':'Author self-check of private reader/assets proposal; independent source/reader audits and Site rendering are separate.',
 'checked_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'check_count':len(checks),
 'reader_sha256':sha(O/'peng1998.json'),'crop_manifest_sha256':sha(B/'reader-assets/crop-manifest.json'),
 'source_audit_sha256':sha(B/'source-audit.json'),'counts':review['counts'],'checks':checks}
(O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['checks','scope']},ensure_ascii=False))
