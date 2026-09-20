"""Private source-specific registry merge proposal; never modifies the Site."""
from pathlib import Path
import json,hashlib,html,textwrap,collections
R=Path(__file__).resolve().parent; REVIEW=R.parent
OLD=Path('[local path redacted]')
DOI='10.1021/cm970189m'; SH='eac4fe78e4bc3ab9c15e0409b69232e4294a0c07787d3ca650c378f6341d4adc'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old={e['id']:e for e in read(OLD/'registry.json')['entries']}
neutralizations=[]
for ident in ['acetonitrile','acetone']:
 note='Free '+ident+' chemical reference. Any conformer is locally computed and illustrative, not measured solution or surface geometry. Amounts, mixtures and applications belong to the individual source record.'
 neutralizations.append({'id':ident,'caption':note,'limitations':[note],'preserveCoordinatesAndAssetHashes':True,'reason':'Remove earlier-paper procedure context from a shared chemical identity.'})
 old[ident]['caption']=note;old[ident]['limitations']=[note]
save(R/'registry-neutralizations.json',{'scope':'Metadata-only corrections to existing shared identities; coordinate assets and hashes unchanged','updates':neutralizations})
entries=read(R/'molecule-registry-proposal.json')['entries']; new={e['id']:e for e in entries}
for e in entries:
 e['provenance']['sourceRecords']=[]
 e['provenance']['visualReview']={'twoDimensional':'passed; all 22 source-named molecular depictions inspected','threeDimensional':'passed; all 22 actual JSON conformers projected and inspected','scope':'Illustrative connectivity/conformers, not experimental coordinates'}
 if e['id']=='thionyl-chloride':
  e['formula']=e['displayFormula']='SOCl2'
  for k in ['model2dPath','model3dPath']:
   d=read(R/e[k]);d['formula']='SOCl2'
   for g in d.get('functionalGroups',[]):
    if g.get('label')=='Sulfoxide':g['label']='Thionyl group'
   save(R/e[k],d)
  for g in e.get('functionalGroups',[]):
   if g.get('label')=='Sulfoxide':g['label']='Thionyl group'
  e['assetHashes']={k:sha(R/e[k]) for k in ['svgPath','model2dPath','model3dPath']}
