from pathlib import Path
import json,hashlib,copy,sys,math,collections,re
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
sys.path.insert(0,r'[local path redacted]')
from rdkit import Chem,rdBase
from rdkit.Chem import rdMolDescriptors,rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw,ImageFont
V=Path(__file__).resolve().parent;N=V.parent;S=Path(r'[local path redacted]');M=V/'molecules';P=V/'products'
for d in [M/'svg',M/'models',M/'review',M/'reused',P/'svg',P/'models',P/'downloads',P/'review']:d.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();dump=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
records=[read(p)for p in sorted((N/'canonical-drafts').glob('*.json'))];registry=read(S/'chemical-registry/registry.json');reg={x['id']:x for x in registry['entries']};checks=[];qualified=[];entries=[]
def ck(ok,label,detail=None):
    checks.append({'passed':bool(ok),'label':label,'detail':detail})
    if not ok:raise AssertionError(label)
def graph(m):
    rw=Chem.RWMol()
    for a in m['atoms']:
        atom=Chem.Atom(a.get('element',a.get('elem')));atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0));rw.AddAtom(atom)
    for b in m['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
    mol=rw.GetMol();Chem.SanitizeMol(mol);return mol
def qualify(id,smiles,formula):
    e=reg[id];reference=Chem.MolFromSmiles(smiles);canon=Chem.MolToSmiles(Chem.RemoveHs(reference));assets=[]
    ck(rdMolDescriptors.CalcMolFormula(reference)==formula,id+': target formula')
    for key in ['svgPath','model2dPath','model3dPath']:
        if not e.get(key):continue
        path=S/'chemical-registry'/e[key];ck(sha(path)==e['assetHashes'][key],id+': existing asset hash '+key)
        dest=M/'reused'/e[key];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        a={'key':key,'source_path':str(path),'source_sha256':sha(path),'private_path':str(dest),'private_sha256':sha(dest)}
        if key!='svgPath':
            model=read(path);mol=graph(model);ck(Chem.MolToSmiles(Chem.RemoveHs(mol))==canon,id+': '+key+' graph equivalence');ck(rdMolDescriptors.CalcMolFormula(mol)==formula,id+': '+key+' formula');ck(all(math.isfinite(v)for at in model['atoms']for k,v in at.items()if k in ['x','y','z']),id+': finite coordinates')
            for group in model.get('functionalGroups',e.get('functionalGroups',[])):
                ck(all(0<=i<len(model['atoms'])for i in group['atomIndices']),id+': highlighted atoms '+group['label']);ck(all(0<=i<len(model['bonds'])for i in group.get('bondIndices',[])),id+': highlighted bonds '+group['label'])
            if key=='model3dPath':
                lengths=[math.dist([model['atoms'][b['a']][k]for k in ['x','y','z']],[model['atoms'][b['b']][k]for k in ['x','y','z']])for b in model['bonds']];ck(min(lengths)>.6 and max(lengths)<2.5,id+': bonded coordinate distances',{'minimum':min(lengths),'maximum':max(lengths)})
                a['geometry_status']='Existing documented free-compound computed/reference conformer; not measured solution or surface geometry.'
            a['canonical_smiles']=canon;a['formula']=formula;a['atoms']=len(model['atoms']);a['bonds']=len(model['bonds'])
        assets.append(a)
    qualified.append({'registry_id':id,'qualification':'identity, formula, graph, indices and frozen asset hashes verified','registry_entry':e,'assets':assets,'reuse_scope':'Pure-compound reference only; Norberg concentration, grade, hydrate, role, measured states and batch identity remain in its canonical record.'})
    return e
reuse={'zinc-acetate-dihydrate':('zinc-acetate-dihydrate','[Zn+2].CC(=O)[O-].CC(=O)[O-].O.O','C4H10O6Zn'),'tmah-pentahydrate':('tetramethylammonium-hydroxide-pentahydrate','C[N+](C)(C)C.[OH-].O.O.O.O.O','C4H23NO6'),'dodecylamine':('dodecylamine','CCCCCCCCCCCCN','C12H27N'),'dmso':('dimethyl-sulfoxide','CS(C)=O','C2H6OS'),'ethanol':('ethanol','CCO','C2H6O'),'ethyl-acetate':('ethyl-acetate','CCOC(C)=O','C4H8O2'),'heptane':('heptane','CCCCCCC','C7H16'),'toluene':('toluene','Cc1ccccc1','C7H8'),'nitrogen':('nitrogen','N#N','N2')}
reuse['nitrogen']=('gu2004-nitrogen-reference','N#N','N2')
for mid,(rid,smiles,f)in reuse.items():qualify(rid,smiles,f)
qualify('topo','CCCCCCCCP(=O)(CCCCCCCC)CCCCCCCC','C24H51OP')
def esc(t):return str(t).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
def wrap(t,n=65):
    lines=[];line=''
    for word in t.split():
        if line and len(line)+len(word)+1>n:lines.append(line);line=word
        else:line+=((' 'if line else'')+word)
    return lines+([line]if line else[])
def card(id,title,formula,lines,mode='context'):
    paragraphs=[line for s in lines for line in wrap(s)];h=210+len(paragraphs)*24
    symbol=''
    if mode=='particles':symbol=''.join(f'<circle cx="{72+i*41}" cy="130" r="15" fill="#7194ad"/>'for i in range(5))
    if mode=='film':symbol='<path d="M57 132l158 -36l109 37l-158 41Z" fill="#dceaf2" stroke="#6b8b9c" stroke-width="2"/>'
    if mode=='disk':symbol='<ellipse cx="193" cy="130" rx="126" ry="34" fill="#dceaf2" stroke="#6b8b9c" stroke-width="2"/>'
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 {h}"><rect width="720" height="{h}" rx="16" fill="#f4f9fc"/><text x="26" y="38" font-family="Arial" font-size="22" fill="#173c4b">{esc(title)}</text><text x="26" y="76" font-family="Arial" font-size="18" fill="#3c667d">{esc(formula or "Source-defined context")}</text>{symbol}'+''.join(f'<text x="26" y="{199+i*24}" font-family="Arial" font-size="16" fill="#426271">{esc(line)}</text>'for i,line in enumerate(paragraphs))+'</svg>'
    return svg
def ionic(id,name,smiles,formula,display,limit):
    mol=Chem.MolFromSmiles(smiles);ck(rdMolDescriptors.CalcMolFormula(mol)==formula,id+': formula');rdDepictor.Compute2DCoords(mol);conf=mol.GetConformer();groups=[]
    # Formula-component diagrams do not display algorithmic radical dots as a source spin measurement.
    for a in mol.GetAtoms():
        if a.GetSymbol()=='Mn':a.SetNumRadicalElectrons(0)
    if 'tetrahydrate'in id:
        fragments=Chem.GetMolFrags(mol);positions=[(0,2),(5,2),(10,2),(0,-3),(3.5,-3),(7,-3),(10.5,-3)]
        for frag,(tx,ty)in zip(fragments,positions):
            cx=sum(conf.GetAtomPosition(i).x for i in frag)/len(frag);cy=sum(conf.GetAtomPosition(i).y for i in frag)/len(frag)
            for i in frag:
                p=conf.GetAtomPosition(i);conf.SetAtomPosition(i,(p.x-cx+tx,p.y-cy+ty,0))
    carbox=Chem.MolFromSmarts('[CX3](=[OX1])[O-]');matches=mol.GetSubstructMatches(carbox)
    if matches:groups=[{'label':'Carboxylate groups','atomIndices':sorted({i for match in matches for i in match}),'bondIndices':sorted({b.GetIdx()for b in mol.GetBonds()if any(b.GetBeginAtomIdx()in match and b.GetEndAtomIdx()in match for match in matches)})}]
    elif 'lithium' in id:groups=[{'label':'Hydroxide anion','atomIndices':[1],'bondIndices':[]}]
    else:groups=[{'label':'Nitrate anions','atomIndices':[i for i,a in enumerate(mol.GetAtoms())if a.GetSymbol()in ['N','O']],'bondIndices':[b.GetIdx()for b in mol.GetBonds()]}]
    legend=display.translate(str.maketrans('₀₁₂₃₄₅₆₇₈₉','0123456789')).replace('·',' . ')
    drawer=rdMolDraw2D.MolDraw2DSVG(720,330);drawer.drawOptions().legendFontSize=18;drawer.DrawMolecule(mol,legend=legend,highlightAtoms=groups[0]['atomIndices'],highlightBonds=groups[0]['bondIndices']);drawer.FinishDrawing();svg=drawer.GetDrawingText();(M/'svg'/f'{id}.svg').write_text(svg,encoding='utf-8')
    cap='Formal disconnected formula components. '+limit+' No coordination bonds, ion-pair geometry, hydrate packing or dissolved complex is inferred.'
    model={'id':id,'name':name,'formula':formula,'representation':'2d','has3D':False,'allowRotation':False,'coordinateUnits':'drawing units','indexConvention':'zero-based','modelType':'Formal ionic components','caption':cap,'atoms':[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':conf.GetAtomPosition(a.GetIdx()).x,'y':conf.GetAtomPosition(a.GetIdx()).y,'z':0,'formalCharge':a.GetFormalCharge(),'implicitHydrogenCount':a.GetTotalNumHs()}for a in mol.GetAtoms()],'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble()}for b in mol.GetBonds()],'functionalGroups':groups,'eligible_training':False,'measuredCoordinates':False,'source':{'doi':'10.1021/ja048427j','sourceFactsSha256':sha(N/'source-facts.json'),'smiles':smiles,'software':'RDKit '+rdBase.rdkitVersion}}
    dump(M/'models'/f'{id}-2d.json',model)
    e={'id':id,'name':name,'formula':formula if 'nitrate'not in id else None,'displayFormula':display,'aliases':[name],'depictionKind':'ionic_components','svgPath':f'svg/{id}.svg','model2dPath':f'models/{id}-2d.json','model3dPath':None,'functionalGroups':groups,'caption':cap,'limitations':[limit],'sourceUrls':['https://doi.org/10.1021/ja048427j'],'provenance':model['source'],'assetHashes':{'svgPath':sha(M/'svg'/f'{id}.svg'),'model2dPath':sha(M/'models'/f'{id}-2d.json')},'eligible_training':False,'measuredCoordinates':False};entries.append(e);return e['id']
