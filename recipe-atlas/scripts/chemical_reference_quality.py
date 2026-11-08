"""Read-only publication checks for the presentation-only chemical overlay.

Called by the existing Audit.chemicals phase. Original registry checks remain
unchanged. Audit.asset provides the same containment, existence and SHA checks
used for every existing molecular/crystal asset.
"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

from chemical_reference_overlay import enrich_registry
import chemical_reference_identity as identity_rules
import h4_named_ligand_references as named_ligands


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _simple_bulk_formula(formula):
    if not isinstance(formula, str):return False
    parts = re.findall(r'([A-Z][a-z]?)(\d*)', formula)
    elements = {element for element, number in parts}
    cations = {'B','Si','Ge','Al','Ga','In','Sn','Pb','Li','Na','K','Rb','Cs','Be','Mg','Ca','Sr','Ba','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Y','Zr','Nb','Mo','Ru','Rh','Pd','Ag','Cd','La','Ce','Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg','Bi'}
    return ''.join(element + number for element, number in parts) == formula and len(elements) == 2 and bool(elements & cations) and bool(elements & {'O','S','Se','Te','As','Sb','P','N','C'})


def molecular_model_errors(model):
    """The established coordinate/bond/group checks plus independent geometry."""
    errors = []
    if not isinstance(model, dict):
        return ['model is not an object']
    if _simple_bulk_formula(model.get('formula')):
        errors.append('neutral binary solid cannot use a gas-phase molecular substitute; apply the existing ambient-reference policy')
    atoms, bonds = model.get('atoms'), model.get('bonds', [])
    if not isinstance(atoms, list) or len(atoms) < 2:
        return ['molecular reference needs at least two atoms']
    for atom in atoms:
        if not isinstance(atom, dict) or not re.fullmatch(r'[A-Z][a-z]?', str(atom.get('element', atom.get('elem', '')))):
            errors.append('invalid atom element')
        if not isinstance(atom, dict) or not all(_number(atom.get(k)) for k in ('x', 'y', 'z')):
            errors.append('nonfinite/missing atom coordinate')
    if not isinstance(bonds, list):
        return errors + ['bonds is not an array']
    graph = [set() for _ in atoms]
    seen = set()
    for bond in bonds:
        if not isinstance(bond, dict) or not all(type(bond.get(k)) is int and 0 <= bond[k] < len(atoms) for k in ('a', 'b')):
            errors.append('bond endpoint outside atom list')
            continue
        a, b = bond['a'], bond['b']
        edge = tuple(sorted((a, b)))
        if a == b or edge in seen:
            errors.append('self/duplicate bond')
        seen.add(edge)
        if not _number(bond.get('order')) or not 0 < bond['order'] <= 3:
            errors.append('invalid bond order')
        graph[a].add(b); graph[b].add(a)
    visited, pending = set(), [0]
    while pending:
        index = pending.pop()
        if index not in visited:
            visited.add(index); pending.extend(graph[index] - visited)
    if len(visited) != len(atoms):
        errors.append('disconnected atoms have relative geometry; use independent component references')
    groups = model.get('functionalGroups', [])
    if not isinstance(groups, list):
        errors.append('functional groups is not an array')
    else:
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get('atomIndices', []), list) or not all(type(i) is int and 0 <= i < len(atoms) for i in group.get('atomIndices', [])):
                errors.append('functional-group atom outside model')
            if isinstance(group, dict) and (not isinstance(group.get('bondIndices', []), list) or not all(type(i) is int and 0 <= i < len(bonds) for i in group.get('bondIndices', []))):
                errors.append('functional-group bond outside model')
    for field, expected in (('referenceOnly', True), ('trainingEligible', False), ('measuredCoordinates', False)):
        if field in model and model[field] is not expected:
            errors.append('model contradicts reference-only scope: ' + field)
    return errors


def _model_path(relative):
    return isinstance(relative, str) and re.fullmatch(r'models/[A-Za-z0-9][A-Za-z0-9._/-]*\.json', relative) is not None and not any(p in ('.', '..') for p in relative.split('/'))


def check_chemical_reference_overlay(audit, base, registry, bindings, overlay, ambient_proof=None, resolved_identity_proof=None, standard_identity_proof=None):
    """Validate every use/target/reference; mutate only Audit errors/counts."""
    digest = lambda name: hashlib.sha256((base / name).read_bytes()).hexdigest()
    try:
        enrich_registry(registry, bindings, overlay, digest('registry.json'), digest('bindings.json'))
    except (ValueError, KeyError, TypeError) as error:
        audit.check(False, 'chemical overlay: ' + str(error))
        return
    entries = {e['id']: e for e in registry['entries']}
    identity_index = identity_rules.ReferenceIndex(registry['entries'])
    uses = Counter(eid for row in bindings['recordBindings'].values() for eid in row.values())
    expected = {eid for eid in uses if eid in entries and not (entries[eid].get('model3dPath') or entries[eid].get('component3dModels'))}
    rows = overlay['entries']
    audit.check(set(rows) == expected, 'chemical overlay: does not cover exactly all used formerly-flat identities')
    loaded = {}
    referenced_new_paths = set()

    def model_reference(ref, label):
        if not audit.check(isinstance(ref, dict) and _model_path(ref.get('model3dPath')), label + ': unsafe/non-model path'):
            return
        path = audit.asset(base, ref['model3dPath'], ref.get('model3dSha256'), label)
        if not path:
            return
        if path not in loaded:
            try:
                loaded[path] = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, ValueError, TypeError):
                audit.check(False, label + ': invalid JSON model')
                return
        model = loaded[path]
        for error in molecular_model_errors(model):
            audit.check(False, label + ': ' + error)
        audit.check(bool(ref.get('caption')), label + ': reference caption absent')
        if ref['model3dPath'].startswith('models/h-reader-'):
            referenced_new_paths.add(ref['model3dPath'])
            audit.check(model.get('referenceOnly') is True and model.get('trainingEligible') is False and model.get('measuredCoordinates') is False, label + ': computed model reference/training/measurement flags absent')
            audit.check(model.get('representation') == '3d' and model.get('coordinateUnits') == 'angstrom' and model.get('allowRotation') is True, label + ': computed model coordinate schema')
            audit.check(model.get('conformerGeneration', {}).get('embeddingMethod') == 'ETKDGv3', label + ': computed model method absent')

    crystal_rows = None
    for eid, ref in rows.items():
        label = 'chemical overlay/' + eid
        route = ref['route']
        audit.check(type(ref.get('chemicalUseCount')) is int and ref['chemicalUseCount'] == uses[eid], label + ': stale chemical-use count')
        audit.check(ref.get('buttonLabel') == ('View formula ↗' if route == 'flat' else 'Rotate 3D ↗'), label + ': button label differs')
        audit.check(isinstance(ref.get('reason'), str) and bool(ref['reason']), label + ': reason absent')
        if route == 'flat':
            audit.check('\n' not in ref['whyNo3d'] and '\r' not in ref['whyNo3d'], label + ': flat reason must be one line')
            audit.check(not any(ref.get(key) for key in ('model3dPath', 'component3dModels', 'crystalReference')), label + ': flat entry assigns coordinates')
            continue
        audit.check(entries[eid].get('depictionKind') not in {'mixture', 'specimen', 'support', 'surface', 'composite', 'equipment', 'polymer', 'material-context', 'sample-context'}, label + ': whole context was promoted to one structure')
        audit.check(identity_rules.context_reason(entries[eid]) is None, label + ': original context/isomer identity excludes a 3D reference')
        audit.check(not identity_rules.unqualified_bulk_hold(entries[eid]) or route == 'ambient_crystal_reference', label + ': unqualified form requires an admitted existing ambient/own-name reference')
        if ref.get('reason') == 'fixed_standard_abbreviation':
            if standard_identity_proof is None:
                standard_identity_proof = json.loads(Path(__file__).with_name('chemical_standard_abbreviation_pins.json').read_text(encoding='utf-8'))
            audit.check(standard_identity_proof.get('schema') == 'MatterSyn-H-fixed-standard-abbreviation-reference-pins/1' and standard_identity_proof.get('originalRegistrySha256') == overlay['originalRegistrySha256'], label + ': fixed-standard identity proof is stale')
            for error in identity_rules.standard_abbreviation_reference_errors(entries[eid], ref, standard_identity_proof.get('entries',{}).get(eid), entries):
                audit.check(False, label + ': ' + error)
        elif 'referenceRegistryId' in ref or ref.get('reason') in identity_rules.REUSED_REFERENCE_REASONS:
            resolved=None
            if ref.get('reason')=='resolved_exact_name_identical_CID':
                if resolved_identity_proof is None:resolved_identity_proof=json.loads(Path(__file__).with_name('chemical_resolved_identity_pins.json').read_text(encoding='utf-8'))
                audit.check(resolved_identity_proof.get('schema')=='MatterSyn-H-exact-reported-name-CID-proof/1'and resolved_identity_proof.get('originalRegistrySha256')==overlay['originalRegistrySha256'],label+': stale exact-name CID proof')
                resolved=resolved_identity_proof.get('entries',{}).get(eid)
            for error in identity_rules.reused_reference_errors(entries[eid], ref, identity_index, resolved):
                audit.check(False, label + ': ' + error)
        if identity_rules.requires_connected_molecule_reference(entries[eid]):
            audit.check(route == 'molecule_reference', label + ': the excluded disconnected CdMe2 representation cannot stand for a molecular reference')
        if route == 'molecule_reference':
            audit.check(not ref.get('component3dModels') and not ref.get('crystalReference'), label + ': mixed viewer routes')
            model_reference(ref, label)
        elif route == 'independent_component_references':
            audit.check(not ref.get('model3dPath') and not ref.get('atoms') and not ref.get('bonds') and not ref.get('crystalReference'), label + ': whole-ion assembly geometry is forbidden')
            scope = ref.get('component3dScope', '')
            audit.check(isinstance(scope, str) and bool(re.search(r'no (?:relative ion geometry|geometry between ions|inter-ion geometry)', scope, re.I)), label + ': independent-component scope absent')
            components = ref.get('component3dModels')
            if not audit.check(isinstance(components, list) and bool(components), label + ': no molecular component references'):
                continue
            proof=ref.get('namedLigandReference')
            if proof is not None:
                try:
                    named_ligands.validate_named_ligand_components(proof,components)
                    expected_name=named_ligands.IN_NAME if eid==named_ligands.IN_ID else named_ligands.SN_NAME
                    audit.check(proof['entry_id']==eid and entries[eid].get('name')==expected_name,label+': named ligand proof and original identity differ')
                    audit.check(named_ligands.REFERENCE_SCOPE in scope,label+': named ligand reference scope absent')
                except (ValueError,KeyError,TypeError)as error:audit.check(False,label+': '+str(error))
            ids = [c.get('id') for c in components if isinstance(c, dict)]
            audit.check(len(ids) == len(components) and len(set(ids)) == len(ids) and all(isinstance(cid, str) and cid for cid in ids), label + ': invalid/duplicate component identities')
            for index, component in enumerate(components):
                if isinstance(component, dict):
                    audit.check(not any(component.get(key) for key in ('position', 'translation', 'rotation', 'transform', 'offset', 'coordinates', 'atoms', 'bonds')), label + ': relative component placement is forbidden')
                if isinstance(component, dict) and 'multiplicityInReferenceFormula' in component:
                    audit.check(type(component['multiplicityInReferenceFormula']) is int and component['multiplicityInReferenceFormula'] > 0, label + ': invalid component multiplicity')
                model_reference(component, label + '/component-' + str(index))
        elif route == 'ambient_crystal_reference':
            audit.check(not ref.get('model3dPath') and not ref.get('component3dModels'), label + ': cell used as molecular geometry')
            crystal_base = base.parent / 'crystal-references'
            if crystal_rows is None:
                crystal_rows = {e['id']: e for e in json.loads((crystal_base / 'registry.json').read_text(encoding='utf-8'))['entries']}
            original = crystal_rows.get(ref.get('referenceId'))
            crystal = ref.get('crystalReference')
            if not audit.check(isinstance(crystal, dict) and isinstance(original, dict) and crystal.get('id') == original['id'], label + ': absent existing crystal reference'):
                continue
            if ambient_proof is None:
                ambient_proof = json.loads(Path(__file__).with_name('chemical_ambient_reference_pins.json').read_text(encoding='utf-8'))
            normalized = lambda text: re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', str(text)).strip()).casefold()
            own_name = normalized(entries[eid].get('name', ''))
            explicit = next((p for p in ambient_proof.get('explicit_phase_names', []) if own_name in {normalized(name) for name in p['reported_names']}), None)
            formula = entries[eid].get('formula') or entries[eid].get('name')
            proof = explicit or ambient_proof.get('formulas', {}).get(formula, {})
            matching = [e for e in crystal_rows.values() if e.get('formula') == original.get('formula')]
            audit.check(bool(proof.get('basis')) and proof.get('reference_id') == original['id'] and (bool(explicit) or proof.get('ambient_structure_unique') is True), label + ': ambient/own-name phase not explicitly admitted')
            audit.check(formula == original.get('formula') or bool(explicit) and explicit.get('formula') == original.get('formula') and not entries[eid].get('formula'), label + ': original chemical and crystal formula differ')
            audit.check(proof.get('registry_sha256') == hashlib.sha256((crystal_base / 'registry.json').read_bytes()).hexdigest(), label + ': stale ambient-library proof')
            audit.check(set(proof.get('existing_reference_ids', [])) == {e['id'] for e in matching} and {e.get('spaceGroupNumber') for e in matching} == {proof.get('space_group_number')}, label + ': ambient structure signature changed')
            audit.check(set(crystal) <= set(original) and all(original.get(key) == value for key, value in crystal.items()), label + ': crystal metadata differs from existing library')
            audit.check(not set(crystal) & {'record_ids', 'sample_ids', 'defaultForSample'}, label + ': source/sample binding copied into chemical reference')
            audit.check(crystal.get('referenceOnly') is True and crystal.get('trainingEligible') is False, label + ': ambient reference scope flags')
            for key in ('modelPath', 'modelSha256', 'cifPath', 'cifSha256'):
                audit.check(ref.get(key) == crystal.get(key) == original.get(key), label + ': mismatched existing crystal ' + key)
            audit.check(_model_path(crystal.get('modelPath')), label + ': unsafe crystal-model path')
            for key, checksum in (('modelPath', 'modelSha256'), ('cifPath', 'cifSha256')):
                if original.get(key):
                    audit.asset(crystal_base, original[key], original.get(checksum), label + '/' + key)
            # Audit.crystals independently validates the exact complete library,
            # cell coordinates/occupancies and pinned CIF/model metadata.
    actual_new = {'models/' + path.name for path in (base / 'models').glob('h-reader-*-3d.json')}
    audit.check(actual_new == referenced_new_paths, 'chemical overlay: unreferenced or missing newly computed models')
    audit.counts['chemical_reference_overlay_entries'] = len(rows)
    audit.counts['chemical_reference_overlay_model_assets'] = len(loaded)
