"""Verified PubChem coordinate assets for the Murray 1993 example."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
identities={p['CID']:p for p in json.loads((ROOT/'murray1993-pubchem-identities.json').read_text())['PropertyTable']['Properties']}
specs=[('top','trioctylphosphine','Trioctylphosphine',20851,'2d'),
       ('topse','trioctylphosphine-selenide','Tri-n-octylphosphine selenide',12163534,'2d'),
       ('1-butanol','1-butanol','1-Butanol',263,'3d'),
       ('methanol','methanol','Methanol',887,'3d')]
results=[]
for ident,slug,name,cid,dim in specs:
    file=f'{slug}-pubchem-{cid}-{dim}.sdf'
    lines=(ROOT/file).read_text().splitlines()
    na,nb=int(lines[3][:3]),int(lines[3][3:6])
    atoms=[{'index':i,'element':s[31:34].strip(),'x':float(s[:10]),'y':float(s[10:20]),'z':float(s[20:30])} for i,s in enumerate(lines[4:4+na])]
    bonds=[{'a':int(s[:3])-1,'b':int(s[3:6])-1,'order':int(s[6:9])} for s in lines[4+na:4+na+nb]]
    counts=Counter(a['element'] for a in atoms)
    order=['C','H']+sorted(set(counts)-{'C','H'})
    formula=''.join(e+(str(counts[e]) if counts[e]>1 else '') for e in order if counts[e])
    assert formula==identities[cid]['MolecularFormula'],(ident,formula)
    assert any(abs(a['z'])>.001 for a in atoms)==(dim=='3d')
    if ident=='top':
        p=next(a['index'] for a in atoms if a['element']=='P')
        ids={p}
        for b in bonds:
            if b['a']==p: ids.add(b['b'])
            if b['b']==p: ids.add(b['a'])
        label='Tertiary phosphine center (P and adjacent carbons)'
    elif ident=='topse':
        ids={a['index'] for a in atoms if a['element'] in {'P','Se'}}
        label='Phosphine selenide headgroup (P-Se)'
        assert len(ids)==2
    else:
        o=next(a['index'] for a in atoms if a['element']=='O')
        ids={o}
        for b in bonds:
            other=b['b'] if b['a']==o else b['a'] if b['b']==o else None
            if other is not None and atoms[other]['element']=='H': ids.add(other)
        label='Hydroxyl (-OH)'
    groups=[{'label':label,'atomIndices':sorted(ids),'bondIndices':[i for i,b in enumerate(bonds) if b['a'] in ids and b['b'] in ids]}]
    entry={'id':ident,'name':name,'formula':formula,'iupacName':identities[cid]['IUPACName'],'pubchemCid':cid,
           'source':f'https://pubchem.ncbi.nlm.nih.gov/compound/{cid}',
           'sdfUrl':f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type={dim}',
           'assetFile':file,'indexConvention':'zero-based','representation':dim,'has3D':dim=='3d','allowRotation':dim=='3d',
           'coordinateUnits':'angstrom' if dim=='3d' else '2D depiction units; not physical distances',
           'modelType':'PubChem computed 3D conformer' if dim=='3d' else 'PubChem 2D connectivity depiction',
           'caption':'Computed 3D conformer; not an experimental structure or a unique solution-state geometry.' if dim=='3d' else '2D connectivity diagram; PubChem 3D coordinates unavailable.',
           'atoms':atoms,'bonds':bonds,'functionalGroups':groups}
    if ident=='top': entry['notes']=['PubChem3D endpoint returned 404. TOP has 21 rotatable bonds, above the usual PubChem3D limit of 15. No conformer was fabricated.']
    if ident=='topse': entry['notes']=['PubChem3D endpoint returned 404. PubChem states conformer generation is disallowed due to unsupported element and excessive flexibility.',
       'P-Se is encoded as order 2 in this PubChem 2D representation; no measured bond length is implied.',
       'This is a named-compound connectivity reference, not a complete or unique speciation model for selenium dissolved in TOP.']
    results.append(entry)
peng=json.loads((ROOT/'peng2000-molecular-structures.json').read_text())
results.extend(e for e in peng if e['id'] in {'topo','dimethylcadmium'})
assert len({e['id'] for e in results})==len(results)==6
(ROOT/'murray1993-molecular-structures.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
for e in results: print(e['id'],e['formula'],e['representation'],len(e['atoms']),e['functionalGroups'])
