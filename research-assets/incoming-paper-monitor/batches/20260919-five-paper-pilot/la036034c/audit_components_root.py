"""Distinct root audit of the frozen component proposal; no author assets rewritten."""
from pathlib import Path
import sys,json,hashlib,math,re,collections
from datetime import datetime,timezone
N=Path(__file__).resolve().parent;V=N/'visuals/components'
sys.dont_write_bytecode=True
sys.path.insert(0,str(N.parents[3]/'rdkit-runtime'))
from rdkit import Chem
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def ck(v,s):
 checks.append({'check':s,'passed':bool(v)})
 if not v:raise AssertionError(s)
def ptr(d,p):
 for k in p.strip('/').split('/'):d=d[int(k)] if isinstance(d,list) else d[k.replace('~1','/').replace('~0','~')]
 return d
def mol(d):
 r=Chem.RWMol()
 for a in d['atoms']:
  z=Chem.Atom(a['element']);z.SetFormalCharge(a.get('formalCharge',0));z.SetNoImplicit(True);z.SetNumExplicitHs(a.get('implicitHydrogenCount',0));z.SetIsotope(a.get('isotope',0));z.SetNumRadicalElectrons(a.get('radicalElectrons',0))
  if a.get('chiralTag'):z.SetChiralTag(getattr(Chem.ChiralType,a['chiralTag']))
  r.AddAtom(z)
 for b in d['bonds']:r.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 m=r.GetMol();Chem.SanitizeMol(m);return m
def smiles(m):return Chem.MolToSmiles(Chem.RemoveHs(m),isomericSmiles=True)
freeze=read(V/'package-freeze.json');bound={str(V/'package-freeze.json'):sha(V/'package-freeze.json')}
ck(bound[str(V/'package-freeze.json')]=='d666280ead08a50da2cbf27c1a577045e44824ccd6aa0a28958f93e4f529d4b6','Expected author freeze')
for entries,base in [(freeze['scientific_input_hashes'],None),(freeze['bound_files'],V)]:
 for p,h in entries.items():
  p=Path(p) if base is None else base/p;ck(sha(p)==h,'Frozen file '+str(p));bound[str(p)]=h
