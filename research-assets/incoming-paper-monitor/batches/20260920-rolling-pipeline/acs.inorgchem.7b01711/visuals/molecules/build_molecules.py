"""Private Morrison reference identities and exact canonical slot/stock proposals.

Local source/cache only. This author program does not approve independent gates.
"""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
from collections import Counter
import json, hashlib, html, math, sys, re, textwrap
sys.dont_write_bytecode = True
O = Path(__file__).resolve().parent
P = O.parents[1]
M = P.parents[4]
S = M / 'recipe-atlas'
REG = S / 'dist/assets/chemical-registry'
C = P / 'canonical-proposal/v2'
sys.path.insert(0, str(M / 'research-assets/rdkit-runtime'))
sys.path.insert(0, str(M / 'research-assets/corpus-20260917/runtime'))
from rdkit import Chem
from rdkit.Chem import rdDepictor, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image, ImageDraw

if (O / 'package-freeze.json').exists():
    raise SystemExit('Frozen package: prepare a separate revision.')
for d in ['svg','models','previews','contacts','reference-snapshots','stock-previews','stock-svg','conformer-previews']:
    (O/d).mkdir(parents=True, exist_ok=True)
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(n,x):
    p=O/n; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def esc(x): return html.escape(str(x),quote=True)
def tx(x,y,s,n=18,color='#294558',anchor='middle'):
    return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{n}" fill="{color}" text-anchor="{anchor}">{esc(s)}</text>'
def wrapped(s,x,y,width=83,size=18,line=25):
    return ''.join(tx(x,y+i*line,v,size,anchor='start') for i,v in enumerate(textwrap.wrap(s,width)))
inputs={}; snapshots=[]; checks=[]; entries=[]; qualifications=[]
def bind(p): p=Path(p); inputs[str(p)]=sha(p)
def snap(p,rel):
    p=Path(p); out=O/'reference-snapshots'/rel
    out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(p.read_bytes())
    bind(p); snapshots.append({'original_path':str(p),'sha256':sha(p),'snapshot_path':str(out.relative_to(O))})
    return out
for p in [C/'package-manifest.json',C/'record-manifest.json',P/'source-facts.json',P/'source-inventory.json',P/'package-freeze.json',P/'source-independent-audit/independent-audit-v2.json',S/'dist/chemical-viewer.mjs']:
    bind(p)
assert sha(C/'package-manifest.json')=='433555d5ccaaa0a3d98c01f3f9657921872611fee766557e9c4756f49e806508'
assert sha(P/'source-independent-audit/independent-audit-v2.json')=='5cabf080455991d4aeb36792f37b884afc29595895785b8c7d38e3d3ab00165d'
bind(P/'canonical-reader-independent-audit/independent-audit-v2.json')
assert sha(P/'canonical-reader-independent-audit/independent-audit-v2.json')=='c8be4ee1522e9c1c4fb9555f8242870e5b75dd0be3c0198eaa0915f1320d4139'
records={}
for row in read(C/'record-manifest.json')['records']:
    assert sha(row['path'])==row['sha256']; bind(row['path'])
    records[row['record_id']]=read(row['path'])
slots={}
for rid,r in records.items():
    for i,m in enumerate(r['materials']): slots.setdefault(m['id'],[]).append((rid,i,m))
assert len(slots)==29 and sum(map(len,slots.values()))==64
base={e['id']:e for e in read(REG/'registry.json')['entries']}
snap(REG/'registry.json','registry.json')
source_url='https://doi.org/10.1021/acs.inorgchem.7b01711'

# Explicit named-identity expansions, not recovered solution structures.
GRAPH={
 'cdcl2':('[Cd+2].[Cl-].[Cl-]','CdCl2','gu2004-cadmium-chloride-reference'),
 'water':('O','H2O','water'), 'ethanol':('CCO','C2H6O','ethanol'),
 'thf':('C1CCOC1','C4H8O','thf'), 'dmso-d6':('[2H]C([2H])([2H])S(=O)C([2H])([2H])[2H]','C2D6OS','dimethyl-sulfoxide-d6'),
 'dmso':('CS(C)=O','C2H6OS','dimethyl-sulfoxide'), 'toluene':('Cc1ccccc1','C7H8','toluene'),
 'dmf':('CN(C)C=O','C3H7NO','dimethylformamide'), 'methanol':('CO','CH4O','methanol'),
 'chloroform':('ClC(Cl)Cl','CHCl3','chloroform'),
 'nh4ptc':('[NH4+].[S-]C(=S)Nc1ccccc1','C7H10N2S2',None),
 'thf-d8':('[2H]C1([2H])C([2H])([2H])C([2H])([2H])OC1([2H])[2H]','C4D8O',None),
 'n-octylamine':('CCCCCCCCN','C8H19N',None), 'aniline':('Nc1ccccc1','C6H7N',None),
 'phenylisothiocyanate':('S=C=Nc1ccccc1','C7H5NS',None), 'carbon-disulfide':('S=C=S','CS2',None),
 'diphenylthiourea':('S=C(Nc1ccccc1)Nc1ccccc1','C13H12N2S',None),
 'dichloromethane':('ClCCl','CH2Cl2',None)}
