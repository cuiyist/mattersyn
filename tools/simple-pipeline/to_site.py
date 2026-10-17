#!/usr/bin/env python3
"""Turn checked pair files into the inputs of the existing MatterSyn site.

  python to_site.py records pairs --repo <mattersyn checkout>

For each pair it writes one record in the site's own format (recipe-atlas/data/records/<id>.json),
so the paper appears in the existing Reader. Every value keeps its page locator. A value the pair
file does not have is written as "not reported"; nothing is filled in.

Records get the review status "source_extracted": extracted from the paper and checked
automatically, not yet reviewed by an expert. They are never marked as reviewed.
"""
from __future__ import annotations
import argparse, json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'recipe-atlas/scripts'))
from reader_presentation_registry import load_reviewed_reader, source_paths, write_reviewed_reader

REVIEW_SCOPE = ('Extracted from the paper by the MatterSyn pipeline. Each value is tied to a quote found in the paper and was '
                'produced by two separate local-model extraction passes that agree. It has not been independently audited.')
UNITS = {'°c': 'degC', 'c': 'degC', 'degc': 'degC', 'k': 'K', 'min': 'min', 'mins': 'min', 'minute': 'min', 'minutes': 'min', 'h': 'h', 'hr': 'h', 'hrs': 'h',
         'hour': 'h', 'hours': 'h', 's': 's', 'sec': 's', 'seconds': 's', 'd': 'd', 'day': 'd', 'days': 'd', 'ml': 'mL', 'l': 'L', 'µl': 'µL', 'μl': 'µL', 'ul': 'µL'}
QUANTITY_KIND = (('amount', r'^(m|µ|μ|u)?mol$'), ('mass', r'^(m|µ|μ|k)?g$'), ('volume', r'^(m|µ|μ)?l$'), ('concentration', r'^(m|µ|μ)?m$|mol/l|wt%|%$'), ('equivalents', r'^equiv'))
WORKUP = {'precipitate', 'centrifuge', 'wash', 'redisperse', 'dry', 'filter', 'purify', 'isolate', 'collect', 'extract', 'decant'}
ARCHITECTURE = {'core': 'single_material', 'core/shell': 'core_shell', 'alloy': 'alloy', 'doped': 'single_material', 'heterostructure': 'heterostructure', 'composite': 'composite'}
SIZE_PROPERTY = {'tem': ('diameter', 'TEM'), 'hrtem': ('diameter', 'HRTEM'), 'stem': ('diameter', 'STEM'), 'sem': ('diameter', 'SEM'), 'xrd': ('crystallite_size', 'XRD'),
                 'saxs': ('diameter', 'SAXS'), 'dls': ('hydrodynamic_diameter', 'DLS'), 'optical': ('optically_derived_size', 'optical sizing')}
ELEMENT = r'A[cglmrstu]|B[aehikr]?|C[adeflmorsu]?|D[sy]|E[rsu]|F[emr]?|G[ade]|H[efgos]?|I[nr]?|Kr?|L[airu]|M[gnot]|N[abdeiop]?|Os?|P[abdmortu]?|R[abehnu]|S[bcegimnr]?|T[abcehilm]|U|V|W|Xe|Yb?|Z[nr]'


def public_figure_caption(figure):
    """An explicit public paraphrase only; raw captions and quotes stay local."""
    caption = figure.get('public_caption')
    return {'public_caption': caption.strip()} if isinstance(caption, str) and caption.strip() else {}


def dump_like(path, data):
    """Write JSON in the style the file already has (line endings, final newline), so only real changes show up."""
    if Path(path).name=='reader-presentation-reviewed.json' and Path(path).parent.name=='data' and Path(path).is_file() and len(source_paths(path))==2:
        write_reviewed_reader(path,data);return
    raw = Path(path).read_bytes() if Path(path).is_file() else b'\n'
    # Compact only the large Reader sidecar; canonical/generic JSON stays unchanged.
    options = {'separators': (',', ':')} if Path(path).name == 'reader-presentation-reviewed.json' else {'indent': 2}
    text = json.dumps(data, ensure_ascii=False, **options) + ('\n' if raw.endswith(b'\n') else '')
    Path(path).write_bytes(text.replace('\n', '\r\n').encode('utf-8') if b'\r\n' in raw else text.encode('utf-8'))


def slug(text, limit=60):
    text = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', text)).strip('-')[:limit].strip('-') or 'x'


def unit_name(unit):
    unit = (unit or '').strip()
    return UNITS.get(unit.lower().replace(' ', ''), unit)


def _formula_token(text):
    """The formula inside a composition phrase; preserve grouped composition punctuation."""
    phrase = re.sub(r'\s*([/@])\s*', r'\1', str(text))
    grouped = []
    depth = 0
    for char in phrase:
        if char in '([':
            depth += 1
        elif char in ')]':
            depth = max(0, depth - 1)
        if char.isspace() and depth > 0:
            continue
        grouped.append(' ' if char == ',' and depth == 0 else char)
    for token in ''.join(grouped).split():
        token = token.strip('.;')
        for left, right in (('(', ')'), ('[', ']')):
            while token.startswith(left) and token.count(left) > token.count(right):
                token = token[1:]
            while token.endswith(right) and token.count(right) > token.count(left):
                token = token[:-1]
        while len(token) > 1 and token[0] in '([' and token[-1] == {'(': ')', '[': ']'}[token[0]]:
            level = 0
            grouped_comma = False
            for index, char in enumerate(token):
                if char == token[0]: level += 1
                elif char == token[-1]: level -= 1
                elif char == ',' and level == 1: grouped_comma = True
                if level == 0: break
            if index != len(token) - 1 or grouped_comma: break
            token = token[1:-1]
        if token in {'NC', 'NCs', 'QD', 'QDs'}: continue
        if any(token.count(left) != token.count(right) for left, right in (('(', ')'), ('[', ']'))): continue
        bare = re.sub(r'[\d.()\[\],xyz\u2212\u2013\u2014\-/@:+δ]', '', token)
        solo = token in ('Au', 'Ag', 'Pt', 'Pd', 'Si', 'Ge', 'Cu', 'Ni', 'Co', 'Fe', 'Bi', 'Sn', 'Te', 'Se', 'Ru', 'Rh', 'Ir')
        if bare and re.fullmatch(rf'(?:(?:{ELEMENT})(?![a-z]))+', bare) and (len(elements_of(token)) > 1 or solo or token == phrase.strip()):
            return token
    return None


