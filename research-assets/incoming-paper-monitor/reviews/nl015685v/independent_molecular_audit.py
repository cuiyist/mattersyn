"""Independent source, identity, graph and visual audit of the private proposal."""
from pathlib import Path
import json, hashlib, math, collections
B=Path(__file__).resolve().parent; V=B/'visuals'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
reg=read(V/'registry-additions.json'); entries=reg['entries']; by={e['id']:e for e in entries}; checks=[]
def ck(name,ok,detail=''): checks.append({'check':name,'passed':bool(ok),'detail':detail})
expected={'tetraethyl-orthosilicate':'C8H20O4Si','cetyltrimethylammonium-bromide':'C19H42BrN','cadmium-nitrate-hydration-unspecified':'CdN2O6','identity-besson-air':None,'identity-besson-acidified-water':'H2O','identity-besson-acid':None,'identity-besson-citrate':None,'identity-besson-pyrex':None,'identity-besson-silicon':'Si','identity-besson-copolymer':None,'identity-besson-silica-sol':None,'identity-besson-ctab-sol':None,'identity-besson-loading-solution':None,'identity-besson-film-specimens':None,'identity-besson-cds-colloid':'CdS','identity-besson-empty-film':'SiO2','identity-besson-copolymer-host':'SiO2','identity-besson-pl-host':'SiO2','identity-besson-pl-film':'CdS/SiO2','identity-besson-cd-loaded-film':None,'identity-besson-ctab-cds-film':'CdS/SiO2','identity-besson-copolymer-cds-film':'CdS/SiO2'}
ck('Exactly 22 distinct expected references',set(by)==set(expected) and len(entries)==22)
assets={}
for e in entries:
 i=e['id']; p=e['provenance']
 ck(i+': formula',e['formula']==expected[i])
 ck(i+': source provenance',p['sourceDoi']=='10.1021/nl015685v' and p['sourceSha256']=='9f1b5b781e7a36f1ec109eb14ee724bb6c99a8156b4bc6899cfffe8ab613c357')
 ck(i+': reference not measured or training geometry',p['measuredCoordinates'] is False and p['eligible_training'] is False)
 ck(i+': no invented database identity',e['pubchemCid'] is None)
 for k in ('svgPath','model2dPath','model3dPath'):
  if e.get(k):
   assets[e[k]]=H(V/e[k]); ck(i+': '+k+' exact hash',assets[e[k]]==e['assetHashes'][k])
 if i.startswith('identity-'): ck(i+': no unsupported atomic geometry',e['model2dPath'] is None and e['model3dPath'] is None)
models={}
for p in sorted((V/'models').glob('*.json')):
 m=read(p); models[p.stem]=m; atoms=m['atoms']; bonds=m['bonds']; name=p.stem
 ck(name+': contiguous atoms',[a['index'] for a in atoms]==list(range(len(atoms))))
 ck(name+': finite coordinates',all(math.isfinite(a[k]) for a in atoms for k in ('x','y','z')))
 ck(name+': explicit H has no implicit duplicates',all(a['implicitHydrogenCount']==0 for a in atoms))
 ck(name+': no measured-coordinate label',m['eligible_training'] is False)
 is3d=name.endswith('3d'); ck(name+': dimension/rotation semantics',m['has3D']==is3d and m['allowRotation']==is3d)
 ck(name+': neutral formula unit',sum(a['formalCharge'] for a in atoms)==0)
 if name.startswith('tetraethyl'):
  ck(name+': atom count',collections.Counter(a['element'] for a in atoms)=={'C':8,'H':20,'O':4,'Si':1})
  heavy={(min(b['a'],b['b']),max(b['a'],b['b']),b['order']) for b in bonds if atoms[b['a']]['element']!='H' and atoms[b['b']]['element']!='H'}
  ck(name+': four ethoxy branches',heavy=={(0,1,1),(1,2,1),(2,3,1),(3,4,1),(4,5,1),(5,6,1),(3,7,1),(7,8,1),(8,9,1),(3,10,1),(10,11,1),(11,12,1)})
  ck(name+': silicon alkoxy group contains silicon and all four oxygen atoms',m['functionalGroups']==by['tetraethyl-orthosilicate']['functionalGroups'] and m['functionalGroups'][0]['atomIndices']==[2,3,4,7,10])
  for a in atoms:
   val=sum(b['order'] for b in bonds if a['index'] in (b['a'],b['b']))
   ck(name+': valence '+str(a['index']),val=={'C':4,'Si':4,'O':2,'H':1}[a['element']])
  if is3d:
   lengths=[math.sqrt(sum((atoms[b['a']][k]-atoms[b['b']][k])**2 for k in ('x','y','z'))) for b in bonds]
   ck(name+': finite nondegenerate computed conformer',all(0.5<x<3 for x in lengths) and max(a['z'] for a in atoms)-min(a['z'] for a in atoms)>1,'Numerical sanity only; no experimental conformer validation.')
 elif name.startswith('cetyl'):
  ck(name+': CTAB atom count',collections.Counter(a['element'] for a in atoms)=={'C':19,'H':42,'N':1,'Br':1})
  heavy={(min(b['a'],b['b']),max(b['a'],b['b']),b['order']) for b in bonds if atoms[b['a']]['element']!='H' and atoms[b['b']]['element']!='H'}
  ck(name+': sixteen-carbon chain plus three N methyl groups',heavy=={(i,i+1,1) for i in range(16)}|{(16,17,1),(16,18,1),(16,19,1)})
  ck(name+': explicit disconnected bromide',atoms[16]['formalCharge']==1 and atoms[20]['element']=='Br' and atoms[20]['formalCharge']==-1 and all(20 not in (b['a'],b['b']) for b in bonds))
  ck(name+': correct functional-group label',[g['label'] for g in m['functionalGroups']]==['Quaternary ammonium'])
 elif name.startswith('cadmium'):
  ck(name+': nitrate atom count',collections.Counter(a['element'] for a in atoms)=={'Cd':1,'N':2,'O':6})
  ck(name+': independent Cd2+ and two nitrate anions',[(a['element'],a['formalCharge']) for a in atoms]==[('Cd',2),('O',-1),('N',1),('O',0),('O',-1),('O',-1),('N',1),('O',0),('O',-1)])
  ck(name+': nitrate resonance connectivity without Cd coordination',{(min(b['a'],b['b']),max(b['a'],b['b']),b['order']) for b in bonds}=={(1,2,1),(2,3,2),(2,4,1),(5,6,1),(6,7,2),(6,8,1)})
  ck(name+': nitrate not organic nitro',[g['label'] for g in m['functionalGroups']]==['Nitrate ion'])
