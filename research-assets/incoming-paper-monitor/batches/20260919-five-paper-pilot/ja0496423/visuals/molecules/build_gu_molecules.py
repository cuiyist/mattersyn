"""Private Gu reference depictions. Does not modify canonical or shared assets.

Run using existing Miniforge Python with read access to the installed task runtimes.
Primary reference fetches are separate and cached; this builder is offline.
"""
from pathlib import Path
from datetime import datetime, timezone
import sys, json, hashlib, re, html, math, copy
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
BATCH = OUT.parent.parent
RESEARCH = BATCH.parents[3]
sys.path.insert(0, str(RESEARCH / 'rdkit-runtime'))
sys.path.insert(0, str(RESEARCH / 'corpus-20260917/runtime'))
import rdkit
from rdkit import Chem
from rdkit.Chem import rdDepictor, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def esc(x): return html.escape(str(x), quote=True)
for folder in ['models', 'svg', 'review', 'raw']:
    (OUT/folder).mkdir(exist_ok=True)
RAW = OUT/'raw'
plan = read(BATCH/'visual-reuse-plan.json')
shared_path = Path(plan['registry_path'])
assert sha(shared_path) == plan['registry_sha256']
shared = {x['id']: x for x in read(shared_path)['entries']}
inputs = [BATCH/x for x in ['source-inventory.json', 'source-facts.json', 'visual-reuse-plan.json', 'visual-reuse-audit.json']]
inputs += sorted((BATCH/'canonical-drafts').glob('*.json')) + [shared_path]
input_hashes = {str(p): sha(p) for p in inputs}
if not (OUT/'input-hashes-before.json').exists(): dump(OUT/'input-hashes-before.json', input_hashes)
assert read(OUT/'input-hashes-before.json') == input_hashes, 'Frozen inputs changed; review before rebuilding.'

