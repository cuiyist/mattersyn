#!/usr/bin/env python3
"""Source-free consistency checks for MatterSyn canonical records (read-only).

Flags internal inconsistencies that a reviewer should look at against the paper. It never
reads paper text and never decides that a value is wrong; every flag is a question for the
auditor. Standard library only.

  python3 check_records.py <records dir> [--groups groups.json] [--out flags.json]

<records dir> is recipe-atlas/data/records (one JSON per record). --groups limits the run to
a JSON list of lineage.source_group values.
"""
from __future__ import annotations
import argparse, collections, json, re, sys
from pathlib import Path

# Standard atomic weights (g/mol), enough for colloidal-synthesis reagents.
AW = {'H': 1.008, 'Li': 6.94, 'B': 10.81, 'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998, 'Na': 22.990,
      'Mg': 24.305, 'Al': 26.982, 'Si': 28.085, 'P': 30.974, 'S': 32.06, 'Cl': 35.45, 'K': 39.098, 'Ca': 40.078,
      'Ti': 47.867, 'V': 50.942, 'Cr': 51.996, 'Mn': 54.938, 'Fe': 55.845, 'Co': 58.933, 'Ni': 58.693, 'Cu': 63.546,
      'Zn': 65.38, 'Ga': 69.723, 'Ge': 72.630, 'As': 74.922, 'Se': 78.971, 'Br': 79.904, 'Rb': 85.468, 'Sr': 87.62,
      'Y': 88.906, 'Zr': 91.224, 'Mo': 95.95, 'Ag': 107.868, 'Cd': 112.414, 'In': 114.818, 'Sn': 118.710,
      'Sb': 121.760, 'Te': 127.60, 'I': 126.904, 'Cs': 132.905, 'Ba': 137.327, 'La': 138.905, 'Ce': 140.116,
      'Nd': 144.242, 'Gd': 157.25, 'Er': 167.259, 'Yb': 173.045, 'W': 183.84, 'Pt': 195.084, 'Au': 196.967,
      'Hg': 200.592, 'Pb': 207.2, 'Bi': 208.980}

MASS = {'g': 1.0, 'mg': 1e-3, 'ug': 1e-6, 'µg': 1e-6, 'kg': 1e3}
AMOUNT = {'mol': 1.0, 'mmol': 1e-3, 'umol': 1e-6, 'µmol': 1e-6, 'nmol': 1e-9}
VOLUME = {'L': 1.0, 'mL': 1e-3, 'uL': 1e-6, 'µL': 1e-6, 'μL': 1e-6}
CONC = {'M': 1.0, 'mol/L': 1.0, 'mM': 1e-3, 'mmol/L': 1e-3, 'uM': 1e-6, 'µM': 1e-6}
CANON_UNIT = {'°C': 'degC', 'uL': 'µL', 'μL': 'µL', 'mol/L': 'M', 'mmol/L': 'mM', 'uM': 'µM', 'ug': 'µg', 'umol': 'µmol'}
EVENT_WORDS = re.compile(r'\buntil\b|\bturn(?:s|ed)?\b|\bbecame\b|\bbecomes\b|\bclear(?:s|ed)?\b|\bdissolv|'
                         r'\bcolou?r change|\bonset\b|\breach(?:es|ed)?\b|\bboil', re.I)
NUM = re.compile(r'(?<![\w.])[-−–]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\d)|(?<![\w.])[-−–]?\d+(?:\.\d+)?(?:\s*[×x]\s*10\s*\^?\s*[-−–]?\d+)?')
RATIO = re.compile(r'(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)')
EXP = re.compile(r'(?<![\w.])(\d+(?:\.\d+)?)?\s*[.·×x]?\s*10\s*\^?\s*([-−–]\s*\d+)')  # 2.10 −3, 10-9, 5 × 10^-4
WORDS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
         'twice': 2, 'thrice': 3, 'once': 1}


