"""Author private Nagasaki component assets; no shared/source/canonical writes."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
OUT=Path(__file__).resolve().parent; B=OUT.parent.parent
R=B.parents[3]; SITE=R.parent/'recipe-atlas'; REG=SITE/'dist/assets/chemical-registry'
sys.path.insert(0,str(R/'rdkit-runtime'));sys.path.insert(0,str(R/'corpus-20260917/runtime'))
import json,hashlib,copy,re,html,math,textwrap,datetime
from rdkit import Chem,rdBase
from rdkit.Chem import rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw,ImageFont
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def h(s):return html.escape(str(s),quote=True)
def tx(x,y,s,size=18,color='#193749',weight=400,anchor='start'):
    return f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{h(s)}</text>'
def lines(x,y,s,width=85,size=17,color='#536575',gap=24):
    return ''.join(tx(x,y+i*gap,line,size,color) for i,line in enumerate(textwrap.wrap(s,width=width)))
def box(x,y,w,hh,fill,stroke='#b9cbd3',r=13):return f'<rect x="{x}" y="{y}" width="{w}" height="{hh}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'
def frame(name,sub,body,footer,desc):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="470" viewBox="0 0 960 470"><title>{h(name)}</title><desc>{h(desc)}</desc><rect width="960" height="470" rx="20" fill="#fff"/>{box(1,1,958,468,"none","#d5e0e5",20)}{tx(28,41,name,23,"#193749",600)}{tx(28,73,sub,15,"#617784")}{body}<path d="M28 370H932" stroke="#e1e8ec"/>{lines(28,400,footer,width=104,size=16,gap=23)}</svg>'
for d in ['raw','models','svg','review','reference-base']: (OUT/d).mkdir(exist_ok=True)
plan=read(B/'visual-reuse-plan.json'); records={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
source=read(B/'source-facts.json'); inputs={str(B/'visual-reuse-plan.json'):sha(B/'visual-reuse-plan.json')}
for name in ['source-facts.json','source-inventory.json','source-scientific-audit.json','canonical-records-audit.json','canonical-record-manifest.json','public-review-proposal/nagasaki2004.json','reader-source-audit.json']:
    inputs[str(B/name)]=sha(B/name)
for rid,expected in plan['canonical_record_hashes'].items():
    p=B/'canonical-drafts'/f'{rid}.json';assert sha(p)==expected,rid;inputs[str(p)]=sha(p)
write(OUT/'input-hashes-before.json',inputs)
entries=[];reuse=[];author=[];byid={};model_files=[]
def eid(mid):return 'nagasaki2004-'+mid+'-reference'
scope={k:v['reference_scope'] for k,v in plan['identity_plans'].items()}
scope.update({
 'water':'Free water reference. Water grade and a unique aqueous arrangement are unreported; no hydrate count is assigned.',
 'thf':'Free THF reference. Initiator-reaction solvent and Soxhlet solvent are separate source contexts; no potassium solvation shell is assigned.',
 '2-propanol':'Free 2-propanol reference. The polymer is precipitated into excess solvent; its amount and purity are not reported.',
 'naoh':'Formal Na+ and OH− components. Polymer neutralization has no reported charge; the separate zeta-potential assay uses 7.5 mM pH-adjustment solution.',
 'nacl':'Formal Na+ and Cl− components. The 0.3 M salt challenge and the 7.5 mM zeta electrolyte remain distinct; the FRET electrolyte identity is unresolved.',
 'hcl':'Source-named HCl is an alternative zeta-assay pH adjuster. It is not identified as the reagent used earlier to protonate PAMA.',
 'acetic-acid':'Acetic acid reference. The hydrolysis medium is acetic acid/water 10:1 v/v, for 5 h at 35 °C; total volume, acid purity and solution speciation are unreported.',
 'cdcl2':'Formal Cd2+ and two Cl− components. The source names CdCl2 from Wako but does not report purity or hydration. Concentration basis and addition volume remain unresolved.',
 'na2s':'Formal Na2S stoichiometry only. The source does not specify hydration, and no hydrate water, solution speciation or crystal geometry is assigned.',
 'nabh4':'Formal sodium borohydride reference: Na+ and BH4−. The source uses it to reduce the stated Schiff base; amount and reduction conditions are unreported.',
 'eo':'Ethylene oxide is the cyclic monomer delivered through a cooled syringe. The free-molecule reference is not ethylene glycol or a PEG-chain structure.',
 'ama':'The reference monomer is interpreted as 2-(N,N-dimethylamino)ethyl methacrylate from the source-named PAMA chemistry. It does not specify polymer tacticity or a fixed protonation state.',
 'pdp-alcohol':'The source says “corresponding alcohol.” The depicted 3,3-diethoxypropan-1-ol reference is an explicit interpretation from the named PDP alkoxide.',
 'potassium-naphthalene':'The literal source name is retained. Exact formula, charge/radical representation and metal–arene geometry are unresolved; no neutral naphthalene substitute is used.',
 'pdp':'Name-based formal potassium 3,3-diethoxypropanolate components. The alkoxide reference has disconnected K+; no solvated aggregate or metal–oxygen geometry is asserted.',
 'biocytin-hydrazide':'Biocytin hydrazide is the Pierce reagent named by the source. The reference includes the lysine hydrazide linker and reference stereochemistry; source isomer assay and polymer conjugation density are unreported.',
 'acetal-peg-pama':'Acetal-ended block topology is schematic. PEG/PAMA segment numbers 4200/15800 and Mw/Mn 1.35 do not establish one chain length, formula, tacticity or conformation.',
 'cho-peg-pama':'Aldehyde-ended block-polymer identity, distinct from acetal and biotin end groups. Chain length, surface coverage and conformation are not assigned.',
 'biotin-peg-pama':'Biotin-functional PEG/PAMA identity. Biotin loading and exact attachment microstructure are unreported; the acetal functionality estimate is not a biotin-conjugation yield.',
 'cho-polymer-before-dialysis':'Neutralized CHO-polymer intermediate before dialysis. Biotinylation occurs at this stage, before dialysis and CdS formation.',
 'peg-prepolymer':'PEG prepolymer is the removed impurity fraction. It is not an added reagent or the separately named PEG-OH Mn 5000 control.',
 'purified-acetal-nmr-specimen':'Purified acetal-polymer NMR context. Almost-quantitative end-acetal functionality is reported, but the spectrum, integration and exact chain sequence are not supplied.',
 'peg-oh':'PEG-OH homopolymer control, Mn 5000 as printed with units not explicitly supplied. It is distinct from the PEG segment of the block copolymer.',
 'pama-homopolymer':'PAMA homopolymer control, Mn 5000. It is distinct from the block-polymer segment number 15800; no fixed repeat count or protonation state is assigned.',
 'polymer-only-xrd':'Generic PEG/PAMA without CdS, separately freeze-dried for XRD. End group and exact batch are unresolved; no separate polymer-only trace is identified.',
 'texasred-streptavidin':'TexasRed-labeled streptavidin identity. Dye loading, conjugation site and protein conformation are unreported. The source-axis shorthand Tex-Avidin/Tex-Av is retained in original figures, not substituted as a different protein.',
 'streptavidin':'Unlabeled streptavidin competition control, distinct from the TexasRed conjugate and from avidin. No protein coordinates are supplied.',
 'bsa':'Unlabeled BSA nonspecific control. The slight intensity enhancement and proposed excluded-volume explanation remain source observations and interpretation, not structural parameters.',
 'cds':'Source-reported CdS product composition. Exact full-particle coordinates and polymer surface coverage are unreported; formula molarity is not particle-number molarity.',
 'biotin-cds-specimen':'Preformed biotin-PEG/PAMA–CdS donor dispersion for recognition assays. The generic SI TEM/XRD specimens are not verified as this biotin specimen.',
 'uv-specimen':'Figure 2d absorption context. Exact a/b/c concentration membership is unresolved; the 4.8 nm optical estimate is author-derived rather than a TEM diameter or atomic model.',
 'fluorescence-specimen-contexts':'Separate fluorescence specimen contexts. Shared acquisition settings do not establish one physical aliquot or a combined mixture.',
 'salt-no-polymer-specimen':'CdS without polymer precipitates in the comparison. This is failed stabilization, not a stable coated dispersion.',
 'salt-peg-specimen':'PEG-OH/CdS comparison with failed stabilization. The homopolymer control is distinct from PEG/PAMA block-polymer specimens.',
 'salt-pama-specimen':'PAMA/CdS control is clear pale yellow at lower salt and precipitates at higher salt. Its weak emission remains distinct from the CHO block-polymer comparison.',
 'salt-cho-specimen':'CHO-PEG/PAMA–CdS salt-comparison context. Stability for several days in 0.3 M NaCl is not an exact lifetime or a universal sample guarantee.',
 'si-tem-dispersion':'Generic SI PEG/PAMA–CdS TEM specimen. End group and batch are unresolved; no exact join to biotin, CHO or FRET specimens is established.',
 'si-xrd-cds-dispersion':'Generic SI polymer–CdS XRD preparation, separately freeze-dried. Wurtzite is the author assignment; lattice parameters and atomic coordinates are not supplied.',
 'zeta-dispersion':'Figure 3 zeta-potential dispersion; exact Figure 2 membership is unresolved. pH 2–11 and region-level potential values are measurement context, not synthesis conditions.',
 'tem-grid':'The source calls the support a “formval film-coated Cu grid.” Mesh, film chemistry and carbon coating are unreported.',
 'glass-slide':'Generic glass slides support the separately freeze-dried XRD specimens. Glass composition, brand and cleaning procedure are not specified.',
 'protonating-agent-unspecified':'PAMA protonation is explicit, but reagent identity is not reported. No acid, chemical formula or geometry is assigned.'
})
names={
 'water':'Water','thf':'Tetrahydrofuran (THF)','2-propanol':'2-Propanol','naoh':'Sodium hydroxide','nacl':'Sodium chloride','hcl':'Hydrochloric acid','acetic-acid':'Acetic acid','cdcl2':'Cadmium chloride','na2s':'Sodium sulfide','nabh4':'Sodium borohydride','eo':'Ethylene oxide (EO)','ama':'AMA monomer: dimethylaminoethyl methacrylate','pdp-alcohol':'Corresponding alcohol for PDP','potassium-naphthalene':'Potassium naphthalene','pdp':'Potassium 3,3-diethoxypropanolate (PDP)','biocytin-hydrazide':'Biocytin hydrazide',
 'acetal-peg-pama':'Acetal-ended PEG/PAMA','cho-peg-pama':'Aldehyde-ended PEG/PAMA','biotin-peg-pama':'Biotin-functional PEG/PAMA','cho-polymer-before-dialysis':'CHO-polymer intermediate before dialysis','peg-prepolymer':'Removed PEG prepolymer','purified-acetal-nmr-specimen':'Purified acetal-polymer: NMR context','peg-oh':'PEG-OH homopolymer control','pama-homopolymer':'PAMA homopolymer control','polymer-only-xrd':'Polymer-only XRD preparation',
 'texasred-streptavidin':'TexasRed-labeled streptavidin','streptavidin':'Unlabeled streptavidin','bsa':'Bovine serum albumin (BSA)',
 'cds':'CdS: product composition context','biotin-cds-specimen':'Biotin-PEG/PAMA–CdS donor','uv-specimen':'Absorption specimen: Figure 2d','fluorescence-specimen-contexts':'Fluorescence acquisition contexts','salt-no-polymer-specimen':'CdS without polymer: comparison','salt-peg-specimen':'PEG-OH/CdS: comparison','salt-pama-specimen':'PAMA/CdS: comparison','salt-cho-specimen':'CHO-PEG/PAMA–CdS: salt comparison','si-tem-dispersion':'PEG/PAMA–CdS: SI TEM specimen','si-xrd-cds-dispersion':'PEG/PAMA–CdS: SI XRD specimen','zeta-dispersion':'CdS dispersion: zeta-potential context',
 'tem-grid':'Film-coated copper TEM grid','glass-slide':'Glass slide: XRD support','protonating-agent-unspecified':'Unreported protonating reagent'
}
def baseentry(mid,formula,kind,caption,urls=None):
    return dict(id=eid(mid),name=names[mid],formula=formula,displayFormula=formula,aliases=[mid],depictionKind=kind,svgPath=f'svg/{eid(mid)}.svg',model2dPath=None,model3dPath=None,functionalGroups=[],caption=caption,limitations=[scope[mid]],sourceUrls=urls or ['https://doi.org/10.1021/la036034c'],provenance={'sourceId':'nagasaki2004','sourceSpecificIdentity':mid,'measuredCoordinates':False},independentScientificAudit='pending',published=False,eligible_training=False,binding_approved=False)
def finish(e,svg):
    (OUT/e['svgPath']).write_text(svg,encoding='utf-8');e['assetHashes']={k:sha(OUT/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}
    doc=pymupdf.open(stream=svg.encode(),filetype='svg');pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25),alpha=False)
    pix.save(str(OUT/'review'/f'{e["id"]}.png'));doc.close()
    entries.append(e);byid[e['provenance']['sourceSpecificIdentity']]=e
def mol_from_model(m):
    rw=Chem.RWMol()
    for a in m['atoms']:
        atom=Chem.Atom(a.get('element',a.get('elem')));atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0));atom.SetNoImplicit(True);atom.SetNumExplicitHs(a.get('implicitHydrogenCount',0));rw.AddAtom(atom)
    for b in m['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
    mol=rw.GetMol();Chem.SanitizeMol(mol);conf=Chem.Conformer(len(m['atoms']));conf.Set3D(False)
    for i,a in enumerate(m['atoms']):conf.SetAtomPosition(i,(a['x'],a['y'],0))
    mol.AddConformer(conf);return mol
group_specs={
 'acetic-acid':[('Carboxylic acid','[CX3](=O)[OX2H1]')], '2-propanol':[('Alcohol','[OX2H1]')], 'thf':[('Ether','[OD2]')],
 'eo':[('Epoxide ring','[O;r3]1[C;r3][C;r3]1')],
 'ama':[('Methacrylate ester','[CX3](=O)[OX2]'),('Tertiary amine','[NX3;H0]([C])([C])[C]'),('Polymerizable alkene','C=C')],
 'pdp-alcohol':[('Acetal','[CH]([OX2])[OX2]'),('Alcohol','[OX2H1]')],
 'pdp':[('Acetal','[CH]([OX2])[OX2]'),('Alkoxide','[O-]')],
 'biocytin-hydrazide':[('Hydrazide','[CX3](=O)[NX3][NX3]'),('Primary amine','[NX3;H2][CX4]'),('Ureido group','[NX3][CX3](=O)[NX3]')]
}
def groups(mol,mid):
    result=[]
    for label,smarts in group_specs.get(mid,[]):
        query=Chem.MolFromSmarts(smarts)
        for match in mol.GetSubstructMatches(query):
            aa=list(match);bb=[b.GetIdx() for b in mol.GetBonds() if b.GetBeginAtomIdx() in aa and b.GetEndAtomIdx() in aa]
            result.append({'label':label,'atomIndices':aa,'bondIndices':bb})
    return result
def model(mol,mid,dim,cid,caption,provenance):
    c=mol.GetConformer(); atoms=[]
    for a in mol.GetAtoms():
        p=c.GetAtomPosition(a.GetIdx());atoms.append(dict(index=a.GetIdx(),element=a.GetSymbol(),x=p.x,y=p.y,z=p.z if dim==3 else 0,formalCharge=a.GetFormalCharge(),isotope=a.GetIsotope(),implicitHydrogenCount=a.GetTotalNumHs(),chiralTag=str(a.GetChiralTag()),radicalElectrons=a.GetNumRadicalElectrons()))
    return dict(id=eid(mid),name=names[mid],formula=rdMolDescriptors.CalcMolFormula(mol),pubchemCid=cid,representation=f'{dim}d',has3D=dim==3,allowRotation=dim==3,coordinateUnits='angstrom' if dim==3 else 'drawing units',indexConvention='zero-based',atoms=atoms,bonds=[dict(a=b.GetBeginAtomIdx(),b=b.GetEndAtomIdx(),order=b.GetBondTypeAsDouble(),stereo=str(b.GetStereo()),stereoAtoms=list(b.GetStereoAtoms())) for b in mol.GetBonds()],functionalGroups=groups(mol,mid),connectivitySmiles=Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=True),caption=caption,notes=[scope[mid]],modelType='Reference conformer' if dim==3 else 'Two-dimensional connectivity reference',coordinateSource=provenance,measuredCoordinates=False,eligible_training=False)
def molecular_svg(mid,mol,gg,formula,sub,footer):
    d=rdMolDraw2D.MolDraw2DSVG(900,245);o=d.drawOptions();o.clearBackground=False;o.fixedFontSize=22;o.padding=.08;o.bondLineWidth=2;o.updateAtomPalette({16:(.55,.40,.05)})
    palette=[(.91,.65,.28),(.49,.70,.75),(.70,.56,.80),(.85,.57,.62)]
    ac={};bc={}
    for j,g in enumerate(gg):
        for a in g['atomIndices']:ac[a]=palette[j%4]
        for b in g['bondIndices']:bc[b]=palette[j%4]
    d.DrawMolecule(mol,highlightAtoms=list(ac),highlightBonds=list(bc),highlightAtomColors=ac,highlightBondColors=bc);d.FinishDrawing()
    inner=d.GetDrawingText();inner=re.sub(r'^.*?<svg[^>]*>','',inner,flags=re.S);inner=inner.rsplit('</svg>',1)[0]
    inner='<g transform="translate(30,91)">'+inner+'</g>'
    legend='';xx=33
    for j,g in enumerate(gg):
        if g['label'] in [z['label'] for z in gg[:j]]:continue
        color='#%02x%02x%02x'%tuple(round(v*255) for v in palette[j%4]);legend+=box(xx,342,10,10,color,color,2)+tx(xx+16,352,g['label'],13)
        xx+=len(g['label'])*7+45
    return frame(names[mid],f'{formula}  ·  {sub}',inner+legend,footer,scope[mid])
# Snapshot exact candidate entries/assets; private new copies never change the registry.
for oldid,snap in plan['candidate_entry_snapshots'].items():
    old=snap['entry'];write(OUT/'reference-base'/f'{oldid}-entry.json',old)
    row={'candidate_id':oldid,'asset_checks':[]}
    for field,digest in old.get('assetHashes',{}).items():
        p=REG/old[field];assert sha(p)==digest,(oldid,field);dest=OUT/'reference-base'/Path(old[field]).name;dest.write_bytes(p.read_bytes());row['asset_checks'].append({'path':str(p),'sha256':digest,'snapshot':str(dest)})
    reuse.append(row)
write(OUT/'candidate-reuse-inputs.json',reuse)
reuseids={'water':'water','thf':'thf','2-propanol':'2-propanol','naoh':'sodium-hydroxide','nacl':'sodium-chloride','acetic-acid':'acetic-acid','cdcl2':'gu2004-cadmium-chloride-reference'}
for mid,oldid in reuseids.items():
    old=plan['candidate_entry_snapshots'][oldid]['entry'];m=read(REG/old['model2dPath']);mol=mol_from_model(m)
    cap='Free-compound connectivity reference. No source-specific grade or aqueous coordination is assigned.' if old.get('model3dPath') else 'Formal stoichiometric components in an arbitrary 2D layout; no salt lattice, ion pair or solution speciation is assigned.'
    e=baseentry(mid,old['formula'],'molecule' if old.get('model3dPath') else 'ionic_components',cap,old.get('sourceUrls'))
    if mid in ['acetic-acid','naoh','nacl','cdcl2']:
        e['sourceUrls']=['https://doi.org/10.1021/la036034c']+({'acetic-acid':['https://pubchem.ncbi.nlm.nih.gov/compound/176'],'cdcl2':['https://pubchem.ncbi.nlm.nih.gov/compound/24947']}.get(mid,[]))
    kept_origin={k:v for k,v in old.get('provenance',{}).items() if k in ['connectivitySource','primaryApiPropertiesUrl','primaryApi2dUrl','sourcePropertiesSha256','source2dSha256','reused3dAsset','smiles','depictionSoftware','computed3d']}
    e['provenance'].update(reusedRegistryId=oldid,originalEntrySnapshot=f'reference-base/{oldid}-entry.json',geometryPolicy='Existing graph and coordinates copied without modification; displayed metadata and SVG newly authored for this source. Original source-specific metadata is archived separately.',referenceGeometryOrigin=kept_origin)
    m=copy.deepcopy(m);m.update(id=eid(mid),name=names[mid],caption=cap,notes=[scope[mid]],functionalGroups=groups(mol,mid),measuredCoordinates=False,eligible_training=False)
    e['model2dPath']=f'models/{eid(mid)}-2d.json';write(OUT/e['model2dPath'],m);e['functionalGroups']=m['functionalGroups']
    if old.get('model3dPath'):
        m3=read(REG/old['model3dPath']);m3=copy.deepcopy(m3)
        # Retain all computational/reference coordinate provenance. Only source prose/identity and group selection change.
        cap3=('Existing locally computed illustrative free-molecule conformer; not measured in this paper.' if m3.get('coordinateSource')=='local-rdkit' or 'computed' in str(m3.get('modelType','')).lower() else 'Existing reference free-molecule conformer; not measured in this paper.')
        mm3=mol_from_model(m3);m3.update(id=eid(mid),name=names[mid],caption=cap3,notes=[scope[mid]],functionalGroups=groups(mm3,mid),measuredCoordinates=False,eligible_training=False)
        e['model3dPath']=f'models/{eid(mid)}-3d.json';write(OUT/e['model3dPath'],m3)
    footer=scope[mid]
    if mid=='cdcl2':footer='Source: CdCl2 (Wako). Purity and hydration are unreported. Formal ions only; no solution or lattice geometry.'
    finish(e,molecular_svg(mid,mol,e['functionalGroups'],old['formula'],'reference connectivity',footer))
# Fresh authoritative connectivity records; salt positions are not a 3D geometry.
fresh={'na2s':('sodium-sulfide',14804),'nabh4':('sodium-borohydride',4311764),'eo':('ethylene-oxide',6354),'ama':('ama',17869),'pdp-alcohol':('pdp-alcohol',140135),'biocytin-hydrazide':('biocytin-hydrazide',128197)}
for mid,(stem,cid) in fresh.items():
    props=read(OUT/'raw'/f'{stem}-properties.json')['PropertyTable']['Properties'][0]
    mol=Chem.MolFromMolFile(str(OUT/'raw'/f'{stem}-2d.sdf'),removeHs=False);assert mol is not None
    expected=Chem.MolFromSmiles(props['SMILES']);assert Chem.MolToSmiles(Chem.RemoveHs(mol),True)==Chem.MolToSmiles(expected,True),(mid,'graph mismatch')
    calculated_formula=rdMolDescriptors.CalcMolFormula(mol)
    def counts(f):return {a:int(n or 1) for a,n in re.findall(r'([A-Z][a-z]?)(\d*)',f)}
    assert counts(calculated_formula)==counts(props['MolecularFormula']),(mid,calculated_formula)
    formula=props['MolecularFormula']
    if mid not in ['na2s','nabh4']:
        mol=Chem.RemoveHs(mol);rdDepictor.Compute2DCoords(mol)
    cap='PubChem connectivity reference; no measured geometry or solution speciation is supplied by Nagasaki et al.'
    if mid=='ama':cap='Reference identity interpreted from the source-named PAMA monomer: 2-(dimethylamino)ethyl methacrylate. No polymer tacticity is assigned.'
    if mid=='pdp-alcohol':cap='Reference interpretation of the source phrase “corresponding alcohol”: 3,3-diethoxypropan-1-ol. This identification is inferred from the named PDP alkoxide.'
    if mid=='biocytin-hydrazide':cap='Biocytin hydrazide free-compound reference, including its lysine linker and reference stereochemistry. This is not a polymer-conjugate structure or a source isomer assay.'
    e=baseentry(mid,formula,'ionic_components' if mid in ['na2s','nabh4'] else 'molecule',cap,[f'https://pubchem.ncbi.nlm.nih.gov/compound/{cid}'])
    e['pubchemCid']=cid;e['provenance'].update(connectivitySource='PubChem PUG REST',propertiesPath=f'raw/{stem}-properties.json',propertiesSha256=sha(OUT/'raw'/f'{stem}-properties.json'),source2dPath=f'raw/{stem}-2d.sdf',source2dSha256=sha(OUT/'raw'/f'{stem}-2d.sdf'),referenceSmiles=props['SMILES'],referenceInChI=props['InChI'],formulaBasis='Reference identity only, not an assay of the source reagent',depictionSoftware=f'RDKit {rdBase.rdkitVersion}')
    if mid=='biocytin-hydrazide':e['sourceUrls'].append('https://documents.thermofisher.com/TFS-Assets/LSG/manuals/MAN0016370_2160451_EZ_Link_Hydrazide_Biocytin_UG.pdf')
    coordinate_basis='PubChem SDF 2D drawing coordinates' if mid in ['na2s','nabh4'] else 'RDKit 2D layout from verified PubChem connectivity; ordinary H labels suppressed while stereochemistry is preserved'
    m=model(mol,mid,2,cid,cap,coordinate_basis);e['functionalGroups']=m['functionalGroups'];e['model2dPath']=f'models/{eid(mid)}-2d.json';write(OUT/e['model2dPath'],m)
    p3=OUT/'raw'/f'{stem}-3d.sdf'
    if p3.exists() and mid not in ['na2s','nabh4']:
        mm=Chem.MolFromMolFile(str(p3),removeHs=False);assert mm is not None
        assert Chem.MolToSmiles(Chem.RemoveHs(mm),True)==Chem.MolToSmiles(expected,True),(mid,'3D graph mismatch')
        m3=model(mm,mid,3,cid,'PubChem reference free-compound conformer. Not measured by Nagasaki et al.; not a polymer, solution complex or conjugate geometry.','PubChem SDF 3D reference');m3['source3dSha256']=sha(p3);m3['source3dUrl']=f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d'
        e['model3dPath']=f'models/{eid(mid)}-3d.json';write(OUT/e['model3dPath'],m3)
    footer={'na2s':'Na2S formula reference only. The source does not specify hydration; no hydrate water or aqueous sulfide speciation is assigned.','nabh4':'Formal Na+ and BH4− components. Four hydrogens belong to borohydride; there is no Na–B bond or 3D ion-pair model.','biocytin-hydrazide':'Reference stereochemistry and lysine hydrazide linker; no source isomer assay, conjugation density or polymer conformation.'}.get(mid,cap)
    finish(e,molecular_svg(mid,mol,e['functionalGroups'],formula,'reference connectivity',footer))
# PDP is a transparent name-based alkoxide interpretation, not an external exact-salt record.
mid='pdp';mol=Chem.MolFromSmiles('CCOC(CC[O-])OCC.[K+]');rdDepictor.Compute2DCoords(mol)
cap='Name-based formal alkoxide interpretation of potassium 3,3-diethoxypropanolate. The alcohol connectivity is independently referenced; K+ is a disconnected stoichiometric component.'
e=baseentry(mid,'C7H15KO3','ionic_components',cap,['https://doi.org/10.1021/la036034c','https://pubchem.ncbi.nlm.nih.gov/compound/140135'])
e['provenance'].update(connectivitySource='Author interpretation from the explicitly named alkoxide and PubChem CID 140135 alcohol reference',identityStatus='source_name_based_formal_components_pending_independent_audit',referenceSmiles=Chem.MolToSmiles(mol),derivation='Remove the terminal alcohol H from 3,3-diethoxypropan-1-ol, assign O− and add disconnected K+. No metal–oxygen bond, solvate or aggregate is inferred.')
m=model(mol,mid,2,None,cap,'RDKit 2D layout of name-derived formal components');e['functionalGroups']=m['functionalGroups'];e['model2dPath']=f'models/{eid(mid)}-2d.json';write(OUT/e['model2dPath'],m)
finish(e,molecular_svg(mid,mol,e['functionalGroups'],e['formula'],'name-based formal components','K+ and alkoxide positions are arbitrary. THF remains a separate solvent; no solvated aggregate or K–O geometry.'))
def polymer(mid):
    label={'acetal-peg-pama':'Acetal','cho-peg-pama':'CHO','biotin-peg-pama':'Biotin','cho-polymer-before-dialysis':'CHO','purified-acetal-nmr-specimen':'Acetal','peg-oh':'OH'}.get(mid,'End group unresolved')
    haspama=mid not in ['peg-prepolymer','peg-oh'];haspeg=mid!='pama-homopolymer'
    parts=[]
    if haspeg:parts.append(('PEG','#d9eef1','#477e87'))
    if haspama:parts.append(('PAMA','#eee0f4','#825e98'))
    lab=tx(138,156,'End group',17,'#684d28',600,'middle')+tx(138,180,'unresolved',17,'#684d28',600,'middle') if label=='End group unresolved' else tx(138,167,label,18,'#684d28',600,'middle')
    body=box(60,125,155,73,'#f5ead4','#c59b52')+lab
    xx=252
    for j,(name,fill,col) in enumerate(parts):
        body+=f'<path d="M{xx-37} 162H{xx}" stroke="#7e929d" stroke-width="3"/>'+box(xx,121,260,82,fill,col)+tx(xx+130,170,name,25,col,600,'middle');xx+=295
    desc={'peg-prepolymer':'Removed during THF Soxhlet extraction; not an added reagent.','peg-oh':'Homopolymer control: Mn 5000 as printed; units not explicitly supplied.','pama-homopolymer':'Homopolymer control: Mn 5000; distinct from the block-polymer PAMA segment.','cho-polymer-before-dialysis':'Neutralized intermediate; biotinylation is performed before dialysis.','polymer-only-xrd':'Separately freeze-dried preparation; no distinct polymer-only trace is identified.','purified-acetal-nmr-specimen':'Almost-quantitative end-acetal functionality is the reported NMR interpretation.','biotin-peg-pama':'End functionalization schematic; biotin loading and exact attachment microstructure are unreported.'}.get(mid,'Source segment numbers: PEG 4200; PAMA 15800; Mw/Mn 1.35. Molecular-weight units are not explicitly supplied.')
    body+=lines(61,255,desc,width=89,size=18)+tx(61,328,'Block lengths are symbolic; no fixed repeat count, tacticity or chain conformation.',16,'#637482')
    return body
def specimen(mid):
    status={'salt-no-polymer-specimen':'Precipitating comparison','salt-peg-specimen':'PEG-OH control; failed stabilization','salt-pama-specimen':'PAMA control; salt-dependent stability','salt-cho-specimen':'CHO block-polymer comparison','biotin-cds-specimen':'Biotin block-polymer donor','si-tem-dispersion':'Generic SI dispersion; end group unresolved','si-xrd-cds-dispersion':'Generic SI XRD preparation; end group unresolved','uv-specimen':'Figure 2d; exact concentration member unresolved','zeta-dispersion':'Figure 3; exact Figure 2 member unresolved','fluorescence-specimen-contexts':'Several specimen contexts; not one mixed aliquot'}.get(mid,'Composition reference; exact specimen lineage is record-dependent')
    body='<circle cx="193" cy="212" r="78" fill="#f6e9ad" stroke="#baa05d" stroke-width="2"/>'+tx(193,223,'CdS',31,'#655322',600,'middle')
    body+=box(330,131,560,120,'#f6f9fb')+lines(355,173,status,width=46,size=20,gap=29)
    body+=tx(330,301,'Composition / sample-context diagram',18,'#546d7b',600)+tx(330,329,'No atomic lattice, particle size or coating thickness to scale.',16,'#637482')
    return body
remaining=[mid for mid in plan['identity_plans'] if mid not in byid]
for mid in remaining:
    category=plan['identity_plans'][mid]['category'];formula='CdS' if category=='cds_specimen_identity_needed' else None
    cap=scope[mid];kind='support' if category in ['support_depiction_needed','support_template_candidate'] else 'formula' if mid in ['hcl','potassium-naphthalene','protonating-agent-unspecified'] else 'specimen';sub='Symbolic source identity · no atomistic coordinates';footer=scope[mid]
    if category=='polymer_identity_schematic_needed':body=polymer(mid);footer='Polymer topology and end-group labels are symbolic. No exact whole-chain formula, conformation or surface attachment geometry is supplied.'
    elif category=='cds_specimen_identity_needed':body=specimen(mid);footer='Source-specific specimen context. Original optical, TEM and XRD evidence remains separate; no atomic coordinates or CIF are recovered.'
    elif category=='protein_or_conjugate_identity_needed':
        protein='BSA' if mid=='bsa' else 'Streptavidin'
        body=box(88,134,385,159,'#e2eef6','#82a6bf',25)+tx(280,225,protein,29,'#3e6683',600,'middle')
        if mid=='texasred-streptavidin':body+=f'<path d="M473 210H555" stroke="#af7481" stroke-width="3" stroke-dasharray="6 6"/>'+box(555,164,278,92,'#f8dce4','#c68498',20)+tx(694,218,'TexasRed label',24,'#9a4865',600,'middle')
        else:body+=tx(525,217,'Unlabeled control',24,'#526976',500)
        body+=tx(89,332,'Symbolic identity; protein fold, binding-site geometry and dye loading are not assigned.',16,'#637482')
        footer='No PDB structure, protein conformation or conjugate coordinates are supplied. Diagram shapes do not represent molecular envelopes.'
    elif mid=='tem-grid':
        body='<ellipse cx="235" cy="212" rx="147" ry="106" fill="#efd5b8" stroke="#ad8055" stroke-width="4"/><ellipse cx="235" cy="212" rx="118" ry="84" fill="#e5eef5" fill-opacity=".85" stroke="#9fb5c5"/>'+tx(235,221,'Cu support',22,'#665343',600,'middle')+lines(450,169,'“formval film-coated Cu grid”',width=34,size=22)+lines(450,234,'Source spelling retained. Mesh, film chemistry and carbon coating are unreported.',width=41,size=18)
        footer='Schematic coated support. No 300-mesh specification, carbon layer or corrected film-polymer identity is imported.'
    elif mid=='glass-slide':
        body='<path d="M142 273L282 137L764 153L624 289Z" fill="#e4f1f3" stroke="#7ca1aa" stroke-width="3"/><path d="M142 273V287L624 305L764 170V153M624 289V305" fill="none" stroke="#7ca1aa" stroke-width="2"/>'+tx(458,217,'Glass support',25,'#527d86',600,'middle')
        footer='Generic glass slide for freeze-dried XRD specimens. Composition, brand and cleaning procedure are not specified.'
    elif mid=='hcl':
        formula='HCl';kind='formula';sub='Source-named acid identity · aqueous pH-adjustment context';body=tx(215,231,'HCl',66,'#567b8f',600,'middle')+lines(410,173,'Alternative pH adjuster in the zeta-potential measurement.',width=40,size=23)+lines(410,258,'This is not the unspecified polymer-protonation reagent.',width=43,size=18);footer='Formula identity only. No discrete aqueous HCl molecule, ion pair or acid solution concentration is inferred.'
    elif mid=='potassium-naphthalene':
        sub='Source-name reference · electronic state unresolved';body=box(81,127,797,166,'#f4f7f9')+tx(480,189,'Potassium naphthalene',29,'#4d697b',600,'middle')+tx(480,242,'Source-named reagent in PDP preparation',20,'#627888',400,'middle');footer='The paper does not specify a formula, electronic-state model or metal–arene structure. A neutral naphthalene model is not substituted.'
    else:
        sub='Explicit missing reagent identity';body=box(107,133,746,150,'#faf1df','#d5bd85')+tx(480,196,'Protonating reagent: not reported',28,'#876c31',600,'middle')+tx(480,245,'PAMA protonation is stated; the acid identity is not.',20,'#876c31',400,'middle');footer='No chemical formula or molecular structure can be assigned. In particular, HCl from the zeta-potential assay is not borrowed.'
    e=baseentry(mid,formula,kind,cap);e['provenance'].update(identitySource='Audited Nagasaki source/canonical inventory',coordinatePolicy='No atomistic model. Source-scoped symbolic diagram only.',sourceUnitContext=[{'record_id':s['record_id'],'material_pointer':s['material_pointer']} for s in plan['material_slots'] if s['material_id']==mid])
    if mid=='potassium-naphthalene':e['provenance']['connectivityStatus']='unresolved; source-name card intentionally used'
    finish(e,frame(names[mid],sub,body,footer,cap))
assert len(entries)==42 and set(byid)==set(plan['identity_plans'])
# Exact bindings for all material slots; no wildcard formula fallback.
bindings={'schemaVersion':'1.0.0','status':'private_proposal_pending_independent_audit','recordBindings':{rid:{} for rid in records},'bindingNotes':{rid:{} for rid in records}}
slots=[]
def ptr(obj,p):
    for bit in p.strip('/').split('/'):obj=obj[int(bit)] if isinstance(obj,list) else obj[bit.replace('~1','/').replace('~0','~')]
    return obj
for s in plan['material_slots']:
    rid,mid=s['record_id'],s['material_id'];material=ptr(records[rid],s['material_pointer']);assert material['id']==mid
    e=byid[mid];bindings['recordBindings'][rid][mid]=e['id']
    source_caption=scope[mid]
    note=dict(registry_id=e['id'],source_material_id=mid,source_name=material['name'],source_formula=material.get('formula'),source_role=material.get('role'),source_stage=material.get('stage'),canonical_record_sha256=sha(B/'canonical-drafts'/f'{rid}.json'),canonical_material_pointer=s['material_pointer'],canonical_evidence=material.get('evidence',[]),source_notes=material.get('notes',[]),display_scope=source_caption,viewOverrides={'name':material['name'],'caption':source_caption,'limitations':[source_caption]},binding_approved=False,independent_scientific_audit='pending')
    bindings['bindingNotes'][rid][mid]=note;slots.append({'record_id':rid,'material_id':mid,'registry_id':e['id'],'canonical_material_pointer':s['material_pointer'],'canonical_record_sha256':note['canonical_record_sha256'],'canonical_material':material,'source_evidence':material.get('evidence',[]),'source_formula_unchanged':True,'reference_formula':e['formula'],'reference_is_not_source_assay':True,'binding_approved':False})
stocks=[]
for rid,rec in records.items():
    for i,stock in enumerate(rec.get('stocks',[])):
        comps=[]
        for j,c in enumerate(stock['components']):comps.append({'material_id':c['material_id'],'registry_id':byid[c['material_id']]['id'],'canonical_pointer':f'/stocks/{i}/components/{j}','canonical_component':c})
        stocks.append({'record_id':rid,'stock_id':stock['id'],'canonical_pointer':f'/stocks/{i}','canonical_record_sha256':sha(B/'canonical-drafts'/f'{rid}.json'),'name':stock['name'],'components':comps,'concentrations':stock.get('concentrations',{}),'scope':stock.get('scope'),'viewer_policy':'Select components separately; never create a combined solution conformer. Quantities and concentration bases are retained verbatim.','binding_approved':False})
write(OUT/'registry-additions.json',{'schemaVersion':'1.0.0','source_id':'nagasaki2004','status':'private_authored_pending_independent_audit','entries':entries})
write(OUT/'molecule-bindings-proposal.json',bindings);write(OUT/'source-slot-mapping.json',{'source_id':'nagasaki2004','slot_count':len(slots),'identity_count':len(entries),'slots':slots})
write(OUT/'stock-component-selectors.json',{'source_id':'nagasaki2004','stocks':stocks,'source_note':'Only two canonical stocks are represented. CdCl2/Na2S 2.5 mM statements do not define independently specified stock volumes or a verified combined solution model.'})
assert len(slots)==61 and len(stocks)==2
write(OUT/'generation-report.json',{'status':'authored_pending_independent_audit','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'entries':len(entries),'slots':len(slots),'stocks':len(stocks),'model2d_count':sum(bool(e.get('model2dPath')) for e in entries),'model3d_count':sum(bool(e.get('model3dPath')) for e in entries),'software':{'rdkit':rdBase.rdkitVersion,'pymupdf':pymupdf.__version__},'input_hashes_unchanged':all(sha(p)==v for p,v in inputs.items()),'unresolved':['Potassium naphthalene exact connectivity/electronic state: source-name card only.','PDP formal alkoxide and corresponding alcohol are labeled name-based interpretations.','No polymer/protein/conjugate/solution/support/CdS atomic coordinates.','All independent molecular, binding, integration and browser gates remain pending.']})
# Static, usable review gallery includes exact source-slot selectors; this is not the public Site.
cards=[]
for e in entries:
    cards.append(f'<article data-id="{h(e["id"])}"><h2>{h(e["name"])}</h2><a href="{e["svgPath"]}"><img src="{e["svgPath"]}" alt="{h(e["name"])}" loading="lazy"></a><p>{h(e["caption"])}</p><p class="muted">{h(e["limitations"][0])}</p></article>')
gallery='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Nagasaki component references · private review</title><style>body{font:17px/1.5 system-ui;background:#f3f6f8;color:#213b4a;margin:24px auto;max-width:1180px}h1{font-size:30px}h2{font-size:20px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(390px,1fr));gap:22px}article{background:white;border:1px solid #d7e1e6;border-radius:16px;padding:20px}img{width:100%}.muted{font-size:14px;color:#617584}input{padding:12px;width:95%;font:inherit;margin-bottom:22px}</style><h1>Nagasaki 2004 · component references</h1><p>Private author package: 42 identities, 61 source slots. Independent scientific and binding review is pending. Click a drawing to inspect its SVG at full size.</p><input type="search" placeholder="Filter identity or source note" oninput="document.querySelectorAll(\'article\').forEach(a=>a.hidden=!a.textContent.toLowerCase().includes(this.value.toLowerCase()))"><main>'+''.join(cards)+'</main></html>'
(OUT/'review.html').write_text(gallery,encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
for page,start in enumerate(range(0,len(entries),6),1):
    subset=entries[start:start+6];canvas=Image.new('RGB',(1920,3*520),'#e9f0f4');draw=ImageDraw.Draw(canvas)
    for n,e in enumerate(subset):
        im=Image.open(OUT/'review'/f'{e["id"]}.png').convert('RGB');im.thumbnail((940,465));x=(n%2)*960+10;y=(n//2)*520+33;canvas.paste(im,(x,y));draw.text((x,y-25),e['id'],font=font,fill='#173b50')
    canvas.save(OUT/'review'/f'contact-{page:02d}.png')
print(json.dumps({'identities':len(entries),'slots':len(slots),'stocks':len(stocks),'model2d':sum(bool(e.get('model2dPath')) for e in entries),'model3d':sum(bool(e.get('model3dPath')) for e in entries)},indent=2))