SNAP = OUT/'reference-base'
(SNAP/'entries').mkdir(parents=True, exist_ok=True)
def snapshot_file(original, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists(): assert sha(original)==sha(target), 'Do not overwrite a different frozen base snapshot.'
    else: target.write_bytes(original.read_bytes())
snapshot_file(shared_path, SNAP/'registry.json')
base_entries=[];base_assets=[]
for candidate in plan['materials']:
    rid=candidate.get('candidate_registry_id')
    if not rid: continue
    original=shared[rid];base_entries.append(copy.deepcopy(original))
    target=SNAP/'entries'/(rid+'.json')
    if target.exists(): assert read(target)==original
    else: dump(target,original)
    for key in ['svgPath','model2dPath','model3dPath']:
        if not original.get(key): continue
        source=shared_path.parent/original[key];saved=SNAP/original[key]
        assert sha(source)==original['assetHashes'][key]
        snapshot_file(source,saved)
        base_assets.append({'registry_id':rid,'kind':key,'path':str(saved.relative_to(OUT)).replace('\\','/'),'sha256':sha(saved)})
dump(SNAP/'snapshot-manifest.json',{'originalRegistrySha256':sha(shared_path),'registryCopyPath':'reference-base/registry.json','entries':len(base_entries),'assets':base_assets,'purpose':'Frozen pre-integration audit input; whole registry retained, assets copied only for the nine proposed reuse candidates.'})
oleyl_original=shared['oleylamine'];oleyl_normalized=copy.deepcopy(oleyl_original)
oleyl_normalized['limitations']=['The (Z)-oleylamine reference depicts one named constituent and geometric isomer. Reagent purity, mixture composition and isomer fractions are source-specific and must be supplied by the bound source record.']
canonical_bytes=json.dumps(oleyl_original,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
dump(OUT/'oleylamine-metadata-normalization-proposal.json',{
    'status':'private_proposal_pending_independent_audit','registry_id':'oleylamine','changedFields':['limitations'],
    'baseRegistrySha256':sha(shared_path),'baseEntryCanonicalSha256':hashlib.sha256(canonical_bytes).hexdigest(),
    'entryHashConvention':'UTF-8 JSON, ensure_ascii=false, sorted keys, separators comma/colon, no trailing newline',
    'baseEntrySnapshotPath':'reference-base/entries/oleylamine.json','baseEntrySnapshotSha256':sha(SNAP/'entries/oleylamine.json'),
    'normalizedEntry':oleyl_normalized,'unchangedAssetHashes':oleyl_original['assetHashes'],
    'scope':'Metadata only. No molecular graph, geometry, SVG, group indices, provenance or aliases changed. Gu 97% stays in its source bindings; no per-paper duplicate oleylamine entry needed.',
    'application':'Do not mutate shared registry until independent audit; replace this entry limitations field only.'})

# The web tool supplied these primary reference facts. Full HTML fetch failed;
# preserve that provenance distinction instead of pretending a raw page was cached.
nist = {'source_url':'https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1000',
        'alternate_read_url':'https://webbook.nist.gov/cgi/cbook.cgi?Mask=1019&Source=1966ART2',
        'retrieved_via':'web tool, parsed NIST Chemistry WebBook table; not raw HTML',
        'table':'Diatomic constants for 14N2', 'state':'X 1Sigma_g+',
        'column':'r_e / internuclear distance (angstrom)', 'raw_numeric_display':'1.09768 with final subscript digit 5',
        'reference_value_angstrom':1.097685, 'depiction_value_angstrom':1.09768,
        'precision_note':'Rounded to five decimal places for this reference depiction; no uncertainty invented.',
        'compilers':'Klaus P. Huber and Gerhard H. Herzberg', 'data_through':'February 1977',
        'scope':'Ground-state reference distance; not measured for the Gu storage gas and not an isotope assay.',
        'full_html_fetch':'unsuccessful; see raw/retrieval-log*.json'}
dump(RAW/'nitrogen-nist-extracted-reference.json', nist)
dump(RAW/'platinum-acac-nist-extracted-reference.json', {
    'source_url':'https://webbook.nist.gov/cgi/cbook.cgi?ID=C15170577&Units=CAL',
    'retrieved_via':'web tool, parsed primary reference record; not raw HTML',
    'name':'Platinum(II) acetylacetonate', 'formula':'C10H14O4Pt', 'cas':'15170-57-7',
    'InChI':'InChI=1S/2C5H8O2.Pt/c2*1-4(6)3-5(2)7;/h2*3,6H,1-2H3;/q;;+2/p-2/b2*4-3-;',
    'scope':'Reference stoichiometry only; no atom positions recovered.'})

def prop(slug): return read(RAW/(slug+'-properties.json'))['PropertyTable']['Properties'][0]
def sdf(slug, rep='2d'):
    m = Chem.SDMolSupplier(str(RAW/f'{slug}-pubchem-{rep}.sdf'), removeHs=False)[0]
    assert m is not None
    return Chem.RemoveHs(m)

PATTERNS = [
    ('Tertiary amine center', '[NX3;H0]([#6])([#6])[#6]'),
    ('Ketone carbonyl', '[#6][CX3](=[OX1])[#6]'),
    ('Acetylacetonate resonance fragment', '[C]([O-])=[C]-[C]=[O]'),
    ('Aryl bromide', '[c]-[Br]'),
    ('Carbon monoxide ligand fragment', '[C-]#[O+]'),
    ('Dinitrogen triple bond', '[N]#[N]')]
def groups(m):
    out=[]
    for label, smarts in PATTERNS:
        for match in m.GetSubstructMatches(Chem.MolFromSmarts(smarts)):
            ids=sorted(match)
            bonds=[b.GetIdx() for b in m.GetBonds() if {b.GetBeginAtomIdx(),b.GetEndAtomIdx()} <= set(ids)]
            out.append({'label':label,'atomIndices':ids,'bondIndices':bonds})
    for a in m.GetAtoms():
        if a.GetAtomicNum() in [26,48,78,17]:
            out.append({'label':'Formal metal center' if a.GetAtomicNum()!=17 else 'Chloride ion', 'atomIndices':[a.GetIdx()],'bondIndices':[]})
    return out

def model(m,e,rep):
    c=m.GetConformer()
    atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,7),
            'y':round(c.GetAtomPosition(a.GetIdx()).y,7),'z':round(c.GetAtomPosition(a.GetIdx()).z,7),
            'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs(),
            'chiralTag':str(a.GetChiralTag())} for a in m.GetAtoms()]
    bonds=[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble(),'stereo':str(b.GetStereo()),
            'stereoAtoms':list(b.GetStereoAtoms())} for b in m.GetBonds()]
    return {'id':e['id'],'name':e['name'],'formula':e['formula'],'pubchemCid':e.get('pubchemCid'),
            'representation':rep,'has3D':rep=='3d','allowRotation':rep=='3d',
            'coordinateUnits':'angstrom' if rep=='3d' else 'drawing units', 'indexConvention':'zero-based',
            'atoms':atoms,'bonds':bonds,'functionalGroups':groups(m), 'connectivitySmiles':Chem.MolToSmiles(m,True),
            'caption':e['caption'],'notes':e['limitations'],'eligible_training':False}