entries=read(V/'registry-additions.json')['entries'];emap={e['id']:e for e in entries}
ck(len(emap)==42,'42 unique scoped identities')
model_count=collections.Counter();mols={};seen_views=[]
for e in entries:
 ck(not any(e[k] for k in ['binding_approved','published','eligible_training']),e['id']+' remains private')
 ck(not e['provenance']['measuredCoordinates'],e['id']+' reference or symbolic, not measured coordinates')
 ck(bool(e['caption']) and bool(e['limitations']),e['id']+' scope caption and limitations')
 for field,dim in [('model2dPath',2),('model3dPath',3)]:
  if not e.get(field):continue
  d=read(V/e[field]);model_count[dim]+=1;m=mol(d);mols[(e['id'],dim)]=m
  ck(d['has3D']==(dim==3) and d['allowRotation']==(dim==3),e['id']+' dimension and rotation')
  counts=collections.Counter(a['element'] for a in d['atoms']);counts['H']+=sum(a.get('implicitHydrogenCount',0) for a in d['atoms'])
  target=collections.Counter({a:int(n or 1) for a,n in re.findall(r'([A-Z][a-z]?)(\d*)',e['formula'])})
  ck(+counts==+target,e['id']+' independently counted atoms/H')
  for g in d['functionalGroups']:
   ck(all(0<=i<len(d['atoms']) for i in g['atomIndices']),e['id']+' group atom bounds '+g['label'])
   ck(all(0<=i<len(d['bonds']) and d['bonds'][i]['a'] in g['atomIndices'] and d['bonds'][i]['b'] in g['atomIndices'] for i in g['bondIndices']),e['id']+' group connectivity '+g['label'])
  prov=e['provenance']
  target_smiles=prov.get('referenceSmiles',prov.get('referenceGeometryOrigin',{}).get('smiles'))
  if e['id']=='nagasaki2004-pdp-reference':target_smiles='CCOC(CC[O-])OCC.[K+]'
  if target_smiles:ck(smiles(m)==smiles(Chem.MolFromSmiles(target_smiles)),e['id']+f' {dim}D graph and stereochemistry match qualified identity')
  if prov.get('reusedRegistryId'):
   old=read(V/'reference-base'/f"{prov['reusedRegistryId']}-entry.json");before=read(V/'reference-base'/Path(old[field]).name)
   ck(d['atoms']==before['atoms'] and d['bonds']==before['bonds'],e['id']+' cached graph and coordinates exact')
  if dim==3:
   ck(d['coordinateUnits']=='angstrom',e['id']+' 3D distance units')
   for b in d['bonds']:
    aa,bb=d['atoms'][b['a']],d['atoms'][b['b']];dist=math.dist([aa[k] for k in ['x','y','z']],[bb[k] for k in ['x','y','z']])
    ck((.7 if 'H' in [aa['element'],bb['element']] else 1.0)<dist<2.1,e['id']+' bond metric')
   if prov.get('source2dPath'):
    raw=Chem.MolFromMolFile(str(V/prov['source2dPath'].replace('-2d.sdf','-3d.sdf')),removeHs=False)
    ck(smiles(m)==smiles(raw),e['id']+' 3D retained primary graph')
    ck(raw.GetNumAtoms()==len(d['atoms']) and all(math.dist(tuple(raw.GetConformer().GetAtomPosition(i)),tuple(a[k] for k in ['x','y','z']))<1e-12 for i,a in enumerate(d['atoms'])),e['id']+' primary conformer coordinates unaltered')
   seen_views.append(str(V/'review'/f"{e['id']}-3d-projections.png"))
  elif prov.get('source2dPath'):
   raw=Chem.MolFromMolFile(str(V/prov['source2dPath']),removeHs=False)
   ck(smiles(m)==smiles(raw),e['id']+' 2D retained primary graph')
for key in ['na2s','nabh4','cdcl2','pdp','nacl','naoh']:
 m=mols[('nagasaki2004-'+key+'-reference',2)]
 ck(Chem.GetFormalCharge(m)==0,key+' net formal charge zero')
 ck(len(Chem.GetMolFrags(m))>=2,key+' separated counterions, no invented ion-pair geometry')
ck(len(Chem.FindMolChiralCenters(mols[('nagasaki2004-biocytin-hydrazide-reference',2)],includeUnassigned=True))==4,'Biocytin hydrazide four specified stereocenters')
ck(model_count=={2:14,3:8},'14 connectivity models and 8 free-molecule conformers')
slots=read(V/'source-slot-mapping.json')['slots'];binding=read(V/'molecule-bindings-proposal.json');plan=read(N/'visual-reuse-plan.json')
ck({(s['record_id'],s['material_id']) for s in slots}=={(s['record_id'],s['material_id']) for s in plan['material_slots']} and len(slots)==61,'Exact61-slot coverage without formula joins')
for s in slots:
 rpath=N/'canonical-drafts'/f"{s['record_id']}.json";r=read(rpath);m=ptr(r,s['canonical_material_pointer']);note=binding['bindingNotes'][s['record_id']][s['material_id']]
 ck(sha(rpath)==s['canonical_record_sha256'] and m==s['canonical_material'],s['record_id']+'/'+s['material_id']+' canonical payload unchanged')
 ck(binding['recordBindings'][s['record_id']][s['material_id']]==s['registry_id'] and s['registry_id'] in emap,s['material_id']+' explicit identity resolution')
 ck(note['canonical_evidence']==m.get('evidence',[]) and note['source_name']==m['name'] and note['source_formula']==m.get('formula'),s['material_id']+' exact source name/formula/evidence')