def formula_from(text):
    """Keep the original text fallback when no formula token is found."""
    token = _formula_token(text)
    return token if token is not None else str(text).strip()


def _named_ge_product_formula(pair):
    """Navigation for explicit whole-product Ge assemblies, not a reported formula."""
    value = ((pair.get('structure') or {}).get('composition') or {}).get('value')
    if value is not None and str(value).strip() not in ('', 'Ge'):
        return None
    label = str(pair.get('product') or '').strip()
    if re.fullmatch(r'Ge\s+(?i:NCs|nanocrystals?)\s+(?i:in)\s+Ge\s*/\s*SiO2\s*/\s*Si\s+(?i:sample)', label):
        return 'Ge/SiO2/Si'
    if re.fullmatch(r'Ge\s+(?i:quantum\s+dots?|NCs|nanocrystals?)\s+(?i:in)\s+(?:(?i:amorphous)\s+)?SiO2\s+(?i:matrix)', label):
        return 'Ge/SiO2'
    if re.fullmatch(r'Ge\s+(?i:quantum\s+dots?\s+with\s+boron\s+on)\s+Ge\s+(?i:wetting\s+layer)', label):
        descriptions = [re.sub(r'\s+', ' ', str(step.get('description') or '')).strip().casefold()
                        for step in ((pair.get('recipe') or {}).get('steps') or []) if isinstance(step, dict)]
        if any(value == 'deposition of boron' and 'deposition of ge top layer' in descriptions[index+1:]
               for index, value in enumerate(descriptions)):
            return 'Ge/B'
    return None


def _explicit_ge_matrix_navigation(pair):
    """Navigation for three explicit whole-product matrices; reported facts stay exact."""
    value = ((pair.get('structure') or {}).get('composition') or {}).get('value')
    label = re.sub(r'\s+', ' ', str(pair.get('product') or '')).strip()
    if label == 'Ge/Si QDSL':
        if value is not None and str(value).strip() not in ('', 'Ge/Si'):
            return None
        return ['Ge', 'Si'], ['Ge', 'Si']
    if value is not None and str(value).strip() not in ('', 'Ge'):
        return None
    named = {
        'Ge nanocrystals embedded in GeO2 matrix': ['Ge', 'GeO2'],
        'Ge nanocrystals embedded in Lu2O3/Al2O3 dielectric stack': ['Ge', 'Lu2O3', 'Al2O3'],
        'nc-Ge (nanocrystalline germanium) embedded in SiO2 matrix': ['Ge', 'SiO2'],
        'Ge nanocrystals in SiOx:Ge/SiOx multilayers': ['Ge', 'SiOx'],
    }
    components = named.get(label)
    if components is None:
        return None
    elements = list(dict.fromkeys(element for component in components for element in elements_of(component)))
    return components, elements


def _embedded_product_formula(pair):
    """Classify an explicit named Ge assembly; never fill a reported fact."""
    named = _named_ge_product_formula(pair)
    if named is not None:
        return named
    value = ((pair.get('structure') or {}).get('composition') or {}).get('value')
    if value is not None and str(value).strip() not in ('', 'Ge'):
        return None
    label = str(pair.get('product') or '').strip()
    if re.fullmatch(r'(?:(?i:nanocrystalline)\s+)?Ge(?:\s+(?i:nanocrystals?))?\s+(?i:embedded\s+in)\s+SiO2(?:\s+(?i:matrix))?', label):
        return 'Ge/SiO2'
    return None


def _composition_from(pair):
    """Keep reported facts; classify an explicit named embedded product system."""
    embedded = _embedded_product_formula(pair)
    if embedded is not None:
        return embedded
    value = ((pair.get('structure') or {}).get('composition') or {}).get('value')
    if value is not None and str(value).strip():
        return formula_from(value)
    return _formula_token(pair.get('product') or '')


def first_upper(text):
    return text[:1].upper() + text[1:]


def elements_of(formula):
    formula = re.sub(r'(?<![A-Za-z0-9])TiO2\(B\)(?![A-Za-z0-9])', 'TiO2', formula or '')
    letters = re.sub(r'[^A-Za-z]', ' ', formula or '')
    letters = re.sub(r'([A-Za-z])[xyz](?=[A-Z]|$)', r'\1', letters)  # variable coefficient after an element
    found = []
    for token in letters.split():
        matches = re.findall(rf'({ELEMENT})(?![a-z])', token)
        unmatched = re.sub(rf'({ELEMENT})(?![a-z])', '', token)
        if re.fullmatch('[xyz]*', unmatched):
            found.extend(matches)
    return list(dict.fromkeys(found))


def components_of(composition):
    """Split only top-level separators; malformed groups remain one opaque label."""
    separator = re.compile(r'[/@]|(?<=[A-Za-z0-9)])[-–—−](?=[A-Z])')
    closers = {'(': ')', '[': ']', '{': '}'}
    stack, parts, start = [], [], 0
    for index, char in enumerate(composition):
        if char in closers:
            stack.append(closers[char])
        elif char in ')]}':
            if not stack or stack.pop() != char:
                return [composition.strip()] if composition.strip() else []
        elif not stack and separator.match(composition, index):
            part = composition[start:index].strip()
            if part:
                parts.append(part)
            start = index + 1
    if stack:
        return [composition.strip()] if composition.strip() else []
    part = composition[start:].strip()
    if part:
        parts.append(part)
    return parts