def inner_svg(m,width=800,height=220):
    draw=rdMolDraw2D.MolDraw2DSVG(width,height)
    o=draw.drawOptions();o.clearBackground=False;o.padding=.10;o.bondLineWidth=2.4;o.minFontSize=17;o.maxFontSize=26
    gg=groups(m);aa=sorted({i for g in gg for i in g['atomIndices']});bb=sorted({i for g in gg for i in g['bondIndices']})
    draw.DrawMolecule(m,highlightAtoms=aa,highlightBonds=bb,
                     highlightAtomColors={i:(.77,.90,.92) for i in aa},highlightBondColors={i:(.44,.70,.76) for i in bb})
    draw.FinishDrawing();s=draw.GetDrawingText()
    s=s[s.index('<svg'):]
    # Explicit group translation is supported consistently by SVG renderers.
    return '<g transform="translate(20,65)">'+s[s.index('>')+1:s.rindex('</svg>')]+'</g>'

def frame(e,body,footer):
    title=esc(e['name']);formula=esc(e['displayFormula'])
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="840" height="360" viewBox="0 0 840 360" role="img"><title>{title}</title><desc>{esc(e["caption"])}</desc><rect width="840" height="360" fill="white"/><path d="M24 54H816" stroke="#d8e3e9"/><text x="28" y="34" font-family="Arial,sans-serif" font-size="24" font-weight="600" fill="#18384d">{title}</text><text x="812" y="34" text-anchor="end" font-family="Arial,sans-serif" font-size="21" fill="#436879">{formula}</text>{body}<rect x="20" y="302" width="800" height="42" rx="8" fill="#edf5f7"/><text x="420" y="328" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" fill="#345b6b">{esc(footer)}</text></svg>'

entries=[];three=[];generation=[]
def entry(slug,name,formula,kind,caption,limitations,urls,display=None,cid=None):
    return {'id':'gu2004-'+slug+'-reference','name':name,'formula':formula,'displayFormula':display or formula,
            'aliases':[name],'depictionKind':kind,'svgPath':None,'model2dPath':None,'model3dPath':None,
            'caption':caption,'limitations':limitations,'sourceUrls':urls,'pubchemCid':cid,
            'functionalGroups':[],'provenance':{'depictionSoftware':'RDKit '+rdkit.__version__,'sourcePaperRole':'Illustration/reference layer; not a new measured source structure'},
            'independentScientificAudit':'pending','published':False,'eligible_training':False}