SYMBOLS={
 'cdptc':('Cadmium bis(phenyldithiocarbamate)', 'C14H12CdN2S4', ['Cd(PTC)2 precursor','Isolated precursor powder identity','Solution nuclearity is not established'], 'No monomer, dissolved complex or product lattice is asserted.'),
 'cdptc-thf-crystal':('Cd(PTC)2·THF precursor crystal','C18H20CdN2OS4',['Cd(PTC)2 · THF','Measured precursor coordination polymer','Atomic tables belong to this precursor'], 'No crystal model is generated in this molecular proposal.'),
 'hexane':('Hexane: source isomer unspecified','C6H14',['Hexane solvent','Isomer composition is not reported','No specific isomer graph selected'], 'Cached n-hexane is not evidence that this source used n-hexane.'),
 'cdse-qb':('Starting CdSe quantum belts','{CdSe[n-octylamine]0.53}',['CdSe quantum belts','Reported n-octylamine ligand composition','Pre-existing nanocrystal dispersion'], 'Symbolic composition only; no ligand binding geometry or atomic coordinates.'),
 'cds-powder':('CdS powder context','CdS',['Cadmium sulfide powder','Source-scoped decomposition product','See original diffraction and microscopy'], 'No particle size, phase or atomic arrangement is encoded by this symbol.'),
 'cdse-cds-qb':('CdSe–CdS quantum-belt context','CdSe / CdS',['CdSe / CdS','Core–shell quantum-belt composition','Use the record-specific specimen context'], 'No shell thickness, complete coverage, exact batch join or lattice is inferred.'),
 'tem-grid':('TEM support: copper with carbon film','Cu / carbon',['Copper TEM grid','Carbon support film','Support identity, not a specimen model'], 'Grid mesh, film thickness and surface atomic structure are not specified.'),
 'xrd-substrate':('XRD support: composition unreported',None,['XRD substrate','Composition and surface are unspecified','No silicon, glass or other identity inferred'], 'This is an unknown support symbol, not a material structure.'),
 'cdoleate-reference':('Cadmium oleate: cited comparison','Cd(oleate)2',['Cadmium oleate comparison','Prior cited shell-growth context','No source-specific coordination model'], 'No hydrate, solution nuclearity, ligand stereochemistry or new recipe inferred.'),
 'bulk-cdse-reference':('Bulk CdSe diffraction reference','CdSe',['Bulk CdSe reference','Reference phase context in the source','Not a measured nanocrystal coordinate set'], 'No reference CIF or atomic coordinates are supplied by this illustration.'),
 'bulk-cds-reference':('Bulk CdS diffraction reference','CdS',['Bulk CdS reference','Reference phase context in the source','Not a measured nanocrystal coordinate set'], 'No reference CIF or atomic coordinates are supplied by this illustration.')}
assert set(GRAPH)|set(SYMBOLS)==set(slots)

def identity(mid,formula,name=None,kind='molecule'):
    m=slots[mid][0][2]; eid='morrison2017-'+mid+'-reference'
    return {'id':eid,'name':name or m['name'],'aliases':[m['name']],'formula':formula,'displayFormula':formula,
      'depictionKind':kind,'pubchemCid':None,'svgPath':'svg/'+eid+'.svg','model2dPath':None,'model3dPath':None,
      'functionalGroups':[],'sourceUrls':[source_url],
      'caption':'Named chemical connectivity reference; not measured solution geometry.',
      'limitations':['No concentration, purity, solution speciation or surface bonding is encoded by this identity drawing.'],
      'provenance':{'sourceDoi':'10.1021/acs.inorgchem.7b01711','sourceMaterialId':mid,'sourceLocators':m['evidence'],
       'canonicalIdentityFormula':m['formula'],'sourceAuditSha256':sha(P/'source-independent-audit/independent-audit-v2.json'),'measuredCoordinates':False},
      'binding_approved':False,'independentScientificAudit':'pending','published':False,'eligible_training':False}

def frame(e,body,footer):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="640" viewBox="0 0 1100 640"><title>{esc(e["name"])}</title><desc>{esc(e["caption"])}</desc><rect x="1" y="1" width="1098" height="638" rx="20" fill="white" stroke="#cbdde5"/>{tx(36,47,e["name"],26 if len(e["name"])<60 else 21,anchor="start")}<path d="M36 72H1064" stroke="#d5e3e8"/>{tx(550,107,e["displayFormula"] or "Composition not reported",22)}{body}<rect x="30" y="566" width="1040" height="53" rx="9" fill="#edf5f7"/>{wrapped(footer,50,589,102,16,20)}</svg>'
def raster(svg,png):
    doc=pymupdf.open(stream=svg.encode(),filetype='svg')
    doc[0].get_pixmap(matrix=pymupdf.Matrix(1,1),alpha=False).save(str(png));doc.close()
