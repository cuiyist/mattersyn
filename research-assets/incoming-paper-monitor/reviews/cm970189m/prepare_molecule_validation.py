from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'molecular-assets'
s=(ROOT.parent/'jp971091y/molecular-assets/validate_assets.py').read_text(encoding='utf-8')
s=s.replace("OUT/'registry-additions.json'","OUT/'molecule-registry-proposal.json'").replace('10.1021/jp971091y','10.1021/cm970189m')
s=s.replace('len(new)==17','len(new)==22').replace('Seventeen unique','Twenty-two unique')
s=s.replace("expected={'octane':{'C':8,'H':18}}","expected={e['id']:counts(e['formula']) for e in registry['entries']}")
s=s.replace('rdMolDescriptors.CalcMolFormula(mol))','rdMolDescriptors.CalcMolFormula(mol,separateIsotopes=True,abbreviateHIsotopes=True))')
a=s.index("for row in read(OUT/'reused-references.json')");b=s.index('contact_paths=[]',a)
s=s[:a]+'''for ident,count in [('dimethyl-sulfoxide-d6',6),('chloroform-d',1),('deuterium-oxide',2)]:
    for key in ['model2dPath','model3dPath']:
        m=read(OUT/new[ident][key])
        check(sum(a['element']=='H' and a['isotope']==2 for a in m['atoms'])==count,ident+' '+key+' explicit deuterium count')
for ident in ['pyrene-1-carboxylic-acid','pyrene-1-carbonyl-chloride','n-pyrene-1-carbonylimidazole']:
    m=Chem.MolFromSmiles(new[ident]['provenance']['smiles'])
    rings=list(m.GetRingInfo().AtomRings())
    check(sum(len(r)==6 for r in rings)==4,ident+' four fused six-member aromatic rings')
check('not a measured structure' in read(OUT/new['4-hydroxythiophenol']['model3dPath'])['caption'],'Free capping precursor is illustrative rather than a surface structure')
''' +s[b:]
s=s.replace(",'bindingsSha256':sha(OUT/'bindings-additions.json')",'')
(OUT/'validate_molecule_references.py').write_text(s,encoding='utf-8')
