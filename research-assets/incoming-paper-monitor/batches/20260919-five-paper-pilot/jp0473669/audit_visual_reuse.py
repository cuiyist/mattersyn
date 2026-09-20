"""Independent, read-only cached-reference checks; writes only private audit files."""
import collections
import datetime as dt
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

B = Path(__file__).resolve().parent
ROOT = B.parents[4]
R = ROOT / 'recipe-atlas/dist/assets/chemical-registry'
Q = ROOT / 'research-assets/quality-20260918/molecules'
TB = ROOT / 'research-assets/incoming-paper-monitor/reviews/j100108a019/molecular-assets'
EXPECTED_PLAN = 'b9751dabb6dd97068bce5bea101eee30243ddb2c05b08808d7aad183872c0a74'
checks = []
bound = {}


def check(label, condition, detail=None):
    checks.append({'check': label, 'passed': bool(condition), **({'detail': detail} if detail is not None else {})})


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(path, expected=None):
    path = Path(path)
    actual = sha(path)
    bound[str(path)] = actual
    if expected:
        check('SHA256 ' + str(path), actual == expected)
    return actual


def read(path):
    bind(path)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def pointer(obj, ptr):
    for part in ptr.lstrip('/').split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def sdf(path):
    bind(path)
    lines = Path(path).read_text().splitlines()
    n, m = int(lines[3][:3]), int(lines[3][3:6])
    atoms = []
    for line in lines[4:4+n]:
        charge_code = int(line[36:39])
        atoms.append({'element': line[31:34].strip(), 'formalCharge': {0:0, 1:3, 2:2, 3:1, 5:-1, 6:-2, 7:-3}.get(charge_code, 0), 'implicitHydrogenCount': 0})
    bonds = [{'a': int(x[:3])-1, 'b': int(x[3:6])-1, 'order': int(x[6:9])} for x in lines[4+n:4+n+m]]
    for line in lines[4+n+m:]:
        if line.startswith('M  CHG'):
            fields = list(map(int, line[6:].split()))
            for i in range(fields[0]):
                atoms[fields[1+2*i]-1]['formalCharge'] = fields[2+2*i]
    props = {match.group(1): match.group(2).strip() for match in re.finditer(r'>\s*<([^>]+)>\s*\n([^\n]*)', '\n'.join(lines))}
    return {'atoms': atoms, 'bonds': bonds, 'properties': props}


def formula(model):
    counts = collections.Counter(x['element'] for x in model['atoms'])
    counts['H'] += sum(x.get('implicitHydrogenCount', 0) for x in model['atoms'])
    return dict(sorted((k, v) for k, v in counts.items() if v))


def heavy_signature(model):
    heavy = [i for i, a in enumerate(model['atoms']) if a['element'] != 'H']
    order = {original: i for i, original in enumerate(heavy)}
    attached_h = {i: model['atoms'][i].get('implicitHydrogenCount', 0) for i in heavy}
    edges = []
    for bond in model['bonds']:
        a, b = bond['a'], bond['b']
        if a in order and b in order:
            edges.append((*sorted((order[a], order[b])), bond['order']))
        elif a in order and model['atoms'][b]['element'] == 'H':
            attached_h[a] += 1
        elif b in order and model['atoms'][a]['element'] == 'H':
            attached_h[b] += 1
    return ([ (model['atoms'][i]['element'], model['atoms'][i].get('formalCharge', 0), attached_h[i]) for i in heavy ], sorted(edges))