new={}
new['manganese-acetate-tetrahydrate']=ionic('norberg2004-manganese-acetate-tetrahydrate','Manganese(II) acetate tetrahydrate','[Mn+2].CC(=O)[O-].CC(=O)[O-].O.O.O.O','C4H14MnO8','Mn(OAc)₂·4H₂O','The reported tetrahydrate includes four waters; free component positions are illustrative.')
new['manganese-nitrate-hydrate']=ionic('norberg2004-manganese-nitrate-hydrate','Manganese(II) nitrate hydrate · hydration unknown','[Mn+2].[O-][N+](=O)[O-].[O-][N+](=O)[O-]','MnN2O6','Mn(NO₃)₂·xH₂O; x not reported','The drawing shows only the Mn²⁺ and nitrate formula components. An unspecified water count is not filled in; this is an oxidation control, not the ZnO synthesis feed.')
new['lithium-hydroxide']=ionic('norberg2004-lithium-hydroxide','Lithium hydroxide · formal components','[Li+].[OH-]','HLiO','LiOH','Source hydration and stock concentration are not stated. This reference does not assert an anhydrous reagent or a solvated cluster.')
new['sodium-acetate']=ionic('norberg2004-sodium-acetate','Sodium acetate · formal components','[Na+].CC(=O)[O-]','C2H3NaO2','CH₃COONa','Source hydration is not stated. The acetate control is separate from the manganese nitrate substitution.')
# Keep a 90%-grade source material distinct from the qualified pure TOPO reference.
id='norberg2004-topo-component';e=copy.deepcopy(reg['topo']);e['id']=id;e['name']='TOPO component of the technical-grade reagent';e['caption']='Pure TOPO reference component of the reported 90% technical reagent. Unidentified impurities and actual solution species are not reconstructed.';e['limitations']=[e['caption']];e['sourceUrls']=list(e['sourceUrls'])+['https://doi.org/10.1021/ja048427j'];e['provenance']['norbergSourceScope']={'reagent_grade_percent':90,'componentOnly':True,'sourceFactsSha256':sha(N/'source-facts.json')}
for key in ['svgPath','model2dPath','model3dPath']:
    old=S/'chemical-registry'/e[key];suffix='-2d.json'if key=='model2dPath'else'-3d.json'if key=='model3dPath'else'.svg';relative=('models/'if key!='svgPath'else'svg/')+id+suffix
    if key=='svgPath':(M/relative).write_bytes(old.read_bytes())
    else:
        model=read(old);model['id']=id;model['name']=e['name'];model['caption']=e['caption'];model['eligible_training']=False;dump(M/relative,model)
    e[key]=relative;e['assetHashes'][key]=sha(M/relative)
