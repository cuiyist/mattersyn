from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent
R=Path('[local path redacted]')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
reg=read(R/'registry.json');mapping=read(P/'thumbnail-map.json');render=read(P/'render-validation.json')
checks=0
def check(test,note):
 global checks
 checks+=1
 assert test,note
def sig(x):return [x.tag.split('}')[-1],dict(x.attrib),x.text or '',[sig(c) for c in x]]
def chem(x):return any(s in x.get('class','') for s in ['atom-','bond-'])
check(sha(R/'registry.json')==mapping['registry_sha256'],'Registry unchanged')
check(set(mapping['entries'])=={x['id'] for x in reg['entries']},'All registry entries mapped')
allowlist=[]
for e in reg['entries']:
 x=mapping['entries'][e['id']];original=R/e['svgPath']
 check(sha(original)==x['original_sha256']==e['assetHashes']['svgPath'],e['id']+' unchanged source SVG')
 if x['status']=='compact':
  candidate=P/x['proposal_path'];container=P/x['source_container_path']
  check(sha(candidate)==x['thumbnail_sha256'],'Output hash')
  check(sha(container)==x['source_container_sha256'],'Drawing-container hash')
  a=ET.fromstring(original.read_bytes());b=ET.fromstring(candidate.read_bytes());c=ET.fromstring(container.read_bytes())
  check([sig(n) for n in a.iter() if chem(n)]==[sig(n) for n in b.iter() if chem(n)],e['id']+' all chemical labels/bonds/highlights identical')
  check([sig(n) for n in b]==[sig(n) for n in c],e['id']+' exact drawing body')
  old=dict(c.attrib);new=dict(b.attrib)
  for k in ['width','height','viewBox']:old.pop(k,None);new.pop(k,None)
  check(old==new,'Only root dimensions/viewBox change')
  check(x['chemical_body_byte_identical'],'Byte-identical drawing body')
  check(all(n>0 for n in x['thumbnail_viewbox'][2:]),'Positive viewport')
  allowlist.append({'proposal_path':x['proposal_path'],'public_asset':x['thumbnail_path'],'sha256':x['thumbnail_sha256'],'entry_id':e['id']})
 else:
  check(x['status']=='original_retained','Explicit fallback')
  check(x['thumbnail_path']==x['original_svg'],'Original fallback retained')
for eid in ['pati2009-cerium-nitrate-reference','sommer2020-zn-nitrate-reference','sommer2020-al-nitrate-reference','friedfeld2019-indium-acetate-reference']:
 check(mapping['entries'][eid]['status']=='original_retained','Whole ionic formula components retained: '+eid)
for eid in ['sasongko2025-oa-reference','sasongko2025-oam-reference','sasongko2025-ode-reference']:
 check(mapping['entries'][eid]['status']=='compact','Requested core examples compact: '+eid)
for c in render['contacts']:check(sha(P/c['path'])==c['sha256'],'Contact sheet hash')
# Earlier unapproved exploratory crops stay local, outside the release allowlist.
approved={Path(x['proposal_path']).name for x in allowlist}
archive=P/'preliminary-not-approved';archive.mkdir(exist_ok=True)
for p in (P/'svg').glob('*.svg'):
 if p.name not in approved:
  dest=archive/p.name
  check(p.resolve().is_relative_to(P) and dest.resolve().is_relative_to(P),'Bounded private move')
  if dest.exists():check(sha(dest)==sha(p),'Existing preliminary snapshot')
  else:p.rename(dest)
(P/'public-assets.json').write_text(json.dumps(allowlist,indent=2)+'\n','utf8')
report={'status':'passed','checks':checks,'counts':mapping['counts'],
 'map_sha256':sha(P/'thumbnail-map.json'),'all_source_svgs_unchanged':True,
 'chemical_change':'None. Atom/bond/highlight elements retain every original attribute and child; selected drawing bodies are unchanged. Only root viewBox/size is adjusted.',
 'visual_review':{'actual_viewed':'All 206 preliminary previews across six contact sheets; final 175 are byte-identical approved subsets of those previews. Final selection excludes partial formula-component crops.',
  'finding_resolved':'Visual review found counterion/hydrate/multiplier labels outside some RDKit subgroups. Those entries retain their full original SVG and are excluded from public-assets.json.',
  'specific_examples':['Sasongko OA/OAm/ODE full drawings','Disconnected formamidinium/acetate','Friedfeld 13C and deuterated labels','Gu acetylacetonate ions','Pati TEA','Nitrate and acetate plates retained intact']},
 'adoption':'Copy only public-assets.json allowlisted SVGs. thumbnail-map entries point either to the new thumbnail or the existing original. Keep the original registry, captions and full viewer unchanged.',
 'known_limits':['Long-chain drawing proportions are preserved, so small head-group labels still benefit from the existing enlargement/3D viewer.','Symbolic, composite and uncertain layouts retain the original plate.']}
(P/'validation-report.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps({'status':report['status'],'checks':checks,'counts':mapping['counts'],'map_sha256':report['map_sha256']}))
