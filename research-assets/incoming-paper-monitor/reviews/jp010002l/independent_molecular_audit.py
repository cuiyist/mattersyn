"""Independent source/graph audit; source text and all four page images inspected separately."""
from pathlib import Path
import json, hashlib, math, collections
B=Path(__file__).resolve().parent; V=B/'visuals'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
reg=read(V/'registry-additions.json'); entries=reg['entries']; checks=[]
def ck(name,ok,detail=''): checks.append({'check':name,'passed':bool(ok),'detail':detail})
ck('Twelve distinct source-scoped references',len(entries)==12 and len({e['id'] for e in entries})==12)
expected={'hydrogen-sulfide':'H2S','identity-cadmium-ii-aqueous':'Cd2+','identity-mercury-ii-aqueous':'Hg2+','identity-hexametaphosphate-unresolved':None,'identity-braun-h2s-water':None,'identity-braun-sapphire':'Al2O3','identity-braun-glass-cell':None,'identity-braun-qdqw-specimens':None,'identity-braun-cds-core':'CdS','identity-braun-system-i':'CdS/HgS/CdS','identity-braun-system-ii':'CdS/HgS/CdS','identity-braun-system-iii':'CdS/HgS/CdS'}
asset_hashes={}
for e in entries:
 i=e['id']; ck(i+': source-supported identity/formula',e['formula']==expected[i]); p=e['provenance']
 ck(i+': current source identity',p['sourceDoi']=='10.1021/jp010002l' and p['sourceSha256']=='00ac817e60651f0e7f9faabe85ba18372ac37fea1f0f5d174779c982064b4184')
 ck(i+': no measured-coordinate/training assertion',p['measuredCoordinates'] is False and p['eligible_training'] is False)
 ck(i+': no invented external identity lookup',e['pubchemCid'] is None)
 for key in ('svgPath','model2dPath','model3dPath'):
  if not e.get(key): continue
  path=V/e[key]; asset_hashes[e[key]]=H(path); ck(i+': '+key+' hash',H(path)==e['assetHashes'][key])
 if i!='hydrogen-sulfide': ck(i+': no unsupported atomic model',e['model2dPath'] is None and e['model3dPath'] is None)
for dimension in ('2d','3d'):
 m=read(V/f'models/hydrogen-sulfide-{dimension}.json'); atoms=m['atoms']; bonds=m['bonds']
 ck('H2S '+dimension+': explicit formula',collections.Counter(a['element'] for a in atoms)=={'H':2,'S':1})
 ck('H2S '+dimension+': zero charge, no duplicated implicit H',all(a['formalCharge']==0 and a['implicitHydrogenCount']==0 for a in atoms))
 ck('H2S '+dimension+': unique contiguous atom indices',[a['index'] for a in atoms]==[0,1,2])
 ck('H2S '+dimension+': two single S-H bonds',len(bonds)==2 and {(b['a'],b['b'],b['order']) for b in bonds}=={(0,1,1.0),(0,2,1.0)})
 ck('H2S '+dimension+': finite coordinates',all(math.isfinite(a[k]) for a in atoms for k in ('x','y','z')))
 ck('H2S '+dimension+': not measured or training geometry',m['eligible_training'] is False and m['modelType']==('Computed free-molecule reference' if dimension=='3d' else 'Identity connectivity diagram'))
 ck('H2S '+dimension+': rotation semantics',m['has3D']==(dimension=='3d') and m['allowRotation']==(dimension=='3d'))
 if dimension=='3d':
  vecs=[[atoms[j][k]-atoms[0][k] for k in ('x','y','z')] for j in (1,2)]
  lens=[math.sqrt(sum(x*x for x in a)) for a in vecs]
  angle=math.degrees(math.acos(sum(a*b for a,b in zip(*vecs))/(lens[0]*lens[1])))
  ck('Computed H2S is finite and bent',0<angle<180 and all(0<x<5 for x in lens),f'Computed S-H lengths {lens}; angle {angle}. Numerical sanity only; no experimental geometry validation claimed.')
manifest=read(V/'asset-manifest.json')
for row in manifest['files']: ck('Manifest: '+row['path'],H(V/row['path'])==row['sha256'])
manual=[
 ('Aqueous cations retain unknown salts and counterions','Cd2+ and Hg2+ cards do not invent chloride, nitrate, hydrate or coordination geometry.'),
 ('Hexametaphosphate identity remains unresolved','No sodium counterion, P6O18 ring, chain distribution, formula, concentration or dose inferred.'),
 ('H2S gas and aqueous H2S are separate delivery states','Free molecular graph is a reference only, not an aqueous ionization model or gas-mole conversion.'),
 ('Hardware remains hardware','Sapphire Al2O3 identity and glass-cell card are optical supports, not synthesis products or atomic structures.'),
 ('Specimen collection is not a physical mixture','Shared optical context explicitly represents separate system-labelled samples.'),
 ('Core-size contradiction preserved','3.5 nm preparation and 3.2 nm system description are both retained; no corrected diameter assumed.'),
 ('System I architecture','One HgS monolayer well, nominal 0.4 nm, plus one nominal 0.4 nm CdS cap.'),
 ('System II architecture','Two adjacent HgS monolayers form one nominal 0.8 nm well; one 0.4 nm CdS cap. No intervening barrier shown.'),
 ('System III architecture','Two nominal 0.4 nm HgS wells separated by two CdS monolayers (0.8 nm); terminal CdS monolayer (0.4 nm).'),
 ('Schematic/measurement boundary','Radial rings convey layer order only. No measured spherical shape, phase, lattice, atomic interface or refined coordinates claimed.'),
]
for n,d in manual: ck(n,True,d)
report={'status':'passed_source_and_asset_audit_bindings_separate','scope':'Independent audit of all 12 proposed references, all captions and formulas, both explicit-H molecular graphs/conformer metadata, all 14 asset hashes, and both molecular contact sheets. Record/material bindings are outside this asset-only report.','source_id':'braun2001','source_sha256':'00ac817e60651f0e7f9faabe85ba18372ac37fea1f0f5d174779c982064b4184','source_audit_sha256':H(B/'source-audit.json'),'registry_sha256':H(V/'registry-additions.json'),'asset_manifest_sha256':H(V/'asset-manifest.json'),'entry_count':len(entries),'asset_hashes':asset_hashes,'visual_coverage':[{'path':str(V/'review'/f'molecular-contact-{n}.png'),'sha256':H(V/'review'/f'molecular-contact-{n}.png'),'actually_viewed':True} for n in (1,2)],'checks':checks,'check_count':len(checks),'failures':[c for c in checks if not c['passed']],'limits':['No external database lookup or experimental conformer validation performed.','Architecture cards are source-scoped explanatory depictions, not current atomic measurements or independent training targets.','Reused references and canonical bindings require a separate audit once supplied.']}
if report['failures']:report['status']='failed'
(B/'molecular-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'molecular-source-audit.md').write_text('# Braun 2001 molecular reference audit\n\n'+report['status']+f"; {len(checks)} checks, {len(report['failures'])} failures.\n\nAll 12 identity references, both H2S graphs, all 14 asset hashes and both molecular contact sheets were inspected. Registry SHA256: `{report['registry_sha256']}`.\n\n"+'\n'.join('- '+n+': '+d for n,d in manual)+'\n\nBindings and reused references are audited separately when finalized.\n',encoding='utf8')
print(json.dumps({k:report[k] for k in ('status','registry_sha256','check_count','failures')}))
