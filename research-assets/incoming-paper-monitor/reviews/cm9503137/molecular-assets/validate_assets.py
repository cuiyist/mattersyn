"""Bounded independent serialized-asset checks and actual-SVG contact sheet."""
import sys,json,hashlib,re,math,collections,xml.etree.ElementTree as ET
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
SITE=Path('[local path redacted]')
EXISTING=SITE/'dist/assets/chemical-registry'
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import pymupdf
from PIL import Image,ImageDraw
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def counts(s):
    c=collections.Counter()
    for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',s):c[e]+=int(n or 1)
    return c
checks=[]
def check(p,label):
    checks.append({'check':label,'passed':bool(p)})
def reconstruct(model):
    rw=Chem.RWMol()
    for a in model['atoms']:
        x=Chem.Atom(a['element']);x.SetFormalCharge(a['formalCharge']);x.SetIsotope(a['isotope']);x.SetNoImplicit(True);x.SetNumExplicitHs(a['implicitHydrogenCount']);rw.AddAtom(x)
    for b in model['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,1.5:Chem.BondType.AROMATIC,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE}[b['order']])
    m=rw.GetMol();Chem.SanitizeMol(m);return m
registry=read(OUT/'registry-additions.json');new={e['id']:e for e in registry['entries']}
old={e['id']:e for e in read(EXISTING/'registry.json')['entries']}
check(len(new)==21 and not set(new)&set(old),'Twenty-one unique new identities; no overwrite or duplicate existing ID')
expected={'diethylzinc':{'C':4,'H':10,'Zn':1},'hydrogen-selenide':{'H':2,'Se':1},'nonane':{'C':9,'H':20},'acetonitrile':{'C':2,'H':3,'N':1}}
images=[]
for ident,e in new.items():
    check(e['pubchemCid'] is None,ident+' no invented external identifier')
    check(e['sourceUrls']==['https://doi.org/10.1021/cm9503137'],ident+' source identity provenance')
    for key,h in e['assetHashes'].items():check(sha(OUT/e[key])==h,ident+' '+key+' file hash')
    svg=(OUT/e['svgPath']).read_text(encoding='utf-8');ET.fromstring(svg)
    check(not re.search(r'<script|onload=|javascript:|(?:href|src)="https?://',svg,re.I),ident+' passive SVG')
    doc=pymupdf.open(stream=svg.encode(),filetype='svg');pdf=pymupdf.open('pdf',doc.convert_to_pdf());pix=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.8,.8),alpha=False)
    image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);images.append((ident,image))
    if e['depictionKind']!='molecule':
        check(not e['model2dPath'] and not e['model3dPath'],ident+' no guessed solid or polymer graph');continue
    reference=Chem.MolFromSmiles(e['provenance']['smiles'])
    for key in ['model2dPath','model3dPath']:
        m=read(OUT/e[key]);aa=m['atoms'];bb=m['bonds'];mol=reconstruct(m)
        check(counts(rdMolDescriptors.CalcMolFormula(mol))==expected[ident],ident+' '+key+' independently reconstructed formula')
        check(Chem.GetFormalCharge(mol)==0 and len(Chem.GetMolFrags(mol))==1,ident+' '+key+' charge and fragment count')
        check(Chem.MolToSmiles(Chem.RemoveHs(mol))==Chem.MolToSmiles(Chem.RemoveHs(reference)),ident+' '+key+' connectivity matches source identity')
        check([a['index'] for a in aa]==list(range(len(aa))) and all(math.isfinite(a[c]) for a in aa for c in ['x','y','z']),ident+' '+key+' atom indices and finite coordinates')
        check(len({tuple(sorted((b['a'],b['b']))) for b in bb})==len(bb) and all(0<=b['a']<len(aa) and 0<=b['b']<len(aa) and b['a']!=b['b'] for b in bb),ident+' '+key+' valid unique bonds')
        check(m.get('eligible_training') is False,ident+' '+key+' excluded from experimental labels')
        if key=='model2dPath':
            check(not m['has3D'] and not m['allowRotation'] and all(a['z']==0 for a in aa),ident+' drawing flags')
        else:
            check(m['has3D'] and m['allowRotation'] and m['coordinateSource']=='local-rdkit' and 'not a measured structure' in m['caption'],ident+' computed conformer flags and limitation')
            check(m['conformerGeneration']['minimizationReturnCode']==0 if ident!='diethylzinc' else m['conformerGeneration']['minimizationReturnCode'] is None and m['conformerGeneration']['forceField'] is None and 'unminimized' in m['caption'],ident+' truthful minimization status')
            distances=[math.dist([aa[b['a']][c] for c in ['x','y','z']],[aa[b['b']][c] for c in ['x','y','z']]) for b in bb]
            check(all(.45<d<2.9 for d in distances),ident+' plausible nonzero bond lengths')
            check(all(math.dist([aa[i][c] for c in ['x','y','z']],[aa[j][c] for c in ['x','y','z']])>.45 for i in range(len(aa)) for j in range(i)),ident+' no gross atomic overlap')
            check(all(a['implicitHydrogenCount']==0 for a in aa),ident+' explicit 3D hydrogen inventory')
            center={'diethylzinc':'Zn','hydrogen-selenide':'Se'}.get(ident)
            if center:
                atom=[a for a in aa if a['element']==center][0]
                check(sum(b['a']==atom['index'] or b['b']==atom['index'] for b in bb)==2,ident+' two central-atom bonds')
            sdf=Chem.MolFromMolFile(str(OUT/'sdf'/(ident+'-computed-illustrative-3d.sdf')),removeHs=False)
            check(Chem.MolToSmiles(Chem.RemoveHs(sdf))==Chem.MolToSmiles(Chem.RemoveHs(mol)),ident+' downloadable SDF connectivity round trip')
        for g in m['functionalGroups']:
            check(all(0<=i<len(aa) for i in g['atomIndices']) and all(0<=i<len(bb) for i in g['bondIndices']),ident+' functional-group indices')