def formula_mass(formula):
    """Molar mass of a plain formula such as C18H34O2, Cd(CH3COO)2 or Na2S·9H2O; None if unparseable."""
    if not formula or any(ch in formula for ch in '/+@–;, '):
        return None
    def group(toks, i):
        """Mass of tokens from i up to a closing bracket; returns (mass, next index)."""
        mass = 0.0
        while i < len(toks):
            t = toks[i]
            if t in ')]':
                return mass, i
            if t in '([':
                inner, i = group(toks, i + 1)
                if i >= len(toks):
                    raise ValueError
                unit = inner
            elif t in AW:
                unit = AW[t]
            else:
                raise ValueError
            i += 1
            n = 1
            if i < len(toks) and toks[i].isdigit():
                n = int(toks[i]); i += 1
            mass += unit * n
        return mass, i

    total = 0.0
    try:
        for part in re.split(r'[·•*]', formula):
            m = re.match(r'^(\d+)(.*)$', part)
            mult, part = (int(m.group(1)), m.group(2)) if m else (1, part)
            toks = re.findall(r'[A-Z][a-z]?|\d+|[()\[\]]|.', part)
            mass, i = group(toks, 0)
            if i != len(toks):
                return None
            total += mult * mass
    except ValueError:
        return None
    return total or None


def qv(q):
    """(value, unit, status) of a quantity dict, value None for ranges/missing."""
    if not isinstance(q, dict):
        return None, None, None
    v = q.get('value')
    return (v if isinstance(v, (int, float)) and not isinstance(v, bool) else None), q.get('unit'), q.get('status')


def numbers_in(text):
    out = set()
    for m in NUM.findall(text or ''):
        s = m.replace('−', '-').replace('–', '-').replace(',', '').replace(' ', '').replace('^', '')
        if re.search(r'[×x]10', s):
            base, exp = re.split(r'[×x]10', s)
            try: out.add(abs(float(base) * 10 ** float(exp)))
            except ValueError: pass
            continue
        try: out.add(abs(float(s)))
        except ValueError: pass
    for a, b in EXP.findall(text or ''):
        exp = float(re.sub(r'\s', '', b.replace('−', '-').replace('–', '-')))
        out.add(abs((float(a) if a else 1.0) * 10 ** exp))
    for m in re.findall(r'\d{1,3}(?:[ \u2009\u202f]\d{3})+', text or ''):  # 30 000
        out.add(float(re.sub(r'\D', '', m)))
    for w in re.findall(r'[a-z]+', (text or '').lower()):
        if w in WORDS: out.add(float(WORDS[w]))
    for m in re.findall(r'\d+(?:\.\d+)?[eE][-+−]?\d+', text or ''):  # 1.5e-6
        out.add(abs(float(m.replace('−', '-'))))
    for a, b in re.findall(r'(?<![\d.])(\d+)\s*/\s*(\d+)(?![\d.])', text or ''):  # 1/6
        if float(b): out.add(float(a) / float(b))
    for a, b in RATIO.findall(text or ''):  # "1:10" may be stored as 0.1 or 10
        if float(a) and float(b):
            out.update({float(a) / float(b), float(b) / float(a)})
    return out


def close(a, b, rel=0.05):
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-12)