entries.append(e);new['topo']=id
# Reuse the previously audited NIST nitrogen geometry, with Norberg source scope.
id='norberg2004-nitrogen-reference';e=copy.deepcopy(reg['gu2004-nitrogen-reference']);e['id']=id;e['caption']='Ground-state dinitrogen reference with NIST internuclear distance 1.09768 Å and arbitrary orientation. Norberg explicitly reports nitrogen for thermal amine cleaning; unspecified anaerobic gas is not relabeled as nitrogen.';e['limitations']=['The reference constant is for 14N2; Norberg does not report isotope composition.','This is reference geometry, not measured gas or source-product coordinates.'];e['provenance']['norbergSourceFactsSha256']=sha(N/'source-facts.json')
for key in ['svgPath','model2dPath','model3dPath']:
    old=S/'chemical-registry'/e[key];suffix='-2d.json'if key=='model2dPath'else'-3d.json'if key=='model3dPath'else'.svg';relative=('models/'if key!='svgPath'else'svg/')+id+suffix
    if key=='svgPath':(M/relative).write_bytes(old.read_bytes())
    else:
        model=read(old);model['id']=id;model['caption']=e['caption'];model['notes']=e['limitations']+['Nitrogen is explicitly stated for Norberg thermal amine cleaning; anaerobic-control gas identity remains unspecified.'];model['sourceType']='Geometry derived from an external reference, not observed Norberg atomic coordinates';dump(M/relative,model)
        if key=='model3dPath':ck(abs(math.dist([model['atoms'][0][q]for q in ['x','y','z']],[model['atoms'][1][q]for q in ['x','y','z']])-1.09768)<1e-9,'NIST nitrogen reference distance')
    e[key]=relative;e['assetHashes'][key]=sha(M/relative)