class Builder:
    def __init__(self, doc, include_optical=False):
        self.doc = doc; self.include_optical = include_optical
        first = slug(re.split(r'[,;]| and ', doc.get('authors') or '')[0].split()[-1] if doc.get('authors') else '', 20)
        year = str(doc.get('year') or '')[:4]
        tail = slug((doc.get('doi') or doc['id']).split('/')[-1], 30)
        self.source_id = '-'.join(x for x in (first + year if first != 'x' or year else '', tail) if x)

    def evidence(self, page=None):
        return [{'source_id': self.source_id, 'locator': f'Main PDF p.{page}' if page else 'Main PDF'}]

    def fact(self, f, note=''):
        if not f: return {'value': None, 'status': 'not_reported', 'evidence': [], 'note': note}
        return {'value': f['value'], 'status': 'reported', 'evidence': self.evidence(f.get('page')), 'note': note}

    def quantity(self, value=None, unit='', page=None):
        if value is None:
            return {'value': None, 'minimum': None, 'maximum': None, 'unit': unit_name(unit), 'status': 'not_reported', 'approximate': False, 'qualifier': '',
                    'basis': '', 'raw_text': 'not reported', 'evidence': [], 'derivation': None}
        return {'value': value, 'minimum': None, 'maximum': None, 'unit': unit_name(unit), 'status': 'reported', 'approximate': False, 'qualifier': '', 'basis': '',
                'raw_text': f'{value:g} {unit or ""}'.strip(), 'evidence': self.evidence(page), 'derivation': None}

    def source(self):
        d = self.doc
        year = int(str(d['year'])[:4]) if str(d.get('year') or '')[:4].isdigit() else None
        return {'id': self.source_id, 'doi': d.get('doi') or None, 'title': d.get('title') or d['id'], 'authors': d.get('authors') or 'not reported', 'year': year,
                'url': 'https://doi.org/' + d['doi'] if d.get('doi') else '', 'main_status': 'main text read by the extraction pipeline',
                'si_status': 'supporting information not read', 'reuse_status': 'bibliographic citation and extracted values only'}

    def record(self, pair, index):
        st, rc = pair.get('structure') or {}, pair.get('recipe') or {}
        composition = _composition_from(pair)
        if composition is None:
            return None
        rid = f'{self.source_id}-{slug(pair.get("product") or composition, 40)}-{index}'
        ident = lambda name: f'{rid}--{slug(name, 40)}'
        materials, by_name = [], {}
        for c in rc.get('chemicals') or []:
            mid = ident(c['name'])
            if mid in {m['id'] for m in materials}: continue
            role = {'metal source': 'metal_precursor', 'ligand': 'ligand', 'solvent': 'solvent', 'reductant': 'reducing_agent'}.get((c.get('role') or '').lower())
            if (c.get('role') or '').lower() == 'anion source':
                els = set(elements_of(c['name']))
                role = 'chalcogen_precursor' if re.search(r'sulf|selen|tellur|thio', c['name'], re.I) or els & {'S', 'Se', 'Te'} else 'halide_precursor' if re.search(r'chlor|brom|iod|fluor', c['name'], re.I) else 'nonmetal_precursor'
            quantities = {}
            if c.get('amount') is not None:
                unit = unit_name(c.get('unit'))
                kind = next((k for k, pattern in QUANTITY_KIND if re.search(pattern, unit.lower())), 'amount')
                quantities[kind] = self.quantity(c['amount'], unit, c.get('page'))
            by_name[c['name'].lower()] = mid
            materials.append({'id': mid, 'name': c['name'], 'formula': None, 'role': role or 'reagent', 'stage': 'synthesis', 'identity': {'pubchem_cid': None, 'smiles': None},
                              'quantities': quantities, 'notes': [], 'evidence': self.evidence(c.get('page'))})
        states, operations, previous_state, previous_op = [], [], None, None
        steps = rc.get('steps') or []
        atmosphere = rc.get('atmosphere')
        for n, s in enumerate(steps, 1):
            oid = f's{n:02d}-{slug(s.get("action") or "step", 24)}'
            last = n == len(steps)
            state = {'id': f'{rid}--after-{oid}', 'name': 'product as isolated' if last else f'mixture after step {n}', 'kind': 'product' if last else 'reaction_batch',
                     'parent_ids': [x for x in [previous_state] if x] + [by_name[u.lower()] for u in s.get('uses') or [] if u.lower() in by_name]}
            states.append(state)
            workup = (s.get('action') or '').lower() in WORKUP
            parameters = {}
            if s.get('temperature') is not None: parameters['temperature'] = self.quantity(s['temperature'], s.get('temperature_unit') or '°C', s.get('page'))
            if s.get('time') is not None: parameters['duration'] = self.quantity(s['time'], s.get('time_unit') or 'min', s.get('page'))
            for m in materials:  # a chemical first used in a workup step belongs to the workup
                if m['id'] in state['parent_ids'] and workup and not any(m['id'] in o['inputs'] for o in operations): m['stage'] = 'workup'
            operations.append({'id': oid, 'action': (s.get('action') or 'step').lower(), 'label': first_upper((s.get('description') or s.get('action') or 'Step').strip()),
                               'stage': 'workup' if workup else 'synthesis', 'branch': '', 'optional': False, 'depends_on': [previous_op] if previous_op else [],
                               'inputs': list(state['parent_ids']), 'outputs': [state['id']], 'parameters': parameters,
                               'environment': self.fact(atmosphere if not workup else None), 'endpoint': self.fact(None), 'retained_fraction': None,
                               'description': first_upper((s.get('description') or s.get('action') or '').strip()), 'evidence': self.evidence(s.get('page'))})
            previous_state, previous_op = state['id'], oid
        sample = f'{rid}--product'
        link_page = next((f.get('page') for f in (rc.get('reaction_temperature'), rc.get('method'), st.get('composition')) if f and f.get('page')), None)
        product = {'sample_id': sample, 'source_sample_label': pair.get('product') or None, 'batch_id': None, 'material_state_id': previous_state, 'parent_sample_id': None,
                   'composition': self.fact(st.get('composition')), 'phase': self.fact(st.get('phase')), 'morphology': self.fact(st.get('shape')), 'surface': self.fact(st.get('ligand')),
                   'recipe_link': 'explicit', 'link_evidence': self.evidence(link_page), 'notes': []}
        measurements = []
        if st.get('size'):
            prop, technique = SIZE_PROPERTY.get(str((st.get('size_method') or {}).get('value') or '').lower(), ('particle_size', 'not reported'))
            measurements.append({'id': f'{rid}--size', 'sample_id': sample, 'property': prop, 'technique': technique,
                                 'value': self.quantity(st['size']['value'], st['size'].get('unit') or 'nm', st['size'].get('page')), 'conditions': '', 'derives_from': [], 'evidence': self.evidence(st['size'].get('page'))})
        for key, prop, technique, default_unit in (('absorption_peak', 'absorption_peak', 'UV-vis absorption spectroscopy', 'nm'), ('emission_peak', 'photoluminescence_peak', 'photoluminescence spectroscopy', 'nm'),
                                                   ('plqy', 'photoluminescence_quantum_yield', 'photoluminescence spectroscopy', '%')):
            if st.get(key) and self.include_optical:
                measurements.append({'id': f'{rid}--{slug(prop)}', 'sample_id': sample, 'property': prop, 'technique': technique,
                                     'value': self.quantity(st[key]['value'], st[key].get('unit') or default_unit, st[key].get('page')), 'conditions': '', 'derives_from': [], 'evidence': self.evidence(st[key].get('page'))})
        missing = [name.replace('_', ' ') for group, names in ((st, ('phase', 'shape', 'ligand', 'size') + (('absorption_peak', 'emission_peak', 'plqy') if self.include_optical else ())), (rc, ('reactor', 'atmosphere', 'reaction_temperature', 'reaction_time'))) for name in names if not group.get(name)]
        missing += [f'amount of {c["name"]}' for c in rc.get('chemicals') or [] if c.get('amount') is None]
        size = st.get('size') or {}
        components = components_of(composition)
        reported_architecture = str((st.get('architecture') or {}).get('value') or '').strip().lower()
        architecture = ARCHITECTURE.get(reported_architecture, reported_architecture if reported_architecture in {'single_material', 'core_shell', 'heterostructure', 'alloy', 'composite', 'phase_mixture', 'unresolved'} else 'unresolved' if len(components) > 1 else 'single_material')
        family = f'{composition} nanocrystals'
        if _embedded_product_formula(pair) is not None:
            architecture = 'composite'
        if _named_ge_product_formula(pair) is not None:
            family = str(pair['product']).strip()
        if architecture == 'single_material' and len(components) > 1:
            components = []  # A printed dopant separator does not establish separate product components.
        navigation = _explicit_ge_matrix_navigation(pair)
        elements = elements_of(composition)
        if navigation is not None:
            composition = family = str(pair['product']).strip()
            components, elements = navigation
            if architecture == 'single_material':
                architecture = 'unresolved'
        method = str((rc.get('method') or {}).get('value') or 'synthesis as described in the source')
        notes = []
        if rc.get('reactor'): notes.append(f'Reactor: {rc["reactor"]["value"]} (Main PDF p.{rc["reactor"].get("page", "?")}).')
        for key, label in (('reaction_temperature', 'Reaction temperature'), ('reaction_time', 'Reaction time')):
            if rc.get(key): notes.append(f'{label}: {rc[key]["value"]:g} {unit_name(rc[key].get("unit"))} (Main PDF p.{rc[key].get("page", "?")}).')
        product['notes'] = notes
        return {'schema_version': '1.3.0', 'record_id': rid, 'revision': 1, 'record_type': 'literature_protocol',
                'title': f'{(self.doc.get("authors") or self.source_id).split(",")[0].strip()} ({self.doc.get("year") or "n.d."}): {pair.get("product") or composition}',
                'material': {'formula': composition, 'family': family, 'elements': elements, 'components': components, 'architecture': architecture},
                'method': method[0].upper() + method[1:], 'sources': [self.source()],
                'lineage': {'source_group': self.source_id, 'recipe_family': rid, 'parent_record_id': None, 'batch_id': None, 'duplicate_of': None},
                'intended_target': {'composition': self.fact(st.get('composition')), 'phase': self.fact(st.get('phase')),
                                    'size': self.quantity(size.get('value'), size.get('unit') or 'nm', size.get('page')), 'morphology': self.fact(st.get('shape'))},
                'materials': materials, 'stocks': [], 'material_states': states, 'operations': operations, 'condition_options': [], 'products': [product],
                'measurements': measurements, 'structure_assets': [],
                'quality': {'review_status': 'source_extracted', 'review_scope': REVIEW_SCOPE, 'missing_fields': [f'{m[0].upper()}{m[1:]} not reported in the extracted text.' for m in missing],
                            'conflicts': [], 'requested_tasks': [], 'experimental_outcome': 'reported_product'},
                'context_links': [], 'collection': 'reviewed_literature', 'reader_role': 'synthesis_route'}


