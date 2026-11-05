"""Reader route names and completeness scores derived from one record's structured fields.

`route_label(record)` names the route of a record whose method is the generic
"Synthesis as described in the source" or "Other", using only that record's own
steps (action, label, parameters, environment) and materials (name, role). The
rules are fixed and deliberately conservative: the first rule that applies wins,
and when none applies the label is empty, so the reader shows no method label
rather than the generic phrase. No model is called.

Route names use the canonical spelling of reader-utils.mjs METHOD_SYNONYMS, which
shows synonyms under one name (MBE as Molecular beam epitaxy) for every record.
`completeness(record)` is the reader's ordering score. The record is never modified.
"""
from __future__ import annotations

import re

GENERIC_METHODS = {'synthesis as described in the source', 'other'}

# [route name, pattern over the record's step actions, step labels, material names
#  and environment values]. Explicit technique names come first.
EXPLICIT = [
    ('Molecular beam epitaxy', r'\bmbe\b|molecular[- ]beam epitax'),
    ('Metal-organic chemical vapor deposition', r'\bmocvd\b|\bmovpe\b|metal[- ]?organic (?:chemical )?vapou?r'),
    ('Chemical vapor deposition', r'\bcvd\b|chemical vapou?r deposition'),
    ('Pulsed laser deposition', r'pulsed[- ]laser deposition|\bpld\b'),
    ('Sputter deposition', r'\bsputter'),
    ('Ion implantation', r'\bimplant'),
    ('Laser ablation', r'laser ablation'),
    ('Ball milling', r'ball[- ]mill'),
    ('Electrodeposition', r'electrodeposit|electrochemical(?:ly)? deposit'),
    ('Spray pyrolysis', r'spray pyrolysis'),
    ('Successive ionic layer adsorption and reaction', r'\bsilar\b|successive ionic layer'),
    ('Chemical bath deposition', r'chemical bath deposition'),
    ('Sol-gel', r'\bsol[- –]gel\b'),
    ('Cation exchange', r'cation[- ]exchange'),
    ('Microwave-assisted synthesis', r'microwave'),
    ('Hydrothermal', r'hydrothermal'),
    ('Solvothermal', r'solvothermal'),
]
AUTOCLAVE = r'autoclave|teflon[- ]lined|ptfe[- ]lined'
# An arsenic or antimony molecular beam (As4, As2, Sb4) is an MBE source flux.
BEAM_FLUX = r'\b(?:as|sb)[24]\b'
WATER = re.compile(r'^(?:(?:deionized|de-ionized|distilled|ultrapure|milli-?q|high-purity|pure|doubly distilled|bidistilled)\s+)*water$|^h2o$|^di water$')
COOL = {'cool', 'quench'}
HOT_C = 100.0       # an injection at or above 100 °C is into a hot solution
HEAT_UP_C = 150.0   # a heat-up route reaches at least 150 °C after all reagents are combined
PRECURSORS = {'chalcogen_precursor', 'nonmetal_precursor', 'halide_precursor'}
AMOUNT_EXCLUDE = re.compile(r'purity|grade|ph$|^ph|density|molar_mass|molecular_weight')
SIZE_PROPERTY = re.compile(r'diameter|particle_size|crystallite_size|size|length|width|thickness|edge')


def _text(value):
    return value.strip().lower() if isinstance(value, str) else ''


def is_generic(method):
    return _text(method) in GENERIC_METHODS


def _reported(quantity):
    return isinstance(quantity, dict) and quantity.get('status') == 'reported' and any(
        isinstance(quantity.get(k), (int, float)) and not isinstance(quantity.get(k), bool)
        for k in ('value', 'minimum', 'maximum'))


def _celsius(quantity):
    if not _reported(quantity):
        return None
    values = [quantity.get(k) for k in ('value', 'maximum', 'minimum')]
    value = next(v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool))
    unit = _text(quantity.get('unit'))
    if unit in ('degc', '°c', 'c'):
        return float(value)
    if unit == 'k':
        return float(value) - 273.15
    return None


def _temperature(operation):
    params = operation.get('parameters') or {}
    temps = [t for t in (_celsius(params.get('temperature')), _celsius(params.get('injection_temperature'))) if t is not None]
    return max(temps) if temps else None


QUENCH_INJECTION = re.compile(r'quench|cold|ice|room[- ]temperature solvent')