def inspect_model(mid, model, expected_formula):
    atoms, bonds = model['atoms'], model['bonds']
    check(mid + ' formula including explicit/implicit H', formula(model) == expected_formula)
    check(mid + ' total formal charge', sum(a['formalCharge'] for a in atoms) == 0)
    check(mid + ' zero-based indices', [a['index'] for a in atoms] == list(range(len(atoms))) and model['indexConvention'] == 'zero-based')
    for atom in atoms:
        check(f'{mid} atom {atom["index"]} finite coordinates', all(math.isfinite(atom[k]) for k in ('x', 'y', 'z')))
        check(f'{mid} atom {atom["index"]} no unsupported isotope', atom.get('isotope', 0) == 0)
    for i, bond in enumerate(bonds):
        check(f'{mid} bond {i} endpoints', 0 <= bond['a'] < len(atoms) and 0 <= bond['b'] < len(atoms) and bond['a'] != bond['b'])
        check(f'{mid} bond {i} single/no invented stereochemistry', bond['order'] == 1 and bond['stereo'] == 'STEREONONE')
    for group in model['functionalGroups']:
        check(mid + ' group atom indices ' + group['label'], all(0 <= i < len(atoms) for i in group['atomIndices']))
        check(mid + ' group bond indices ' + group['label'], all(0 <= i < len(bonds) for i in group['bondIndices']))
    if model['representation'] == '2d':
        check(mid + ' 2D units and controls', model['coordinateUnits'] == 'drawing units' and model['has3D'] is False and model['allowRotation'] is False and all(a['z'] == 0 for a in atoms))
    else:
        check(mid + ' 3D units and controls', model['coordinateUnits'] == 'angstrom' and model['has3D'] is True and model['allowRotation'] is True)
        check(mid + ' illustrative provenance', model['coordinateSource'] == 'local-rdkit' and 'not measured' in model['caption'] and 'not PubChem3D' in model['caption'])
        cg = model['conformerGeneration']
        check(mid + ' saved generation/convergence metadata', model['method'] == 'ETKDGv3 + MMFF94s' and cg['randomSeed'] == 20260918 and cg['embeddingStatus'] == 0 and cg['minimizationReturnCode'] == 0 and cg['minimizationStatus'] == 'converged')
        check(mid + ' energy limitation', 'not an experimental value or a global minimum' in cg['energyMeaning'])


plan = read(B / 'visual-preparation-plan.json')
check('Frozen plan SHA256', bound[str(B / 'visual-preparation-plan.json')] == EXPECTED_PLAN)
registry = read(R / 'registry.json')
check('Registry equals plan hash', bound[str(R / 'registry.json')] == plan['registry_sha256'])
entries = {x['id']: x for x in registry['entries']}
manifest = read(B / 'canonical-record-manifest.json')
bind(B / 'source-facts.json', manifest['source_facts_sha256'])
bind(B / 'source-inventory.json', manifest['source_inventory_sha256'])
bind(B / 'source-scientific-audit.json', manifest['source_extraction_audit_sha256'])
bind(B / 'canonical-records-audit.json', 'a91decb813ca2e729406a8e8c238f41c5b6f154dae9ae8efac7df60f1070d459')
bind(plan['reader_audit_path'], plan['reader_audit_sha256'])
for path, digest in manifest['source_pdf_hashes'].items():
    bind(path, digest)
records = {}
for rid, digest in plan['record_hashes'].items():
    path = B / 'canonical-drafts' / (rid + '.json')
    records[rid] = read(path)
    check(rid + ' frozen record hash', bound[str(path)] == digest)
for eid, entry in plan['candidate_registry_snapshots'].items():
    check(eid + ' exact registry snapshot', entries[eid] == entry)
for path, digest in plan['candidate_asset_hashes'].items():
    bind(path, digest)
check('All 13 canonical material slots inventoried exactly once', {(rid, f'/materials/{i}') for rid, r in records.items() for i, _ in enumerate(r['materials'])} == {(x['record_id'], x['json_pointer']) for x in plan['material_slots']} and len(plan['material_slots']) == 13)
check('Nine source material identities', len({x['source_material']['id'] for x in plan['material_slots']}) == 9)
for slot in plan['material_slots']:
    check(slot['record_id'] + slot['json_pointer'] + ' exact source material', pointer(records[slot['record_id']], slot['json_pointer']) == slot['source_material'])
    check(slot['record_id'] + slot['json_pointer'] + ' no binding approval', slot['binding_approved'] is False)
