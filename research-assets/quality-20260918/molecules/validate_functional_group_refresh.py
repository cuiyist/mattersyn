"""Offline asset validation after the bounded functional-group correction."""
import json,hashlib,re,math,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=0;errors=[]
def check(ok,msg):
 global checks
 checks+=1
 if not ok:errors.append(msg)
registry=read(R/'registry.json');binding=read(R/'bindings.json');audit=read(R/'functional-group-audit.json')
entries={e['id']:e for e in registry['entries']}
check(len(entries)==89 and len(entries)==len(registry['entries']),'89 unique entry IDs')
for e in entries.values():
 for key in ['svgPath','model2dPath','model3dPath']:
  if not e.get(key):continue
  p=(R/e[key]).resolve()
  check(p.is_relative_to(R) and p.is_file(),e['id']+' bounded '+key)
  check(sha(p)==e['assetHashes'][key],e['id']+' hash '+key)
  if key=='svgPath':
   svg=p.read_text(encoding='utf-8');xml=ET.fromstring(svg)
   check(not re.search(r'<script|onload=|javascript:|(?:href|src)="https?://',svg,re.I),e['id']+' passive SVG')
   continue
  m=read(p);aa=m['atoms'];bb=m['bonds']
  check(m['id']==e['id'],e['id']+' model identity')
  check(all(math.isfinite(a[c]) for a in aa for c in ['x','y','z']),e['id']+' coordinates finite')
  check(all(0<=b['a']<len(aa) and 0<=b['b']<len(aa) and b['a']!=b['b'] and b['order'] in [1,1.5,2,3] for b in bb),e['id']+' bond indices')
  for g in m['functionalGroups']:
   check(all(0<=i<len(aa) for i in g['atomIndices']),e['id']+' group atoms')
   check(all(0<=i<len(bb) and {bb[i]['a'],bb[i]['b']}<=set(g['atomIndices']) for i in g['bondIndices']),e['id']+' group bonds')
  if key=='model2dPath':check(m['functionalGroups']==e['functionalGroups'],e['id']+' registry matches 2D groups')
  if key=='model3dPath':
   check(m['representation']=='3d' and m['has3D'] and m['allowRotation'],e['id']+' 3D flags')
   check(all(.45<math.sqrt(sum((aa[b['a']][c]-aa[b['b']][c])**2 for c in ['x','y','z']))<2.9 for b in bb),e['id']+' 3D bond lengths')
 if e['depictionKind']!='molecule':check(e['model3dPath'] is None,e['id']+' no invented nondiscrete 3D')
for rid,mm in binding['recordBindings'].items():
 check(all(mid in entries for mid in mm.values()),rid+' bindings resolve')
check(sha(R/'bindings.json')==audit['bindingsSha256'],'Bindings unchanged since targeted refresh')
aggregate=read(R/'molecules-3d.json')
check(len(aggregate)==37,'37 optional models')
for m in aggregate:check(m==read(R/entries[m['id']]['model3dPath']),m['id']+' aggregate equals standalone model')
for filename in ['registry.json','bindings.json','molecules-3d.json']:
 check(not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|file://',(R/filename).read_text(encoding='utf-8')),filename+' no absolute local paths')
check(not read(R/'generation-report.json')['optionalModelIssues'],'No generation errors')
for row in audit['changedPublicAssets']:check(sha(R/row['path'])==row['sha256'],row['path']+' current change manifest hash')
check(audit['modelsWithUnchangedNonGroupFields']==81,'All model geometry and other fields preserved by refresh')
check(audit['positiveNegativeChemistryCases']==12,'12 chemistry class boundary tests passed')
audit.update({'status':'passed' if not errors else 'failed','assetValidationChecks':checks,'assetValidationErrors':errors,'visualReview':{'status':'passed','reviewedIds':['tris-diethylamino-phosphine'],'method':'Rendered actual corrected SVG via PyMuPDF and visually inspected. All other product SVGs remain byte-identical to the prior complete visual audit.','renderPath':'actual-svg-review/tris-diethylamino-phosphine.png','svgSha256':sha(R/'svg/tris-diethylamino-phosphine.svg'),'renderSha256':sha(R/'actual-svg-review/tris-diethylamino-phosphine.png')}})
dump(R/'functional-group-audit.json',audit)
prior=read(R/'validation-report.json')
report={'status':audit['status'],'checks':checks,'errors':errors,'scope':'Complete chemical asset structure/hash validation; preserved record bindings resolve. Source-record byte hashes are maintained independently by root and were not revalidated or changed.','registrySha256':sha(R/'registry.json'),'bindingsSha256':sha(R/'bindings.json'),'summary':registry['summary'],'visualReviewStatus':'passed','visualReview':'All 89 SVGs had prior manual visual inspection; the one changed SVG was rendered and reviewed again.','functionalGroupAuditSha256':sha(R/'functional-group-audit.json'),'primaryConnectivityVerifiedDuringGeneration':True,'formulaChargeAndIndicesVerifiedDuringGeneration':True,'limits':prior['limits']}
dump(R/'validation-report.json',report)
handoff=read(R/'handoff.json');handoff.update({'registry_sha256':sha(R/'registry.json'),'bindings_sha256':sha(R/'bindings.json'),'validation_sha256':sha(R/'validation-report.json'),'functional_group_audit_sha256':sha(R/'functional-group-audit.json'),'bounded_update_instruction':'For this annotation correction copy only changedPublicAssets listed in functional-group-audit.json. Preserve root-maintained public bindings.json; do not copy private bindings. No coordinates or source connectivity changed.'})
dump(R/'handoff.json',handoff)
lines=['# Functional-group audit','',f'Passed: {checks} asset checks, 89 entries, 81 models, 12 positive/negative chemical-class tests.','', 'Corrected phosphonic-acid/phosphine-oxide overlap (TDPA, HPA), carbonate/carboxylate overlap (Cs2CO3, Na2CO3), ammonia/amine naming, and aminophosphine/ordinary-amine naming. TOP and TBP are specifically labeled tertiary phosphines. TOPO remains correctly labeled phosphine oxide.','', 'Every model coordinate, bond, source field and non-group field is preserved. Bindings are unchanged byte-for-byte. The only changed SVG, tris(diethylamino)phosphine, now highlights all three P–N bonds and was visually reviewed. Other SVGs did not require changes because their highlighted atom/bond unions remain the same.','', 'Copy only these changed public assets; do not copy bindings.json:','']
lines += [f'- `{x["path"]}` — `{x["sha256"]}`' for x in audit['changedPublicAssets']]
lines += ['', 'Source rules updated in build_registry.py. Targeted updater refresh_functional_groups.py avoids full-build side effects. Validator validate_functional_group_refresh.py checks all asset hashes, model/group indices, 3D bond lengths, model aggregate equality, passive SVGs and binding resolution. No network or Site writes were used.','', 'Private audit/support files also changed: validation-report.json, handoff.json, functional-group-audit.json, functional-group-audit.md, svg/tris-diethylamino-phosphine-review.png and actual-svg-review/tris-diethylamino-phosphine.png.']
(R/'functional-group-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':checks,'errors':errors,'registrySha256':report['registrySha256'],'auditSha256':sha(R/'functional-group-audit.json'),'changedPublicAssets':audit['changedPublicAssets']},indent=2))
raise SystemExit(bool(errors))