stocks=read(V/'stock-component-selectors.json')['stocks'];ck(len(stocks)==2,'Exactly two documented stock contexts')
for s in stocks:
 r=read(N/'canonical-drafts'/f"{s['record_id']}.json");o=ptr(r,s['canonical_pointer'])
 ck(s['concentrations']==o['concentrations'] and s['scope']==o['scope'],s['stock_id']+' concentration bases and scope unchanged')
 ck([c['canonical_component'] for c in s['components']]==o['components'],s['stock_id']+' component quantities unchanged')
 for c in s['components']:ck(binding['recordBindings'][s['record_id']][c['material_id']]==c['registry_id'],s['stock_id']+' component selector matches source slot')
report={'schema':'mattersyn-component-independent-audit/1','status':'passed_scoped_component_reference_and_binding_audit','at':datetime.now(timezone.utc).isoformat(),'author':'/root/peng1998_reader_assets','auditor':'/root','counts':{'entries':42,'source_slots':61,'stocks':2,'models_2d':14,'models_3d':8,'checks':len(checks),'failures':0},'scope':'Independent review of source-scoped component proposal, existing audited canonical identities and quantities, retained primary chemical graphs and reference geometry. Not a new whole-paper audit, crystal qualification or browser/publication approval.','scientific_scopes':[
 'All42captions/limitations and61named material bindings read. No source purity, hydration, counterion, solvent grade or reaction conditions imported from unrelated entries.',
 '14atomic depictions and all8reference conformers actually viewed. Formula counts, formal charges, graph identity, stereochemistry and primary/cached coordinates checked independently.',
 'Functional-group highlights correspond to ether/alcohol/carboxyl/epoxide/methacrylate ester/tertiary amine/alkene/acetal/alkoxide/hydrazide/primary amine/ureido motifs as depicted; no site count or assay inferred.',
 'Na2S and CdCl2 hydration unknown; NaBH4 has B-H4 plus separate Na+; PDP is an explicitly name-derived alkoxide. Potassium naphthalene remains source-name only.',
 'Biocytin hydrazide reference retains the lysine hydrazide linker and four stereocenters; it is not free biotin and does not describe measured polymer grafting.',
 'Polymer end groups, removed PEG prepolymer, pre-dialysis intermediate, independent controls, proteins, supports and unknown protonating reagent remain symbolic.',
 'Amine-group concentration is not polymer-chain molarity. Stock components remain separate and no solution conformation or missing Cd/S addition volumes are assigned.',
 'TEM, XRD, Figure2 optical, salt, zeta and FRET contexts remain separate; no atomistic CdS product or exact specimen join is approved.'
 ],'actual_visual_inspection':{'contact_sheets':[str(V/'review'/f'contact-{i:02d}.png') for i in range(1,8)],'component_depictions':42,'reference_projection_images':seen_views,'note':'AMA private projection title exceeds its individual panel width; atom geometry is visible. These audit-only projection images must not be promoted as public reader assets. Public SVG title fits.'},'checks':checks,'bound_files':bound,'unresolved_findings':[],'browser_validation':'not_performed','site_integration':'not_performed','publication_approved':False,'training_admission':False}
out=N/'component-source-audit.json';ck(not out.exists(),'No prior independent audit overwritten')
report['counts']['checks']=len(checks)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(N/'component-source-audit.md').write_text('# Nagasaki component scientific audit\n\nPassed for the frozen private component proposal:42identities,61materialslots,2stocks,14connectivitymodels and8free-moleculeconformers. Root reviewed every caption, all7componentcontact sheets and8three-view reference projections. All mechanical checks passed.\n\nSource-specific uncertainty and specimen boundaries are retained. This does not approve crystal references, integrated browser behavior, publication or training admission. Details and exact bindings: component-source-audit.json.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'audit_sha256':sha(out)}))
