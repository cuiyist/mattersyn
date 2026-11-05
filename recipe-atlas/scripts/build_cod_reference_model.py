"""Write the reader model for a COD bulk reference CIF, in the library's existing format.

  python recipe-atlas/scripts/build_cod_reference_model.py --cif <COD id>.cif --id <entry id> \
      --name "<name>" --formula <formula> --scope "<scope>" --retrieved-date YYYY-MM-DD --out models/<id>.json

Fractional sites are expanded with the symmetry operations of the CIF, in CIF order,
wrapped into one half-open unit cell and deduplicated; Cartesian coordinates are the
fractional coordinates times the cell vectors. No relaxation or fitting is done and the
CIF bytes are not changed. Partially occupied sites keep their occupancy and are marked
as statistical sites; sites shared by several elements become one mixed site "X".
Needs gemmi (CIF parsing and symmetry operators only).
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import gemmi

NOTES = [
    'Fractional sites are expanded using the symmetry operations of the original CIF, including its origin choice; no structure relaxation or coordinate fitting was performed.',
    'Cartesian coordinates equal the source-cell fractional coordinates multiplied by the source cell vectors. Sites are wrapped into one half-open periodic unit cell.',
    'A periodic unit cell is not a complete finite nanocrystal. No particle cut, dopant substitution, surface termination or ligand decoration is generated.',
]
STATISTICAL_NOTE = 'Partially occupied or shared sites are statistical crystallographic populations, not independently occupied atoms or one ordered microstate.'
TOL = 1e-4


def text(block, *tags):
    for tag in tags:
        value = block.find_value(tag)
        if value not in (None, '?', '.'):
            return gemmi.cif.as_string(value).strip()
    return None


def number(value, default=None):
    if value is None or value in ('?', '.'):
        if default is None:
            raise ValueError('missing CIF number')
        return default
    return gemmi.cif.as_number(value)


def wrap(f):
    out = []
    for v in f:
        v = v - int(v // 1)
        if v >= 1 - TOL or abs(v) < TOL:
            v = 0.0
        out.append(v)
    return out


def same(a, b):
    return all(min(abs(x - y), 1 - abs(x - y)) < TOL for x, y in zip(a, b))


def r(value, digits):
    value = round(value, digits)
    return 0.0 if value == 0 else value


def model(cif_path, entry_id, name, formula, scope, retrieved):
    raw = Path(cif_path).read_bytes()
    block = gemmi.cif.read_string(raw.decode('utf-8')).sole_block()
    lengths = [number(block.find_value(t)) for t in ('_cell_length_a', '_cell_length_b', '_cell_length_c')]
    angles = [number(block.find_value(t), 90.0) for t in ('_cell_angle_alpha', '_cell_angle_beta', '_cell_angle_gamma')]
    cell = gemmi.UnitCell(*lengths, *angles)
    ops = list(block.find_values('_space_group_symop_operation_xyz')) or list(block.find_values('_symmetry_equiv_pos_as_xyz'))
    ops = [gemmi.Op(gemmi.cif.as_string(o)) for o in ops]
    sites = block.find('_atom_site_', ['label', 'fract_x', 'fract_y', 'fract_z', '?type_symbol', '?occupancy'])
    expanded = []  # [fractional, [(element, occupancy, label)]]
    for row in sites:
        label = row.str(0)
        symbol = re.match(r'[A-Z][a-z]?', row.str(4) if row.has(4) else label)  # 'S2-' -> 'S'
        element = gemmi.Element(symbol.group(0) if symbol else label).name
        occ = number(row[5], 1.0) if row.has(5) else 1.0
        base = [number(row[1]), number(row[2]), number(row[3])]
        seen = []
        for op in ops:
            f = wrap(op.apply_to_xyz(base))
            if any(same(f, s) for s in seen):
                continue
            seen.append(f)
            hit = next((e for e in expanded if same(e[0], f)), None)
            if hit:
                hit[1].append((element, occ, label))
            else:
                expanded.append([f, [(element, occ, label)]])
    m = cell.orth.mat.tolist()
    vectors = [[r(m[0][i], 8), r(m[1][i], 8), r(m[2][i], 8)] for i in range(3)]
    atoms, counters, statistical, mixed = [], {}, False, False
    for f, parts in expanded:
        labels = [p[2] for p in parts]
        site = '/'.join(dict.fromkeys(labels))
        counters[site] = counters.get(site, 0) + 1
        cart = cell.orthogonalize(gemmi.Fractional(*f))
        multi = len({p[0] for p in parts}) > 1
        partial = multi or any(abs(p[1] - 1) > 1e-6 for p in parts)
        statistical |= partial
        mixed |= multi
        components = [{'element': e, 'occupancy': o, 'asymmetric_site_label': l} for e, o, l in parts]
        atoms.append({'element': 'X' if multi else parts[0][0], 'x': r(cart.x, 8), 'y': r(cart.y, 8), 'z': r(cart.z, 8),
                      'occupancy': 1.0 if multi else parts[0][1], 'site': site, 'label': f'{site}_{counters[site]}',
                      'mixed_site': multi, 'components': components, 'fractional': [r(v, 6) for v in f],
                      'properties': {'site_label': site, 'occupancies': {e: o for e, o, _ in parts}, 'statistical_site': partial}})
    cod = text(block, '_cod_database_code') or Path(cif_path).stem
    authors = [gemmi.cif.as_string(a) for a in block.find_values('_publ_author_name')]
    out = {
        'id': entry_id, 'name': name, 'formula': formula,
        'atoms': atoms,
        'cell': {k: getattr(cell, k) for k in ('a', 'b', 'c', 'alpha', 'beta', 'gamma')},
        'cellVectors': vectors,
        'spaceGroup': text(block, '_space_group_name_H-M_alt', '_symmetry_space_group_name_H-M'),
        'spaceGroupNumber': int(number(block.find_value('_space_group_IT_number') or block.find_value('_symmetry_Int_Tables_number'))),
        'units': 'angstrom', 'periodic': True, 'representation': 'conventional_unit_cell_sites',
        'mixedOccupancy': mixed, 'mixedSiteSymbol': 'X represents a statistical shared site, not an extra element.' if mixed else None,
        'source': {'database': 'Crystallography Open Database', 'entry': cod,
                   'record_url': f'https://www.crystallography.net/cod/{cod}.html', 'cif_url': f'https://www.crystallography.net/cod/{cod}.cif',
                   'authors': authors, 'title': ' '.join((text(block, '_publ_section_title') or '').split()),
                   'journal': text(block, '_journal_name_full'), 'year': text(block, '_journal_year'), 'doi': text(block, '_journal_coden_DOI', '_journal_DOI'),
                   'license': 'COD data are in the public domain; the original notice in the CIF is retained.',
                   'cif_file': Path(cif_path).name, 'sha256': hashlib.sha256(raw).hexdigest(), 'retrieved_date': retrieved,
                   'source_formula': text(block, '_chemical_formula_sum'), 'formula_units_Z': text(block, '_cell_formula_units_Z'),
                   'journal_volume': text(block, '_journal_volume'), 'journal_page_first': text(block, '_journal_page_first')},
        'sourceType': 'literature_bulk_reference', 'phaseScope': scope, 'scope': scope, 'caption': name + '. ' + scope,
        'training_eligible': False, 'measured_sample_structure': False,
        'renderingNotes': NOTES + ([STATISTICAL_NOTE] if statistical else []),
    }
    return out, statistical, mixed


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ('cif', 'id', 'name', 'formula', 'scope', 'retrieved-date', 'out'):
        p.add_argument('--' + name, required=True)
    a = p.parse_args()
    out, _, _ = model(a.cif, a.id, a.name, a.formula, a.scope, a.retrieved_date)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