def _is_injection(operation):
    label = _text(operation.get('label'))
    return (_text(operation.get('action')) == 'inject' or 'inject' in label) and not QUENCH_INJECTION.search(label)


def _cues(record):
    parts = []
    for op in record.get('operations') or []:
        parts += [_text(op.get('action')), _text(op.get('label')), _text((op.get('environment') or {}).get('value'))]
    parts += [_text(m.get('name')) for m in record.get('materials') or []]
    return ' | '.join(p for p in parts if p)


def _solvents(record):
    names = [_text(m.get('name')) for m in record.get('materials') or [] if m.get('role') == 'solvent']
    water = any(WATER.match(n) for n in names)
    organic = any(n and not WATER.match(n) for n in names)
    return water, organic


def _hot_injection(operations):
    last = None
    for op in operations:
        temp = _temperature(op)
        if _is_injection(op):
            context = temp if temp is not None else last
            if (context is not None and context >= HOT_C) or re.search(r'\bhot\b', _text(op.get('label'))):
                return True
        if _text(op.get('action')) in COOL:
            last = temp
        elif temp is not None:
            last = temp
    return False


def _heat_up(record, operations):
    if any(_is_injection(op) for op in operations):
        return False
    roles = {m.get('role') for m in record.get('materials') or []}
    if 'metal_precursor' not in roles or not roles & PRECURSORS:
        return False
    if not any(m.get('role') in ('ligand', 'solvent') and _text(m.get('name')) and not WATER.match(_text(m.get('name')))
               for m in record.get('materials') or []):
        return False
    hot, reached, combined = None, False, False
    for op in operations:
        action, temp = _text(op.get('action')), _temperature(op)
        if action in ('add', 'mix', 'dissolve', 'load'):
            if hot is not None and hot >= HOT_C:
                return False  # a reagent added to a hot mixture is not a heat-up route
            combined = True
        if action in COOL:
            hot = temp
            continue
        if temp is not None:
            hot = temp
            # The reagents must be combined in a recorded step before the mixture is heated.
            if combined and temp >= HEAT_UP_C and action in ('heat', 'grow', 'reflux', 'hold', 'react', 'stir', 'age'):
                reached = True
    return reached


def route_label(record):
    """Route name for a generic-method record, or '' when no fixed rule applies."""
    if not is_generic(record.get('method')):
        return ''  # the recorded method is shown
    cues = _cues(record)
    for name, pattern in EXPLICIT:
        if re.search(pattern, cues):
            return name
    operations = record.get('operations') or []
    if any(re.search(BEAM_FLUX, _text((op.get('environment') or {}).get('value'))) for op in operations):
        return 'Molecular beam epitaxy'
    if re.search(AUTOCLAVE, cues):
        water, organic = _solvents(record)
        if water and not organic:
            return 'Hydrothermal'
        if organic and not water:
            return 'Solvothermal'
        return ''
    if _hot_injection(operations):
        return 'Hot injection'
    if _heat_up(record, operations):
        return 'Heat-up'
    return ''


def completeness(record):
    """Precursors with a reported amount + steps with a reported condition + reported size, phase, morphology."""
    score = 0
    for material in record.get('materials') or []:
        if material.get('role') == 'solvent' and not material.get('quantities'):
            continue
        if any(_reported(q) for key, q in (material.get('quantities') or {}).items() if not AMOUNT_EXCLUDE.search(key.lower())):
            score += 1
    for op in record.get('operations') or []:
        if any(_reported(q) for q in (op.get('parameters') or {}).values()) or (op.get('environment') or {}).get('status') == 'reported':
            score += 1
    products = record.get('products') or []
    samples = {p.get('sample_id') for p in products}
    if any(SIZE_PROPERTY.search(_text(m.get('property'))) and _reported(m.get('value')) and
           (not m.get('sample_id') or m.get('sample_id') in samples) for m in record.get('measurements') or []):
        score += 1
    for field in ('phase', 'morphology'):
        if any((p.get(field) or {}).get('status') == 'reported' for p in products):
            score += 1
    return score


def reader_sort_key(record, direct, score, earlier):
    """Material-page order: direct records before component contexts, then records not
    marked source_extracted, then completeness (highest first); ties keep `earlier`,
    the previous year/paper order."""
    return (not direct, (record.get('quality') or {}).get('review_status') == 'source_extracted', -score, *earlier)