def records_of(doc, include_optical=False):
    """(builder, [records]) for the pairs that describe a synthesis."""
    builder = Builder(doc, include_optical)
    usable = [(n, p) for n, p in enumerate(doc.get('pairs') or [], 1) if (p.get('recipe') or {}).get('steps') or (p.get('recipe') or {}).get('chemicals')]
    records = []
    builder.omitted_composition_indices = []
    for n, pair in usable:
        record = builder.record(pair, n)
        if record is None:
            builder.omitted_composition_indices.append(n)
        else:
            records.append(record)
    return builder, records


def sha_file(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def step_svg(op, reactor):
    """Conceptual step diagram; a reported recipe-level vessel is not assigned to this step."""
    import textwrap
    esc = lambda s: str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    q = lambda k: op['parameters'].get(k)
    shown = lambda unit: {'degC': '°C'}.get(unit, unit)
    lines = [op['label'][:70]]
    if q('temperature'): lines.append(f'temperature: {q("temperature")["value"]:g} {shown(q("temperature")["unit"])}')
    if q('duration'): lines.append(f'duration: {q("duration")["value"]:g} {shown(q("duration")["unit"])}')
    condition_lines = list(lines)
    if reactor:
        lines.append('Recipe-level reported vessel:')
        lines.extend(textwrap.wrap(str(reactor), width=66))
    else:
        lines.append('Recipe-level vessel: not reported')
    lines.append('No vessel assignment is made for this step.')
    lines.append('Conceptual action diagram; not measured apparatus')
    height = max(320, 202 + 25 * (len(lines) - 1))
    text = ''.join(f'<text x="300" y="{172 + 25 * i}" text-anchor="middle" font-size="{18 if i == 0 else 14}" fill="#24394b">{esc(line)}</text>' for i, line in enumerate(lines))
    vessel = f'Recipe-level reported vessel: {reactor}.' if reactor else 'Recipe-level vessel: not reported.'
    caption = '. '.join(condition_lines) + '. ' + vessel + ' No vessel assignment is made for this step. Conceptual action diagram. Arrows indicate an action only; no apparatus detail is inferred.'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 {height}" role="img" aria-labelledby="title desc"><title id="title">{esc(op["label"][:70])} · conceptual</title>'
           f'<desc id="desc">{esc(caption)}</desc><rect width="600" height="{height}" rx="18" fill="#f4f8fb"/><rect x="224" y="48" width="152" height="86" rx="12" fill="#dbe9ef" stroke="#63808f" stroke-width="3"/>'
           '<path d="M148 91H214M386 91H452M442 81L452 91 442 101" fill="none" stroke="#517d88" stroke-width="4"/>'
           f'<text x="300" y="97" text-anchor="middle" font-size="16" fill="#314f5d">{esc(op["action"])}</text>{text}</svg>\n')
    return svg, caption