G=N.parent/'ja0496423/visuals/molecules';(M/'raw').mkdir(exist_ok=True)
for name in ['nitrogen-nist-extracted-reference.json','nitrogen-nist-web-tool-excerpt.txt']:(M/'raw'/name).write_bytes((G/'raw'/name).read_bytes())
entries.append(e);new['nitrogen']=id
def identity(mid,name,formula,lines,mode='context',folder=M):
    id='norberg2004-'+mid;svg=card(id,name,formula,lines,mode);(folder/'svg'/f'{id}.svg').write_text(svg,encoding='utf-8');e={'id':id,'name':name,'formula':formula,'displayFormula':formula,'depictionKind':'sample-context'if folder==P else'material-context','svgPath':f'svg/{id}.svg','model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':' '.join(lines),'limitations':['No atomic coordinates, measured surface geometry, exact particle model or training structure label is supplied.'],'sourceUrls':['https://doi.org/10.1021/ja048427j'],'provenance':{'sourceFactsSha256':sha(N/'source-facts.json'),'measuredCoordinates':False,'eligible_training':False},'assetHashes':{'svgPath':sha(folder/'svg'/f'{id}.svg')}};return e
for mid,name,f,lines in [('air','Air',None,['Atmospheric reaction / annealing / control context.','Mixture composition, humidity and numerical pressure are unreported.']),('fused-silica','Fused-silica substrate','SiO₂',['Noncrystalline support composition; no discrete SiO₂ molecule.','Films A–C: 1 × 0.5 cm support; spin settings remain unknown.']),('quartz-disks','Quartz disks','SiO₂',['Support for frozen TOPO-capped colloids in MCD.','No quartz phase refinement, disk diameter or lattice coordinates supplied.'])]:
    e=identity(mid,name,f,lines,mode='disk'if mid=='quartz-disks'else'film'if mid!='air'else'context');entries.append(e);new[mid]=e['id']