def save(e,m=None,m3=None,footer='',custom=None):
    if m is not None:
        assert rdMolDescriptors.CalcMolFormula(m)==e['formula'], (e['id'],rdMolDescriptors.CalcMolFormula(m),e['formula'])
        rdDepictor.Compute2DCoords(m)
        m2=model(m,e,'2d');m2.update({'modelType':'Reference connectivity / 2D drawing','coordinateSource':'RDKit 2D layout from declared graph','computedBy':'RDKit '+rdkit.__version__})
        e['model2dPath']='models/'+e['id']+'-2d.json';dump(OUT/e['model2dPath'],m2);e['functionalGroups']=m2['functionalGroups']
        body=inner_svg(m)
    else: body=''
    if custom is not None:body=custom
    e['svgPath']='svg/'+e['id']+'.svg';(OUT/e['svgPath']).write_text(frame(e,body,footer),encoding='utf-8')
    if m3 is not None:
        assert e['depictionKind']=='molecule' and m3.GetConformer().Is3D()
        assert Chem.MolToSmiles(m3,True)==Chem.MolToSmiles(m,True)
        d=model(m3,e,'3d')
        d.update({'modelType':'PubChem computed reference conformer','coordinateSource':'PubChem3D cached SDF',
                  'sourceType':'database-computed reference; not experimental', 'caption':'One PubChem computed reference conformer. Not measured in Gu et al.; no unique solution or surface conformation is asserted.',
                  'rawSourcePath':e['provenance']['reference3d']['path'],'rawSourceSha256':e['provenance']['reference3d']['sha256']})
        e['model3dPath']='models/'+e['id']+'-3d.json';dump(OUT/e['model3dPath'],d);three.append(d)
    e['assetHashes']={k:sha(OUT/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e[k]}
    doc=pymupdf.open(stream=(OUT/e['svgPath']).read_bytes(),filetype='svg')
    doc[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).save(str(OUT/'review'/(e['id']+'.png')))
    entries.append(e)

for slug,name,formula,footer,limitations in [
 ('triethylamine','Triethylamine','C6H15N','Tertiary amine · neutral reference molecule',['Gu reagent is 99%; protonation and solution populations are not determined by this reference.']),
 ('acetylacetone','Acetylacetone','C5H8O2','Diketo reference · solution tautomer proportions unreported',['Gu names 2,4-pentanedione 99%. This depicts the diketo tautomer; no keto/enol ratio or chelated structure is implied.']),
 ('dibromoanthracene','9,10-Dibromoanthracene','C14H8Br2','Aryl bromides at 9,10 · fluorescence reference identity',['Optical quantum-yield standard, not a synthesis reagent. Purity and source-batch geometry are unreported.'])]:
    pr=prop(slug);m=sdf(slug);m3=sdf(slug,'3d')
    assert pr['MolecularFormula']==formula
    assert Chem.MolToSmiles(m,True)==Chem.MolToSmiles(Chem.MolFromSmiles(pr['ConnectivitySMILES']),True)
    e=entry(slug,name,formula,'molecule','Named reference molecule with verified connectivity; not a recovered molecular structure from the Gu paper.',limitations,[f'https://pubchem.ncbi.nlm.nih.gov/compound/{pr["CID"]}'],cid=pr['CID'])
    e['provenance'].update({'connectivitySource':'PubChem property record and original 2D SDF, mutually checked','smiles':Chem.MolToSmiles(m,True),
        'reference2d':{'path':f'raw/{slug}-pubchem-2d.sdf','sha256':sha(RAW/f'{slug}-pubchem-2d.sdf')},
        'reference3d':{'path':f'raw/{slug}-pubchem-3d.sdf','sha256':sha(RAW/f'{slug}-pubchem-3d.sdf')},
        'referenceProperties':{'path':f'raw/{slug}-properties.json','sha256':sha(RAW/f'{slug}-properties.json')}})
    save(e,m,m3,footer)

ligand=sdf('acetylacetonate')
assert rdMolDescriptors.CalcMolFormula(ligand)=='C5H7O2-' and Chem.GetFormalCharge(ligand)==-1
for metal,slug,name,formula in [('Pt','platinum-acac','Pt(acac)2','C10H14O4Pt'),('Cd','cadmium-acac','Cd(acac)2','C10H14CdO4')]:
    m=Chem.CombineMols(Chem.MolFromSmiles(f'[{metal}+2]'),Chem.CombineMols(ligand,ligand))
    Chem.SanitizeMol(m);assert len(Chem.GetMolFrags(m))==3
    rejected=prop(slug)
    e=entry(slug,name,formula,'ionic_components',f'Formal {metal}2+ and two acetylacetonate ligand fragments. Fragment layout is not a molecular coordination structure or evidence of free ions in the reagent.',
            ['Metal–oxygen bonds and 3D geometry deliberately unavailable.','The ligand is one reference resonance form; displayed Z connectivity is not a source conformational measurement.',
             'Hydration, oligomerization, solution speciation and actual solid structure are unreported.','Formula is the named anhydrous stoichiometric unit, not measured complete reagent composition.'],
            ['https://pubchem.ncbi.nlm.nih.gov/compound/5460482','https://doi.org/10.1021/ja0496423']+(['https://webbook.nist.gov/cgi/cbook.cgi?ID=C15170577&Units=CAL'] if metal=='Pt' else []))
    e['provenance'].update({'connectivitySource':'Unconnected formal metal center plus two exact copies of PubChem 5460482 acetylacetonate graph; no metal coordination edges added.',
       'ligandReference':{'cid':5460482,'path':'raw/acetylacetonate-pubchem-2d.sdf','sha256':sha(RAW/'acetylacetonate-pubchem-2d.sdf')},
       'formulaBasis':'NIST Pt reference and verified ligand stoichiometry' if metal=='Pt' else 'Source name Cd(acac)2 plus independently verified acac− formula; does not establish hydration or actual isolated structure.',
       'rejectedWholePrecursorLookup':{'cid':rejected['CID'],'formula':rejected['MolecularFormula'],'path':f'raw/{slug}-properties.json','sha256':sha(RAW/f'{slug}-properties.json'),
          'reason':'Neutral protonated-ligand fragments give two extra H; not the source-named acetylacetonate stoichiometry.'}})
    save(e,m,footer='Formal component view · coordination and hydration unspecified')

m=sdf('iron-pentacarbonyl');assert len(Chem.GetMolFrags(m))==6
e=entry('iron-pentacarbonyl','Iron pentacarbonyl','C5FeO5','ionic_components',
        'Fe(CO)5 ligand inventory: one Fe center and five CO reference fragments. No metal–carbon geometry is encoded; these are not asserted to be free components in the reagent.',
        ['No 3D or Fe–C bonds are provided.','Formal C−/O+ charges are one carbon-monoxide resonance representation.','Gu does not print a purity next to Fe(CO)5; Pt(acac)2 98% must not be transferred.'],
        ['https://pubchem.ncbi.nlm.nih.gov/compound/518773','https://doi.org/10.1021/ja0496423'],display='Fe(CO)5',cid=518773)
e['provenance'].update({'connectivitySource':'Exact disconnected PubChem 518773 2D SDF graph; no fragment stitching.',
 'reference2d':{'path':'raw/iron-pentacarbonyl-pubchem-2d.sdf','sha256':sha(RAW/'iron-pentacarbonyl-pubchem-2d.sdf')}})
save(e,m,footer='Ligand inventory only · Fe–C bonds and 3D geometry unavailable')

m=Chem.MolFromSmiles('[Cd+2].[Cl-].[Cl-]')
e=entry('cadmium-chloride','Cadmium chloride','CdCl2','ionic_components',
        'Formal Cd2+ and two Cl− stoichiometric components; no lattice, coordination geometry or dissolved-species distribution is implied.',
        ['Gu prints CdCl2 at 80.5%; hydration and assay basis are unspecified.','No hydrate shell, isolated linear molecule, mass correction or 3D geometry is assigned.'],
        ['https://pubchem.ncbi.nlm.nih.gov/compound/24947','https://doi.org/10.1021/ja0496423'])
e['provenance'].update({'formulaReference':{'path':'raw/cadmium-chloride-properties.json','sha256':sha(RAW/'cadmium-chloride-properties.json'),'cid':24947},
 'graphConvention':'Source stoichiometry expressed as formal charged components. PubChem Cl–Cd–Cl connectivity is not reused as the solid/reagent geometry.'})
save(e,m,footer='Salt components · 80.5% as printed; hydration unspecified')

e=entry('sulfur-element','Elemental sulfur powder','S','formula','Elemental sulfur identity. The paper does not identify a powder allotrope or a discrete dissolved molecule.',
        ['No S8 ring, monatomic vapor, crystal lattice or 3D structure is assigned.','Source grade 99.998%; precursor form is powder.'],['https://doi.org/10.1021/ja0496423'])
e['provenance']['identitySource']='Gu supporting information p1, chemical inventory and sulfur-addition procedure; no molecular allotrope lookup substituted.'
save(e,footer='Allotrope unspecified · no discrete molecular model',custom='<text x="420" y="190" text-anchor="middle" font-family="Arial,sans-serif" font-size="90" fill="#bd9415">S</text><text x="420" y="242" text-anchor="middle" font-family="Arial,sans-serif" font-size="21" fill="#526975">Elemental powder · 99.998% source grade</text>')

old=shared['nitrogen'];old3=read(shared_path.parent/old['model3dPath'])
old_distance=math.dist([old3['atoms'][0][k] for k in ['x','y','z']],[old3['atoms'][1][k] for k in ['x','y','z']])
m=Chem.MolFromSmiles('N#N')
e=entry('nitrogen','Nitrogen','N2','molecule','Ground-state dinitrogen reference. The 3D reference uses a NIST internuclear distance with arbitrary overall orientation, not Gu gas coordinates.',
        ['NIST constant refers to 14N2; Gu does not report isotopic composition.','Nitrogen is stated for storage; the general inert reaction gas remains unspecified.'],
        [nist['source_url'],'https://pubchem.ncbi.nlm.nih.gov/compound/947'])
e['provenance'].update({'connectivitySource':'Existing qualified N≡N connectivity; PubChem947 reference.',
 'distanceReference':{'path':'raw/nitrogen-nist-extracted-reference.json','sha256':sha(RAW/'nitrogen-nist-extracted-reference.json')},
 'replacesOnlyPrivately':{'registryId':'nitrogen','old3dSha256':sha(shared_path.parent/old['model3dPath']),'oldDistanceAngstrom':old_distance,'sharedAssetUnchanged':True}})
save(e,m,footer='N≡N reference · 1.09768 Å NIST ground-state bond')
m3=Chem.Mol(m);m3.RemoveAllConformers();c=Chem.Conformer(2);c.Set3D(True)
c.SetAtomPosition(0,(-.54884,0,0));c.SetAtomPosition(1,(.54884,0,0));m3.AddConformer(c)
d=model(m3,e,'3d');d.update({'modelType':'Reference-distance-derived diatomic geometry','coordinateSource':'NIST ground-state 14N2 r_e, rounded to 1.09768 Å (half-even rounding); centered on x axis',
 'construction':'Atoms placed at ±r_e/2 on an arbitrary x axis; no force field or recovered XYZ claimed.',
 'referenceDistanceAngstrom':1.09768,'referenceIsotopologue':'14N2','sourceType':'Coordinates constructed from a published reference scalar, not an observed Gu structure'})
e['model3dPath']='models/'+e['id']+'-3d.json';dump(OUT/e['model3dPath'],d);e['assetHashes']['model3dPath']=sha(OUT/e['model3dPath']);three.append(d)

registry={'schemaVersion':'1.0.0','assetPurpose':'Private Gu source-specific reference depictions; independent audit pending','entries':entries,
          'summary':{'entries':len(entries),'models2d':sum(bool(e['model2dPath']) for e in entries),'models3d':sum(bool(e['model3dPath']) for e in entries),'svg':len(entries)},
          'notes':['Additions only; shared registry remains unchanged.','Metal and sulfur representations have no rotate control.','Functional group indices are local to each 2D/3D model.','No precursor atomic structure was recovered from Gu.']}
dump(OUT/'registry-additions.json',registry);dump(OUT/'molecules-3d.json',three)

source_to_entry={
 'triethylamine':'gu2004-triethylamine-reference','sulfur':'gu2004-sulfur-element-reference',
 'iron-pentacarbonyl':'gu2004-iron-pentacarbonyl-reference','platinum-acac':'gu2004-platinum-acac-reference',
 'cadmium-chloride':'gu2004-cadmium-chloride-reference','acetylacetone':'gu2004-acetylacetone-reference',
 'cadmium-acac':'gu2004-cadmium-acac-reference','dibromoanthracene':'gu2004-dibromoanthracene-reference','nitrogen':'gu2004-nitrogen-reference',
 'oleylamine':'oleylamine','oleic-acid':'oleic-acid','diol':'hexadecane-1-2-diol','dioctyl-ether':'dioctyl-ether',
 'topo':'topo','water':'water','ethanol':'ethanol','hexane':'hexane'}
scope_notes={
 'oleylamine':'Reference cis/Z oleylamine component. Gu reports 97% reagent purity; geometric-isomer composition is unassayed.',
 'oleic-acid':'Named oleic acid reference; Gu 99%. No measured surface-bound oleate geometry.',
 'diol':'Named hexadecane-1,2-diol reference component; technical 90%. Stereochemistry and impurities unspecified; a reference conformer does not assign the source enantiomer.',
 'dioctyl-ether':'Named dioctyl ether reference; Gu 99%. No numerical boiling temperature or pressure supplied by model.',
 'topo':'Pure named TOPO component only; Gu technical 90% mixture, unspecified impurities. Do not infer pure stock composition.',
 'water':'Water reference. DI specified for initial dissolution; recrystallization water not explicitly DI.',
 'ethanol':'Ethanol reference; purity and ethanol/water recrystallization ratio unreported.',
 'hexane':'Illustrative n-hexane reference. Gu says hexane; exact isomer composition/assay unreported.',
 'nitrogen':'Nitrogen storage atmosphere only; inert reaction gas identity is not thereby established. Uses a private NIST-distance 3D reference; no source-batch molecular coordinates.'}
new={e['id']:e for e in entries};bindings={};details={};unowned=[]
for f in sorted((BATCH/'canonical-drafts').glob('*.json')):
    r=read(f);rid=r['record_id'];bindings[rid]={};details[rid]={}
    for m in r['materials']:
        key=m['id']
        if key not in source_to_entry:
            unowned.append({'record_id':rid,'material_id':key,'name':m['name'],'owner':'root product/specimen bindings'});continue
        eid=source_to_entry[key];bindings[rid][key]=eid
        ee=new.get(eid,shared.get(eid));note=scope_notes.get(key,ee['caption']+' '+' '.join(ee['limitations']))
        details[rid][key]={'source_material_id':'gu2004-'+key,'registry_id':eid,'asset_origin':'private additions' if eid in new else 'existing independently reuse-qualified registry',
                          'source_name':m['name'],'source_role':m['role'],'source_stage':m.get('stage'),
                          'canonical_evidence':m.get('evidence',[]),'source_notes':m.get('notes',[]),
                          'display_scope':note,'viewOverrides':{'name':m['name'],'caption':note,'limitations':[note],'modelNotes':[note]},
                          'override_policy':'Replace unrelated source-specific purity/mixture notes in displayed shared entry/model metadata; retain original reference provenance separately.',
                          'binding_approved':False,'independent_scientific_audit':'pending'}
assert sum(map(len,bindings.values()))==20 and len(unowned)==8
dump(OUT/'molecule-bindings-proposal.json',{'schemaVersion':'1.0.0','status':'private_proposal_pending_independent_audit','recordBindings':bindings,'bindingNotes':details,
    'sourceRecordSha256':{f.stem:sha(f) for f in sorted((BATCH/'canonical-drafts').glob('*.json'))},
    'inventoryMaterialReferences':{'gu2004-'+k:v for k,v in source_to_entry.items()},'source_material_identity_count':17,'reagent_slot_count':20,
    'uncovered_specimen_slots':unowned,'registryAdditionsSha256':sha(OUT/'registry-additions.json'),
    'reuseRegistry':{'path':str(shared_path),'sha256':sha(shared_path)},'productCardReference':{'record_id':'gu-2004-cdacac-preparation','registry_id':'gu2004-cadmium-acac-reference','label':'Cd(acac)2 formal ligand context; coordination/hydration unreported'},
    'published':False,'training_eligible':False})
assert all(sha(Path(q))==h for q,h in input_hashes.items())
dump(OUT/'generation-report.json',{'status':'generated_author_checks_pending','rdkitVersion':rdkit.__version__,'svgRenderer':'PyMuPDF '+pymupdf.VersionBind,
 'registrySha256':sha(OUT/'registry-additions.json'),'bindingProposalSha256':sha(OUT/'molecule-bindings-proposal.json'),
 'summary':registry['summary'],'frozenInputsUnchanged':True,'oldNitrogenDistanceAngstrom':old_distance,'replacementNitrogenDistanceAngstrom':1.09768,
 'primaryReference3dReused':3,'locallyEmbeddedConformers':0,'referenceDistanceDerived3d':1,
 'wholePrecursorLookupRejections':['Pt-acac neutral ligand H16 mismatch','Cd-acac neutral ligand H16 mismatch'],
 'no3d':['sulfur','CdCl2','Fe(CO)5','Pt(acac)2','Cd(acac)2'],'independentScientificAudit':'pending','visualInspection':'pending'})
print(json.dumps(registry['summary']))