CHEMICAL_KINDS = {'molecule', 'formula', 'identity', 'identity_only', 'symbolic_identity', 'ionic', 'ionic_components', 'ionic_identity', 'connectivity',
                  'molecular_connectivity', 'molecular', 'abbreviated_connectivity', 'single_atom', 'element', 'solid', 'polymer', 'reference_2d'}


def name_keys(name):
    """Exact normalized names only: preserve groups, oxidation states and qualifications."""
    written = unicodedata.normalize('NFKC', str(name)).strip(' .,;')
    full = re.sub(r'\s+', ' ', written.lower()).strip(' .,;')
    full = re.sub(r'\s*([()])\s*', r'\1', full)
    return [full] if full else []


def chemical_match(index, name, rank, preferred_id=None):
    """Keep a safe existing match; an optional token needs two explicit aliases of the same entry."""
    def acceptable(entry):
        return entry.get('pubchemCid') or not re.search(r'(19|20)\d\d', entry['id']) or entry.get('depictionKind') in CHEMICAL_KINDS
    groups = [[e for e in index.get(key, []) if acceptable(e)] for key in name_keys(name)]
    written = unicodedata.normalize('NFKC', str(name)).strip(' .,;')
    terminal = re.search(r'\s+\(([A-Z][A-Za-z0-9-]{1,12})\)$', written)
    if terminal:
        prefix = name_keys(written[:terminal.start()])
        token = name_keys(terminal.group(1))
        if prefix and token:
            token_ids = {e['id'] for e in index.get(token[0], []) if acceptable(e)}
            groups.append([e for e in index.get(prefix[0], []) if acceptable(e) and e['id'] in token_ids])
    first = None
    for hits in groups:
        if hits:
            if preferred_id is not None:
                preferred = next((e for e in hits if e['id'] == preferred_id), None)
                if preferred:
                    return preferred
            if first is None:
                first = sorted(hits, key=rank)[0]
    return first


def bind_chemicals(atlas, records, doi_url, new_assets, only_material_ids=None):
    """Link each chemical to the site's molecule library. A name the library does not know gets a plain
    name card: no structure is drawn for it."""
    base = atlas / 'static/assets/chemical-registry'
    registry = json.loads((base / 'registry.json').read_text(encoding='utf-8')); bindings = json.loads((base / 'bindings.json').read_text(encoding='utf-8'))
    index = {}
    for e in registry['entries']:
        for name in [e['name']] + list(e.get('aliases') or []):
            for key in name_keys(name): index.setdefault(key, []).append(e)
    rank = lambda e: (e.get('depictionKind') != 'molecule' or not e.get('model3dPath'), not e.get('pubchemCid'), bool(re.search(r'(19|20)\d\d', e['id'])), len(e['id']))
    known = {e['id'] for e in registry['entries']}; matched = cards = 0
    for record in records:
        rid = record['record_id']; bound = dict(bindings['recordBindings'].get(rid, {})) if only_material_ids is not None else {}
        for m in record['materials']:
            if only_material_ids is not None and m['id'] not in only_material_ids:
                continue
            # an entry made for one paper's specimen, mixture or sample context is not a general chemical
            hit = chemical_match(index, m['name'], rank, bindings['recordBindings'].get(rid, {}).get(m['id']))
            if hit:
                bound[m['id']] = hit['id']; matched += 1; continue
            eid = 'name-card-' + slug(m['name'], 60)
            if eid not in known:
                caption = 'Name as printed in the paper. The chemical is not in the molecule library, so no formula or structure is shown.'
                esc = m['name'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="840" height="360" viewBox="0 0 840 360" role="img"><title>{esc}</title><desc>{caption}</desc>'
                       '<rect x="22" y="36" width="796" height="288" rx="18" fill="#f1f6fa" stroke="#ccdae5"/>'
                       f'<text x="420" y="159" text-anchor="middle" font-family="Arial,sans-serif" font-size="{44 if len(esc) < 24 else 26}" fill="#18384d">{esc[:60]}</text>'
                       '<text x="420" y="219" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" fill="#476276">Name as printed · no structure asserted</text></svg>\n')
                target = base / 'svg' / f'{eid}.svg'; target.write_text(svg, encoding='utf-8', newline='\n'); new_assets.append(target)
                registry['entries'].append({'id': eid, 'name': m['name'], 'aliases': [m['name']], 'depictionKind': 'formula', 'pubchemCid': None, 'formula': '', 'displayFormula': '',
                                            'sourceUrls': [doi_url or 'https://doi.org/'], 'svgPath': f'svg/{eid}.svg', 'model2dPath': None, 'model3dPath': None, 'functionalGroups': [],
                                            'limitations': ['Identity is the name printed in the source; it was not resolved against a chemical database.'],
                                            'provenance': {'connectivitySource': None, 'sourceLookupStatus': 'name_as_printed_not_resolved'}, 'caption': caption,
                                            'assetHashes': {'svgPath': sha_file(target)}})
                known.add(eid)
            bound[m['id']] = eid; cards += 1
        bindings['recordBindings'][rid] = bound
        bindings['sourceRecordSha256'][rid] = sha_file(atlas / 'data/records' / f'{rid}.json')
    dump_like(base / 'registry.json', registry)
    dump_like(base / 'bindings.json', bindings)
    return matched, cards