titles={'acquisition-specimens-epr-x':'X-band EPR specimen context','acquisition-specimens-epr-q':'Q-band EPR colloid context','acquisition-specimens-epr-sim':'EPR simulation context','acquisition-specimens-abs':'Absorption specimen contexts','acquisition-specimens-mcd':'Frozen TOPO-capped MCD specimen','acquisition-specimens-lum':'Luminescence specimen context','acquisition-specimens-xrd-powder':'Powder XRD specimen context','acquisition-specimens-xrd-film':'Thin-film XRD specimen context','acquisition-specimens-tem':'HRTEM specimen context','acquisition-specimens-icp':'ICP-AES specimen context','acquisition-specimens-mag':'SQUID specimen contexts','dodecylamine-capped-colloids':'Preformed dodecylamine-capped colloids','cleaned-final-colloids':'Cleaned precursor colloids for films A–C','early-growth-bulk':'Early growth reaction bulk','remaining-growth-bulk':'Remaining growth reaction bulk','later-growth-product':'Later growth product','input-acquire-magnetism':'Magnetometry specimen contexts','input-zfc-series':'Films A and B: ZFC contexts','input-film-epr':'Film A / precursor EPR comparison','input-acquire-optics':'Optical specimen series','input-prepare-powder':'Analytical powder preparation','input-characterize-structure':'Structural characterization specimens','undoped-zno-control':'Pure-ZnO surface-control substrate','grown-colloids':'Nanocrystals for the TOPO alternative'}
scopes={'acquisition-specimens-epr-sim':['Hamiltonian model, not a physical chemical charge.','No measured atomic coordinates are represented.'],'acquisition-specimens-mcd':['TOPO-capped 1.1% Mn specimen on quartz; frozen at 5 K.','Do not equate this with the 0.20% Mn film precursor.'],'input-acquire-optics':['Distinct undoped, estimated 0.13% Mn and reported 1.3% Mn colloids.','Absorption normalization and emission scaling do not establish a shared batch.'],'input-film-epr':['Film A is compared with its precursor colloid.','The new g = 2.00 signal has a tentative radical/redox interpretation.'],'cleaned-final-colloids':['Dodecylamine-treated 0.20 ± 0.01% Mn precursor colloids.','The reported coating sequence applies only to films A–C.'],'early-growth-bulk':['Common-route reaction with 0.02% Mn feed.','Early sampled aliquot and continuing bulk are distinct.'],'remaining-growth-bulk':['Original reaction bulk after early sampling.','The analyzed early aliquot is not returned.'],'later-growth-product':['Later-growth product for separate cleaning.','No reuse of the analyzed later aliquot is inferred.'],'input-zfc-series':['Films A and B are separate source specimens.','No shared batch, atomistic structure or additional preparation is inferred.'],'undoped-zno-control':['Prepared by the common route without manganese feed.','Mn is added subsequently to create the surface-bound reference.'],'input-characterize-structure':['TEM / HRTEM and powder / film diffraction retain panel assignments.','6.1 ± 0.7 nm TEM distribution differs from film-A Scherrer domain size.'],'input-prepare-powder':['Rapid precipitation from the cleaned colloid.','Powder XRD and SQUID descriptions do not prove identical physical aliquots.'],'grown-colloids':['Preformed nanocrystals for technical-TOPO treatment.','Temperature, duration and initial feed are not supplied here.']}
products=[];productmap={};bindings={};bindingnotes={};coverage=[]
for r in records:
    bindings[r['record_id']]={};bindingnotes[r['record_id']]={}
    for i,m in enumerate(r['materials']):
        mid=m['id']
        if mid=='nitrogen':rid=new['nitrogen']
        elif mid in reuse:rid=reuse[mid][0]
        elif mid in new:rid=new[mid]
        else:
            ck(mid in titles,'Explicit readable specimen title: '+mid)
            rid='norberg2004-'+mid
            if rid not in productmap:
                lines=scopes.get(mid,['Technique-specific source specimen or specimen set.','Shared acquisition descriptions do not establish identical batches or physical aliquots.'])
                e=identity(mid,titles[mid],m['formula'],lines,mode='particles'if m['formula']=='Mn:ZnO'and 'film'not in mid else'context',folder=P);products.append(e);productmap[rid]=e
        bindings[r['record_id']][mid]=rid
        bindingnotes[r['record_id']][mid]={'binding_approved':False,'approval_status':'private author proposal; independent audit pending','canonical_pointer':f'/materials/{i}','source_evidence':m.get('evidence',[]),'viewOverrides':{'name':titles.get(mid,m['name']),'caption':'Source identity: '+m['name']+'. '+' '.join(m.get('notes',[])),'limitations':['Reference identity only; source quantities and specimen assignments remain in the canonical material record.']}}
        coverage.append({'record_id':r['record_id'],'material_id':mid,'pointer':f'/materials/{i}','registry_id':rid,'source_evidence':m.get('evidence',[]),'source_formula':m['formula'],'source_notes':m.get('notes',[])})