check('13 operation pointers inventoried; scene approval outside this audit', len(plan['operation_scenes']) == 13 and len({(x['record_id'], x['json_pointer']) for x in plan['operation_scenes']}) == 13)
for scene in plan['operation_scenes']:
    op = pointer(records[scene['record_id']], scene['json_pointer'])
    check(scene['operation_id'] + ' scene points to exact operation', op['id'] == scene['operation_id'])
    check(scene['operation_id'] + ' no scene approval', scene['scene_approved'] is False)
    for source_key, op_key in [('parameters_from_canonical', 'parameters'), ('environment_from_canonical', 'environment'), ('endpoint_from_canonical', 'endpoint')]:
        check(scene['operation_id'] + ' ' + op_key + ' preserved', scene[source_key] == op[op_key])

catalog = {x['id']: x for x in read(Q / 'source-catalog.json')}
geometry = {}
for eid, cid, expected_formula, smiles in [('ethanol', 702, {'C':2,'H':6,'O':1}, 'CCO'), ('water', 962, {'H':2,'O':1}, 'O')]:
    e = entries[eid]
    props_path = Q / 'raw' / (eid + '-properties.json')
    sdf_path = Q / 'raw' / (eid + '-pubchem-2d.sdf')
    props = read(props_path)['PropertyTable']['Properties'][0]
    lookup = read(Q / 'raw' / (eid + '-lookup.json'))
    raw = sdf(sdf_path)
    check(eid + ' cached properties identity', props['CID'] == cid and props['MolecularFormula'] == e['formula'] and props['SMILES'] == smiles and props['IUPACName'] == e['iupacName'])
    check(eid + ' cached lookup CID', lookup['IdentifierList']['CID'] == [cid])
    check(eid + ' retained SDF CID/formula', raw['properties']['PUBCHEM_COMPOUND_CID'] == str(cid) and raw['properties']['PUBCHEM_MOLECULAR_FORMULA'] == e['formula'] and formula(raw) == expected_formula)
    check(eid + ' raw cache provenance hashes', sha(props_path) == e['provenance']['sourcePropertiesSha256'] == catalog[eid]['propertiesSha256'] and sha(sdf_path) == e['provenance']['source2dSha256'] == catalog[eid]['sdfSha256'])
    check(eid + ' catalog metadata', catalog[eid]['pubchemCid'] == cid and catalog[eid]['fetchStatus'] == 'verified_api_record' and catalog[eid]['properties'] == props)
    models = {}
    for rep in ['2d', '3d']:
        mid = eid + '-' + rep
        models[rep] = read(R / 'models' / (mid + '.json'))
        inspect_model(mid, models[rep], expected_formula)
        check(mid + ' heavy-atom graph and attached H match raw SDF', heavy_signature(models[rep]) == heavy_signature(raw))
        check(mid + ' registry identity', models[rep]['formula'] == e['formula'] and models[rep]['pubchemCid'] == cid)
        check(mid + ' group metadata matches registry', models[rep]['functionalGroups'] == e['functionalGroups'])
        original = Q / 'models' / (mid + '.json')
        bind(original)
        check(mid + ' retained generation copy matches current', sha(original) == sha(R / 'models' / (mid + '.json')))
    expected_groups = [{'label':'Alcohol group','atomIndices':[0,1],'bondIndices':[0]}] if eid == 'ethanol' else []
    check(eid + ' chemically scoped functional groups', e['functionalGroups'] == expected_groups)
    atoms = models['3d']['atoms']
    coords = [(a['x'], a['y'], a['z']) for a in atoms]
    distances = []
    for i, bond in enumerate(models['3d']['bonds']):
        a, b = bond['a'], bond['b']
        length = math.dist(coords[a], coords[b])
        pair = tuple(sorted((atoms[a]['element'], atoms[b]['element'])))
        limits = {('C','C'):(1.2,1.7),('C','O'):(1.1,1.6),('C','H'):(0.8,1.2),('H','O'):(0.7,1.2)}[pair]
        check(f'{eid} computed bond {i} plausible nondegenerate distance', limits[0] <= length <= limits[1])
        distances.append({'atom_indices':[a,b], 'elements':list(pair), 'distance_angstrom':length})
    check(eid + ' computed atoms do not coincide', all(math.dist(coords[i], coords[j]) > 0.5 for i in range(len(coords)) for j in range(i)))
    geometry[eid] = {'bonds':distances, 'scope':'Independent calculation from retained locally computed coordinates; no experimental geometry or regenerated conformer.'}
    if eid == 'water':
        vectors = [[coords[i][k] - coords[0][k] for k in range(3)] for i in [1,2]]
        cosine = sum(x*y for x,y in zip(*vectors)) / (math.sqrt(sum(x*x for x in vectors[0])) * math.sqrt(sum(x*x for x in vectors[1])))
        geometry[eid]['computed_HOH_angle_degrees'] = math.degrees(math.acos(cosine))
    bind(Q / 'svg' / (eid + '.svg'))
    check(eid + ' retained SVG matches current SVG', sha(Q / 'svg' / (eid + '.svg')) == sha(R / 'svg' / (eid + '.svg')))
    bind(Q / 'actual-svg-review' / (eid + '.png'))