def source_collision(inventory, source_id, doi):
    """Existing audited sources and different source identities are never changed here."""
    return any(row.get('source_group') == source_id and
               (row.get('review_status') != 'source_extracted' or
                str(row.get('doi') or '').lower() != str(doi or '').lower())
               for row in inventory.get('per_paper', []))


def same_extracted_identity(existing, incoming):
    source_id = (incoming.get('lineage') or {}).get('source_group')
    doi = next((str(s.get('doi') or '').lower() for s in incoming.get('sources') or [] if s.get('id') == source_id), '')
    return bool(source_id and doi and
                (existing.get('quality') or {}).get('review_status') == 'source_extracted' and
                existing.get('record_id') == incoming.get('record_id') and
                (existing.get('lineage') or {}).get('source_group') == source_id and
                any(s.get('id') == source_id and str(s.get('doi') or '').lower() == doi
                    for s in existing.get('sources') or []))


def cmd_sync(a):
    """Write step diagrams, figures and the Reader entries for extracted records; align material pages with a build's hubs."""
    import hashlib, shutil
    repo = Path(a.repo); atlas = repo / 'recipe-atlas'; pairs_dir = Path(a.pairs)
    side_path = atlas / 'data/reader-presentation-reviewed.json'; side = load_reviewed_reader(side_path)
    new_assets = []
    side_changed = False
    inventory = json.loads((atlas / 'data/inventory-evidence.json').read_text(encoding='utf-8'))
    for f in sorted(pairs_dir.glob('*.pairs.json')):
        doc = json.loads(f.read_text(encoding='utf-8'))
        if doc.get('check') != 'two passes agree, quotes found':
            print(f'{doc.get("id") or f.stem}: not two-pass checked; left out'); continue
        builder, records = records_of(doc, a.include_optical)
        sid = builder.source_id
        if source_collision(inventory, sid, doc.get('doi')):
            print(f'{sid}: protected source identity; no presentation changed'); continue
        reactors = [((p.get('recipe') or {}).get('reactor') or {}).get('value') for p in doc.get('pairs') or []
                    if ((p.get('recipe') or {}).get('steps') or (p.get('recipe') or {}).get('chemicals')) and _composition_from(p) is not None]
        reactor_by_record = dict(zip((r['record_id'] for r in records), reactors))
        accepted = []
        for record in records:
            target = atlas / 'data/records' / f'{record["record_id"]}.json'
            if not target.is_file(): continue
            existing = json.loads(target.read_text(encoding='utf-8'))
            if not same_extracted_identity(existing, record):
                print(f'{record["record_id"]}: protected record identity; no presentation changed'); continue
            if existing != record:
                print(f'{record["record_id"]}: pair differs from canonical record; run records --replace first'); continue
            accepted.append(existing)
        records = accepted
        if not records: continue
        side_changed = True
        figures = []
        for fig in doc.get('figures') or []:
            src = pairs_dir / 'figures' / fig['file']
            if not src.is_file(): continue
            name = slug(fig.get('figure') or Path(fig['file']).stem) + '.png'
            target = atlas / 'static/assets/paper-reviews' / sid / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src, target)
            cats = [c for c in fig.get('categories') or [] if c in ('structure', 'property')] or ['other']
            scope = 'Figure from the paper, placed by its caption. It is not matched to a specific sample of this record.'
            figures.append({'id': f'{sid}-{slug(fig.get("figure") or name)}', 'source_id': sid, 'public_asset': f'assets/paper-reviews/{sid}/{name}', 'public_asset_sha256': sha_file(target),
                            'category': cats[0], 'categories': cats, 'title': fig.get('figure') or name, 'caption': f'{fig.get("figure") or "Source figure"}; cited main article, PDF page {fig.get("page") or "not reported"}. Automatic caption-based category: {" and ".join(cats)}. Paper-level evidence; no sample match is asserted.', 'summary': scope, 'scope': scope, 'sample_scope': scope,
                            **public_figure_caption(fig),
                            'source_locator': {'document_role': 'main', 'page': fig.get('page'), 'figure': fig.get('figure') or ''}, 'record_links': [r['record_id'] for r in records], 'sample_links': [],
                            'sample_links_by_record': {r['record_id']: [] for r in records}, 'selected_evidence_only': True, 'same_batch_asserted': False, 'copyright_permission_verified': False,
                            'provenance': {'render_tool': 'PyMuPDF automatic PDF figure-region crop', 'pdf_page': fig.get('page'), 'asset_sha256': sha_file(target), 'resampled': False,
                                           'crop_includes': 'Automatically selected figure-region graphics and nearby labels; raw caption text remains in the private working files; only an explicitly supplied public caption is displayed.', 'license_statement': 'permission_not_established', 'source_pixels_redrawn': False,
                                           **{k: fig[k] for k in ('source_pdf_sha256', 'render_dpi', 'page_size_pdf_points', 'crop_box_pdf_points', 'pixel_size') if k in fig}}})
            new_assets.append(target)
        if figures: side['figures_by_source'][sid] = figures
        for record in records:
            reactor = reactor_by_record.get(record['record_id'])
            rid = record['record_id']; record_path = atlas / 'data/records' / f'{rid}.json'
            if not record_path.is_file(): print(f'{rid}: record file missing; run "records" first'); continue
            digest = sha_file(record_path); pointer = lambda p: {'data_path': f'data/records/{rid}.json', 'json_pointer': p, 'input_sha256': digest}
            bindings = []
            for op in record['operations']:
                svg, caption = step_svg(op, reactor)
                target = atlas / 'static/assets/protocol' / f'{rid}-{op["id"]}.svg'; target.write_text(svg, encoding='utf-8', newline='\n'); new_assets.append(target)
                bindings.append({'operation_id': op['id'], 'asset_path': f'assets/protocol/{target.name}', 'asset_sha256': sha_file(target), 'caption': caption, 'source_locator': op['evidence'][0]['locator']})
            (atlas / 'static/data/protocol-art-bindings' / f'{rid}.json').write_text(json.dumps({'record_id': rid, 'source_record_sha256': digest, 'bindings': bindings}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
            sample = record['products'][0]['sample_id']; facts = []
            for i, m in enumerate(record['measurements']):
                v = m['value']
                facts.append({'label': m['property'].replace('_', ' ').capitalize(), 'value': f'{v["value"]:g} {v["unit"]}'.strip(), 'scope': f'{m["technique"]}; as stated for this product.', 'sample_id': sample,
                              'status': 'reported', 'source': pointer(f'/measurements/{i}/value'), 'source_locator': m['evidence'], 'record_id': rid, 'kind': 'measurement', 'measurement_id': m['id']})
            for key, label in (('phase', 'Crystal phase'), ('morphology', 'Shape'), ('surface', 'Surface ligand')):
                fact = record['products'][0][key]
                if fact['value'] is not None:
                    facts.append({'label': label, 'value': str(fact['value']), 'scope': 'As stated for this product.', 'sample_id': sample, 'status': 'reported',
                                  'source': pointer(f'/products/0/{key}'), 'source_locator': fact['evidence'], 'record_id': rid, 'kind': 'product_fact'})
            side['records'][rid] = {'source_id': sid, 'title': record['title'], 'material_formula': record['material']['formula'], 'conflictPairs': [], 'productFacts': facts, 'featuredProductFacts': [],
                                    'allProductFacts': facts, 'productContexts': [{'sample_id': sample, 'label': record['products'][0]['source_sample_label'] or 'Product', 'recipe_link': 'explicit',
                                                                                    'notes': record['products'][0]['notes'], 'record_id': rid, 'source': pointer('/products/0')}],
                                    'primary_product': {'record_id': rid, 'sample_ids': [sample], 'default_sample_id': sample}, 'nominalTarget': [],
                                    'figures': [dict(fig, source=pointer('/products')) for fig in figures], 'intuition': [],
                                    'scopeLabel': 'Synthesis and product as extracted from this paper. Other preparations in the paper are not covered.', 'source': pointer(''),
                                    'data_links': [{'label': 'Canonical record and evidence', 'url': f'records/{rid}.html?view=data#evidence'}],
                                    'availability': {'atomic_coordinates': 'not_reported', 'morphology_illustration': 'none', 'reference_cell': 'Bulk reference by composition, where the library has one.'},
                                    'protocol_art': {'record_id': rid, 'bindings': bindings}, 'presentation_status': 'pending'}
        matched, cards = bind_chemicals(atlas, [r for r in records if (atlas / 'data/records' / f'{r["record_id"]}.json').is_file()], builder.source()['url'], new_assets)
        print(f'{sid}: {matched} chemicals linked to the molecule library, {cards} shown as name cards')
        if figures: side['figures_by_source'][sid] = [dict(fig, source={'data_path': f'data/records/{records[0]["record_id"]}.json', 'json_pointer': '/products', 'input_sha256': sha_file(atlas / 'data/records' / f'{records[0]["record_id"]}.json')}) for fig in figures]
    if a.dist:  # material pages must list exactly the routes the site build puts on them
        hubs = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in (Path(a.dist) / 'data/materials').glob('*.json')}
        for hid, hub in hubs.items():
            is_new = hid not in side['materials']
            view = side['materials'].setdefault(hid, {'id': hid, 'formula': hub['formula'], 'record_ids': [], 'component_only': hub.get('component_only', False),
                                                      'scopeLabel': 'Source-specific methods and samples are kept separate.', 'figure_count': 0, 'property_figure_count': 0})
            if is_new or view['record_ids'] != hub['record_ids']: side_changed = True
            view['record_ids'] = hub['record_ids']
        for hid in [h for h in side['materials'] if h not in hubs]:
            del side['materials'][hid]; side_changed = True
        # the record baseline lists every record with its checksum; add the new rows exactly as the build computed them
        built = json.loads((Path(a.dist) / 'data/dataset-manifest.json').read_text(encoding='utf-8'))
        base_path = atlas / 'data/release-baseline-manifest.json'; base = json.loads(base_path.read_text(encoding='utf-8'))
        known = {r['record_id'] for r in base['records']}
        added = [r for r in built['records'] if r['record_id'] not in known]
        # rows of extracted records follow the record files; rows of reviewed records are never touched here
        extracted = {p.stem for p in (atlas / 'data/records').glob('*.json') if '"review_status": "source_extracted"' in p.read_text(encoding='utf-8')}
        fresh = {r['record_id']: r for r in built['records'] if r['record_id'] in extracted}
        stale = [i for i, r in enumerate(base['records']) if r['record_id'] in fresh and r != fresh[r['record_id']]]
        for i in stale: base['records'][i] = fresh[base['records'][i]['record_id']]
        if added or stale:
            import bisect
            ids = [r['record_id'] for r in base['records']]; in_order = ids == sorted(ids)
            for row in added:
                at = bisect.bisect(ids, row['record_id']) if in_order else len(ids)
                base['records'].insert(at, row); ids.insert(at, row['record_id'])
            for key in ('record_count', 'group_count', 'families'): base[key] = built[key]
            dump_like(base_path, base)
            print(f'baseline: {len(added)} new record rows, {len(stale)} refreshed')
    if side_changed: dump_like(side_path, side)
    print(f'reader entries: {sum(1 for v in side["records"].values() if v.get("presentation_status") == "pending" and "extracted" in v.get("scopeLabel", ""))} extracted records; {len(new_assets)} asset files written')


def inventory_entry(builder, doc, record_ids):
    """The site keeps one entry per paper saying what was read. This one says: extracted, not reviewed."""
    src = builder.source()
    pages = doc.get('pages_read') or []
    return {'source_group': builder.source_id, 'paper_id': builder.source_id, 'doi': src['doi'] or '', 'url': src['url'], 'title': src['title'], 'year': src['year'],
            'has_local_corpus_group': False, 'review_status': 'source_extracted',
            'review_scope': 'Synthesis and product pages of the main text, read by the extraction pipeline. Not a whole-paper reading and not an expert review.',
            'documents': [{'role': 'main', 'page_count': doc.get('page_count') or (max(pages) if pages else 0), 'pages_read': pages, 'actual_pages_text_read': pages,
                           'actual_pages_visually_read': [], 'all_text_read': bool(pages) and len(pages) == doc.get('page_count'), 'all_visually_reviewed': False,
                           'scope': 'Pages selected automatically as describing the synthesis and the product.'}],
            'evidence_locator': f'data/records/{record_ids[0]}.json', 'paper_review_url': None, 'main_status': 'extracted_not_expert_reviewed',
            'si_status': 'not_read', 'notes': [REVIEW_SCOPE], 'record_ids': record_ids}


def cmd_records(a):
    repo = Path(a.repo); out = repo / 'recipe-atlas/data/records'
    sys.path.insert(0, str(repo / 'recipe-atlas/scripts'))
    from schema_definition import SCHEMA
    import jsonschema
    validator = jsonschema.Draft202012Validator(SCHEMA)
    written = 0; omitted_composition = 0
    inventory_path = repo / 'recipe-atlas/data/inventory-evidence.json'; inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    on_site = {p['doi'].lower() for p in inventory['per_paper'] if p.get('doi') and p.get('review_status') != 'source_extracted'}
    for f in sorted(Path(a.pairs).glob('*.pairs.json')):
        doc = json.loads(f.read_text(encoding='utf-8'))
        if doc.get('check') != 'two passes agree, quotes found':
            print(f'{doc.get("id") or f.stem}: not two-pass checked; left out'); continue
        builder, records = records_of(doc, a.include_optical); ids = []
        if (doc.get('doi') or '').lower() in on_site:
            print(f'{doc["id"]}: {doc["doi"]} is already on the site as a reviewed paper; skipped'); continue
        if source_collision(inventory, builder.source_id, doc.get('doi')):
            print(f'{builder.source_id}: protected source identity; no records changed'); continue
        for index in getattr(builder, 'omitted_composition_indices', []):
            print(f'{builder.source_id}: pair {index} left out: missing composition and no chemical formula in product')
            omitted_composition += 1
        for record in records:
            if (record.get('material') or {}).get('elements') == []:
                print(f'{record["record_id"]}: left out: technical unresolved composition for navigation; original pair unchanged, not a source-absence decision')
                continue
            errors = sorted(validator.iter_errors(record), key=lambda e: list(e.path))
            if errors:
                print(f'{record["record_id"]}: NOT WRITTEN, {len(errors)} schema errors; first: {"/".join(map(str, errors[0].path))}: {errors[0].message[:160]}'); continue
            target = out / f'{record["record_id"]}.json'
            if target.exists() and not same_extracted_identity(json.loads(target.read_text(encoding='utf-8')), record):
                print(f'{record["record_id"]}: protected record identity; not replaced'); continue
            if target.exists() and not a.replace:
                print(f'{record["record_id"]}: already exists, skipped'); ids.append(record['record_id']); continue
            target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n'); written += 1
            ids.append(record['record_id'])
            print(f'{record["record_id"]}: {len(record["materials"])} chemicals, {len(record["operations"])} steps, {len(record["measurements"])} measurements')
        if ids and not any(p['source_group'] == builder.source_id for p in inventory['per_paper']):
            inventory['per_paper'].append(inventory_entry(builder, doc, ids))
    dump_like(inventory_path, inventory)
    print(f'{written} records written to {out}')
    if omitted_composition:
        print(f'{omitted_composition} pairs left out: missing composition and no chemical formula in product')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('records'); r.add_argument('pairs'); r.add_argument('--repo', required=True); r.add_argument('--replace', action='store_true')
    r.add_argument('--include-optical', action='store_true', help='also write absorption and emission peaks and quantum yield (held back by default)'); r.set_defaults(fn=cmd_records)
    s = sub.add_parser('sync'); s.add_argument('pairs'); s.add_argument('--repo', required=True)
    s.add_argument('--dist', help='dist folder of a site build attempt; its material pages decide which routes each material lists')
    s.add_argument('--include-optical', action='store_true'); s.set_defaults(fn=cmd_sync)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
