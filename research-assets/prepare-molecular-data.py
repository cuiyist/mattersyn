"""Parse downloaded PubChem SDFs into browser-ready JSON; no geometry is generated."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMPOUNDS = [
    ('oleic-acid', 'Oleic acid', 445639, 'C18H34O2', '(9Z)-octadec-9-enoic acid'),
    ('oleylamine', 'Oleylamine', 5356789, 'C18H37N', '(9Z)-octadec-9-en-1-amine'),
    ('1-octadecene', '1-Octadecene', 8217, 'C18H36', 'octadec-1-ene'),
    ('myristic-acid', 'Myristic acid', 11005, 'C14H28O2', 'tetradecanoic acid'),
    ('2-propanol', '2-Propanol', 3776, 'C3H8O', 'propan-2-ol'),
    ('toluene', 'Toluene', 1140, 'C7H8', 'toluene'),
    ('methanol', 'Methanol', 887, 'CH4O', 'methanol'),
]

results = []
for slug, name, cid, formula, iupac in COMPOUNDS:
    path = ROOT / f'{slug}-pubchem-{cid}-3d.sdf'
    lines = path.read_text().splitlines()
    na, nb = int(lines[3][:3]), int(lines[3][3:6])
    atoms = []
    for i, line in enumerate(lines[4:4+na]):
        atoms.append({'index': i, 'element': line[31:34].strip(),
                      'x': float(line[:10]), 'y': float(line[10:20]), 'z': float(line[20:30])})
    bonds = [{'a': int(s[:3])-1, 'b': int(s[3:6])-1, 'order': int(s[6:9])}
             for s in lines[4+na:4+na+nb]]
    counts = Counter(a['element'] for a in atoms)
    reconstructed = ''.join(e + (str(counts[e]) if counts[e] > 1 else '') for e in ['C','H','N','O'] if counts[e])
    assert reconstructed == formula, (slug, reconstructed, formula)
    assert any(abs(a['z']) > 0.001 for a in atoms)
    alkene = [b for b in bonds if b['order'] == 2 and atoms[b['a']]['element'] == atoms[b['b']]['element'] == 'C']
    groups = []
    if slug in {'oleic-acid','oleylamine','1-octadecene'}:
        assert len(alkene) == 1
        groups = [{'label': 'Terminal alkene' if slug == '1-octadecene' else 'cis (Z) alkene',
                   'atomIndices': [alkene[0]['a'], alkene[0]['b']], 'bondIndices': [bonds.index(alkene[0])]}]
    if slug in {'oleic-acid','myristic-acid'}:
        oxygen_ids = [a['index'] for a in atoms if a['element'] == 'O']
        ids = set(oxygen_ids)
        for b in bonds:
            if b['a'] in oxygen_ids: ids.add(b['b'])
            if b['b'] in oxygen_ids: ids.add(b['a'])
        groups.insert(0, {'label': 'Carboxylic acid (-COOH)', 'atomIndices': sorted(ids),
                          'bondIndices': [i for i,b in enumerate(bonds) if b['a'] in ids and b['b'] in ids]})
    if slug == 'oleylamine':
        nitrogen = next(a['index'] for a in atoms if a['element'] == 'N')
        ids = {nitrogen}
        for b in bonds:
            other = b['b'] if b['a'] == nitrogen else b['a'] if b['b'] == nitrogen else None
            if other is not None and atoms[other]['element'] == 'H': ids.add(other)
        groups.insert(0, {'label': 'Primary amine (-NH2)', 'atomIndices': sorted(ids),
                          'bondIndices': [i for i,b in enumerate(bonds) if b['a'] in ids and b['b'] in ids]})
    if slug in {'2-propanol','methanol'}:
        oxygen = next(a['index'] for a in atoms if a['element']=='O')
        ids = {oxygen}
        for b in bonds:
            other=b['b'] if b['a']==oxygen else b['a'] if b['b']==oxygen else None
            if other is not None and atoms[other]['element']=='H': ids.add(other)
        groups.append({'label':'Hydroxyl (-OH)', 'atomIndices':sorted(ids),
                       'bondIndices':[i for i,b in enumerate(bonds) if b['a'] in ids and b['b'] in ids]})
    if slug == 'toluene':
        ids={a for b in alkene for a in [b['a'],b['b']]}
        assert len(ids)==6
        groups.append({'label':'Aromatic ring', 'atomIndices':sorted(ids),
                       'bondIndices':[i for i,b in enumerate(bonds) if b['a'] in ids and b['b'] in ids]})
    results.append({'id':slug,'name':name,'formula':formula,'iupacName':iupac,'pubchemCid':cid,
                    'source':f'https://pubchem.ncbi.nlm.nih.gov/compound/{cid}',
                    'sdfUrl':f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d',
                    'assetFile':path.name,'coordinateUnits':'angstrom','indexConvention':'zero-based',
                    'modelType':'PubChem computed 3D conformer',
                    'caption':'One computed molecular conformation; not an experimental structure or a unique solution-state shape.',
                    'atoms':atoms,'bonds':bonds,'functionalGroups':groups})

existing_path=ROOT/'molecular-structures.json'
if existing_path.exists():
    existing=json.loads(existing_path.read_text(encoding='utf-8'))
    existing_by_id={entry['id']:entry for entry in existing}
    # Preserve every existing entry exactly and append only new molecules.
    results=existing+[entry for entry in results if entry['id'] not in existing_by_id]
existing_path.write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
for entry in results:
    print(entry['name'], entry['formula'], len(entry['atoms']), 'atoms;', entry['functionalGroups'])