def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def check_record(r):
    flags = []
    def flag(kind, where, msg, severity='check'):
        flags.append({'record_id': r['record_id'], 'kind': kind, 'where': where, 'message': msg, 'severity': severity})

    mats = {m['id']: m for m in r.get('materials', [])}
    states = {s['id']: s for s in r.get('material_states', [])}
    stocks = {s.get('id'): s for s in r.get('stocks', []) if isinstance(s, dict)}
    known = set(mats) | set(states) | set(stocks)
    def ref_id(ref):
        if isinstance(ref, str):
            return ref
        ref = ref or {}
        return ref.get('id') or ref.get('material_id') or ref.get('state_id') or ref.get('stock_id')
    producers = collections.defaultdict(set)  # state/stock id -> inputs of the steps that output it
    for op in r.get('operations', []):
        for out in op.get('outputs') or []:
            producers[ref_id(out)] |= {ref_id(i) for i in (op.get('inputs') or [])}
    for sid, s in stocks.items():
        for oid in s.get('preparation_operation_ids') or []:
            for op in r.get('operations', []):
                if op.get('id') == oid:
                    producers[sid] |= {ref_id(i) for i in (op.get('inputs') or [])}
    def closure(ids):
        """ids plus everything they were made from (parent_ids, stock components, producing steps)."""
        seen, todo = set(), list(ids)
        while todo:
            x = todo.pop()
            if x in seen:
                continue
            seen.add(x)
            node = states.get(x) or stocks.get(x) or {}
            todo += [ref_id(p) for p in (node.get('parent_ids') or [])]
            todo += [ref_id(c) for c in (node.get('components') or [])]
            todo += list(producers.get(x, ()))
        return seen
    used = set()
    # --- operations
    for op in r.get('operations', []):
        oid = op.get('id')
        refs = [ref_id(x) for x in (op.get('inputs') or []) + (op.get('outputs') or [])]
        for rid in refs:
            if rid not in known:
                flag('dangling_reference', oid, f'input/output "{rid}" is not a declared material or state', 'error')
        used |= closure(refs)
        desc = op.get('description') or ''
        params = op.get('parameters') or {}
        env = json.dumps(op.get('environment') or {}, ensure_ascii=False)
        # reagent named in the step text but not among its inputs/outputs or what they were made from
        bound = closure(refs)
        text = re.sub(r'\([^)]*\)', ' ', desc)  # ignore parenthetical asides
        for mid, m in mats.items():
            if mid in bound:
                continue
            for name in {m.get('name'), m.get('formula')}:
                if (name and len(name) >= 4 and re.search(r'(?<![\w])' + re.escape(name) + r'(?![\w])', text, re.I)
                        and not re.search(re.escape(name), env, re.I)):
                    flag('input_named_not_bound', oid, f'step text names "{name}" but "{mid}" is not bound to this step')
                    break
        has_event = bool(EVENT_WORDS.search(desc))
        for key, q in params.items():
            v, unit, status = qv(q)
            if not isinstance(q, dict):
                continue
            if status in ('reported', 'author_derived') and v is None and q.get('minimum') is None and q.get('maximum') is None:
                flag('reported_without_value', f'{oid}.{key}', 'status says reported but no value or range')
            if unit in CANON_UNIT:
                flag('noncanonical_unit', f'{oid}.{key}', f'unit "{unit}" (canonical "{CANON_UNIT[unit]}")', 'style')
            suffix = key.split('_')[-1]
            if suffix in ('time', 'duration', 'temperature') and not unit and (v is not None or q.get('minimum') is not None):
                flag('missing_unit', f'{oid}.{key}', f'{suffix} has a value but no unit', 'error')
            if suffix == 'temperature' and v is not None and unit in ('degC', '°C') and not (-200 <= v <= 500):
                flag('implausible_temperature', f'{oid}.{key}', f'{v} {unit}', 'error')
            raw = q.get('raw_text') or ''
            if v is not None and raw and status == 'reported':
                nums = numbers_in(raw)
                if nums and not any(close(abs(v), n, 0.005) for n in nums):
                    flag('value_not_in_raw_text', f'{oid}.{key}', f'value {v} {unit or ""} not among the numbers of its quoted raw text "{raw[:80]}"', 'error')
            if has_event and suffix in ('temperature', 'time', 'duration') and v is not None and not (q.get('qualifier') or q.get('basis')):
                flag('event_or_setpoint', f'{oid}.{key}', 'step describes an observed event ("until", "turned", "clear"...); confirm this number is a set-point and not the event')
        # mass/amount pairs within one step (prefix match)
        by_prefix = collections.defaultdict(dict)
        for key, q in params.items():
            if '_' in key:
                pre, suf = key.rsplit('_', 1); by_prefix[pre][suf] = q
        for pre, d in by_prefix.items():
            check_stoich(flag, f'{oid}.{pre}', match_formula(pre, mats), d)
    for mid, m in mats.items():
        check_stoich(flag, f'materials.{mid}', m.get('formula'), m.get('quantities') or {})
    envs = json.dumps([op.get('environment') for op in r.get('operations', [])], ensure_ascii=False).lower()
    for mid, m in mats.items():
        if mid in used or (m.get('name') or '\0').lower() in envs or (m.get('formula') or '\0').lower() in envs:
            continue
        flag('unused_material', f'materials.{mid}', f'"{m.get("name")}" ({m.get("role")}) is declared but never enters any step')
    # --- products, measurements, assets
    samples = {p.get('sample_id') for p in r.get('products', [])}
    for p in r.get('products', []):
        if p.get('recipe_link') == 'explicit' and not p.get('link_evidence'):
            flag('link_without_evidence', p.get('sample_id'), 'recipe_link is explicit but link_evidence is empty', 'error')
        for fld in ('composition', 'phase', 'morphology', 'surface'):
            f = p.get(fld) or {}
            if f.get('status') == 'reported' and f.get('value') in (None, '') :
                flag('reported_without_value', f'{p.get("sample_id")}.{fld}', 'status reported with no value', 'error')
            if f.get('status') == 'reported' and not f.get('evidence'):
                flag('reported_without_evidence', f'{p.get("sample_id")}.{fld}', 'reported value has no locator', 'error')
            if f.get('status') == 'not_reported' and f.get('value') not in (None, ''):
                flag('value_marked_not_reported', f'{p.get("sample_id")}.{fld}', f'value "{f.get("value")}" but status not_reported', 'error')
        if p.get('size'):
            pass
    for ms in r.get('measurements', []):
        if ms.get('sample_id') not in samples:
            flag('measurement_unknown_sample', ms.get('id'), f'sample "{ms.get("sample_id")}" is not a product of this record', 'error')
    for a in r.get('structure_assets', []):
        if a.get('sample_id') and a.get('sample_id') not in samples:
            flag('asset_unknown_sample', a.get('id'), f'asset bound to "{a.get("sample_id")}", not a product here', 'error')
        if a.get('eligible_as_measured_label') and a.get('role') != 'measured_sample':
            flag('illustration_as_measured', a.get('id'), f'role {a.get("role")} is eligible as a measured label', 'error')
    # --- material header
    mat = r.get('material') or {}
    fm = mat.get('formula') or ''
    if re.search(r'/[A-Z][a-z]?[A-Z][a-z]?\d+$|/[A-Z][a-z]?\d+[A-Z]', fm) and not mat.get('elements'):
        flag('formula_layer_notation', 'material.formula', f'"{fm}" reads as stoichiometry but looks like a shell/monolayer count; elements list is empty')
    return flags