svg_text = {}
for eid in plan['candidate_registry_snapshots']:
    tree = ET.fromstring((R / entries[eid]['svgPath']).read_text(encoding='utf-8'))
    svg_text[eid] = [{'tag':x.tag.rsplit('}',1)[-1], 'text':''.join(x.itertext()).strip()} for x in tree.iter() if x.tag.rsplit('}',1)[-1] in ['title','desc','text']]
    check(eid + ' SVG title/description present', all(any(x['tag'] == tag for x in svg_text[eid]) for tag in ['title','desc']))
for eid in ['ethanol','water']:
    text = ' '.join(x['text'] for x in svg_text[eid]) + entries[eid].get('caption', '')
    check(eid + ' displayed reference caption has no supplier or unrelated paper grade', all(word.lower() not in text.lower() for word in ['Milli-Q','Merck','70%','97%','Stowell','Yi et al']))
check('Water broad lookup alias is not source-grade evidence', 'Milli-Q water' in entries['water']['aliases'])

eid = 'tetrabutylammonium-bromide'
e = entries[eid]
model = read(R / e['model2dPath'])
inspect_model(eid, model, {'Br':1,'C':16,'H':36,'N':1})
props_path = TB / 'raw' / (eid + '-properties.json')
sdf_path = TB / 'raw' / (eid + '-pubchem-2d.sdf')
props = read(props_path)['PropertyTable']['Properties'][0]
read(TB / 'raw' / (eid + '-lookup.json'))
raw = sdf(sdf_path)
check('TBAB cached CID/formula', props['CID'] == 74236 and props['MolecularFormula'] == 'C16H36BrN' and e['formula'] == 'C16H36BrN')
check('TBAB provenance hashes', sha(props_path) == e['provenance']['sourcePropertiesSha256'] and sha(sdf_path) == e['provenance']['source2dSha256'])
check('TBAB graph equals cached SDF', heavy_signature(model) == heavy_signature(raw))
adj = {i:set() for i in range(len(model['atoms']))}
for bond in model['bonds']:
    adj[bond['a']].add(bond['b']); adj[bond['b']].add(bond['a'])
check('TBAB bromide is charged/disconnected, not hydroxide', model['atoms'][0]['element'] == 'Br' and model['atoms'][0]['formalCharge'] == -1 and not adj[0] and all(a['element'] != 'O' for a in model['atoms']))
check('TBAB quaternary N+', model['atoms'][1]['element'] == 'N' and model['atoms'][1]['formalCharge'] == 1 and len(adj[1]) == 4)
chains=[]
for start in adj[1]:
    seen={1}; todo=[start]; branch=set()
    while todo:
        i=todo.pop()
        if i in seen: continue
        seen.add(i); branch.add(i); todo.extend(adj[i]-seen)
    chains.append(branch)