for row in read(OUT/'reused-references.json')['entries']:
    check(row['id'] in old,row['id']+' reuse resolves')
    for key,path in row['assetPaths'].items():check(sha(EXISTING/path)==row['assetHashes'][key],row['id']+' reused hash unchanged '+key)
bindings=read(OUT/'bindings-additions.json');allentries={**old,**new}
for path in (OUT.parent/'canonical-drafts').glob('*.json'):
    r=read(path);rid=r['record_id'];mapped=bindings['recordBindings'][rid]
    check(set(mapped)=={m['id'] for m in r['materials']},rid+' complete exact material IDs')
    check(sha(path)==bindings['sourceRecordSha256'][rid],rid+' draft source hash')
    for material in r['materials']:
        check(mapped[material['id']] in allentries,rid+' '+material['id']+' valid registry binding')
        check(material.get('formula')==allentries[mapped[material['id']]].get('formula'),rid+' '+material['id']+' matching formula scope')
check(new['identity-butanol-unspecified-isomer']['model2dPath'] is None,'Butanol isomer remains unresolved')
check(new['identity-danek-rhodamine590']['formula'] is None,'Rhodamine 590 salt/formula remains unresolved')
check(new['identity-danek-electrospray-particle-options']['formula'] is None,'Alternative particle inputs not assigned a single formula')
check(len({bindings['recordBindings'][r]['dots'] for r in ['danek-1996-bare-dot-film','danek-1996-overcoated-dot-film','danek-1996-annealing-control','danek-1996-electrospray-dispersion']})==4,'Distinct particle/film-feed scope cards remain distinct')
check(bindings['recordBindings']['danek-1996-characterization']['si-wafer']=='identity-danek-silicon-wafer','XRF support does not inherit blanket (100) orientation')
check(len(bindings['recordBindings'])==12 and sum(map(len,bindings['recordBindings'].values()))==63,'All 12 records and 63 material bindings covered')
contact_paths=[]
for sheetnum in range((len(images)+7)//8):
    batch=images[sheetnum*8:sheetnum*8+8];height=((len(batch)+1)//2)*340
    sheet=Image.new('RGB',(1400,height),'white');draw=ImageDraw.Draw(sheet)
    for n,(ident,im) in enumerate(batch):
        x=(n%2)*700;y=(n//2)*340;draw.text((x+15,y+10),ident,fill='black');sheet.paste(im,(x+14,y+40))
    dest=OUT/'review'/('svg-contact-sheet-'+str(sheetnum+1)+'.png');sheet.save(dest);contact_paths.append(str(dest))
fail=[x['check'] for x in checks if not x['passed']]
report={'status':'passed' if not fail else 'failed','scope':'Bounded serialized molecular asset, identity, formula, connectivity, hash and record-binding checks. Visual SVG review separately recorded.','checkCount':len(checks),'errors':fail,'checks':checks,'registrySha256':sha(OUT/'registry-additions.json'),'bindingsSha256':sha(OUT/'bindings-additions.json')}
(OUT/'validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'errors':fail,'contactSheets':contact_paths}))
assert not fail
