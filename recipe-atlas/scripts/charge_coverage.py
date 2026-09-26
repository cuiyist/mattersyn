"""Conservative, source-linked documentation of quantified synthesis inputs.

This is a documentation measure, not a recipe-completeness or training gate.
No chemical-name, abbreviation, narrative or figure inference is used.
"""
import math
import re

AMOUNT_WORDS = re.compile(r'(?:^|[._\s-])(?:amount|mass|volume|concentration|loading|moles?|mol|mmol|umol|dose|charge|ratio)(?:$|[._\s-])', re.I)
NON_CHARGE = re.compile(r'purity|molecular.?weight|molar.?mass|density|capacity|diameter|radius|particle.?size|pore|thickness|wavelength|yield|conversion|flow|rate|percentage|percent', re.I)
AMOUNT_UNITS = {'g', 'mg', 'ug', 'kg', 'ng', 'mol', 'mmol', 'umol', 'nmol', 'l', 'ml', 'ul', 'nl'}
CONCENTRATION_UNITS = {'m', 'mm', 'um', 'mol/l', 'mmol/l', 'mol/liter', 'mol/litre', 'mol/ml', 'mmol/ml', 'g/l', 'g/ml', 'mg/ml', 'mg/l', 'mol/kg', 'mmol/g', 'molar'}
RATIO_UNITS = {'dimensionless', 'ratio', 'mol/mol', 'molar ratio', 'volume ratio', 'mass ratio'}

def _ptr(value):
    return str(value).replace('~', '~0').replace('/', '~1')

def _supported(q, source_ids):
    if not isinstance(q, dict) or q.get('status') not in {'reported', 'calculated', 'inherited', 'author_derived'}:
        return False
    numbers = [q.get(k) for k in ('value', 'minimum', 'maximum')]
    if not any(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in numbers):
        return False
    evidence = q.get('evidence')
    return bool(evidence and all(isinstance(e, dict) and e.get('source_id') in source_ids and isinstance(e.get('locator'), str) and e['locator'].strip() for e in evidence))

def charge_quantity(key, q, source_ids):
    if not _supported(q, source_ids) or NON_CHARGE.search(key):
        return False
    unit = str(q.get('unit') or '').strip().replace('µ', 'u').replace('μ', 'u').lower().replace(' ', '')
    words = str(key).replace('µ', 'u').replace('μ', 'u')
    if unit in AMOUNT_UNITS:
        return bool(AMOUNT_WORDS.search(words))
    if unit in {x.replace(' ', '') for x in CONCENTRATION_UNITS}:
        return bool(re.search(r'concentration|molarity|loading', words, re.I))
    if unit in {x.replace(' ', '') for x in RATIO_UNITS}:
        return bool(re.search(r'ratio', words, re.I))
    return False

def quantified_inputs(record):
    source_ids = {s['id'] for s in record.get('sources', [])}
    materials = {m['id']: (i, m) for i, m in enumerate(record.get('materials', []))}
    qualifying = []
    for mid, (i, material) in materials.items():
        if material.get('stage') in {'workup', 'characterization', 'storage', 'measurement', 'analysis'} or material.get('role') in {'equipment', 'apparatus', 'substrate_for_characterization'}:
            continue
        for key, quantity in material.get('quantities', {}).items():
            if charge_quantity(key, quantity, source_ids):
                qualifying.append({'material_id': mid, 'pointer': f'/materials/{i}/quantities/{_ptr(key)}', 'binding_basis': 'quantity of this named material', 'quantity': quantity})
    for i, stock in enumerate(record.get('stocks', [])):
        for j, component in enumerate(stock.get('components', [])):
            mid = component.get('material_id')
            if mid not in materials:
                continue
            material = materials[mid][1]
            if material.get('stage') in {'workup', 'characterization', 'storage', 'measurement', 'analysis'}:
                continue
            for key, quantity in component.get('quantities', {}).items():
                if charge_quantity(key, quantity, source_ids):
                    qualifying.append({'material_id': mid, 'stock_id': stock['id'], 'pointer': f'/stocks/{i}/components/{j}/quantities/{_ptr(key)}', 'binding_basis': 'explicit stock-component material_id', 'quantity': quantity})
    for i, operation in enumerate(record.get('operations', [])):
        if operation.get('stage') not in {'synthesis', 'precursor_preparation'}:
            continue
        inputs = operation.get('inputs', [])
        material_inputs = [mid for mid in inputs if mid in materials]
        for key, quantity in operation.get('parameters', {}).items():
            if not charge_quantity(key, quantity, source_ids):
                continue
            explicit = quantity.get('material_id')
            if explicit in material_inputs:
                mid, basis = explicit, 'explicit parameter material_id also present in operation inputs'
            else:
                # Literal material IDs only, separated by field-name delimiters.
                # No synonym, chemistry-name or guessed abbreviation matching.
                matches = [mid for mid in material_inputs if re.search(r'(?:^|[.])' + re.escape(mid) + r'(?:$|[._-])', key)]
                if len(matches) == 1:
                    mid, basis = matches[0], 'exact material ID in parameter key and operation inputs'
                elif len(inputs) == 1 and len(material_inputs) == 1 and AMOUNT_WORDS.fullmatch(key):
                    mid, basis = material_inputs[0], 'single operation input is this material; generic charge field'
                else:
                    continue
            qualifying.append({'material_id': mid, 'operation_id': operation['id'], 'pointer': f'/operations/{i}/parameters/{_ptr(key)}', 'binding_basis': basis, 'quantity': quantity})
    # Count materials, never the number of repeated mass/volume/amount measurements.
    return {'material_ids': sorted({x['material_id'] for x in qualifying}), 'fields': qualifying,
            'scope': 'Source-backed quantitative input fields present in the record. This does not establish that all reagent charges are known or that the recipe is complete.'}