def match_formula(prefix, mats):
    p = norm(prefix)
    for m in mats.values():
        if p in {norm(m.get('id')), norm(m.get('name')), norm(m.get('formula'))}:
            return m.get('formula')
    return None


def check_stoich(flag, where, formula, d):
    mass, mu, _ = qv(d.get('mass')); amt, au, _ = qv(d.get('amount'))
    vol, vu, _ = qv(d.get('volume') or d.get('stock_volume')); conc, cu, _ = qv(d.get('concentration') or d.get('stock_concentration'))
    mw = formula_mass(formula)
    if mass is not None and amt is not None and mw and mu in MASS and au in AMOUNT:
        calc = mass * MASS[mu] / mw / AMOUNT[au]
        if not close(calc, amt, 0.05):
            flag('mass_amount_mismatch', where, f'{mass} {mu} of {formula} (M={mw:.1f}) is {calc:.3g} {au}, record says {amt} {au}', 'error')
    if conc is not None and vol is not None and amt is not None and cu in CONC and vu in VOLUME and au in AMOUNT:
        calc = conc * CONC[cu] * vol * VOLUME[vu] / AMOUNT[au]
        if not close(calc, amt, 0.05):
            flag('conc_volume_amount_mismatch', where, f'{conc} {cu} × {vol} {vu} = {calc:.3g} {au}, record says {amt} {au}', 'error')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('records', type=Path)
    ap.add_argument('--groups', type=Path)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    groups = set(json.loads(a.groups.read_text())) if a.groups else None
    flags, per_group, n = [], collections.defaultdict(collections.Counter), collections.Counter()
    for f in sorted(a.records.glob('*.json')):
        r = json.loads(f.read_text(encoding='utf-8'))
        g = (r.get('lineage') or {}).get('source_group')
        if groups is not None and g not in groups:
            continue
        n[g] += 1
        for x in check_record(r):
            x['source_group'] = g; flags.append(x); per_group[g][x['severity']] += 1
    summary = {'records': sum(n.values()), 'papers': len(n),
               'by_kind': collections.Counter(x['kind'] for x in flags).most_common(),
               'by_paper': {g: {'records': n[g], **per_group[g]} for g in sorted(n)}}
    if a.out:
        a.out.write_text(json.dumps({'summary': summary, 'flags': flags}, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
