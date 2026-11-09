"""Authored general chemistry background; no source interpretation is generated.

Selection reads only one record's own J route and explicit reported roles.
The immutable source records and reviewed Reader sidecar are never modified.
"""
import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from method_families import NAMED_METHODS, ROUTE_CLASSES, route

SCHEMA = 'mattersyn-reader-background-library/1'
LABEL = "General background, not the authors' interpretation"
LIMIT = 3
DOI = re.compile(r'^10\.\d{4,9}/\S+$', re.I)
ID = re.compile(r'^[a-z][a-z0-9-]*$')
ROLE_PRIORITY = ('carboxylic-acid-ligand', 'amine-ligand', 'phosphine',
                 'phosphine-oxide', 'noncoordinating-solvent', 'metal-source',
                 'chalcogen-pnictogen-source', 'reducing-agent', 'antisolvent',
                 'ligand', 'solvent')
EXCLUDED_ROLE = re.compile(r'\b(?:not used|unused|inventory(?: only)?|source listed|not reported|unknown|unspecified|unresolved|unassigned)\b')
ELEMENTS = ('cadmium', 'zinc', 'indium', 'lead', 'gold', 'silver', 'gallium',
            'copper', 'iron', 'nickel', 'cobalt', 'manganese', 'tin', 'titanium',
            'aluminium', 'aluminum', 'chromium', 'platinum', 'palladium', 'metal')
NONMETALS = ('selenium', 'sulfur', 'sulphur', 'tellurium', 'arsenic',
             'phosphorus', 'chalcogen', 'pnictogen', 'nonmetal', 'non metal')
ACIDS = {'oleic acid', 'oleate', 'stearic acid', 'stearate', 'myristic acid',
         'myristate', 'palmitic acid', 'palmitate', 'lauric acid', 'laurate',
         'octanoic acid', 'octanoate', 'acetic acid', 'acetate'}
AMINES = {'oleylamine', 'octylamine', 'hexadecylamine', 'dodecylamine',
          'octadecylamine', 'dioctylamine', 'trioctylamine'}
PHOSPHINES = {'trioctylphosphine', 'tri n octylphosphine', 'top',
              'tributylphosphine', 'tri n butylphosphine', 'tbp', 'triphenylphosphine'}
PHOSPHINE_OXIDES = {'trioctylphosphine oxide', 'tri n octylphosphine oxide', 'topo',
                   'tributylphosphine oxide', 'triphenylphosphine oxide'}


def words(value):
    return re.sub(r'\s+', ' ', re.sub(r'[_\-]+', ' ', str(value or '')).casefold()).strip()


def reported_roles(record):
    """Finite role aliases; names may subtype an explicitly reported ligand only.

    Neither a molecule's formula/model nor generic reagent status assigns a role.
    The entry is background about the reported role, never a source-specific claim.
    """
    found = set()
    for material in record.get('materials', []):
        role = words(material.get('role'))
        if not role or EXCLUDED_ROLE.search(role):
            continue
        name = words(material.get('name'))
        if re.fullmatch(r'(?:carboxylic acid|carboxylate)(?: surface)? ligand', role):
            found.add('carboxylic-acid-ligand')
        elif re.fullmatch(r'(?:primary |secondary |tertiary )?amine(?: surface)? ligand', role):
            found.add('amine-ligand')
        elif role in {'phosphine', 'phosphine ligand', 'phosphine solvent', 'phosphine precursor solvent'}:
            found.add('phosphine')
        elif role in {'phosphine oxide', 'phosphine oxide ligand', 'phosphine oxide solvent'}:
            found.add('phosphine-oxide')
        elif role in {'ligand', 'surface ligand', 'capping ligand', 'capping agent', 'coordinating ligand'}:
            if name in ACIDS:
                found.add('carboxylic-acid-ligand')
            elif name in AMINES:
                found.add('amine-ligand')
            elif name in PHOSPHINES:
                found.add('phosphine')
            elif name in PHOSPHINE_OXIDES:
                found.add('phosphine-oxide')
            else:
                found.add('ligand')
        elif role in {'non coordinating solvent', 'noncoordinating solvent'}:
            found.add('noncoordinating-solvent')
        elif role in {'solvent', 'reaction solvent', 'dispersion solvent'}:
            found.add('solvent')
        elif role in {'reducing agent', 'reductant'}:
            found.add('reducing-agent')
        elif role in {'antisolvent', 'anti solvent', 'precipitating solvent', 'precipitation solvent'}:
            found.add('antisolvent')
        else:
            source = r'(?:source|precursor)(?: (?:solute|feed|component|stock component|reagent))?'
            if re.fullmatch(r'(?:main |initial |aqueous |gas phase )?(?:'+'|'.join(ELEMENTS)+r') '+source, role):
                found.add('metal-source')
            elif re.fullmatch(r'(?:main |initial |aqueous |gas phase )?(?:'+'|'.join(NONMETALS)+r') '+source, role):
                found.add('chalcogen-pnictogen-source')
    # A specific reported ligand category subsumes the generic ligand card.
    if found & {'carboxylic-acid-ligand', 'amine-ligand', 'phosphine', 'phosphine-oxide'}:
        found.discard('ligand')
    if 'noncoordinating-solvent' in found:
        found.discard('solvent')
    return [key for key in ROLE_PRIORITY if key in found]


