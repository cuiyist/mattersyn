"""Prepare a private generator for explicit source-named free molecules only."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'molecular-assets';OUT.mkdir(exist_ok=True)
src=(ROOT.parent/'jp971091y/molecular-assets/build_assets.py').read_text(encoding='utf-8')
src=src.replace('Dabbousi1997','Veinot1997').replace('Dabbousi et al. 1997','Veinot et al. 1997').replace('10.1021/jp971091y','10.1021/cm970189m').replace('dac183303049a3275d4f1874c66ac0ceece9895bc175f7f7e9727ef7c9cd8f9d','eac4fe78e4bc3ab9c15e0409b69232e4294a0c07787d3ca650c378f6341d4adc')
pyrene='c1ccc2ccc3cccc4ccc1c2c34'
rows=[
 ('dmso','dimethyl-sulfoxide','Dimethyl sulfoxide','C2H6OS','CS(C)=O'),
 ('acetic-acid','acetic-acid','Acetic acid','C2H4O2','CC(=O)O'),
 ('hydroxythiophenol','4-hydroxythiophenol','4-Hydroxythiophenol','C6H6OS','Oc1ccc(S)cc1'),
 ('diethyl-ether','diethyl-ether','Diethyl ether','C4H10O','CCOCC'),
 ('imidazole','imidazole','Imidazole','C3H4N2','c1ncc[nH]1'),
 ('pyrene-acid','pyrene-1-carboxylic-acid','Pyrene-1-carboxylic acid','C17H10O2','O=C(O)'+pyrene),
 ('thionyl-chloride','thionyl-chloride','Thionyl chloride','Cl2OS','O=S(Cl)Cl'),
 ('butanoyl-chloride','butanoyl-chloride','Butanoyl chloride','C4H7ClO','CCCC(=O)Cl'),
 ('decanoyl-chloride','decanoyl-chloride','Decanoyl chloride','C10H19ClO','CCCCCCCCCC(=O)Cl'),
 ('benzoyl-chloride','benzoyl-chloride','Benzoyl chloride','C7H5ClO','O=C(Cl)c1ccccc1'),
 ('acetic-anhydride','acetic-anhydride','Acetic anhydride','C4H6O3','CC(=O)OC(C)=O'),
 ('butyric-anhydride','butyric-anhydride','Butyric anhydride','C8H14O3','CCCC(=O)OC(=O)CCC'),
 ('pyrene-acid-chloride','pyrene-1-carbonyl-chloride','Pyrene-1-carbonyl chloride','C17H9ClO','O=C(Cl)'+pyrene),
 ('acylimidazole-3a','n-acetylimidazole','N-Acetylimidazole','C5H6N2O','CC(=O)n1ccnc1'),
 ('acylimidazole-3b','n-butanoylimidazole','N-Butanoylimidazole','C7H10N2O','CCCC(=O)n1ccnc1'),
 ('acylimidazole-3c','n-pyrene-1-carbonylimidazole','N-Pyrene-1-carbonylimidazole','C20H12N2O','O=C(n1ccnc1)'+pyrene),
 ('acylimidazole-3d','n-benzoylimidazole','N-Benzoylimidazole','C10H8N2O','O=C(n1ccnc1)c1ccccc1'),
 ('acylimidazole-3e','n-decanoylimidazole','N-Decanoylimidazole','C13H22N2O','CCCCCCCCCC(=O)n1ccnc1'),
 ('dmso-d6','dimethyl-sulfoxide-d6','Dimethyl sulfoxide-d6','C2D6OS','[2H]C([2H])([2H])S(=O)C([2H])([2H])[2H]'),
 ('chloroform-d','chloroform-d','Chloroform-d','CDCl3','[2H]C(Cl)(Cl)Cl'),
 ('heavy-water','deuterium-oxide','Deuterium oxide','D2O','[2H]O[2H]'),
 ('dmf','dimethylformamide','Dimethylformamide','C3H7NO','CN(C)C=O')]
inventory=json.loads((ROOT/'chemical-identity-inventory.json').read_text(encoding='utf-8'))
inv={x['inventory_id']:x for x in inventory['items']}
molecules=[]
for mid,ident,name,formula,smiles in rows:
 note=inv[mid]['source_scope']+' Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'
 if 'pyrene' in ident:note+=' The substituent is at the source-named pyrene 1-position; the ring graph is checked against the original Scheme 1 and compound illustration.'
 if mid in ['dmso-d6','chloroform-d','heavy-water']:note+=' Deuterium positions are explicitly represented as hydrogen isotope 2; isotopic purity is not supplied.'
 if mid=='hydroxythiophenol':note+=' This free thiol is distinct from the sulfur-bound, deprotonated surface cap; its S–H bond must not be assigned to the nanocluster surface.'
 molecules.append((mid,ident,name,formula,smiles,note))
a=src.index('REUSE_MAP=');b=src.index('def groups(m):')
src=src[:a]+'REUSE_MAP={}\nREUSE=[]\nMOLECULES='+repr(molecules)+"\nCARDS=[]\nGROUPS=[('Phenolic hydroxyl','[OX2H]-[c]'),('Thiol','[SX2H]'),('Acyl group','[CX3](=O)'),('Imidazole ring','n1ccnc1'),('Sulfoxide','[S](=O)')]\n"+src[b:]
src=src.replace('rdMolDescriptors.CalcMolFormula(m))','rdMolDescriptors.CalcMolFormula(m,separateIsotopes=True,abbreviateHIsotopes=True))')
# When a complete force field is unavailable, retain and explicitly label distance geometry.
src=src.replace("if ident=='diethylzinc':\n        assert method is None", "if method is None:")
src=src.replace('RDKit reported no complete MMFF/UFF parameterization for Zn. Coordinates are an unminimized ETKDG distance-geometry illustration; no optimized Zn–C bond length or exact C–Zn–C angle is claimed.','RDKit reported no complete MMFF/UFF parameterization for this molecule. Coordinates are an unminimized ETKDG distance-geometry illustration; no optimized bond lengths or angles are claimed.')
a=src.index('for ident,name,formula,display,kind,note in CARDS:')
src=src[:a]+'''summary={'newMoleculeEntries':len(entries),'new2dModels':len(entries),'new3dModels':len(models),'allModelsIllustrative':True}
dump(OUT/'molecule-registry-proposal.json',{'schemaVersion':'1.0.0','assetPurpose':'Source-named free-molecule references; no Site changes; exact canonical bindings pending','entries':entries,'summary':summary})
dump(OUT/'molecules-3d-additions.json',models)
dump(OUT/'molecule-identity-map.json',{'inventoryToRegistry':mapping,'sourceDoi':'10.1021/cm970189m','sourceSha256':SOURCE_HASH,'bindingsStatus':'pending canonical material IDs'})
print(json.dumps(summary,indent=2))
'''
(OUT/'build_molecule_references.py').write_text(src,encoding='utf-8')
