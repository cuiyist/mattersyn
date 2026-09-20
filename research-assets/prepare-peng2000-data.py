"""Create Peng-2000 assets without inventing molecular 3D coordinates."""
import json, math
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
specs=[
 ('hexylphosphonic-acid','Hexylphosphonic acid','HPA',312552,'C6H15O3P','3d'),
 ('trioctylphosphine-oxide','Trioctylphosphine oxide','TOPO',65577,'C24H51OP','2d'),
 ('tributylphosphine','Tributylphosphine','TBP',13831,'C12H27P','3d'),
 ('dimethylcadmium','Dimethylcadmium','Cd(CH3)2',10479,'C2H6Cd','2d'),
]
identities={x['CID']:x for x in json.loads((ROOT/'peng2000-pubchem-identities.json').read_text())['PropertyTable']['Properties']}
results=[]
for slug,name,abbreviation,cid,formula,dim in specs:
    sourcefile=f'{slug}-pubchem-{cid}-{dim}.sdf'
    lines=(ROOT/sourcefile).read_text().splitlines()
    na,nb=int(lines[3][:3]),int(lines[3][3:6])
    atoms=[]
    for i,line in enumerate(lines[4:4+na]):
        atoms.append({'index':i,'element':line[31:34].strip(),'x':float(line[:10]),'y':float(line[10:20]),'z':float(line[20:30])})
    bonds=[{'a':int(s[:3])-1,'b':int(s[3:6])-1,'order':int(s[6:9])} for s in lines[4+na:4+na+nb]]
    counts=Counter(a['element'] for a in atoms)
    hill_order=['C','H']+sorted(e for e in counts if e not in {'C','H'})
    reconstructed=''.join(e+(str(counts[e]) if counts[e]>1 else '') for e in hill_order if counts[e])
    assert reconstructed==formula,(slug,reconstructed,formula)
    assert formula==identities[cid]['MolecularFormula']
    assert (any(abs(a['z'])>.001 for a in atoms))==(dim=='3d')
    groups=[]
    if slug!='dimethylcadmium':
        p=next(a['index'] for a in atoms if a['element']=='P')
        if slug=='hexylphosphonic-acid':
            ids={p}|{a['index'] for a in atoms if a['element']=='O'}
            oxy=set(ids)-{p}
            for b in bonds:
                other=b['b'] if b['a'] in oxy else b['a'] if b['b'] in oxy else None
                if other is not None and atoms[other]['element']=='H': ids.add(other)
            label='Phosphonic acid headgroup (-P(=O)(OH)2)'
        elif slug=='trioctylphosphine-oxide':
            ids={p}|{a['index'] for a in atoms if a['element']=='O'}
            label='Phosphine oxide headgroup (P=O)'
        else:
            ids={p}
            for b in bonds:
                if b['a']==p: ids.add(b['b'])
                if b['b']==p: ids.add(b['a'])
            label='Tertiary phosphine center (P-C3)'
        groups=[{'label':label,'atomIndices':sorted(ids),'bondIndices':[i for i,b in enumerate(bonds) if b['a'] in ids and b['b'] in ids]}]
    asset_id={'hexylphosphonic-acid':'hpa','trioctylphosphine-oxide':'topo','tributylphosphine':'tbp'}.get(slug,slug)
    entry={'id':asset_id,'name':name,'abbreviation':abbreviation,'formula':formula,
           'iupacName':identities[cid]['IUPACName'],'pubchemCid':cid,
           'source':f'https://pubchem.ncbi.nlm.nih.gov/compound/{cid}',
           'sdfUrl':f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type={dim}',
           'assetFile':sourcefile,'indexConvention':'zero-based','representation':dim,
           'has3D':dim=='3d','allowRotation':dim=='3d',
           'coordinateUnits':'angstrom' if dim=='3d' else '2D depiction units; not physical distances',
           'modelType':'PubChem computed 3D conformer' if dim=='3d' else 'PubChem 2D connectivity depiction',
           'caption':'Computed 3D conformer; not an experimental structure or a unique solution-state geometry.' if dim=='3d' else '2D connectivity diagram; 3D coordinates unavailable.',
           'atoms':atoms,'bonds':bonds,'functionalGroups':groups}
    if slug=='trioctylphosphine-oxide':
        entry['notes']=['PubChem 3D SDF endpoint returned 404. TOPO has 21 rotatable bonds; PubChem3D normally permits at most 15.',
                        'RDKit was not installed in the local miniforge Python; no local conformer was generated.',
                        'These flat 2D coordinates must not be presented as a 3D conformer.']
    if slug=='dimethylcadmium':
        entry.update({'representation':'formula-only','modelType':'2D chemical-connectivity schematic; no atomic coordinates claimed',
                      'caption':'Dimethylcadmium connectivity schematic; molecular 3D coordinates unavailable.',
                      'atoms':[],'bonds':[],'functionalGroups':[],
                      'coordinateUnits':None,'schematicFormula':'CH3–Cd–CH3',
                      'notes':['PubChem CID 10479 is standardized as [CH3-].[CH3-].[Cd+2], not a connected Cd-C molecule.',
                               'Its 3D generation is disallowed. The downloaded 2D SDF is retained for provenance only, not as the displayed molecular structure.',
                               'There are no valid source Cd-C bond indices to highlight; render the separate formula-only schematic.',
                               'Schematic connectivity is not a claim about bond lengths, angles, solvent coordination, or measured solid-state structure.'],
                      'additionalSource':'https://doi.org/10.1039/C6CC05851E'})
    results.append(entry)