check('TBAB four independent n-butyl chains', len(chains) == 4 and all(len(c) == 4 and all(model['atoms'][i]['element']=='C' for i in c) for c in chains) and len(set.union(*chains)) == 16 and all(len(adj[i]) <= 2 for i in set.union(*chains)))
check('TBAB no 3D salt geometry', not e.get('model3dPath') and model['has3D'] is False)
bind(TB / 'review' / (eid + '.png'))
bind(TB / 'svg' / (eid + '.svg'))
check('TBAB retained/current SVG equality', sha(TB / 'svg' / (eid + '.svg')) == sha(R / e['svgPath']))

support = entries['identity-carbon-coated-copper-tem-grid-b47959']
nitric = entries['identity-yi-nitric-acid']
check('Support is nonmolecular with other-paper provenance', support['depictionKind']=='support' and not support.get('model2dPath') and not support.get('model3dPath') and any('nl050648f' in x for x in support['sourceUrls']))
check('Nitric acid is formula-only with other-paper provenance', nitric['formula']=='HNO3' and nitric['depictionKind']=='formula' and not nitric.get('model2dPath') and not nitric.get('model3dPath') and any('cm0115416' in x for x in nitric['sourceUrls']))

slot_results=[]
for slot in plan['material_slots']:
    mid=slot['source_material']['id']
    status='pending_missing_qualified_depiction'
    reason=slot['required_scope']
    if mid in ['ethanol','hydrolysis-water','dialysis-water']:
        status='qualified_cached_reference_only'
        extra={
            'ethanol':'Retain source name Absolute ethanol and supplier Merck; amount is unreported. The neutral ethanol reference does not establish solution or surface geometry.',
            'hydrolysis-water':'Hydrolysis-water grade is unreported. Do not inherit Milli-Q or deionized grade. Preserve the approximate 500:1 water/Sn ratio with its unspecified basis and unreported dose/order/rate.',
            'dialysis-water':'The source explicitly identifies deionized dialysis water. Do not infer Milli-Q, volume, membrane, schedule, duration or endpoint. Keep this slot separate from hydrolysis water.'}
        reason=extra[mid]
    elif mid=='carbon-copper-grid':
        status='rejected_unchanged_entry_template_only'
        reason='Existing entry is explicitly sourced to Stowell (10.1021/nl050648f). Its source-neutral support SVG can be considered as a template only after Ribeiro metadata is supplied and checked. No mesh, Formvar, thickness or atomic geometry is transferable.'
    elif mid=='nitric-acid':
        status='rejected_unchanged_entry_template_only'
        reason='Existing entry is explicitly sourced to Yi (10.1021/cm0115416); HNO3 formula/counts are correct but the disconnected atom-count diagram is not qualified molecular connectivity. A template adaptation must retain Synth dilute nitric acid, unreported concentration/dose, unresolved aqueous species and separate water roles.'
    elif mid=='tbaoh-aqueous':
        status='rejected_wrong_counterion'
        reason='Cached TBAB is C16H36BrN, with disconnected Br− and four n-butyl chains on N+. Ribeiro reports aqueous tetrabutylammonium hydroxide (J. T. Baker, 0.4 mol/L stock). It cannot be bound as this reagent; no Br/OH substitution, solvent structure or final pH may be inferred. A cation fragment would require a separately qualified component depiction.'
    slot_results.append({'record_id':slot['record_id'],'json_pointer':slot['json_pointer'],'material_id':mid,'source_name':slot['source_material']['name'],'candidate_registry_ids':slot['candidate_registry_ids'],'status':status,'reference_qualification_only':True,'binding_approved':False,'reason':reason,'required_scope_from_plan':slot['required_scope']})