def render(e,svg):
    (O/e['svgPath']).write_text(svg,encoding='utf-8')
    raster(svg,O/'previews'/(e['id']+'.png'))
    e['assetHashes']={k:sha(O/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}
    entries.append(e)
def fg(mol):
    groups=[]
    patterns=[('Ammonium cation','[N+;H4]'),('Dithiocarbamate reference','[S-]C(=S)N'),('Primary amine','[NX3;H2]'),('Ether oxygen','[OD2]([#6])[#6]'),('Hydroxyl group','[OX2H]'),('Sulfoxide','[#16X3](=[#8])'),('Amide','[NX3][CX3]=[OX1]'),('Isothiocyanate','N=C=S'),('Thiourea','N[C](=S)N'),('Carbon disulfide','S=C=S'),('Aromatic ring','c1ccccc1'),('C–Cl functionality','[#6]-[#17]'),('Formal cadmium ion','[Cd+2]'),('Chloride counterion','[Cl-]')]
    for label,pat in patterns:
        ids=sorted({a for match in mol.GetSubstructMatches(Chem.MolFromSmarts(pat)) for a in match})
        if ids: groups.append({'label':label,'atomIndices':ids,'bondIndices':[b.GetIdx() for b in mol.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]})
    return groups
def graph_from_model(raw):
    rw=Chem.RWMol()
    for a in raw['atoms']:
        atom=Chem.Atom(a['element']);atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0));rw.AddAtom(atom)
    for b in raw['bonds']:
        rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
    mol=rw.GetMol();Chem.SanitizeMol(mol);return mol