ck(len(coverage)==73,'All 73 material slots bound')
recordbindings={}
for r in records:
    if r['record_id']=='norberg-2004-hydrolysis':recordbindings[r['record_id']]='norberg2004-dodecylamine-capped-colloids'
    elif r['record_id']=='norberg-2004-films-a-c':
        e=identity('films-a-c-product','Nanocrystalline films A–C','Mn:ZnO',['Distinct A, B and C outcomes; 0.20 ± 0.01% Mn source composition.','A: 40 coats; B / C: 20 coats. No refined dopant coordinates.','Film A: about 20 nm Scherrer domain size; not particle diameter.'],mode='film',folder=P);products.append(e);recordbindings[r['record_id']]=e['id']
    elif r['record_id']=='norberg-2004-films-d-f':
        e=identity('films-d-f-product','Additional films D–F','Mn:ZnO',['Separate film outcomes with incomplete preparation assignment.','Table S4 and Figure S3b disagree on the D/F magnetization trend.','Do not exchange labels or copy A–C coating / annealing conditions.'],mode='film',folder=P);products.append(e);recordbindings[r['record_id']]=e['id']
    elif r['record_id']in ['norberg-2004-structure','norberg-2004-optical','norberg-2004-magnetism']:
        mid={'norberg-2004-structure':'input-characterize-structure','norberg-2004-optical':'input-acquire-optics','norberg-2004-magnetism':'input-acquire-magnetism'}[r['record_id']];recordbindings[r['record_id']]=bindings[r['record_id']][mid]
for suffix,title,lines in [('amine-cleaning','Surface-cleaned Mn:ZnO colloids',['Product of the dodecylamine thermal cleaning and ethanol workup.','Redispersed in toluene or another nonpolar solvent.','No measured dopant coordinates or ligand coverage model.']),('surface-control','Deliberately surface-bound Mn reference',['Mn is added to preformed pure ZnO, followed by ethanolic LiOH.','Washed, dodecylamine-capped and dispersed in toluene for EPR.','The 180 °C stripping treatment is not applied.']),('topo','TOPO-capped optical / MCD specimen',['1.1% Mn specimen used for absorption and variable-field MCD.','Thermal preparation follows cited reference 32; conditions not restated.','Distinct from dodecylamine-treated 0.20% Mn film precursors.']),('growth-series','Growth and cleaning specimen progression',['Early sampled aliquot, continued reaction bulk and later product are distinct.','0.02% Mn is the feed fraction, not a measured coordinate occupancy.','Sample d is the separately cleaned later-growth product.'])]:
    e=identity(suffix+'-product',title,'Mn:ZnO',lines,mode='particles',folder=P);products.append(e);recordbindings['norberg-2004-'+suffix]=e['id']