counts=dict(collections.Counter(x['status'] for x in slot_results))
check('All 13 dispositions and zero final binding approvals', len(slot_results)==13 and not any(x['binding_approved'] for x in slot_results))
check('Expected bounded scope counts', counts=={'pending_missing_qualified_depiction':7,'qualified_cached_reference_only':3,'rejected_unchanged_entry_template_only':2,'rejected_wrong_counterion':1})
bind(Path(__file__))
for path,digest in list(bound.items()):
    check('Input unchanged at close ' + path, sha(path)==digest)
failures=[x for x in checks if not x['passed']]
report={
    'schema':'mattersyn-cached-visual-reuse-audit/1',
    'source_id':'ribeiro2004', 'source_doi':'10.1021/jp0473669',
    'auditor':'/root/backlog_eta', 'candidate_plan_author':'/root',
    'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
    'status':'passed_bounded_reference_qualification' if not failures else 'failed_checks',
    'scope':'Independent qualification of cached reference candidates, not final source binding, new asset generation, apparatus audit, browser approval or promotion.',
    'source_scope':'Local main paper only; SI unverified. Existing passed source, canonical and reader audits are dependencies, not repeated full-source reviews in this task.',
    'counts':{'material_slots':13,'source_material_identities':9,'canonical_records':11,'planned_operation_scenes_pointer_checked_only':13,'candidate_registry_entries':5,'candidate_asset_files':10,'qualified_reference_identities':2,'qualified_reference_slots':3,'rejected_unchanged_entry_slots':3,'pending_no_qualified_candidate_slots':7,'final_binding_approvals':0,'new_assets':0,'mechanical_checks':len(checks),'failures':len(failures),'bound_files':len(bound)},
    'disposition_counts':counts,
    'qualified_reference_identities':['ethanol','water'],
    'manual_review':{
        'cached_pngs_actually_viewed':[str(Q/'actual-svg-review/ethanol.png'),str(Q/'actual-svg-review/water.png'),str(TB/'review/tetrabutylammonium-bromide.png')],
        'svg_markup_read':list(plan['candidate_registry_snapshots']),
        'support_and_nitric_visual_scope':'SVG labels/description/primitive structure inspected from retained markup; no new rendering or browser approval claimed.',
        'chemistry':'Inspected PubChem cached properties, CID lookups, raw V2000 connectivity, model atoms/bonds/implicit H, charge, functional-group indices, source/coordinate provenance and captions. Ethanol has no stereocentre or alkene stereochemistry; water has none. TBAB bromide is not the hydroxide counterion.',
        'geometry_limit':'Computed coordinates and derived distances are reference-model checks only. Water model angle is reported as computed (about 103.978°), not asserted to be an experimental value; no optimization or generation was performed.',
        'scene_limit':'13 operation pointers and saved canonical parameters/environment/endpoint were checked for exact equality only; no apparatus asset or scene scientific approval.'},
    'slot_dispositions':slot_results,
    'reference_geometry':geometry,
    'svg_labels_and_captions':svg_text,
    'candidate_registry_snapshots':plan['candidate_registry_snapshots'],
    'preserved_constraints':[
        'Water lookup alias Milli-Q water is not evidence of the Ribeiro water grade. Hydrolysis water (grade unreported) and deionized dialysis water remain distinct source-role bindings.',
        'Absolute ethanol, Merck, and role-specific missingness belong to the Ribeiro binding, not a universal molecule caption.',
        'Support and nitric-acid entries cannot carry another paper’s DOI/record provenance into Ribeiro unchanged. Formula-only nitric acid does not provide atomistic connectivity or 3D.',
        'Tetrabutylammonium bromide remains rejected as tetrabutylammonium hydroxide. A matching cation alone does not qualify the complete salt/reagent.',
        'SnCl2·2H2O hydration count must be explicit; no local candidate is qualified here. Sn(OH)4 remains an author-proposed intermediate, not measured species geometry.',
        'All five SnO2 material contexts remain separate specimens. Source prose mentions cassiterite/XRD, but supplies no trace here, SAED, lattice parameters, CIF or atomic coordinates. No fake structure or training sample join is approved.',
        'All 13 final material bindings and 13 apparatus scenes remain unapproved. No model generation, network lookup, download, Site/global ledger/canonical/reader/source edit occurred.'
    ],
    'bound_files_sha256':bound,'checks':checks,'failures':failures
}
(B/'visual-reuse-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=[
    '# Ribeiro cached visual-reference qualification', '',
    '**Result:** '+report['status']+'. This is cached-reference qualification only; final visual bindings, apparatus scenes and browser approval remain pending.', '',
    'All 13 material slots across 9 source identities and 11 frozen canonical records are accounted for. Ethanol and water qualify as source-neutral molecular references for 3 slots. Three unchanged candidate entries are rejected; 7 slots still lack a qualified depiction. No asset was generated and no source, canonical, reader, Site or ledger file was changed.', '',
    'Ethanol (PubChem CID 702, C2H6O) and water (CID 962, H2O) match retained PubChem properties, explicit-H SDF connectivity and current models. The 2D drawings use drawing units; 3D files use angstroms and explicitly identify locally computed illustrative conformers. Ethanol C–O/C–C distances are approximately 1.420/1.515 Å. Water O–H distances are approximately 0.969 Å and its computed H–O–H angle is 103.978°; these are checks of the cached model, not experimental molecular measurements.', '',
    'The ethanol binding must retain Absolute ethanol / Merck. Hydrolysis water has unreported grade and must not inherit the registry’s Milli-Q alias or the dialysis-water grade. The separate dialysis slot explicitly uses deionized water. Neither the approximate 500:1 ratio nor its unspecified basis establishes a water volume or addition schedule.', '',
    'The carbon-coated copper-grid entry carries Stowell provenance, and the nitric-acid formula entry carries Yi provenance. They are rejected as unchanged complete entries; their generic artwork can only be considered as templates after source-specific metadata qualification. HNO3 atom counts do not qualify molecular connectivity. Tetrabutylammonium bromide (C16H36BrN; Br−) is the wrong counterion for aqueous TBAOH and remains rejected.', '',
    'Pending depictions cover SnCl2·2H2O, proposed Sn(OH)4, and five distinct SnO2 specimen contexts. Hydration, author-model status and source-specific specimen boundaries must survive later work. This paper’s main-only scope does not establish a supplied XRD trace, SAED, lattice parameters, CIF or atomic geometry.', '',
    'Actual visual inspection covered the retained ethanol, water and TBAB PNGs, with matching current SVG hashes; all five SVG titles/descriptions/labels were read. Support and nitric-acid SVG markup was inspected without claiming newly rendered or browser-tested output. Mechanical checks separately verify source/plan/record/cache/asset hashes, all 13 slot pointers, all 13 scene pointers and copied canonical fields, formula/charge/graph/H counts, model indices/groups/units and computed geometry.', '',
    '| Record / material | Disposition |', '|---|---|']
for item in slot_results:
    lines.append('| '+item['record_id']+' / '+item['material_id']+' | '+item['status']+' |')
lines += ['', f"Validation: {len(checks)} checks, {len(failures)} failures; {len(bound)} exact file hashes retained in the JSON audit. Candidate plan SHA256: `{EXPECTED_PLAN}`.", '',
          'No final binding, apparatus, browser, publication or training approval is conferred by this report. The local main paper is the source scope; supporting information remains unverified.', '']
(B/'visual-reuse-audit.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'status':report['status'],'counts':report['counts'],'failures':failures,'audit_sha256':sha(B/'visual-reuse-audit.json'),'markdown_sha256':sha(B/'visual-reuse-audit.md')},ensure_ascii=False,indent=2))
raise SystemExit(bool(failures))
