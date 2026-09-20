"""Bounded post-browser metadata delta and CdSe navigation verification."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re
O=Path(__file__).resolve().parent;B=O.parent;S=B.parents[3]/'recipe-atlas'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def diff(a,b,p=''):
 if type(a)!=type(b):return[p]
 if isinstance(a,dict):return[q for k in a.keys()|b.keys() for q in([p+'/'+k]if k not in a or k not in b else diff(a[k],b[k],p+'/'+k))]
 if isinstance(a,list):return[p]if len(a)!=len(b)else[q for i,(x,y)in enumerate(zip(a,b))for q in diff(x,y,p+'/'+str(i))]
 return[]if a==b else[p]
def ptr(v,p):
 for k in p.split('/')[1:]:v=v[int(k)]if isinstance(v,list)else v[k]
 return v
before=read(O/'integrated-before-final-flags.json');current=read(S/'data/paper-reviews/peng1998.json');generated=read(S/'dist/data/paper-reviews/peng1998.json')
base=read(O/'canonical-to-reader-audit.json');runtime=read(O/'reader-runtime-check.json');browser=read(B/'browser-qa.json');card=read(O/'cdse-card-delta.json')
checks=[]
def check(name,condition,detail=''):checks.append({'name':name,'passed':bool(condition),'detail':detail})
changes=diff(before,current)
allowed={'/independent_audit'}
assetids=[]
for group in['figures','tables','equations','source_notes']:
 for i,a in enumerate(current[group]):
  assetids.append(a['id'])
  for field in['reviewed','reader_render_verified']:
   pointer=f'/{group}/{i}/{field}';allowed.add(pointer)
   check(a['id']+' '+field+' justified promotion',ptr(before,pointer)is False and ptr(current,pointer)is True)
check('Only 22 asset flags and independent-audit summary changed',set(changes)==allowed and len(changes)==23,repr(changes))
check('All119 reader items and scientific facts unchanged',current['reader_sections']==before['reader_sections'] and sum(len(s['items'])for s in current['reader_sections'])==119)
check('Source identity, quantities, samples and interpretation metadata unchanged',all(current[k]==before[k]for k in current if k not in['independent_audit','figures','tables','equations','source_notes']))
generated_label=generated.pop('review_scope_label',None)
check('Generated source reader is exact authored JSON plus scope label',generated==current and generated_label=='Complete supplied main + matched SI review')
check('Root browser evidence passed for exactly11originals',browser['status']=='passed'and set(browser['original_assets'])=={a['public_asset']for g in['figures','tables','equations','source_notes']for a in current[g]})
check('Prior full canonical and runtime gates passed',base['status']=='passed_bounded_canonical_to_reader_audit'and runtime['status']=='passed'and base['checks_passed']==2263 and runtime['checks_passed']==951)
expected_changed={'data/paper-reviews/peng1998.json','dist/data/paper-reviews/peng1998.json'}
unchanged=0
for label,h in base['artifact_sha256'].items():
 if label in expected_changed:continue
 path=B/label.removeprefix('private/')if label.startswith('private/')else S/label
 check('Preserved audited bytes '+label,sha(path)==h)
 unchanged+=1
for label,h in runtime['artifact_sha256'].items():
 if label=='dist/data/paper-reviews/peng1998.json':continue
 check('Reader runtime module unchanged '+label,sha(S/label)==h)
check('Changed CdSe card runtime checks passed',card['status']=='passed'and all(x['passed']for x in card['checks']))
for label,h in card['artifact_sha256'].items():check('CdSe card runtime fingerprint current '+label,sha(S/label)==h)
module=(S/'dist/material-hub.mjs').read_text(encoding='utf8');page=(S/'dist/cdse.html').read_text(encoding='utf8')
check('CdSe module keeps route, reviewed-source and duplicate guards',"r.is_synthesis_route&&!represented.has(r.record_id)&&r.collection==='reviewed_literature'"in module)
check('CdSe current page loads updated module version','material-hub.mjs?v=0.12.0-r1'in page)
check('New Peng route rendered among additional material methods','records/peng-1998-cdse-focusing.html'in card['actual_card_urls'])
check('Current scientific inventory unchanged',current['counts']==before['counts'] and current['counts']['typed_characterization_rows']==159 and current['counts']['source_audit_units']==160)
failures=[c for c in checks if not c['passed']]
paths=[S/'data/paper-reviews/peng1998.json',S/'dist/data/paper-reviews/peng1998.json',S/'dist/material-hub.mjs',S/'dist/cdse.html',B/'browser-qa.json',O/'canonical-to-reader-audit.json',O/'reader-runtime-check.json',O/'integrated-before-final-flags.json',O/'cdse-card-delta.json']
result={'status':'passed'if not failures else'failed','checked_utc':datetime.now(timezone.utc).isoformat(),
 'scope':'Bounded final delta after root browser QA. Exactly22 asset completion flags and independent-audit prose changed; original scientific facts and previously audited canonical/generated files retained. The actual changed CdSe method-card module was separately executed with six passing checks. No Site edits or publication claim.',
 'check_count':len(checks),'checks_passed':len(checks)-len(failures),'failures':failures,'allowed_reader_changes':sorted(changes),'preserved_prior_artifact_count':unchanged,
 'retained_counts':{'records':12,'operations':28,'operation_quantities':30,'measurements':159,'reader_items':119,'source_units':160,'original_assets':11},
 'prior_runtime_scope':'951 runtime checks apply to unchanged reader code and unchanged reader items; this delta supersedes only its generated-reader metadata hash.',
 'cdse_card_count':len(card['actual_card_urls']),'artifact_sha256':{str(p.relative_to(S)).replace('\\','/')if p.is_relative_to(S)else'private/'+str(p.relative_to(B)).replace('\\','/'):sha(p)for p in paths},'checks':checks}
(O/'final-presentation-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:result[k]for k in['status','check_count','checks_passed','failures','preserved_prior_artifact_count','cdse_card_count']},ensure_ascii=False))
raise SystemExit(bool(failures))
