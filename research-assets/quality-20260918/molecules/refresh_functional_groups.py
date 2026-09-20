"""Targeted annotation refresh; never rebuild bindings or molecular coordinates.

Loads only the builder's definitions and SMARTS literal, not its executable build.
Run with the existing Miniforge Python / task-local RDKit dependency.
"""
import sys, ast, json, hashlib, copy, math, html, collections, re
from pathlib import Path
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parents[1] / 'rdkit-runtime'))
import rdkit
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def highlights(gg):
    return ({i for g in gg for i in g['atomIndices']}, {i for g in gg for i in g['bondIndices']})

# Preserve every binding byte, including root's independently maintained revisions.
bindings_before = (OUT/'bindings.json').read_bytes()
tracked = [OUT/'registry.json', OUT/'molecules-3d.json'] + list((OUT/'models').glob('*.json')) + list((OUT/'svg').glob('*'))
before = {str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in tracked}
syntax = ast.parse((OUT/'build_registry.py').read_text(encoding='utf-8'))
definitions = [n for n in syntax.body if isinstance(n, ast.FunctionDef) or
    (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PATTERNS' for t in n.targets))]
exec(compile(ast.Module(body=definitions, type_ignores=[]), 'build_registry.py definitions only', 'exec'), globals())
assert all(Chem.MolFromSmarts(s) is not None for _,s in PATTERNS)

# Deliberate positive and negative examples for chemical class boundaries.
cases = [
    ('CP(=O)(O)O', {'Phosphonic acid'}, {'Phosphine oxide'}),
    ('CP(=O)(C)C', {'Phosphine oxide'}, {'Phosphonic acid'}),
    ('OP(=O)(O)O', set(), {'Phosphonic acid','Phosphine oxide'}),
    ('O=C([O-])[O-]', {'Carbonate'}, {'Carboxylate'}),
    ('CC(=O)[O-]', {'Carboxylate'}, {'Carbonate'}),
    ('O=C[O-]', {'Carboxylate'}, {'Carbonate'}),
    ('N', {'Ammonia'}, {'Amine nitrogen'}),
    ('CN', {'Amine nitrogen'}, {'Ammonia'}),
    ('CN(C)P(N(C)C)N(C)C', {'Aminophosphine head group'}, {'Amine nitrogen','Tertiary phosphine center'}),
    ('CP(C)C', {'Tertiary phosphine center'}, {'Aminophosphine head group'}),
    ('COC(=O)OC', set(), {'Ester'}),
    ('CC(=O)OC', {'Ester'}, set()),
]
for smi, present, absent in cases:
    labels={g['label'] for g in groups(Chem.MolFromSmiles(smi))}
    assert present <= labels and not absent & labels, (smi, labels, present, absent)

registry = read(OUT/'registry.json')
changes=[]; redrawn=[]; model_count=0; unchanged_geometry_count=0
for e in registry['entries']:
    prior=copy.deepcopy(e['functionalGroups']); model_changes=[]
    for key in ['model2dPath','model3dPath']:
        if not e.get(key): continue
        p=OUT/e[key]; m=read(p); oldgroups=copy.deepcopy(m['functionalGroups'])
        immutable=copy.deepcopy({k:v for k,v in m.items() if k!='functionalGroups'})
        mol=from_legacy(m)
        # Explicit-H ammonia needs the same chemical identity label as implicit-H 2D.
        gg=groups(mol)
        m['functionalGroups']=gg
        validate_model(copy.deepcopy(m),e)
        assert {k:v for k,v in m.items() if k!='functionalGroups'} == immutable
        unchanged_geometry_count+=1; model_count+=1
        if oldgroups!=gg:
            dump(p,m);model_changes.append(e[key])
        if key=='model2dPath':
            e['functionalGroups']=gg
            if highlights(oldgroups)!=highlights(gg) and not e.get('ionicFormulaComponents'):
                mol.GetConformer().Set3D(False)
                depiction(mol,e);redrawn.append(e['id'])
    if prior!=e['functionalGroups'] or model_changes:
        changes.append({'id':e['id'],'before':prior,'after':e['functionalGroups'],'modelPaths':model_changes})
    e['assetHashes']={k:sha(OUT/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}

dump(OUT/'registry.json', registry)
aggregate=read(OUT/'molecules-3d.json')
assert isinstance(aggregate,list)
for n,m in enumerate(aggregate):
    e=next(e for e in registry['entries'] if e['id']==m['id'])
    aggregate[n]=read(OUT/e['model3dPath'])
dump(OUT/'molecules-3d.json',aggregate)
assert (OUT/'bindings.json').read_bytes()==bindings_before

entries={e['id']:e for e in registry['entries']}
expectations={
    'tetradecylphosphonic-acid':(['Phosphonic acid'],['Phosphine oxide']),
    'hpa':(['Phosphonic acid'],['Phosphine oxide']),
    'topo':(['Phosphine oxide'],['Phosphonic acid']),
    'cesium-carbonate':(['Carbonate'],['Carboxylate']),
    'sodium-carbonate':(['Carbonate'],['Carboxylate']),
    'ammonia':(['Ammonia'],['Amine nitrogen']),
    'tris-diethylamino-phosphine':(['Aminophosphine head group'],['Amine nitrogen','Tertiary phosphine center']),
    'top':(['Tertiary phosphine center'],['Aminophosphine head group']),
    'tbp':(['Tertiary phosphine center'],['Aminophosphine head group']),
}
for id,(yes,no) in expectations.items():
    for key in ['model2dPath','model3dPath']:
        if not entries[id].get(key):continue
        labels={g['label'] for g in read(OUT/entries[id][key])['functionalGroups']}
        assert set(yes)<=labels and not set(no)&labels,(id,key,labels)

changed_files=[p for p,h in before.items() if sha(OUT/p)!=h]
public_changes=[p for p in changed_files if not p.endswith('-review.png')]
report={
    'status':'passed_pending_visual_review' if redrawn else 'passed',
    'scope':'Chemical functional-group annotation audit across the complete registry; no source recipe or geometry changes.',
    'rdkitVersion':rdkit.__version__, 'entriesAudited':len(entries),'modelsValidated':model_count,
    'positiveNegativeChemistryCases':len(cases),'modelsWithUnchangedNonGroupFields':unchanged_geometry_count,
    'changedChemicals':changes,'redrawnSvgIds':redrawn,
    'changedPublicAssets':[{'path':p,'sha256':sha(OUT/p)} for p in public_changes],
    'changedReviewRasters':[p for p in changed_files if p.endswith('-review.png')],
    'registrySha256':sha(OUT/'registry.json'),'aggregate3dSha256':sha(OUT/'molecules-3d.json'),
    'bindingsSha256':sha(OUT/'bindings.json'),'bindingsPreservedByteForByte':True,
    'limits':['The labels describe a reference connectivity graph, not measured solution speciation or ligand binding.','Full record-binding source hashes are maintained separately by the parent and were not rewritten by this bounded audit.']
}
dump(OUT/'functional-group-audit.json',report)
print(json.dumps({k:report[k] for k in ['status','entriesAudited','modelsValidated','positiveNegativeChemistryCases','redrawnSvgIds','registrySha256','bindingsSha256']},indent=2))
print('Changed IDs: '+', '.join(x['id'] for x in changes))