dump(M/'registry-additions.json',{'schemaVersion':'1.0.0','entries':entries,'assetPurpose':'Private Norberg source-scoped identity proposals; independent audit pending'})
dump(M/'bindings-additions.json',{'schemaVersion':'1.0.0','recordBindings':bindings,'bindingNotes':bindingnotes,'sourceRecordSha256':{r['record_id']:sha(N/'canonical-drafts'/f"{r['record_id']}.json")for r in records},'publicationApproved':False})
dump(M/'material-slot-coverage.json',{'slots':coverage,'count':len(coverage),'status':'author_complete_pending_independent_audit'})
dump(M/'reuse-qualification.json',{'sourceRegistry':str(S/'chemical-registry/registry.json'),'sourceRegistrySha256':sha(S/'chemical-registry/registry.json'),'entries':qualified,'checks':checks,'status':'author_qualified_pending_independent_audit','downloaded':False})
dump(P/'product-registry-additions.json',{'schemaVersion':'1.0.0','entries':products,'assetPurpose':'Source specimen-context diagrams, not atomistic reconstructions'})
dump(P/'product-reference-proposal.json',{'recordBindings':recordbindings,'scope':'Context/source-product cards only; independent audit and Site integration pending','publicationApproved':False})
# Reuse the exact independently sourced undoped bulk ZnO cell. Never add Mn coordinates.
creg=read(S/'crystal-references/registry.json');z=next(x for x in creg['entries']if x['id']=='zno-wurtzite');cif=S/'crystal-references'/z['cifPath'];cellpath=S/'crystal-references'/z['modelPath'];cell=read(cellpath)
ck(sha(cif)==z['cifSha256'],'Host reference CIF hash');ck(sha(cellpath)==z['modelSha256'],'Host reference model hash');ck(len(cell['atoms'])==4,'Host cell four expanded sites');ck(collections.Counter(a['element']for a in cell['atoms'])=={'Zn':2,'O':2},'Host cell 1:1 composition; no Mn');ck(cell['measured_sample_structure']is False and cell['training_eligible']is False,'Host reference exclusion flags');
vec=cell['cellVectors']
for a in cell['atoms']:
    xyz=[sum(a['fractional'][j]*vec[j][i]for j in range(3))for i in range(3)];ck(max(abs(xyz[i]-a[['x','y','z'][i]])for i in range(3))<1e-6,'Host fractional/Cartesian agreement '+a['site'])
(P/'downloads/norberg-undoped-zno-cod9004178.cif').write_bytes(cif.read_bytes())
(P/'reference-origin').mkdir(exist_ok=True);(P/'reference-origin/zno-wurtzite-original-metadata.json').write_bytes(cellpath.read_bytes())
host=copy.deepcopy(cell);host.update({'id':'norberg-undoped-zno-unit-cell','name':'Undoped ZnO external host reference','scope':'Independent COD9004178 Kihara–Donnay 1985 bulk ZnO host reference. No measured Norberg Mn:ZnO atomic coordinates, dopant positions or surface geometry.','caption':'External undoped wurtzite ZnO reference, not a measured Norberg colloid or film.','originalReferenceModel':{'path':'reference-origin/zno-wurtzite-original-metadata.json','sha256':sha(cellpath),'metadata_change_only':True}});dump(P/'models/norberg-undoped-zno-unit-cell.json',host)
atoms=[]
for i in range(4):
 for j in range(4):
  for k in range(3):
   for a in cell['atoms']:
    xyz=[a[['x','y','z'][t]]+sum([i,j,k][l]*vec[l][t]for l in range(3))for t in range(3)]
    atoms.append({'serial':len(atoms)+1,'element':a['element'],'x':xyz[0],'y':xyz[1],'z':xyz[2],'bonds':[],'bondOrder':[],'properties':{'reference_only':True,'measured_sample':False,'cell_translation':[i,j,k],'reference_site':a['site']}})
center=[sum(a[q]for a in atoms)/len(atoms)for q in ['x','y','z']]
for a in atoms:
 for i,q in enumerate(['x','y','z']):a[q]-=center[i]
