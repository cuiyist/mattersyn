#!/usr/bin/env python3
"""Add bulk reference unit cells to the MatterSyn crystal library from COD CIF files.

  python add_crystal_references.py --repo <mattersyn checkout> --cif-dir <folder of COD .cif files> --list chosen.json
  python add_crystal_references.py --verify <mattersyn checkout>      # rebuild existing models and compare

For each CIF it writes the site's model file (every atom of the conventional cell, from the CIF's own
symmetry operations), a registry entry and the matching pin. Entries are bound to no record: the
Reader shows them through the composition default. Standard library only.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, shlex
from collections import Counter
from fractions import Fraction
from pathlib import Path

SCOPE = ('Independent bulk reference for comparison. It is not a structure of any synthesized sample and does not '
         'establish a sample phase, particle size, surface, defects, ligands, strain or interface.')
NOTES = ['Fractional sites are expanded using the symmetry operations of the original CIF, including its origin choice; no structure relaxation or coordinate fitting was performed.',
         'Cartesian coordinates equal the source-cell fractional coordinates multiplied by the source cell vectors. Sites are wrapped into one half-open periodic unit cell.',
         'A periodic unit cell is not a complete finite nanocrystal. No particle cut, dopant substitution, surface termination or ligand decoration is generated.']


def number(text):
    """'4.0862(3)' -> 4.0862 ; '1/3' -> 0.3333"""
    text = str(text).strip().split('(')[0]
    return float(Fraction(text)) if '/' in text else float(text)


def read_cif(text):
    """Return ({tag: value}, [loops]) where each loop is (tags, rows). Handles quotes and ';' text blocks."""
    tokens, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(';'):
            block = [line[1:]]; i += 1
            while i < len(lines) and not lines[i].startswith(';'):
                block.append(lines[i]); i += 1
            tokens.append(('text', '\n'.join(block).strip())); i += 1; continue
        if not line.strip().startswith('#'):
            lex = shlex.shlex(line, posix=True); lex.whitespace_split = True; lex.commenters = ''
            try:
                tokens += [('word', t) for t in lex]
            except ValueError:  # an apostrophe inside a word, e.g. a name
                tokens += [('word', t) for t in line.split()]
        i += 1
    tags, loops, k = {}, [], 0
    while k < len(tokens):
        value = tokens[k][1]
        if tokens[k][0] == 'word' and value.lower() == 'loop_':
            k += 1; names = []
            while k < len(tokens) and tokens[k][0] == 'word' and tokens[k][1].startswith('_'):
                names.append(tokens[k][1].lower()); k += 1
            cells = []
            while k < len(tokens) and not (tokens[k][0] == 'word' and (tokens[k][1].startswith('_') or tokens[k][1].lower() in ('loop_',) or tokens[k][1].lower().startswith('data_'))):
                cells.append(tokens[k][1]); k += 1
            loops.append((names, [cells[j:j + len(names)] for j in range(0, len(cells) - len(names) + 1, len(names))]))
        elif tokens[k][0] == 'word' and value.startswith('_') and k + 1 < len(tokens):
            tags[value.lower()] = tokens[k + 1][1]; k += 2
        else:
            k += 1
    return tags, loops


def symmetry_function(expression):
    """'-x+1/2, y, -z' -> function mapping (x, y, z) to the image position."""
    rows = []
    for part in expression.lower().replace(' ', '').split(','):
        coeff, shift = [0.0, 0.0, 0.0], 0.0
        for sign, num, den, axis in re.findall(r'([+-]?)(\d*\.?\d*)(?:/(\d+))?([xyz]?)', part):
            if not num and not axis: continue
            value = (float(num) if num else 1.0) / (float(den) if den else 1.0) * (-1 if sign == '-' else 1)
            if axis: coeff['xyz'.index(axis)] += value
            else: shift += value
        rows.append((coeff, shift))
    return lambda p: tuple((sum(c * v for c, v in zip(coeff, p)) + shift) % 1.0 for coeff, shift in rows)


def cell_vectors(a, b, c, alpha, beta, gamma):
    al, be, ga = (math.radians(x) for x in (alpha, beta, gamma))
    bx, by = b * math.cos(ga), b * math.sin(ga)
    cx = c * math.cos(be); cy = c * (math.cos(al) - math.cos(be) * math.cos(ga)) / math.sin(ga)
    cz = math.sqrt(max(c * c - cx * cx - cy * cy, 0.0))
    tidy = lambda v: [round(x, 8) + 0.0 for x in v]
    return [tidy([a, 0, 0]), tidy([bx, by, 0]), tidy([cx, cy, cz])]


def element_of(symbol):
    m = re.match(r'([A-Z][a-z]?)', symbol.strip())
    return m.group(1) if m else symbol


def build_model(cif_text):
    tags, loops = read_cif(cif_text)
    cell = {k: number(tags['_cell_length_' + k]) for k in 'abc'}
    cell.update({k: number(tags['_cell_angle_' + k]) for k in ('alpha', 'beta', 'gamma')})
    ops = next(([row[names.index(t)] for row in rows] for names, rows in loops
                for t in ('_space_group_symop_operation_xyz', '_symmetry_equiv_pos_as_xyz') if t in names), ['x,y,z'])
    names, rows = next((n, r) for n, r in loops if '_atom_site_fract_x' in n)
    col = lambda row, tag, default=None: row[names.index(tag)] if tag in names else default
    vectors = cell_vectors(**cell)
    sites = {}  # wrapped position -> {(element, asymmetric label): occupancy}

    def same_site(p, q, tol=0.002):  # CIF values such as 0.3333 and 0.6667 give images that differ in the fourth decimal
        return all(min(abs(u - v), 1 - abs(u - v)) < tol for u, v in zip(p, q))
    for row in rows:
        label = col(row, '_atom_site_label'); element = element_of(col(row, '_atom_site_type_symbol') or label)
        occupancy = number(col(row, '_atom_site_occupancy', '1') or '1') if col(row, '_atom_site_occupancy', '1') not in ('.', '?') else 1.0
        base = tuple(number(col(row, '_atom_site_fract_' + ax)) for ax in 'xyz')
        for op in ops:
            p = symmetry_function(op)(base)
            key = tuple(0.0 if v > 1 - 1e-4 else round(v, 6) for v in p)
            key = next((q for q in sites if same_site(q, key)), key)
            sites.setdefault(key, {}).setdefault((element, label), occupancy)
    atoms, mixed_any = [], False
    for n, (frac, parts) in enumerate(sorted(sites.items(), key=lambda kv: (sorted(e for e, _ in kv[1])[0], kv[0])), 1):
        comps = [{'element': e, 'occupancy': occ, 'asymmetric_site_label': lab} for (e, lab), occ in parts.items()]
        elements = {c['element'] for c in comps}; mixed = len(elements) > 1; mixed_any |= mixed
        xyz = [round(sum(frac[i] * vectors[i][j] for i in range(3)), 8) + 0.0 for j in range(3)]
        symbol = 'X' if mixed else comps[0]['element']; site_label = '/'.join(c['element'] for c in comps) if mixed else comps[0]['asymmetric_site_label']
        atoms.append({'element': symbol, 'x': xyz[0], 'y': xyz[1], 'z': xyz[2], 'occupancy': round(sum(c['occupancy'] for c in comps), 6) if mixed else comps[0]['occupancy'],
                      'site': site_label, 'label': f'{site_label}_{n}', 'mixed_site': mixed, 'components': comps, 'fractional': [round(v, 6) for v in frac],
                      'properties': {'site_label': site_label, 'occupancies': {c['element']: c['occupancy'] for c in comps}, 'statistical_site': mixed}})
    info = {'space_group': tags.get('_symmetry_space_group_name_h-m') or tags.get('_space_group_name_h-m_alt') or '',
            'space_group_number': int(tags.get('_space_group_it_number') or tags.get('_symmetry_int_tables_number') or 0),
            'formula': tags.get('_chemical_formula_sum', ''), 'Z': tags.get('_cell_formula_units_z'),
            'title': ' '.join((tags.get('_publ_section_title') or '').split()), 'journal': tags.get('_journal_name_full'), 'year': tags.get('_journal_year'),
            'volume': tags.get('_journal_volume'), 'page_first': tags.get('_journal_page_first'), 'doi': tags.get('_journal_paper_doi'),
            'authors': next(([row[0] for row in r] for n, r in loops if n == ['_publ_author_name']), []), 'cod': tags.get('_cod_database_code')}
    return cell, vectors, atoms, mixed_any, info


def counts(atoms):
    total = Counter()
    for a in atoms:
        for c in a['components']: total[c['element']] += c['occupancy']
    return {k: round(v, 6) for k, v in sorted(total.items())}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def add_entries(repo, cif_dir, chosen, retrieved):
    base = repo / 'recipe-atlas/static/assets/crystal-references'
    registry_path, pins_path = base / 'registry.json', repo / 'recipe-atlas/scripts/crystal_reference_pins.json'
    registry, pins = json.loads(registry_path.read_text(encoding='utf-8')), json.loads(pins_path.read_text(encoding='utf-8'))
    have = {e['id'] for e in registry['entries']}
    for item in chosen:
        cod, formula, phase = str(item['cod']), item['formula'], item['phase']
        cid = re.sub(r'[^a-z0-9]+', '-', f'{formula}-{phase}'.lower()).strip('-') + f'-cod-{cod}'
        if cid in have: print('already present:', cid); continue
        cif = (cif_dir / f'{cod}.cif').read_bytes()
        cell, vectors, atoms, mixed, info = build_model(cif.decode('utf-8', errors='replace'))
        info['space_group_number'] = item.get('space_group_number') or info['space_group_number']  # a few CIFs omit the number
        if not info['space_group_number'] or not atoms: print('SKIPPED (no space group number or atoms):', cid); continue
        name = f'{formula} {phase} bulk reference'; url = f'https://www.crystallography.net/cod/{cod}.html'
        scope = f'Bulk {phase} {formula} (COD {cod}). ' + SCOPE
        model = {'id': cid, 'name': name, 'formula': formula, 'atoms': atoms, 'cell': cell, 'cellVectors': vectors, 'spaceGroup': info['space_group'],
                 'spaceGroupNumber': info['space_group_number'], 'units': 'angstrom', 'periodic': True, 'representation': 'conventional_unit_cell_sites',
                 'mixedOccupancy': mixed, 'mixedSiteSymbol': 'X represents a statistical mixed site, not an extra element.' if mixed else None,
                 'source': {'database': 'Crystallography Open Database', 'entry': cod, 'record_url': url, 'cif_url': f'https://www.crystallography.net/cod/{cod}.cif',
                            'authors': info['authors'], 'title': info['title'], 'journal': info['journal'], 'year': info['year'], 'doi': info['doi'],
                            'license': 'COD data are in the public domain; the original notice in the CIF is retained.', 'cif_file': f'{cod}.cif', 'sha256': sha(cif),
                            'retrieved_date': retrieved, 'source_formula': info['formula'], 'formula_units_Z': info['Z'], 'journal_volume': info['volume'], 'journal_page_first': info['page_first']},
                 'sourceType': 'literature_bulk_reference', 'phaseScope': scope, 'scope': scope, 'caption': f'{name}. {scope}',
                 'training_eligible': False, 'measured_sample_structure': False, 'renderingNotes': NOTES}
        model_bytes = (json.dumps(model, ensure_ascii=False, indent=1) + '\n').encode('utf-8')
        (base / f'{cod}.cif').write_bytes(cif); (base / 'models').mkdir(exist_ok=True); (base / 'models' / f'{cid}.json').write_bytes(model_bytes)
        entry = {'id': cid, 'name': name, 'formula': formula, 'record_ids': [], 'material_ids': [], 'description': f'{name}. {SCOPE}', 'scope': scope, 'phaseScope': scope,
                 'sourceType': 'literature_bulk_reference', 'sourceUrl': url, 'cifPath': f'{cod}.cif', 'modelPath': f'models/{cid}.json', 'spaceGroup': info['space_group'],
                 'spaceGroupNumber': info['space_group_number'], 'mixedOccupancy': mixed, 'cifSha256': sha(cif), 'modelSha256': sha(model_bytes), 'referenceOnly': True,
                 'trainingEligible': False, 'measuredSampleStructure': False, 'referenceType': 'literature_bulk_reference', 'structureAssetRole': 'external_reference_unit_cell',
                 'displayPolicy': 'independent_reference', 'defaultForSample': False, 'phaseName': phase}
        registry['entries'].append(entry)
        pins['entries'].append({'id': cid, 'cif_sha256': sha(cif), 'model_sha256': sha(model_bytes), 'expected_occupancy_weighted_counts': counts(atoms),
                                'space_group_number': info['space_group_number'],
                                'qualified_entry_semantic_sha256': sha(json.dumps(entry, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()),
                                'record_ids': [], 'reference_type': 'literature_bulk_reference', 'display_policy': 'independent_reference', 'default_for_sample': False, 'source_url': url})
        have.add(cid)
        print(f'added {cid}: {len(atoms)} atoms {counts(atoms)}  {info["space_group"]} (#{info["space_group_number"]})')
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    pins_path.write_text(json.dumps(pins, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def verify(repo):
    """Rebuild models for CIFs already in the library and compare the atom positions with the stored models."""
    base = repo / 'recipe-atlas/static/assets/crystal-references'
    ok = bad = 0
    for e in json.loads((base / 'registry.json').read_text(encoding='utf-8'))['entries']:
        if not str(e.get('sourceUrl', '')).startswith('https://www.crystallography.net/cod/') or not (base / e['cifPath']).is_file(): continue
        stored = json.loads((base / e['modelPath']).read_text(encoding='utf-8'))
        try:
            cell, vectors, atoms, mixed, info = build_model((base / e['cifPath']).read_text(encoding='utf-8', errors='replace'))
        except Exception as error:
            print('cannot rebuild', e['id'], type(error).__name__, error); bad += 1; continue
        close = lambda p, q: all(min(abs(u % 1.0 - v % 1.0), 1 - abs(u % 1.0 - v % 1.0)) < 0.003 for u, v in zip(p, q))
        theirs = [a for a in stored['atoms'] if 'fractional' in a]; left = list(theirs); mine = atoms
        for a in atoms:  # every rebuilt atom must have its own partner in the stored model
            hit = next((b for b in left if b['element'] == a['element'] and close(a['fractional'], b['fractional'])), None)
            if hit is not None: left.remove(hit)
        same = len(atoms) == len(theirs) and not left and all(abs(vectors[i][j] - stored['cellVectors'][i][j]) < 1e-3 for i in range(3) for j in range(3))
        ok += same; bad += not same
        if not same: print('DIFFERENT', e['id'], e['cifPath'], len(mine), 'vs', len(theirs))
    print(f'verify: {ok} models reproduced, {bad} different')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', type=Path); ap.add_argument('--cif-dir', type=Path); ap.add_argument('--list', type=Path)
    ap.add_argument('--retrieved', default=''); ap.add_argument('--verify', type=Path)
    a = ap.parse_args()
    if a.verify: verify(a.verify)
    else: add_entries(a.repo, a.cif_dir, json.loads(a.list.read_text(encoding='utf-8')), a.retrieved)


if __name__ == '__main__':
    main()