def validate_library(library, pins):
    if library.get('schema') != SCHEMA or library.get('label') != LABEL or library.get('limit') != LIMIT:
        raise ValueError('Invalid authored background library schema/label/limit')
    if pins.get('schema') != 'mattersyn-reader-background-doi-pins/1':
        raise ValueError('Invalid background DOI pin schema')
    references = library.get('references')
    if not isinstance(references, dict) or not references:
        raise ValueError('Background references are required')
    for key, ref in references.items():
        pin = pins.get('references', {}).get(key, {})
        doi = ref.get('doi', '')
        if (not DOI.fullmatch(doi) or ref.get('url') != 'https://doi.org/'+doi
                or ref.get('kind') not in {'review', 'textbook'} or not ref.get('title')
                or pin.get('doi', '').casefold() != doi.casefold()
                or not pin.get('resolver_redirect_verified') or not pin.get('exact_DOI_metadata_verified')
                or not re.fullmatch(r'[a-f0-9]{64}', pin.get('metadata_response_sha256', ''))
                or pin.get('paper_or_abstract_requested') is not False):
            raise ValueError('Unverified background reference: '+key)
    items = library.get('statements')
    if not isinstance(items, list) or not items:
        raise ValueError('Authored background statements are required')
    ids = set()
    for item in items:
        key, text = item.get('id', ''), item.get('summary', '')
        if not ID.fullmatch(key) or key in ids:
            raise ValueError('Duplicate/invalid background statement ID')
        ids.add(key)
        # Statement bodies contain no recipe values/numbers. Citation years/DOIs
        # are separate reference metadata, not scientific statements.
        if (not isinstance(text, str) or not 35 <= len(text) <= 520
                or any(c.isdigit() for c in text)
                or not 1 <= len(re.findall(r'[.!?](?:\s|$)', text)) <= 2
                or not item.get('title') or item.get('reference') not in references):
            raise ValueError('Invalid short authored background statement: '+key)
    expected_routes = {name for name, _ in ROUTE_CLASSES+NAMED_METHODS}
    if set(library.get('routes', {})) != expected_routes:
        raise ValueError('Background route map must cover exact J route classes and named methods')
    if set(library.get('roles', {})) != set(ROLE_PRIORITY):
        raise ValueError('Background role map differs from finite selector roles')
    if (any(key not in ids for table in ('routes', 'roles') for key in library[table].values())
            or library.get('fallback') not in ids):
        raise ValueError('Background selector points to an unknown statement')
    return library


def load_library(root):
    root = Path(root)
    raw = (root/'data/reader-background-library.json').read_bytes()
    pins = json.loads((root/'scripts/reader_background_reference_pins.json').read_bytes())
    return validate_library(json.loads(raw), pins)


def select_background(record, presentation, library):
    """One route then ordered distinct roles, or a universal nonmechanistic fallback."""
    by_id = {item['id']: item for item in library['statements']}
    selected = []
    own_route = route(record, presentation.get('method_label'))
    if own_route in library['routes']:
        selected.append(library['routes'][own_route])
    selected.extend(library['roles'][role] for role in reported_roles(record))
    selected = list(dict.fromkeys(selected))[:LIMIT] or [library['fallback']]
    result = []
    for key in selected:
        item = by_id[key]
        ref = library['references'][item['reference']]
        result.append({'id': key, 'title': item['title'], 'summary': item['summary'],
                       'label': LABEL, 'reference': copy.deepcopy(ref)})
    return result


def attach_background(view, records, library):
    """Return a new projection and quote-free counts; every original field is retained."""
    projected = {}
    counts = Counter()
    selection_counts = Counter()
    before_visible = 0
    for rid, entry in view['records'].items():
        record = records[rid]
        # Match the existing Reader's source-array precedence, including [] truthiness
        # in JavaScript (an explicitly empty intuition array wins over the alias).
        source_items = source_interpretations(entry)
        source = bool(source_items)
        background = select_background(record, entry, library)
        counts['both' if source else 'background_only'] += 1
        counts['source_content_before'] += int(source)
        counts['source_cards_before'] += min(len(source_items), 3)
        before_visible += int(source or record.get('lineage', {}).get('source_group') == 'wu2008')
        selection_counts[str(len(background))] += 1
        projected[rid] = {**entry, 'general_background': background}
    coverage = {'schema': 'mattersyn-reader-background-coverage/1',
                'canonical_records': len(records), 'reader_records': len(projected),
                'before_sections_visible': before_visible,
                'before_sections_with_source_content': counts['source_content_before'],
                'after_sections_visible': len(projected),
                'source_cards_before_and_after': counts['source_cards_before'],
                'source_only': 0, 'background_only': counts['background_only'],
                'both': counts['both'], 'neither': 0,
                'background_card_distribution': {str(n): selection_counts[str(n)] for n in range(4)},
                'status_affects_selection': False, 'scientific_record_values_modified': False,
                'scope': 'Current Reader records; protected source-only placeholder sections count as visible before, not as source content.'}
    return {**view, 'records': projected}, coverage


def source_interpretations(entry):
    items = entry.get('intuition')
    # Empty arrays are truthy in the existing browser expression. Null/missing,
    # false and empty-string values fall through to its legacy alias.
    if items is None or items is False or items == '' or items == 0:
        items = entry.get('chemical_intuition', [])
    if not isinstance(items, list):
        raise ValueError('Reader source interpretations must be an array')
    return items


def library_digest(root):
    return hashlib.sha256((Path(root)/'data/reader-background-library.json').read_bytes()).hexdigest()