for i,a in enumerate(atoms):
 for j,b in enumerate(atoms[:i]):
  distance=math.dist([a[q]for q in ['x','y','z']],[b[q]for q in ['x','y','z']])
  if a['element']!=b['element'] and 1.7<distance<2.2:a['bonds'].append(j);a['bondOrder'].append(1);b['bonds'].append(i);b['bondOrder'].append(1)
caption='Illustrative finite 4 × 4 × 3 cell crop of independent undoped bulk ZnO COD9004178. Chosen block geometry, not a Norberg nanocrystal or film. No Mn atoms, inferred vacancies, surface ligands or passivation are added. Zn–O links use a stated 1.7–2.2 Å visualization window, not a measured bond refinement.'
finite={'id':'norberg-undoped-zno-finite-reference','name':'Undoped ZnO finite reference block','formula':'ZnO','atoms':atoms,'periodic':False,'representation':'finite_illustrative_particle','measured_sample_structure':False,'training_eligible':False,'caption':caption,'source':{'reference_cif_sha256':sha(cif),'reference_model_sha256':sha(cellpath),'cell_replication':[4,4,3],'atom_counts':dict(collections.Counter(a['element']for a in atoms)),'geometry_source':'Exact translations of the retained COD host model; chosen finite crop, not a source sample'}}
dump(P/'models/norberg-undoped-zno-finite-reference.json',finite);(P/'downloads/norberg-undoped-zno-finite-reference.xyz').write_text(str(len(atoms))+'\n'+caption+'\n'+'\n'.join(f"{a['element']} {a['x']:.8f} {a['y']:.8f} {a['z']:.8f}"for a in atoms)+'\n',encoding='utf-8')
entry=copy.deepcopy(z);entry.update({'id':'norberg-undoped-zno-cod9004178-reference','name':'Undoped bulk ZnO · external host reference','record_ids':['norberg-2004-hydrolysis','norberg-2004-amine-cleaning','norberg-2004-films-a-c','norberg-2004-structure'],'description':'Independent bulk wurtzite ZnO comparison. No measured Norberg atomic coordinates.','scope':'Undoped Kihara–Donnay 1985 reference only, a=3.2494 Å and c=5.2038 Å. Neither the paper dopant fraction nor ligand surface geometry is represented. D–F outcomes and model-spin coordinates are not supplied by this reference.','cifPath':'downloads/norberg-undoped-zno-cod9004178.cif','modelPath':'models/norberg-undoped-zno-unit-cell.json','finiteModelPath':'models/norberg-undoped-zno-finite-reference.json','finiteModelSha256':sha(P/'models/norberg-undoped-zno-finite-reference.json'),'finiteCaption':caption,'finiteModelPeriodic':False,'measuredSampleStructure':False,'structureAssetRole':'external_reference','additionalDownloads':[{'label':'Illustrative undoped host block XYZ','path':'downloads/norberg-undoped-zno-finite-reference.xyz','sha256':sha(P/'downloads/norberg-undoped-zno-finite-reference.xyz')} ]})
entry['modelSha256']=sha(P/'models/norberg-undoped-zno-unit-cell.json')
dump(P/'crystal-reference-proposal.json',{'schema_version':'mattersyn-reference-registry/1','entries':[entry],'sourceReferenceRegistrySha256':sha(S/'crystal-references/registry.json'),'sourceReferenceModelSha256':sha(cellpath),'sourceReferenceCifSha256':sha(cif),'measuredNorbergStructureCount':0,'publicationApproved':False})
dump(P/'reference-author-checks.json',{'checks':checks,'counts':{'reused_molecular_references':len(qualified),'new_source_scoped_molecular_or_identity_entries':len(entries),'material_slots':len(coverage),'specimen_context_cards':len(products),'product_record_bindings':len(recordbindings),'unit_cell_atoms':len(cell['atoms']),'finite_atoms':len(atoms)},'status':'author_checks_passed_pending_visual_and_independent_audit','source_manifest_sha256':sha(N/'canonical-record-manifest.json'),'no_source_or_site_changes':True})
print(json.dumps({'checks':len(checks),'reuse':len(qualified),'entries':len(entries),'products':len(products),'bindings':len(coverage),'finite_atoms':len(atoms)}))