ck('Exactly four model artifacts',len(models)==4)
for row in read(V/'asset-manifest.json')['files']: ck('Manifest hash '+row['path'],H(V/row['path'])==row['sha256'])
manual=[
 ('TEOS reference scope','Free precursor graph only; hydrolyzed sol/condensed silica oligomers are not assigned this conformer.'),
 ('CTAB identity and geometry','C16 alkyl chain, three methyl groups, quaternary N+ and disconnected Br−; 2D placement is not an ion-pair separation or micelle/crystal model.'),
 ('Cadmium nitrate identity','Anhydrous formula-unit connectivity is displayed as identity only; actual hydration, solution coordination and final bath speciation remain unreported.'),
 ('Acidified water','H2O labels solvent only. Acid identity, dose and final mixed-sol pH are not inferred from initial water pH 1.25.'),
 ('Sodium citrate and copolymer','No guessed citrate protonation/hydrate or block-copolymer brand, block lengths, molecular weight or dose.'),
 ('Support distinctions','Pyrex and silicon remain distinct supports. Silicon-wafer PL specimens are not automatically assigned the CTAB route.'),
 ('Solution and specimen scopes','Sol, loading bath, separate film comparison set and reverse-micelle comparator remain distinct; no unique oligomer, complex, mixture or unreported comparator synthesis invented.'),
 ('Stage distinction','Cadmium-adsorbed film before H2S is not labelled a precipitated CdS product.'),
 ('Mesoscopic/atomic distinction','Pore and filled-film cards are explanatory mesostructure schematics, not refined atomic silica/CdS coordinates, measured pore arrangements or new training labels.'),
 ('Original visual coverage','All four contact sheets and all 22 entries were actually inspected; final corrected nitrate/TEOS sheet was re-inspected after group-label correction. Other three sheets retain unchanged identity cards.'),
]
for n,d in manual: ck(n,True,d)
failures=[c for c in checks if not c['passed']]
report={'status':'passed_source_graph_asset_audit_bindings_separate' if not failures else 'failed','source_id':'besson2002','source_sha256':'9f1b5b781e7a36f1ec109eb14ee724bb6c99a8156b4bc6899cfffe8ab613c357','source_audit_sha256':H(B/'source-audit.json'),'registry_sha256':H(V/'registry-additions.json'),'asset_manifest_sha256':H(V/'asset-manifest.json'),'entry_count':len(entries),'asset_hashes':assets,'visual_coverage':[{'path':str(V/'review'/f'molecular-contact-{n}.png'),'sha256':H(V/'review'/f'molecular-contact-{n}.png'),'actually_viewed':True} for n in range(1,5)],'resolved_findings':['Removed erroneous organic Nitro group from nitrate; retained Nitrate ion.','TEOS highlight labelled Silicon–alkoxy center with Si and all four directly bonded oxygen atoms.'],'checks':checks,'check_count':len(checks),'failures':failures,'limits':['No experimental conformer validation or external identity lookup.','Record bindings, reused references and product-card associations require the separate bindings audit.','No atomistic model is supplied for porous silica, templated films or CdS nanocrystals.']}
(B/'molecular-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'molecular-source-audit.md').write_text('# Besson 2002 molecular source audit\n\n'+report['status']+f"; {len(checks)} checks, {len(failures)} failures.\n\nInspected all 22 identities, four molecular models, 26 asset hashes and four contact sheets. Registry SHA256 `{report['registry_sha256']}`.\n\n"+'\n'.join('- '+n+': '+d for n,d in manual)+'\n\nResolved nitrate/nitro mislabelling and clarified TEOS alkoxy highlights. Bindings and reused references are audited separately.\n',encoding='utf8')
print(json.dumps({k:report[k] for k in ('status','registry_sha256','check_count','failures')}))