mapping={'acn':'acetonitrile','n2':'nitrogen','hpt':'4-hydroxythiophenol','dmso':'dimethyl-sulfoxide','cdcl3':'chloroform-d','d2o':'deuterium-oxide','kbr':'potassium-bromide','socl2':'thionyl-chloride','pyrene-acid':'pyrene-1-carboxylic-acid','pyrene-chloride':'pyrene-1-carbonyl-chloride','dmso-d6':'dimethyl-sulfoxide-d6'}
mapping.update({x:x for x in ['toluene','water','methanol','acetone','chloroform','imidazole','acetic-acid','acetic-anhydride','butyric-anhydride','butanoyl-chloride','benzoyl-chloride','decanoyl-chloride']})
mapping.update(dict(zip(['3a','3b','3c','3d','3e'],['n-acetylimidazole','n-butanoylimidazole','n-pyrene-1-carbonylimidazole','n-benzoylimidazole','n-decanoylimidazole'])))
cards=[
('na2s','Sodium sulfide nonahydrate','Na2S·9H2O','Na₂S · 9H₂O','salt','Explicit nonahydrate reagent; no crystal, coordination geometry or dissolved speciation is supplied.'),
('cd-acetate','Cadmium acetate, hydration unspecified','Cd(C2H3O2)2','Cd(OAc)₂ · hydration unresolved','salt','Acetate-unit formula reference only; the source does not specify a hydrate or coordination structure. Printed 5.05 g and 29 mmol are inconsistent; no hydration is inferred from them.'),
('ether','Ether, unspecified workup identity',None,'Ether · identity unspecified','formula','Workup sections print ether without expansion. The separate diethyl-ether solubility observation does not prove the workup identity.'),
('sieves','4 Å molecular sieves','Unspecified aluminosilicate','4 Å molecular sieves','support','Source drying medium. Pore-size designation is not an exact composition, stoichiometry, phase or molecular graph.'),
('mixed-bed','D8902 mixed-bed ion-exchange medium','Mixture','D8902 · mixed-bed resin','support','Exact resin formulation and exchange-site structures are unreported; no finite polymer molecule is inferred.'),
('charcoal','D8204 activated charcoal','C','C · activated charcoal','support','Carbonaceous purification medium; porosity, impurity composition and atomic structure are unreported.'),
('filter-paper','Filter paper',None,'Filter paper','support','Wicking support; composition and grade are unreported. No cellulose formula or molecular graph is assigned.'),
('grid','JBS-183 carbon-coated copper TEM grid','C/Cu','C coating / Cu grid · 300 mesh','support','Support architecture only, not a compound formula. Carbon phase and coating thickness are unreported; no atomic coordinates are assigned.'),
('si-grid','Silicon calibration grid','Si','Si · calibration grid','support','Source specifies 21600 lines/cm. This is an instrument calibration reference, not a synthesized Si specimen or a measured unit cell.'),
('tms','TMS NMR reference, conventional interpretation','C4H12Si','TMS · NMR reference','formula','Figure 3 prints TMS without expansion. Tetramethylsilane and C4H12Si are the conventional NMR-reference interpretation retained from the canonical record, not an explicitly expanded source identity. No 2D/3D graph is asserted here.'),
('acyl-agent','N-Acylimidazole, unspecified member','Variable','R–C(=O)–imidazole','formula','Control/degradation exposure does not identify the acyl member. R is variable; this family card has no finite molecular graph.'),
('acyl-chloride','Acyl chloride, unspecified member','Variable','R–C(=O)–Cl','formula','Degradation experiment does not identify the acyl member. R is variable; no dose or unique molecular graph is assigned.'),
('qdoh','QDOH phenolic CdS nanoclusters','CdS','QDOH · source compound 1','surface','CdS is the inorganic composition label only, not a complete cluster formula. The sulfur-bound para-hydroxyphenyl motif is illustrative; no atomic lattice, ligand count, particle shape or coverage is assigned.'),
('bare-capped','Thiophenolate-capped control nanoclusters','CdS','Thiophenolate-capped CdS','surface','The control lacks the phenolic OH substituent; it is ligand-capped, not a bare inorganic surface. No exact particle or ligand geometry is reported.'),
('cluster','Source-specific functionalized CdS specimen','CdS','CdS · specimen-specific surface','surface','Analytical family card: QDOH and derivatives 2a–e are separate specimens. This does not claim every measurement used one material, a unique phase, or one fully substituted surface.'),
('quartz-cuvette','Quartz optical cuvette','SiO2','SiO₂ · optical cuvette','support','Source 1 cm optical path; support composition reference only. No crystalline quartz unit cell or specimen atomic structure is assigned.'),
('imidazolium-chloride','Imidazolium chloride byproduct','C3H5ClN2','Imidazolium chloride','salt','White precipitate from the acyl-chloride precursor route is removed by hot filtration. Ion-pair geometry and crystal structure are unreported.'),
('corresponding-acid','Corresponding organic acid',None,'R–C(=O)–OH','formula','Family byproduct of anhydride preparation or recovered control workup; exact member is source-context dependent.'),
('bulk-cds','Bulk CdS degradation product','CdS','CdS · bulk degradation product','support','Reported degradation outcome; polymorph, dimensions and crystal coordinates are unreported.'),
('os-diester','Corresponding O,S-diester',None,'O,S-diester · variable acyl groups','formula','Crystalline degradation product family. Exact reagent variant, formula, crystal structure and isolated yield are not supplied.')]
for letter,name in zip('abcde',['acetyl','butanoyl','pyrene-1-carbonyl','benzoyl','decanoyl']):
 cards.append(('ester-2'+letter,'CdS surface '+name+' ester 2'+letter,'CdS','Surface ester · compound 2'+letter,'surface','CdS is the inorganic composition label, not the whole capped-particle formula. The source assigns an O-acylated para-phenolic thiolate cap. Motif and R group are illustrative; conversion is not assumed to be complete, and no atomistic phase, ligand count or measured geometry is assigned.'))
def text(x,y,t,size=20):return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#214458">{html.escape(t)}</text>'
def surface(mid):
 # One connection motif, not a whole finite molecule or a particle surface lattice.
 q=mid=='qdoh';bare=mid=='bare-capped';ester=mid.startswith('ester-2')
 if not(q or bare or ester):return text(420,156,'CdS · choose the source specimen',28)+text(420,218,'QDOH and 2a–e are distinct analytical inputs',18)
 end='OH' if q else 'H' if bare else 'O'
 s='<circle cx="130" cy="172" r="63" fill="#ead391" stroke="#8b7943" stroke-width="2"/>'+text(130,180,'CdS',25)
 s+='<path d="M193 172H228M259 172H296M296 172L321 129H371L396 172L371 215H321Z" fill="none" stroke="#466b7e" stroke-width="3"/>'+text(244,181,'S',24)
 s+='<circle cx="346" cy="172" r="30" fill="none" stroke="#466b7e" stroke-width="2"/><path d="M396 172H432" stroke="#466b7e" stroke-width="3"/>'+text(455,180,end,24)
 if ester:
  s+='<path d="M472 172H511M530 159V114M537 159V114M549 172H602" stroke="#466b7e" stroke-width="3"/>'+text(533,181,'C',23)+text(534,100,'O',23)+text(630,181,'R',25)
  labels={'a':'R = CH₃','b':'R = n-C₃H₇','c':'R = pyren-1-yl','d':'R = phenyl','e':'R = n-C₉H₁₉'}
  s+=text(644,229,labels[mid[-1]],19)
 s+=text(420,299,'Illustrative connection motif · no lattice or ligand count',18)
 return s