(ROOT/'peng2000-molecular-structures.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')

# Existing experimental CdSe CIF: restore exact symmetry thirds, keeping measured z(Se).
cif=(ROOT/'cdse-wurtzite-cod-9016056.cif').read_text()
assert '_cell_length_a                   4.299' in cif
assert '_cell_length_c                   7.010' in cif
assert 'Se 0.33333 0.66667 0.37679' in cif
a,c,u=4.299,7.010,.37679
vectors=[[a,0,0],[-a/2,math.sqrt(3)*a/2,0],[0,0,c]]
basis=[{'element':'Cd','x':1/3,'y':2/3,'z':0},
       {'element':'Cd','x':2/3,'y':1/3,'z':.5},
       {'element':'Se','x':1/3,'y':2/3,'z':u},
       {'element':'Se','x':2/3,'y':1/3,'z':u+.5}]
crystal={'id':'cdse-wurtzite','name':'Wurtzite CdSe bulk reference','formula':'CdSe',
         'spaceGroup':'P63mc','spaceGroupNumber':186,'a':a,'b':a,'c':c,
         'alpha':90,'beta':90,'gamma':120,'formulaUnitsPerCell':2,
         'latticeVectors':vectors,'fractionalAtoms':basis,'coordinateUnits':'angstrom',
         'modelType':'Symmetry-expanded experimental bulk reference, COD 9016056',
         'caption':'Bulk wurtzite CdSe reference; nanorod shape and surface are illustrative.',
         'source':{'citation':'D. K. Freeman, S. L. Mair, Z. Barnea, The structure and Bijvoet ratios of cadmium selenide, Acta Crystallographica A33 (1977) 355-359',
                   'doi':'10.1107/S0567739477000977','url':'https://www.crystallography.net/cod/9016056.html',
                   'cifUrl':'https://www.crystallography.net/cod/9016056.cif','localCif':'cdse-wurtzite-cod-9016056.cif'},
         'notes':['Source CIF rounds one-third/two-thirds fractional coordinates to five decimals. Exact symmetry fractions are used in the expanded basis.',
                  'Measured Se internal coordinate u=0.37679 is preserved; this is not exact geometrically ideal wurtzite u=0.375.',
                  'The c-axis is the third lattice vector; a crop elongated along c is an illustrative nanorod geometry.',
                  'This is not the resolved atomic geometry of the nanorods in Peng et al. Nature 2000.',
                  'Ligand binding, surface reconstruction, defects, precursor speciation and growth dynamics are not provided by this bulk reference.']}
(ROOT/'peng2000-crystal-reference.json').write_text(json.dumps(crystal,indent=2)+'\n',encoding='utf-8')
for e in results: print(e['id'],e['formula'],e['representation'],len(e['atoms']),e['functionalGroups'])
print('Saved peng2000-crystal-reference.json, a=',a,'c=',c,'u=',u)