def canon(mol):return Chem.MolToSmiles(Chem.RemoveHs(mol))
def m2d(e,mol):
    rdDepictor.Compute2DCoords(mol); conf=mol.GetConformer();groups=fg(mol)
    atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':conf.GetAtomPosition(a.GetIdx()).x,'y':conf.GetAtomPosition(a.GetIdx()).y,'z':0.0,'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in mol.GetAtoms()]
    bonds=[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':1.5 if b.GetIsAromatic() else b.GetBondTypeAsDouble()} for b in mol.GetBonds()]
    e['model2dPath']='models/'+e['id']+'-2d.json';e['functionalGroups']=groups
    save(e['model2dPath'],{'id':e['id'],'name':e['name'],'formula':e['formula'],'representation':'2d','has3D':False,'allowRotation':False,'indexConvention':'zero-based','coordinateUnits':'arbitrary drawing units','modelType':'Named connectivity reference; generated 2D drawing','caption':e['caption'],'connectivitySmiles':Chem.MolToSmiles(mol),'atoms':atoms,'bonds':bonds,'functionalGroups':groups,'source':{'urls':e['sourceUrls'],'retainedRegistryId':e['provenance'].get('retainedRegistryId'),'identityBasis':e['provenance'].get('identityBasis')},'notes':e['limitations']})
    drawer=rdMolDraw2D.MolDraw2DSVG(1000,405);opts=drawer.drawOptions();opts.padding=.11;opts.addStereoAnnotation=True
    palette=[(.85,.69,.33),(.62,.48,.77),(.29,.68,.65),(.84,.47,.53)];colors={}
    for i,g in enumerate(groups):
        for a in g['atomIndices']:colors[a]=palette[i%4]
    rdMolDraw2D.PrepareAndDrawMolecule(drawer,mol,highlightAtoms=list(colors),highlightAtomColors=colors);drawer.FinishDrawing()
    svg=drawer.GetDrawingText();start=svg.index('>',svg.index('<svg'))+1
    return '<g transform="translate(50,135)">'+svg[start:svg.rindex('</svg>')]+'</g>'

for mid,(smiles,formula,cached) in GRAPH.items():
    mol=Chem.MolFromSmiles(smiles); assert mol is not None
    if mid=='water':mol=Chem.AddHs(mol)
    calculated=rdMolDescriptors.CalcMolFormula(mol,separateIsotopes=True,abbreviateHIsotopes=True)
    assert calculated==formula,(mid,calculated,formula)
    e=identity(mid,formula)
    e['provenance']['identityBasis']='Exact named identity expanded into conventional 2D connectivity; author-generated layout, not an experimental structural determination.'
    if mid=='water': e['caption']='Water molecular reference. The source explicitly specifies deionized water; preparation and wash roles remain separate at their canonical operations.'
    if mid=='cdcl2': e['caption']='Cadmium chloride formal-ion reference: Cd²⁺ and two Cl⁻ ions, with no Cd–Cl bonds or inferred hydrate.';e['limitations'].append('Hydration, purity and dissolved cadmium coordination are not specified in this source.')
    if mid=='nh4ptc': e['caption']='Ammonium phenyldithiocarbamate formal-ion connectivity: NH₄⁺ and one PTC⁻ ligand reference. The depicted resonance form is conventional.'; e['limitations'].append('This ligand salt is not a cadmium complex. Its cited upstream preparation has not been recovered here.')
    if mid=='thf-d8': e['caption']='Tetrahydrofuran-d₈ connectivity with eight explicit deuterium atoms; 2D isotope reference only.'
    if mid=='dmso-d6': e['caption']='Dimethyl sulfoxide-d₆ reference with six deuterium atoms. No isotopic enrichment percentage is inferred.'
    if mid in ['n-octylamine','aniline']: e['limitations'].append('A free-molecule reference does not identify which amine was used in the source-conflicted catalysis description (C5), or establish surface coordination.')
    if mid in ['phenylisothiocyanate','carbon-disulfide','diphenylthiourea']: e['limitations'].append('Observed or proposed reaction-species context does not turn this identity into a charged reagent or an isolated yield claim.')
    if cached:
        old=base[cached];save('reference-snapshots/entry-'+cached+'.json',old)
        for key in ['svgPath','model2dPath','model3dPath']:
            if old.get(key):
                assert sha(REG/old[key])==old['assetHashes'][key],(cached,key)
                snap(REG/old[key],old[key])
        raw2=read(REG/old['model2dPath']); cm=graph_from_model(raw2)
        assert canon(cm)==canon(mol),(mid,canon(cm),canon(mol))
        e['pubchemCid']=old.get('pubchemCid')
        e['sourceUrls']=list(dict.fromkeys([source_url]+old.get('sourceUrls',[])))
        e['provenance'].update(retainedRegistryId=cached,retainedEntrySha256=jsha(old),retainedModel2dSha256=sha(REG/old['model2dPath']),identityBasis='Exact cached graph independently compared to the named-identity expansion; source-specific stock, purity and role are bound separately.')
        q={'material_id':mid,'registry_id':cached,'graph_identity_matches':True,'cached_entry_snapshot':'reference-snapshots/entry-'+cached+'.json','source_specific_metadata_removed':True,'approval':'author_qualification_pending_independent_audit'}
        if old.get('model3dPath'):
            raw3=read(REG/old['model3dPath']); assert canon(graph_from_model(raw3))==canon(mol),(mid,'3d graph')
            assert raw3['coordinateUnits'].lower() in ['angstrom','angstroms','å']
            new=deepcopy(raw3)
            new.update(id=e['id'],name=e['name'],caption='Retained illustrative free-molecule conformer; not a measured molecule, solution species or surface-bound structure.',notes=['Atom, isotope, bond and coordinate arrays are unchanged from the retained reference. No source-specific grade or other-paper sample assignment is inherited.'])
            new['source']=deepcopy(raw3.get('source'))
            new['functionalGroups']=fg(graph_from_model(raw3))
            e['model3dPath']='models/'+e['id']+'-3d.json';save(e['model3dPath'],new)
            assert new['atoms']==raw3['atoms'] and new['bonds']==raw3['bonds']
            lengths=[]
            for b in new['bonds']:
                a,z=new['atoms'][b['a']],new['atoms'][b['b']]
                distance=math.sqrt(sum((a[k]-z[k])**2 for k in ['x','y','z']))
                assert .6<distance<2.4,(mid,distance);lengths.append(distance)
            assert all(math.isfinite(a[k]) for a in new['atoms'] for k in ['x','y','z'])
            q.update(model3d_sha256=sha(O/e['model3dPath']),retained_model3d_sha256=sha(REG/old['model3dPath']),atomic_arrays_unchanged=True,min_bond_A=min(lengths),max_bond_A=max(lengths),original_model_type=raw3.get('modelType'))
        qualifications.append(q)
    body=m2d(e,mol)
    render(e,frame(e,body,'2D connectivity reference · colored functional groups · no measured molecular geometry'))
    checks.append({'material_id':mid,'formula':formula,'computed_formula':calculated,'canonical_smiles':canon(mol),'net_charge':sum(a.GetFormalCharge() for a in mol.GetAtoms()),'atoms':mol.GetNumAtoms(),'bonds':mol.GetNumBonds(),'deuterium_atoms':sum(a.GetAtomicNum()==1 and a.GetIsotope()==2 for a in mol.GetAtoms()),'cached_identity':cached,'three_dimensional_reference':bool(e['model3dPath'])})
for mid,(name,formula,lines,limit) in SYMBOLS.items():
    e=identity(mid,formula,name,'symbolic_context')
    e['caption']='Symbolic source identity or specimen context. '+limit
    e['limitations']=[limit,'No atomic coordinates, bond network, ordered supercell or training structure label is supplied.']
    body='<rect x="105" y="165" width="890" height="345" rx="24" fill="#f4f8fa" stroke="#b6ccd9"/>'
    for j,line in enumerate(lines):body+=tx(550,245+j*80,line,30 if j==0 else 23,'#80519b' if j==0 else '#294558')
    render(e,frame(e,body,'Symbolic identity / context · no atomistic or dissolved-species model'))
    checks.append({'material_id':mid,'symbol_only':True,'atoms_generated':0,'bonds_generated':0,'source_formula':slots[mid][0][2]['formula'],'display_formula':formula})
by_mid={e['provenance']['sourceMaterialId']:e for e in entries}

# Retained primary identity/coordinate artifacts and computed-reference inputs.
# They are private provenance snapshots, not new retrievals or measurements.
primary_checks=[]
raw=M/'research-assets/quality-20260918/molecules/raw'
newraw=M/'research-assets/new-molecular-assets'
primary={
 'water':[raw/'water-properties.json',raw/'water-pubchem-2d.sdf',raw/'water-lookup.json'],
 'ethanol':[raw/'ethanol-properties.json',raw/'ethanol-pubchem-2d.sdf',raw/'ethanol-lookup.json'],
 'toluene':[raw/'toluene-properties.json',raw/'toluene-pubchem-2d.sdf',M/'research-assets/toluene-pubchem-1140-3d.sdf'],
 'methanol':[M/'research-assets/methanol-pubchem-887-3d.sdf'],
 'thf':[newraw/'thf-pubchem-identity.json',newraw/'thf-pubchem-8028-2d.sdf',newraw/'thf-pubchem-8028-3d.sdf',newraw/'thf-retrieval.json'],
 'chloroform':[raw/'chloroform-properties.json',newraw/'chloroform-pubchem-6212-2d.sdf',newraw/'chloroform-pubchem-6212-3d.sdf',newraw/'chloroform-retrieval.json']}
for mid,name in [('dmf','dimethylformamide'),('dmso','dimethyl-sulfoxide'),('dmso-d6','dimethyl-sulfoxide-d6')]:
    primary[mid]=[M/'research-assets/incoming-paper-monitor/reviews/cm970189m/molecular-assets/sdf'/(name+'-computed-illustrative-3d.sdf')]
for mid,paths in primary.items():
    for path in paths:
        assert path.is_file(),path
        out=snap(path,'primary/'+mid+'/'+path.name)
        row={'material_id':mid,'snapshot_path':str(out.relative_to(O)),'sha256':sha(out),'reference_type':'computed_reference' if 'computed-' in path.name else 'retained_PubChem_artifact'}
        if path.suffix=='.sdf':
            source_mol=Chem.SDMolSupplier(str(out),removeHs=False)[0];assert source_mol is not None
            assert canon(source_mol)==canon(Chem.MolFromSmiles(GRAPH[mid][0])),(mid,path,'retained SDF identity')
            row.update(graph_matches=True,formula=rdMolDescriptors.CalcMolFormula(source_mol,separateIsotopes=True,abbreviateHIsotopes=True))
        primary_checks.append(row)

# Exact quantity selections: only fields in the same canonical record/operation.
QMAP={
 ('precursor-preparation','cdcl2'):[('precursor-add','cdcl2_mass'),('precursor-add','cdcl2_amount')],
 ('precursor-preparation','nh4ptc'):[('precursor-add','nh4ptc_mass'),('precursor-add','nh4ptc_amount')],
 ('precursor-preparation','water'):[('precursor-add','cdcl2_water'),('precursor-add','nh4ptc_water'),('precursor-wash-dry','water_wash')],
 ('precursor-preparation','ethanol'):[('precursor-wash-dry','ethanol_wash_cycles'),('precursor-wash-dry','ethanol_each_wash')],
 ('precursor-crystallization','cdptc'):[('crystal-solution','printed_solution_amount')],
 ('decomposition-nmr','cdptc'):[('nmr-heat','precursor_mass'),('nmr-heat','printed_precursor_amount')],
 ('decomposition-nmr','dmso-d6'):[('nmr-heat','dmso_d6_mass')],
 ('decomposition-nmr','toluene'):[('nmr-isolate','wash_count'),('nmr-isolate','toluene_each_wash')],
 ('decomposition-thf','cdptc'):[('thf-heat','precursor_mass'),('thf-heat','printed_precursor_amount')],
 ('decomposition-thf','thf'):[('thf-heat','thf_volume')],
 ('decomposition-thf','toluene'):[('thf-wash','wash_count'),('thf-wash','toluene_each_wash')],
 ('excess-precursor-rt','cdptc'):[('rt-combine','saturated_concentration')],
 ('monolayer-shell','cdse-qb'):[('qb-wash','dispersion_aliquot_mass')],
 ('monolayer-shell','cdptc'):[('qb-shell','precursor_concentration'),('qb-shell','relative_estimated_monolayer_precursor')],
 ('monolayer-shell','thf'):[('qb-shell','thf_solution_volume'),('aliquot-thf','thf_dilution')],
 ('monolayer-shell','toluene'):[('qb-wash','toluene_per_cycle'),('qb-wash','total_cycles'),('aliquot-toluene-wash','toluene_wash')]}
def quantity_links(rid,pairs):
    out=[];r=records[rid]
    for op_id,key in pairs:
        i,op=next((i,op) for i,op in enumerate(r['operations']) if op['id']==op_id)
        out.append({'record_id':rid,'json_pointer':f'/operations/{i}/parameters/{key}','operation_id':op_id,'field':key,'quantity':deepcopy(op['parameters'][key])})
    return out
def qfmt(q):
    if q.get('value') is not None:
        value=q['value'];s=str(int(value)) if isinstance(value,(int,float)) and value==int(value) else str(value)
    else:s=f'{q.get("minimum")}–{q.get("maximum")}'
    return ('≈' if q.get('approximate') else '')+s+' '+q.get('unit','')
def slot_note(rid,mid,m,refs):
    branch=rid.replace('morrison-2017-','');s=f'{m["name"]}; source role: {m["role"].replace("_"," ")}; stage: {m["stage"].replace("_"," ")}.'
    if refs:s+=' Reported fields: '+'; '.join(x['field'].replace('_',' ')+': '+qfmt(x['quantity']) for x in refs)+'.'
    else:s+=' No material dose is independently assigned by this component card.'
    if mid=='cdse-qb' and branch=='monolayer-shell':s+=' The 0.512 g value is the starting dispersion aliquot, not dry CdSe mass.'
    if mid=='cdptc' and branch in ['decomposition-nmr','decomposition-thf']:s+=' The printed 12 mg / 0.003 mmol pair is retained as source-conflicted (C2), without a guessed correction.'
    if mid=='cdptc' and branch=='precursor-crystallization':s+=' Printed “20 mmol solution” is ambiguous (C3), not a reported 20 mM concentration.'
    if branch=='excess-precursor-hot':s+=' The approximate 40 mM value from the room-temperature control is not assigned to this heated experiment.'
    if mid in ['aniline','n-octylamine']:s+=' The conflicting catalyst names in C5 remain unresolved; a reference identity does not resolve that sample assignment.'
    return s
bindings={'schemaVersion':'1.0','source_id':'morrison2017','status':'author_proposal_pending_independent_molecular_audit','recordBindings':{},'bindingNotes':{},'binding_approved':False,'published':False,'eligible_training':False}
slot_rows=[]
for rid,r in records.items():
    if not r['materials']:continue
    bindings['recordBindings'][rid]={};bindings['bindingNotes'][rid]={}
    for i,m in enumerate(r['materials']):
        mid=m['id'];e=by_mid[mid];refs=quantity_links(rid,QMAP.get((rid.replace('morrison-2017-',''),mid),[]));caption=slot_note(rid,mid,m,refs)
        note={'record_id':rid,'material_id':mid,'json_pointer':f'/materials/{i}','canonical_record_sha256':inputs[str(C/(rid+'.json'))],'registry_id':e['id'],'entry_sha256':jsha(e),'canonical_identity':deepcopy(m),'quantity_links':refs,'viewOverrides':{'name':m['name'],'caption':caption,'limitations':deepcopy(e['limitations'])},'binding_approved':False,'source_specific_join':'Exact record/material pointer only; no cross-record dose, property, batch or structure join.'}
        bindings['recordBindings'][rid][mid]=e['id'];bindings['bindingNotes'][rid][mid]=note;slot_rows.append(note)

STOCK_SPEC={
 'cdcl2-aqueous':{'title':'Cadmium chloride aqueous feed','amounts':{'cdcl2':[('precursor-add','cdcl2_mass'),('precursor-add','cdcl2_amount')],'water':[('precursor-add','cdcl2_water')]},'summary':'98 mg (0.54 mmol) CdCl2 + 40 mL deionized water','limit':'Water charge, not independently measured final solution volume. No hydrate or dissolved complex assigned.'},
 'nh4ptc-aqueous':{'title':'Ammonium PTC aqueous feed','amounts':{'nh4ptc':[('precursor-add','nh4ptc_mass'),('precursor-add','nh4ptc_amount')],'water':[('precursor-add','nh4ptc_water')]},'summary':'200 mg (1.07 mmol) NH4PTC + 60 mL deionized water','limit':'No calibrated final stock concentration. Ligand salt upstream preparation remains cited-only.'},
 'cdptc-thf-crystal-feed':{'title':'Precursor crystallization solution','amounts':{'cdptc':[('crystal-solution','printed_solution_amount')],'thf':[]},'summary':'Cd(PTC)2 in THF; printed “20 mmol solution”','limit':'C3: the wording does not establish a 20 mM concentration or an independently known volume.'},
 'cdptc-dmso-excess':{'title':'Room-temperature excess-precursor solution','amounts':{'cdptc':[('rt-combine','saturated_concentration')],'dmso':[]},'summary':'Cd(PTC)2 in DMSO; approximately 40 mM','limit':'Absolute volume and precursor/core ratio are unreported. Do not transfer this value to the heated control.'},
 'cdptc-thf-shell':{'title':'THF precursor feed for shell growth','amounts':{'cdptc':[('qb-shell','precursor_concentration')],'thf':[]},'solution_amounts':[('qb-shell','thf_solution_volume')],'summary':'2 mL of 10 mM Cd(PTC)2 solution in THF','limit':'2 mL is solution volume, not a separately measured neat-THF charge. Exact CdSe core amount is unknown.'}}
stock_rows=[];solution_contexts=[]
for rid,r in records.items():
    for si,stock in enumerate(r['stocks']):
        spec=STOCK_SPEC[stock['id']];comps=[]
        for ci,component in enumerate(stock['components']):
            mid=component['material_id']; mi=next(i for i,m in enumerate(r['materials']) if m['id']==mid);e=by_mid[mid]
            comps.append({'material_id':mid,'registry_id':e['id'],'json_pointer':f'/stocks/{si}/components/{ci}','material_json_pointer':f'/materials/{mi}','source_quantities':deepcopy(component['quantities']),'quantity_links':quantity_links(rid,spec['amounts'][mid]),'binding_approved':False})
        row={'record_id':rid,'stock_id':stock['id'],'json_pointer':f'/stocks/{si}','canonical_record_sha256':inputs[str(C/(rid+'.json'))],'components':comps,'concentrations':deepcopy(stock['concentrations']),'scope':stock['scope'],'evidence':deepcopy(stock['evidence']),'solution_quantity_links':quantity_links(rid,spec.get('solution_amounts',[])),'display_summary':spec['summary'],'display_limit':spec['limit'],'binding_approved':False}
        stock_rows.append(row)
        ctx={'record_id':rid,'id':'morrison2017-'+stock['id'],'label':spec['title'],'scope':spec['summary']+'. '+spec['limit']+' Select components as references; the selector does not describe dissolved speciation.','components':[{'material_id':z['material_id'],'registry_id':z['registry_id'],'role':'solute' if ci==0 else 'solvent','label':r['materials'][int(z['material_json_pointer'].split('/')[-1])]['name'],'viewOverrides':{'caption':spec['summary']+'. '+spec['limit'],'limitations':[spec['limit'],'Component identity only; no dissolved complex or ion-pair geometry.']}} for ci,z in enumerate(comps)],'binding_approved':False}
        solution_contexts.append(ctx)
        body=wrapped(spec['summary'],45,151,86,22,30)
        for j,z in enumerate(comps):
            e=next(e for e in entries if e['id']==z['registry_id']);x=45+j*520
            body+=f'<rect x="{x}" y="212" width="490" height="197" rx="16" fill="#f1f7fa" stroke="#bdd1dd"/>'+tx(x+245,258,'Solute component' if j==0 else 'Solvent component',22)+tx(x+245,303,e['displayFormula'] or e['name'],24)
            values='; '.join(qfmt(a['quantity']) for a in z['quantity_links']) or 'No separate component dose specified'
            if stock['id']=='cdptc-thf-crystal-feed' and j==0:values='Printed, ambiguous: '+values
            body+=wrapped(values,x+20,347,43,18,24)
        body+=wrapped(spec['limit'],45,462,94,19,27)
        e={'name':spec['title'],'caption':ctx['scope'],'displayFormula':'Component selector • two separate reference identities'}
        svg=frame(e,body,'Formulation already described by the linked operation · not an additional charge or separate batch')
        (O/'stock-svg'/(stock['id']+'.svg')).write_text(svg,encoding='utf-8');raster(svg,O/'stock-previews'/(stock['id']+'.png'))

# Source-neutral retained coordinate previews, strictly illustrative projection.
for e in entries:
    if not e['model3dPath']:continue
    model=read(O/e['model3dPath']);atoms=model['atoms'];xy=[(a['x']+.32*a['z'],a['y']+.16*a['z']) for a in atoms]
    lo=[min(a[j] for a in xy) for j in [0,1]];hi=[max(a[j] for a in xy) for j in [0,1]]
    scale=min(800/max(hi[0]-lo[0],1),330/max(hi[1]-lo[1],1));points=[(150+(a[0]-lo[0])*scale,160+(a[1]-lo[1])*scale) for a in xy]
    body=''
    for b in model['bonds']:
        a,z=points[b['a']],points[b['b']];body+=f'<path d="M{a[0]} {a[1]} L{z[0]} {z[1]}" stroke="#9caeb9" stroke-width="6"/>'
    palette={'C':'#49697e','H':'#eaf2f6','O':'#e77372','N':'#648cce','S':'#d6b34c','Cl':'#70b186'}
    for a,(x,y) in zip(atoms,points):
        label=('D' if a.get('isotope')==2 and a['element']=='H' else a['element']);color=palette.get(a['element'],'#c49cc4')
        body+=f'<circle cx="{x}" cy="{y}" r="17" fill="{color}" stroke="#78909e"/>'+tx(x,y+5,label,14,'#172d39')
    svg=frame(e,body,'Projection of retained illustrative conformer · Å coordinate units · no measured or bound geometry')
    raster(svg,O/'conformer-previews'/(e['id']+'.png'))

assert len(entries)==29 and len(slot_rows)==64 and len(stock_rows)==5
assert sum(len(x['components']) for x in stock_rows)==10
assert sum(bool(e['model2dPath']) for e in entries)==18
assert sum(bool(e['model3dPath']) for e in entries)==9
assert sum(e['depictionKind']=='symbolic_context' for e in entries)==11
for e in entries:
    for field in ['model2dPath','model3dPath']:
        if not e[field]:continue
        model=read(O/e[field]);n=len(model['atoms']);b=len(model['bonds'])
        assert [a.get('index',i) for i,a in enumerate(model['atoms'])]==list(range(n))
        for x in model['bonds']:assert 0<=x['a']<n and 0<=x['b']<n and x['a']!=x['b']
        for g in model['functionalGroups']:
            assert all(0<=i<n for i in g['atomIndices']) and all(0<=i<b for i in g.get('bondIndices',[]))
        if field=='model2dPath':assert not model['has3D'] and all(a['z']==0 for a in model['atoms'])
for path,expected in inputs.items():assert sha(path)==expected,(path,'input changed during generation')
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'morrison2017','status':'private_author_proposal','entries':entries,'binding_approved':False})
save('bindings-proposal.json',bindings)
save('material-slot-map.json',{'schema':'mattersyn-molecular-slot-proposal/1','material_slot_count':64,'identity_count':29,'slots':slot_rows,'independent_audit':'pending'})
save('stock-component-map.json',{'schema':'mattersyn-stock-component-proposal/1','stock_count':5,'component_count':10,'stocks':stock_rows,'independent_audit':'pending'})
save('solution-components-proposal.json',{'schemaVersion':'1.0','contexts':solution_contexts,'binding_approved':False})
save('reference-qualification.json',{'status':'author_checks_only','cached_identity_count':10,'qualifications':qualifications,'retained_primary_artifacts':primary_checks,'rejected':[{'registry_id':'hexane','cached_name':'n-Hexane','source_name':'Hexane','reason':'Source isomer unspecified; no exact-isomer binding approved.'}],'normalization':'Ten source-scoped entries reuse identical cached connectivity; nine retain atom/bond/coordinate arrays unchanged with source-neutral model captions/notes. Other-paper grades and sample assignments are not copied into new display metadata.'})
save('reference-snapshots/manifest.json',{'snapshots':snapshots,'note':'Registry and reused assets are immutable private byte snapshots. Original absolute paths are audit-only metadata.'})
save('author-validation.json',{'schema':'mattersyn-molecule-author-validation/1','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'automated_author_checks_passed_manual_visual_check_pending','counts':{'entries':29,'material_slots':64,'stocks':5,'stock_components':10,'source_graph_models_2d':18,'retained_illustrative_3d':9,'symbolic_contexts':11,'new_named_graphs':8,'cached_graphs':10},'scientific_checks':checks,'supporting_checks':['Exact canonical-v1 and passed source-revision-2 audit hashes','Every current input remains unchanged','Named graph formula/charge/isotope and cached graph identity','Zero-based atom/bond/functional-group indices','Retained three-dimensional atom/bond/coordinate arrays unchanged','Finite Å coordinates and plausible reference bond ranges','Exact per-record quantity JSON pointers; approximation fields retained','Five stock definitions and ten exact component memberships','No 20 mmol to 20 mM conversion; no 40 mM cross-control transfer','No dry-core mass from dispersion aliquot; no precursor coordinates used for products'],'independent_scientific_audit':'pending','browser_validation':'not_claimed','binding_approved':False,'bound_files':inputs})
save('input-bindings.json',inputs)

for folder,prefix in [('previews','identities'),('stock-previews','stocks'),('conformer-previews','conformers')]:
    images=sorted((O/folder).glob('*.png'))
    for start in range(0,len(images),6):
        canvas=Image.new('RGB',(1500,1410),'#dce7ed');draw=ImageDraw.Draw(canvas)
        for j,p in enumerate(images[start:start+6]):
            im=Image.open(p).convert('RGB');im.thumbnail((730,425));x=10+(j%2)*750;y=30+(j//2)*470
            canvas.paste(im,(x,y));draw.text((x,y+430),p.stem.replace('morrison2017-',''),fill='#203a4b')
        canvas.save(O/'contacts'/f'{prefix}-{start//6+1:02}.png')
print(json.dumps({'entries':len(entries),'slots':len(slot_rows),'stocks':len(stock_rows),'models_2d':18,'models_3d':9,'symbolic':11,'status':'generated; manual visual check and freeze pending'}))