for mid,name,formula,display,kind,lim in cards:
 ident='identity-veinot-'+mid;mapping[mid]=ident
 assert ident not in old
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="840" height="360" viewBox="0 0 840 360" role="img"><title>'+html.escape(name)+'</title><desc>'+html.escape(lim)+'</desc><rect x="20" y="28" width="800" height="304" rx="18" fill="#f3f7fa" stroke="#d1dfe8"/>'
 if kind=='surface':svg+=surface(mid)
 else:
  for i,t in enumerate(textwrap.wrap(display,38)):svg+=text(420,149+i*34,t,27)
  svg+=text(420,253,'Material reference · no atomic or molecular model',18)
 svg+='</svg>'
 p='svg/'+ident+'.svg';(R/p).write_text(svg,encoding='utf8')
 e={'id':ident,'name':name,'aliases':[name],'formula':formula,'displayFormula':display,'depictionKind':'surface' if kind=='surface' else 'support' if kind=='support' else 'formula','pubchemCid':None,'sourceUrls':['https://doi.org/'+DOI],'svgPath':p,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':lim,'limitations':[lim],'assetHashes':{'svgPath':sha(R/p)},'provenance':{'identitySource':'Source-specific designation; conventional interpretation explicitly marked if applicable','sourceDoi':DOI,'sourceSha256':SH,'sourceRecords':[],'eligible_training':False,'measured_coordinates':False}}
 entries.append(e);new[ident]=e
allentries={**old,**new};bindings={};notes={};hashes={};reused=set()
for p in sorted((REVIEW/'canonical-drafts').glob('*.json')):
 r=read(p);rid=r['record_id'];bindings[rid]={};notes[rid]={};hashes[rid]=sha(p)
 for m in r['materials']:
  ident=mapping[m['id']];e=allentries[ident]
  assert m.get('formula')==e.get('formula'),(rid,m['id'],m.get('formula'),e.get('formula'))
  bindings[rid][m['id']]=ident;notes[rid][m['id']]=' '.join(e.get('limitations',[]))
  if ident in new:e['provenance']['sourceRecords'].append({'recordId':rid,'materialId':m['id'],'evidence':m.get('evidence',[])})
  else:reused.add(ident)
  if m['id']=='water':notes[rid][m['id']]+=' Water molecular identity is distinct from the source D8902/D8204 purification process.'
  if m['id']=='cluster':notes[rid][m['id']]+=' In NMR, precursor 3e is a separate molecular specimen, not this CdS family.'
summary={'newEntryCount':len(entries),'newMoleculeCount':22,'referenceCardCount':len(cards),'reusedEntryCount':len(reused),'recordCount':len(bindings),'materialBindingCount':sum(len(x) for x in bindings.values()),'missingBindingCount':0}
save(R/'registry-additions.json',{'schemaVersion':'1.0.0','assetPurpose':'Private Veinot1997 source-specific references; illustrative, not measured structures','entries':entries,'summary':summary})
save(R/'bindings-additions.json',{'schemaVersion':'1.0.0','recordBindings':bindings,'bindingNotes':notes,'sourceRecordSha256':hashes,'unresolved':[]})
save(R/'reused-references.json',{'existingRegistrySha256':sha(OLD/'registry.json'),'entries':[{'id':i,'assetPaths':{k:old[i][k] for k in ['svgPath','model2dPath','model3dPath'] if old[i].get(k)},'assetHashes':old[i]['assetHashes'],'sourceUrls':old[i]['sourceUrls']} for i in sorted(reused)]})
save(R/'missing-identities.json',{'entries':[{'id':e['id'],'name':e['name'],'formula':e['formula'],'limitation':e['caption'],'model2d':False,'model3d':False} for e in entries if not e['model3dPath']], 'scope':'References with no unique finite molecular/atomic model are fully bound as honest cards; no formula is used to invent a structure.'})
save(R/'molecules-3d-additions.json',[read(R/e['model3dPath']) for e in entries if e['model3dPath']])
save(R/'model-provenance.json',{'sourceDoi':DOI,'sourceSha256':SH,'summary':summary,'newReferences':[{'id':e['id'],'provenance':e['provenance'],'assetHashes':e['assetHashes']} for e in entries],'visualReview':'All 22 free-molecule 2D drawings and actual 3D JSON projections inspected; source cards reviewed separately.','notExperimental':'No atomistic CdS phase, measured particle, surface coverage, coordination structure or crystal asset is invented.'})
save(R/'product-reference-proposal.json',{'scope':'Optional reader identity illustrations; not measured structures or canonical inputs','references':{'veinot-1997-qdoh':'identity-veinot-qdoh',**{'veinot-1997-ester-2'+x:'identity-veinot-ester-2'+x for x in 'abcde'},**{'veinot-1997-acylimidazole-3'+x:mapping['3'+x] for x in 'abcde'},'veinot-1997-pyrenecarbonyl-chloride':mapping['pyrene-chloride']}})
print(json.dumps(summary))
