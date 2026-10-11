#!/usr/bin/env python3
"""MatterSyn simple pipeline: paper -> synthesis-structure pairs -> checked -> website.

Standard library only (PyMuPDF is used for PDFs if it is installed).

  python mattersyn_simple.py extract papers/*.pdf --out work --model qwen3-32b
  python mattersyn_simple.py figures papers/*.pdf --out work
  python mattersyn_simple.py check   work --out pairs
  python mattersyn_simple.py score   pairs --records records.jsonl
  python mattersyn_simple.py build   pairs --out site

extract  picks the synthesis pages of each paper and asks a local model (any OpenAI-compatible
         server on this machine) for the pairs, twice.
figures  finds each figure and its caption, crops it, and labels it structure or property.
check    keeps a value only if its quote is found in the paper, the number is in the quote, and
         both passes agree. Everything else is left "not reported".
score    compares extracted values with the audited records of the same paper (by DOI).
build    writes a static website from the checked pair files.
"""
from __future__ import annotations
import argparse, html, json, re, sys, unicodedata, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STRUCTURE_FIELDS = ['composition', 'architecture', 'phase', 'shape', 'ligand', 'size', 'size_method',
                    'absorption_peak', 'emission_peak', 'plqy']
RECIPE_FIELDS = ['method', 'reactor', 'atmosphere', 'reaction_temperature', 'reaction_time']
NUMERIC = {'size', 'absorption_peak', 'emission_peak', 'plqy', 'reaction_temperature', 'reaction_time'}
LIMITS = {'size': (0.3, 5000), 'absorption_peak': (150, 5000), 'emission_peak': (150, 5000), 'plqy': (0, 100),
          'reaction_temperature': (-200, 1500), 'reaction_time': (0, 60 * 24 * 60)}
WORDS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
         'ten': 10, 'eleven': 11, 'twelve': 12, 'half': 0.5}


# ---------- text helpers ----------
def clean(s):
    s = unicodedata.normalize('NFKC', str(s))
    for a in '‐‑‒–—−': s = s.replace(a, '-')
    return s.replace('­', '').replace('’', "'").replace('“', '"').replace('”', '"')


def squash(s):
    """Form used to look a quote up in the paper: no spaces, no line-break hyphens, lower case."""
    return re.sub(r'\s+', '', re.sub(r'-\s*\n\s*', '', clean(s))).lower()


def letters(s):
    """Letters and digits only, lower case. PDF line-break hyphens, odd spaces, degree signs and ligatures then no longer matter."""
    return ''.join(ch for ch in clean(s).lower() if ch.isalnum())


def find_quote(quote, paper_letters):
    """Where the quote sits in the paper (index into letters(paper)), or -1.
    A quote shortened with '...' is found if its parts appear in order, close together."""
    parts = [x for x in (letters(part) for part in re.split(r'\.{3,}|\u2026', clean(quote))) if len(x) >= 6]
    if sum(map(len, parts)) < 8: return -1
    start = paper_letters.find(parts[0])
    while start != -1:
        pos = start + len(parts[0])
        for part in parts[1:]:
            nxt = paper_letters.find(part, pos, pos + 1500 + len(part))
            if nxt == -1: break
            pos = nxt + len(part)
        else:
            return start
        start = paper_letters.find(parts[0], start + 1)
    return -1


def nearness(quote, matcher):
    """Share of the quote that appears as one unbroken run in the paper: tells a small wording slip from an invented quote."""
    q = letters(quote)
    if len(q) < 8: return 0.0
    matcher.set_seq1(q)
    return matcher.find_longest_match(0, len(q), 0, len(matcher.b)).size / len(q)


def numbers_in(s):
    s = clean(s)
    out = [float(x.replace(',', '')) for x in re.findall(r'(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+', s)]
    out += [float(v) for w, v in WORDS.items() if re.search(rf'\b{w}\b', s, re.I)]
    return out


def to_canonical(value, unit, field):
    """Return the value in the field's standard unit (deg C, min, nm), or None if it cannot be converted."""
    if not isinstance(value, (int, float)) or isinstance(value, bool): return None
    u = clean(unit or '').lower().replace(' ', '').replace('°', '').replace('deg', '')
    if 'temperature' in field:
        return value - 273.15 if u in ('k', 'kelvin') else value
    if 'time' in field:
        for names, f in ((('s', 'sec', 'secs', 'second', 'seconds'), 1 / 60), (('min', 'mins', 'minute', 'minutes', ''), 1),
                         (('h', 'hr', 'hrs', 'hour', 'hours'), 60), (('d', 'day', 'days'), 1440)):
            if u in names: return value * f
        return None
    if field == 'size':
        return value * {'a': 0.1, 'å': 0.1, 'angstrom': 0.1, 'nm': 1, '': 1, 'um': 1000, 'µm': 1000, 'μm': 1000}.get(u, float('nan'))
    return value


def same_number(a, b, tol=0.02):
    return a is not None and b is not None and a == a and b == b and abs(a - b) <= tol * max(abs(a), abs(b), 1e-9) + 1e-9


def tokens(s):
    return set(re.findall(r'[a-z0-9]+', clean(s).lower()))


def same_text(a, b):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb: return False
    return ta <= tb or tb <= ta or len(ta & tb) / len(ta | tb) >= 0.5


# ---------- reading papers ----------
DOI = re.compile(r'10\.\d{4,9}/[^\s"<>,;]+')


def tidy_doi(text):
    m = DOI.search(str(text or ''))
    return m.group(0).rstrip('.)]') if m else ''


def doi_guess(pages, stem):
    """A DOI printed on the first pages, else one spelled in the file name."""
    printed = next((tidy_doi(p) for p in pages[:2] if tidy_doi(p)), '')
    return printed or tidy_doi(stem.replace('_', '/', 1))


def load_pages(path):
    path = Path(path)
    if path.suffix.lower() == '.pdf':
        try:
            import pymupdf as fitz
        except ImportError:
            sys.exit(f'{path.name}: install PyMuPDF (pip install pymupdf) or convert it first with: pdftotext -layout file.pdf')
        with fitz.open(path) as doc:
            return [p.get_text() for p in doc]
    text = path.read_text(encoding='utf-8', errors='replace')
    return text.split('\f') if '\f' in text else [text]


SYNTH = r'synthes|prepar|inject|precursor|mmol|\bmL\b|°\s?C|degass|purchas|dissolv|heated|stirr|centrifug|flask|autoclave'
CHAR = r'\bTEM\b|XRD|diffraction|absorption|photoluminescence|\bnm\b|zinc.?blende|wurtzite|diameter'


def select_pages(pages, budget=40000):
    """Pick the pages that describe the synthesis and the product, in reading order, within a size budget."""
    scored = []
    for i, p in enumerate(pages):
        synth, char = len(re.findall(SYNTH, p, re.I)), len(re.findall(CHAR, p, re.I))
        header = bool(re.search(r'^\s*(\d\.?\s*)?(experimental|methods|materials and methods)', p, re.I | re.M))
        if header or synth >= 3 or char >= 4:  # a page with a stray keyword is not worth sending
            scored.append((3 * synth + char + 40 * header, i))
    chosen, used = [], 0
    for score, i in sorted(scored, reverse=True):
        if used + len(pages[i]) > budget and chosen: continue
        chosen.append(i); used += len(pages[i])
    return sorted(chosen) or list(range(min(len(pages), 3)))


# ---------- extraction with a local model ----------
def call_model(base_url, model, system, user, temperature, seed, max_tokens=12288, timeout=1800):
    body = {'model': model, 'temperature': temperature, 'seed': seed, 'max_tokens': max_tokens,
            'response_format': {'type': 'json_object'},
            'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]}
    req = urllib.request.Request(base_url.rstrip('/') + '/chat/completions', json.dumps(body).encode(),
                                 {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        response = json.loads(r.read())
    choice = response['choices'][0]
    reply = choice['message']['content']
    try:
        parse_json(reply)
    except json.JSONDecodeError as error:
        # Diagnostics stay local and contain no paper or response content.
        finish = choice.get('finish_reason')
        tokens = (response.get('usage') or {}).get('completion_tokens')
        raise json.JSONDecodeError(
            f'{error.msg}; finish_reason={finish}; completion_tokens={tokens}',
            error.doc, error.pos) from None
    return reply


def parse_json(reply):
    reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.S)
    a, b = reply.find('{'), reply.rfind('}')
    return json.loads(reply[a:b + 1])


def cmd_extract(a):
    host = urllib.request.urlparse(a.base_url).hostname
    if host not in ('localhost', '127.0.0.1', '::1') and not a.allow_remote:
        sys.exit(f'{a.base_url} is not on this machine. Paper text stays local; pass --allow-remote only if the owner has approved it.')
    prompt = (HERE / 'PROMPT.md').read_text(encoding='utf-8')
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for paper in a.papers:
        stem = Path(paper).stem
        pages = load_pages(paper)
        keep = select_pages(pages, a.budget)
        text = '\n\n'.join(f'[page {i + 1}]\n{pages[i]}' for i in keep)
        (out / f'{stem}.text.txt').write_text(text, encoding='utf-8')
        (out / f'{stem}.pages.json').write_text(json.dumps({'page_count': len(pages), 'pages_read': [i + 1 for i in keep], 'doi_in_pdf': doi_guess(pages, stem)}), encoding='utf-8')
        if a.passes == 0:
            print(f'{stem}: text ready (pages {[i + 1 for i in keep]})')
        user = text + ('\n\n/no_think' if 'qwen3' in a.model.lower() else '')
        for name, temp, seed in (('A', 0.0, 1), ('B', 0.4, 2))[:a.passes]:
            target = out / f'{stem}.pass{name}.json'
            if target.exists() and not a.redo: continue
            try:
                data = parse_json(call_model(a.base_url, a.model, prompt, user, temp, seed))
            except Exception as e:  # keep going; the failure is recorded and counted by check
                data = {'error': f'{type(e).__name__}: {e}'}
            target.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
            print(f'{stem} pass {name}: {"FAILED " + data["error"] if "error" in data else str(len(data.get("pairs", []))) + " pairs"}  (pages {[i + 1 for i in keep]})')


# ---------- figures ----------
CAPTION = re.compile(r'^\s*(Figure|Fig\.?|Scheme|Chart)\s*(S?\d+)\s*(?:[.:|]|\n)', re.I)
# A caption with no punctuation after the number must continue with a capital or a bracket ("Figure 2 shows ..." is body text).
CAPTION_PLAIN = re.compile(r'^\s*(Figure|Fig\.?|Scheme|Chart)\s*(S?\d+)\s+(?=[A-Z(|])')
STRUCTURE_WORDS = (r'\bTEM\b|HRTEM|STEM\b|\bSEM\b|\bAFM\b|XRD|diffract|SAED|SAXS|\bEDS\b|\bEDX\b|\bXPS\b|Raman|FT-?IR|'
                   r'size distribution|histogram|lattice|crystal structure|unit cell|morpholog|micrograph|elemental map')
PROPERTY_WORDS = (r'absor|UV-?vis|photoluminescen|\bPL\b|emission|fluorescen|quantum yield|lifetime|decay|J-?V\b|current|EQE|IPCE|'
                  r'photocurrent|voltamm|impedance|magneti|conductiv|band ?gap|efficienc|catalytic|photocatal|sensing|transmittance|reflectance')


NOT_THE_PRODUCT = r'kinetic|reaction progress|conversion (?:of|versus|vs)|mechanism|speciation|\bNMR\b|precursor (?:conversion|decomposition)|schematic|illustration of'
IMAGING_WORDS = r'\bTEM\b|HRTEM|STEM\b|\bSEM\b|\bAFM\b|XRD|diffract|SAED|SAXS|micrograph'
LABEL_PROMPT = ('You label one figure caption from a paper on nanomaterial synthesis. Answer with JSON only: {"shows": "structure" | "property" | "both" | "other"}.\n'
                'structure: what the synthesized material is. Microscopy images, diffraction patterns, size distributions, composition or surface analysis of the product.\n'
                'property: how the synthesized material behaves. Optical spectra of the product, quantum yield, lifetimes, electrical, magnetic, catalytic or device measurements.\n'
                'both: the caption has panels of each kind.\n'
                'other: schemes, reaction mechanisms, reaction kinetics, precursor or solution chemistry, calculations, photographs of equipment.')


def figure_categories(caption, ask=None):
    """Label a figure from its caption. With a local model (ask), the model decides; the keyword rule is the fallback."""
    if ask:
        try:
            shows = str(parse_json(ask(caption)).get('shows', '')).lower()
            said = {'structure': ['structure'], 'property': ['property'], 'both': ['structure', 'property'], 'other': []}.get(shows)
            if said is not None:  # a panel the model missed is often named by a keyword, so take both views together
                words = [c for c in figure_categories(caption) if c != 'other']
                return [c for c in ('structure', 'property') if c in said or c in words] or ['other']
        except Exception:
            pass
    cats = [name for name, words in (('structure', STRUCTURE_WORDS), ('property', PROPERTY_WORDS)) if re.search(words, caption, re.I)]
    if re.search(NOT_THE_PRODUCT, caption, re.I) and not re.search(IMAGING_WORDS, caption, re.I): return ['other']
    return cats or ['other']


def find_figures(pdf_path):
    """Yield (page number, label, caption, clip rectangle) for each figure whose caption and graphics are found."""
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    with fitz.open(pdf_path) as doc:
        for page in doc:
            W, H = page.rect.width, page.rect.height
            blocks = [b for b in page.get_text('blocks') if b[6] == 0 and b[4].strip()]
            graphics = [fitz.Rect(i['bbox']) for i in page.get_image_info()] + [fitz.Rect(d['rect']) for d in page.get_drawings()]
            graphics = [g for g in graphics if g.width > 3 and g.height > 3 and g.get_area() < 0.9 * W * H]
            body = [fitz.Rect(b[:4]) for b in blocks if len(b[4].split()) >= 15 and not CAPTION.match(b[4])]
            captions = [fitz.Rect(b[:4]) for b in blocks if CAPTION.match(b[4])]
            for b in blocks:
                m = CAPTION.match(b[4]) or CAPTION_PLAIN.match(b[4])
                if not m: continue
                certain = bool(CAPTION.match(b[4]))
                cap = fitz.Rect(b[:4])
                wide = cap.width > 0.55 * W or cap.x0 < 0.45 * W < 0.55 * W < cap.x1
                x0, x1 = (0, W) if wide else (0, W / 2) if (cap.x0 + cap.x1) / 2 < W / 2 else (W / 2, W)
                in_col = [r for r in body + [c for c in captions if c != cap] if min(r.x1, x1) - max(r.x0, x0) > 0.5 * r.width]
                top = max([r.y1 for r in in_col if r.y1 <= cap.y0 + 1], default=0)
                bottom = min([r.y0 for r in in_col if r.y0 >= cap.y1 - 1], default=H)
                for region in (fitz.Rect(x0, top, x1, cap.y0), fitz.Rect(x0, cap.y1, x1, bottom)):  # figure above, else below
                    inside = [g & region for g in graphics if (g & region).get_area() > 0.5 * g.get_area()]
                    if not inside: continue
                    clip = inside[0]
                    for g in inside[1:]: clip |= g
                    for t in blocks:  # axis labels and panel letters that sit next to the graphics
                        r = fitz.Rect(t[:4])
                        if len(t[4].split()) < 15 and r.intersects(region) and not CAPTION.match(t[4]) and r in region: clip |= r
                    clip = (clip + (-4, -4, 4, 4)) & page.rect
                    if clip.width >= 60 and clip.height >= 60:
                        label = ('Figure' if m.group(1).lower().startswith('fig') else m.group(1).capitalize()) + ' ' + m.group(2).upper()
                        yield page.number + 1, label, ' '.join(b[4].split())[:1500], clip, certain
                        break


def cmd_figures(a):
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    out = Path(a.out); (out / 'figures').mkdir(parents=True, exist_ok=True)
    ask = None
    if a.model:  # captions are labelled by the local model; the server must be on this machine
        host = urllib.request.urlparse(a.base_url).hostname
        if host not in ('localhost', '127.0.0.1', '::1'): sys.exit(f'{a.base_url} is not on this machine.')
        ask = lambda caption: call_model(a.base_url, a.model, LABEL_PROMPT, caption + ('\n\n/no_think' if 'qwen3' in a.model.lower() else ''), 0.0, 1, max_tokens=60, timeout=300)
    for pdf in a.papers:
        import hashlib
        with open(pdf, 'rb') as pdf_file:
            source_pdf_sha256 = hashlib.file_digest(pdf_file, 'sha256').hexdigest()
        stem, rows, seen = Path(pdf).stem, [], set()
        with fitz.open(pdf) as doc:
            found = list(find_figures(pdf))
            # captions with punctuation first; the plainer form only for figures not found that way
            for page_no, label, caption, clip, certain in sorted(found, key=lambda f: not f[4]):
                cats = figure_categories(caption, ask)
                if label in seen or (cats == ['other'] and not a.all): continue
                seen.add(label)
                name = f'{stem}-{label.lower().replace(" ", "-")}.png'
                pixmap = doc[page_no - 1].get_pixmap(clip=clip, dpi=a.dpi)
                target = out / 'figures' / name; pixmap.save(target)
                page_rect = doc[page_no - 1].rect
                rows.append({'file': name, 'figure': label, 'page': page_no, 'caption': caption, 'categories': cats,
                             'render_tool': 'PyMuPDF automatic PDF figure-region crop', 'render_dpi': a.dpi,
                             'source_pdf_sha256': source_pdf_sha256,
                             'page_size_pdf_points': [page_rect.width, page_rect.height], 'crop_box_pdf_points': list(clip),
                             'pixel_size': [pixmap.width, pixmap.height], 'asset_sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
        (out / f'{stem}.figures.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'{stem}: {len(rows)} figures  ' + ', '.join(f'{r["figure"]} ({"+".join(r["categories"])})' for r in rows))


# ---------- checking ----------
def fact_problem(field, fact, paper):
    """Why a value cannot be trusted, or None. A missing value is fine: it is simply not reported."""
    if not isinstance(fact, dict) or fact.get('value') in (None, '', 'not reported'): return 'empty'
    q = fact.get('quote') or ''
    if len(letters(q)) < 8: return 'no quote'
    if find_quote(q, paper) == -1: return 'quote not in paper'
    if field in NUMERIC or isinstance(fact['value'], (int, float)):
        v = fact['value']
        if not isinstance(v, (int, float)) or isinstance(v, bool): return 'not a number'
        if not any(same_number(v, n, 1e-6) for n in numbers_in(q)): return 'number not in quote'
        c = to_canonical(v, fact.get('unit'), field)
        lo, hi = LIMITS.get(field, (float('-inf'), float('inf')))
        if c is None or c != c or not lo <= c <= hi: return 'unit or range'
    return None


def facts_agree(field, x, y):
    if not isinstance(y, dict) or y.get('value') in (None, ''): return False
    if isinstance(x['value'], (int, float)):
        return same_number(to_canonical(x['value'], x.get('unit'), field), to_canonical(y.get('value'), y.get('unit'), field))
    return same_text(x['value'], y['value'])


def match_pairs(A, B):
    """Pair up the products of two passes: same composition first, then the most similar name."""
    def sim(p, q):
        cp = squash((p.get('structure', {}).get('composition') or {}).get('value') or '')
        cq = squash((q.get('structure', {}).get('composition') or {}).get('value') or '')
        tp, tq = tokens(p.get('product', '')), tokens(q.get('product', ''))
        return (2 if cp and cp == cq else 0) + (len(tp & tq) / len(tp | tq) if tp | tq else 0)
    free, out = list(range(len(B))), []
    for p in A:
        best = max(free, key=lambda j: sim(p, B[j]), default=None)
        if best is not None and sim(p, B[best]) > 0.3:
            free.remove(best); out.append((p, B[best]))
        else:
            out.append((p, None))
    return out


def step_fact(step, key):
    return {'value': step.get(key), 'unit': step.get(key + '_unit'), 'quote': step.get('quote')}


def page_finder(paper_text):
    """Return a function giving the PDF page a quote is on (the text carries [page N] markers)."""
    blocks = re.split(r'\[page (\d+)\]\n', paper_text)
    pages = [(int(blocks[i]), letters(blocks[i + 1])) for i in range(1, len(blocks) - 1, 2)]
    return lambda quote: next((n for n, text in pages if find_quote(quote, text) != -1), None)


def check_paper(paper_text, passA, passB, stats):
    import difflib
    paper = letters(paper_text); page_of = page_finder(paper_text)
    matcher = difflib.SequenceMatcher(None, autojunk=False); matcher.set_seq2(paper)

    def missed(quote):  # count a rejected quote by how close it came
        stats['dropped: quote not in paper'] += 1
        share = nearness(quote or '', matcher)
        stats['  of which: wording nearly matches the paper' if share >= 0.85 else '  of which: partly found in the paper' if share >= 0.4 else '  of which: not found in the paper'] += 1
    two = passB is not None
    final = []
    for p, q in match_pairs(passA.get('pairs') or [], (passB or {}).get('pairs') or []):
        if two and q is None:
            stats['pairs_dropped'] += 1; continue
        pair = {'product': p.get('product', ''), 'structure': {}, 'recipe': {'chemicals': [], 'steps': []}}

        def keep(field, fact, other):
            why = fact_problem(field, fact, paper)
            if why is None and two and not facts_agree(field, fact, other): why = 'passes disagree'
            if why == 'empty': return None
            stats['values'] += 1
            if why == 'quote not in paper': missed(fact.get('quote')); return None
            if why: stats['dropped: ' + why] += 1; return None
            stats['kept'] += 1
            out = {k: fact[k] for k in ('value', 'unit', 'quote') if fact.get(k) not in (None, '')}
            if page_of(fact['quote']): out['page'] = page_of(fact['quote'])
            return out

        for group, fields in (('structure', STRUCTURE_FIELDS), ('recipe', RECIPE_FIELDS)):
            for f in fields:
                v = keep(f, (p.get(group) or {}).get(f), ((q or {}).get(group) or {}).get(f))
                if v: pair[group][f] = v
        others = {squash(c.get('name', '')): c for c in ((q or {}).get('recipe') or {}).get('chemicals') or []}
        for c in (p.get('recipe') or {}).get('chemicals') or []:
            name = c.get('name') or ''
            other = others.get(squash(name)) or next((o for o in others.values() if same_text(name, o.get('name', ''))), None)
            stats['values'] += 1
            if find_quote(c.get('quote') or '', paper) == -1:
                missed(c.get('quote')); continue
            if two and other is None:
                stats['dropped: passes disagree'] += 1; continue
            item = {'name': name, 'role': c.get('role') or '', 'quote': c['quote'], 'page': page_of(c['quote'])}
            amount = {'value': c.get('amount'), 'unit': c.get('unit'), 'quote': c.get('quote')}
            o_amount = {'value': (other or {}).get('amount'), 'unit': (other or {}).get('unit')}
            if c.get('amount') is not None:
                why = fact_problem('amount', amount, paper)
                if why is None and two and not (facts_agree('amount', amount, o_amount) and squash(c.get('unit') or '') == squash(o_amount['unit'] or '')):
                    why = 'passes disagree'
                if why: stats['dropped: ' + why] += 1
                else: item['amount'], item['unit'] = c['amount'], c.get('unit') or ''
            stats['kept'] += 1
            pair['recipe']['chemicals'].append(item)
        o_steps = ((q or {}).get('recipe') or {}).get('steps') or []
        for s in (p.get('recipe') or {}).get('steps') or []:
            stats['values'] += 1
            if find_quote(s.get('quote') or '', paper) == -1:
                missed(s.get('quote')); continue
            item = {'action': s.get('action') or '', 'description': s.get('description') or '', 'quote': s['quote'], 'page': page_of(s['quote']),
                    'uses': [u for u in s.get('uses') or [] if isinstance(u, str)]}
            twin = next((o for o in o_steps if squash(o.get('action', '')) == squash(item['action']) and
                         all(o.get(k) is None and s.get(k) is None or
                             facts_agree(k, step_fact(s, k), step_fact(o, k)) for k in ('temperature', 'time') if s.get(k) is not None or o.get(k) is not None)), None)
            if two and twin is None:
                stats['dropped: passes disagree'] += 1; continue
            for k in ('temperature', 'time'):
                if s.get(k) is not None and fact_problem('reaction_' + k, step_fact(s, k), paper) is None:
                    item[k], item[k + '_unit'] = s[k], s.get(k + '_unit') or ''
            stats['kept'] += 1
            pair['recipe']['steps'].append(item)
        final.append(pair)
    return final


def cmd_check(a):
    import collections
    work, out = Path(a.work), Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if (work / 'figures').is_dir():
        import shutil; shutil.copytree(work / 'figures', out / 'figures', dirs_exist_ok=True)
    total = collections.Counter()
    for text_file in sorted(work.glob('*.text.txt')):
        stem = text_file.name[:-len('.text.txt')]
        passes, missing, failed = [], [], []
        for name in ('A', 'B'):
            path = work / f'{stem}.pass{name}.json'
            if not path.exists():
                missing.append(name); continue
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, UnicodeError, json.JSONDecodeError):
                failed.append(name); continue
            if (not isinstance(data, dict) or 'error' in data or not isinstance(data.get('pairs'), list)
                    or any(not isinstance(pair, dict) for pair in data.get('pairs', []))):
                failed.append(name); continue
            passes.append(data)
        total['papers'] += 1
        if len(passes) != 2:
            total['papers_failed'] += 1
            total['papers_missing_pass_files'] += bool(missing)
            total['papers_failed_pass_files'] += bool(failed)
            # Preserve an earlier output, but keep it out of the converter's input glob.
            stale = out / f'{stem}.pairs.json'
            if stale.exists():
                parked = out / 'left-out'; parked.mkdir(exist_ok=True)
                target = parked / stale.name; n = 1
                while target.exists():
                    target = parked / f'{stem}.{n}.pairs.json'; n += 1
                stale.rename(target)
            print(f'{stem}: LEFT OUT: two successful passes required (missing: {",".join(missing) or "none"}; failed: {",".join(failed) or "none"})')
            continue
        stats = collections.Counter()
        pairs = check_paper(text_file.read_text(encoding='utf-8'), passes[0], passes[1], stats)
        meta = json.loads((work / f'{stem}.meta.json').read_text(encoding='utf-8')) if (work / f'{stem}.meta.json').exists() else {}
        figures = json.loads((work / f'{stem}.figures.json').read_text(encoding='utf-8')) if (work / f'{stem}.figures.json').exists() else meta.get('figures') or []
        cite = lambda k: meta.get(k) or passes[0].get(k) or ''
        pages_info = json.loads((work / f'{stem}.pages.json').read_text(encoding='utf-8')) if (work / f'{stem}.pages.json').exists() else {}
        doi = tidy_doi(meta.get('doi')) or pages_info.get('doi_in_pdf') or tidy_doi(passes[0].get('doi')) or tidy_doi(stem.replace('_', '/', 1))
        doc = {'id': stem, 'doi': doi, 'title': cite('title'), 'authors': cite('authors'), 'year': cite('year'), 'journal': cite('journal'),
               'check': 'two passes agree, quotes found',
               'values_kept': stats['kept'], 'values_extracted': stats['values'], 'figures': figures, 'pairs': pairs,
               **{k: v for k, v in pages_info.items() if k != 'doi_in_pdf'}}
        (out / f'{stem}.pairs.json').write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
        total.update(stats); total['pairs'] += len(pairs)
        print(f'{stem}: {len(pairs)} pairs, kept {stats["kept"]} of {stats["values"]} values')
    print('\nTOTAL', json.dumps(dict(total), indent=1))


# ---------- scoring against audited records ----------
def audited_index(records_path):
    """For each DOI: the audited temperatures, times, amounts, sizes, peaks, formulas and chemical names."""
    idx = {}
    for line in open(records_path, encoding='utf-8'):
        if not line.strip(): continue
        r = json.loads(line)
        for doi in {s.get('doi', '').lower() for s in r.get('sources') or [] if s.get('doi')}:
            d = idx.setdefault(doi, {k: [] for k in ('temperature', 'time', 'amount', 'size', 'peak', 'formula', 'name')})
            d['formula'] += [squash(x) for x in [(r.get('material') or {}).get('formula')] + [((p.get('composition') or {}).get('value')) for p in r.get('products') or []] if x]
            for m in r.get('materials') or []:
                d['name'] += [x for x in (m.get('name'), m.get('formula')) if x]
                for qv in (m.get('quantities') or {}).values():
                    if isinstance(qv, dict) and isinstance(qv.get('value'), (int, float)): d['amount'].append((qv['value'], squash(qv.get('unit') or '')))
            for op in r.get('operations') or []:
                for k, v in (op.get('parameters') or {}).items():
                    if not isinstance(v, dict) or not isinstance(v.get('value'), (int, float)): continue
                    if 'temperature' in k: d['temperature'].append(to_canonical(v['value'], (v.get('unit') or '').replace('degC', 'C'), 'temperature'))
                    elif 'duration' in k or k.endswith('time'):
                        t = to_canonical(v['value'], v.get('unit'), 'time')
                        if t is not None: d['time'].append(t)
            for m in r.get('measurements') or []:
                v = m.get('value') if isinstance(m.get('value'), dict) else {}
                if not isinstance(v.get('value'), (int, float)) or squash(v.get('unit') or '') != 'nm': continue
                prop = (m.get('property') or '').lower()
                d['size' if re.search(r'size|diameter|thickness|length|width', prop) else 'peak'].append(v['value'])
    return idx


def cmd_score(a):
    import collections
    idx = audited_index(a.records)
    got, hit, missing, unmatched = collections.Counter(), collections.Counter(), [], []
    for f in sorted(Path(a.pairs).glob('*.json')):
        doc = json.loads(f.read_text(encoding='utf-8'))
        ref = idx.get((doc.get('doi') or '').lower())
        if ref is None:
            missing.append(f.name); continue

        def count(kind, ok, item=None):
            got[kind] += 1; hit[kind] += bool(ok)
            if not ok and item is not None: unmatched.append({'paper': doc.get('id'), 'doi': doc.get('doi'), 'field': kind, **{k: item.get(k) for k in ('name', 'value', 'amount', 'unit', 'temperature', 'time', 'quote', 'page') if item.get(k) is not None}})
        for p in doc.get('pairs') or []:
            st, rc = p.get('structure') or {}, p.get('recipe') or {}
            if st.get('composition'): count('composition', any(squash(st['composition']['value']) in x or x in squash(st['composition']['value']) for x in ref['formula']), st['composition'])
            if st.get('size'): count('size', any(same_number(to_canonical(st['size']['value'], st['size'].get('unit'), 'size'), x) for x in ref['size']), st['size'])
            for k in ('absorption_peak', 'emission_peak'):
                if st.get(k): count('optical peak', any(same_number(st[k]['value'], x, 0.005) for x in ref['peak']), st[k])
            temps = [rc['reaction_temperature']] if rc.get('reaction_temperature') else []
            times = [rc['reaction_time']] if rc.get('reaction_time') else []
            for s in rc.get('steps') or []:
                if s.get('temperature') is not None: temps.append({'value': s['temperature'], 'unit': s.get('temperature_unit'), 'quote': s.get('quote'), 'page': s.get('page')})
                if s.get('time') is not None: times.append({'value': s['time'], 'unit': s.get('time_unit'), 'quote': s.get('quote'), 'page': s.get('page')})
            for t in temps: count('temperature', any(abs((to_canonical(t['value'], t.get('unit'), 'temperature') or 1e9) - x) <= 1 for x in ref['temperature']), t)
            for t in times: count('time', any(same_number(to_canonical(t['value'], t.get('unit'), 'time'), x) for x in ref['time']), t)
            for c in rc.get('chemicals') or []:
                count('chemical name', any(same_text(c['name'], n) for n in ref['name']), c)
                if c.get('amount') is not None:
                    count('chemical amount', any(same_number(c['amount'], v, 0.01) and squash(c.get('unit') or '') == u for v, u in ref['amount']), c)
    print(f'{"field":18s} {"extracted":>9s} {"in audited record":>18s} {"share":>7s}')
    for k in ('composition', 'chemical name', 'chemical amount', 'temperature', 'time', 'size', 'optical peak'):
        if got[k]: print(f'{k:18s} {got[k]:9d} {hit[k]:18d} {100 * hit[k] / got[k]:6.0f}%')
    if missing: print(f'\nNo audited record for: {", ".join(missing)}')
    if a.details:
        Path(a.details).write_text(json.dumps(unmatched, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'\n{len(unmatched)} values without a match written to {a.details} (contains quoted paper text: keep it on this machine)')
    print('\nA value "in the audited record" matches a value of the same kind that auditors recorded for that paper.'
          '\nIt does not prove the value is attached to the right product; read a sample by eye as well.')


# ---------- website ----------
CSS = """body{font:16px/1.5 system-ui,sans-serif;margin:0;color:#1d2a30;background:#f6f9fa}main{max-width:1000px;margin:auto;padding:16px}
h1{font-size:1.5rem}h2{font-size:1.15rem;margin-top:2rem}a{color:#0b6b8a}table{border-collapse:collapse;width:100%;background:#fff}
td,th{border:1px solid #d5e0e5;padding:6px 8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#e8f1f4}
.card{background:#fff;border:1px solid #d5e0e5;border-radius:10px;padding:14px;margin:14px 0}.nr{color:#8a979d}
input{font:inherit;padding:8px;width:100%;box-sizing:border-box;margin:8px 0}.tag{font-size:.8rem;background:#fff3cd;border-radius:6px;padding:2px 8px}
.wrap{overflow-x:auto}svg{max-width:100%}"""


def show(fact, unit=True):
    if not fact: return '<span class="nr">not reported</span>'
    return html.escape(f'{fact["value"]}{" " + fact["unit"] if unit and fact.get("unit") else ""}')


def profile_svg(steps):
    """Temperature against step number, drawn from the data."""
    pts = [(i, to_canonical(s['temperature'], s.get('temperature_unit'), 'temperature')) for i, s in enumerate(steps) if s.get('temperature') is not None]
    pts = [(i, t) for i, t in pts if t is not None]
    if len(pts) < 2: return ''
    top = max(t for _, t in pts) or 1; n = max(len(steps) - 1, 1)
    xy = [(40 + 520 * i / n, 130 - 100 * max(t, 0) / top) for i, t in pts]
    dots = ''.join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="#c0392b"/><text x="{x:.0f}" y="{y - 8:.0f}" font-size="11" text-anchor="middle">{t:.0f}</text>' for (x, y), (_, t) in zip(xy, pts))
    return (f'<svg viewBox="0 0 600 150" role="img" aria-label="Temperature by step"><line x1="40" y1="130" x2="570" y2="130" stroke="#8a979d"/>'
            f'<polyline fill="none" stroke="#c0392b" stroke-width="2" points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in xy)}"/>{dots}'
            f'<text x="40" y="146" font-size="11">step 1</text><text x="570" y="146" font-size="11" text-anchor="end">step {len(steps)}</text>'
            f'<text x="8" y="16" font-size="11">°C</text></svg>')


def without_quotes(value):
    """Return a fresh JSON-compatible tree without private quote fields."""
    if isinstance(value, dict):
        return {k: without_quotes(v) for k, v in value.items() if str(k).lower() not in ('quote', 'quotes')}
    if isinstance(value, list):
        return [without_quotes(v) for v in value]
    return value


def public_pair(pair):
    """Keep only checked factual fields and locators, not private annotations."""
    def fields(value, keys):
        if not isinstance(value, dict): return {}
        result = {}
        for k in keys:
            if k not in value: continue
            item = value[k]
            if isinstance(item, dict): continue
            if isinstance(item, list):
                if k == 'uses': result[k] = [v for v in item if isinstance(v, str)]
            else: result[k] = item
        return result

    def fact(value):
        # Checked facts have scalar values. A nested annotation object is not
        # part of that factual schema and cannot smuggle paths into an export.
        value = fields(value, ('value', 'unit', 'page'))
        return value if 'value' in value else {}

    structure, recipe = pair.get('structure') or {}, pair.get('recipe') or {}
    return {
        'product': pair.get('product') or '',
        'structure': {k: fact(structure[k]) for k in STRUCTURE_FIELDS if k in structure},
        'recipe': {
            **{k: fact(recipe[k]) for k in RECIPE_FIELDS if k in recipe},
            'chemicals': [fields(c, ('name', 'role', 'amount', 'unit', 'page')) for c in recipe.get('chemicals') or []],
            'steps': [fields(s, ('action', 'description', 'uses', 'temperature', 'temperature_unit', 'time', 'time_unit', 'page'))
                      for s in recipe.get('steps') or []],
        },
    }


def public_document(doc):
    """Publish facts and page locators, not source captions or private metadata."""
    keys = ('id', 'doi', 'title', 'authors', 'year', 'journal', 'check', 'values_kept',
            'values_extracted', 'page_count', 'pages_read')
    public = without_quotes({k: doc[k] for k in keys if k in doc})
    public['pairs'] = [public_pair(pair) for pair in doc.get('pairs') or []]
    public['figures'] = []
    for fig in doc.get('figures') or []:
        categories = [c for c in fig.get('categories') or ['other'] if c in ('structure', 'property', 'other')]
        categories = categories or ['other']
        label = fig.get('figure') or 'Source figure'
        page = fig.get('page')
        caption = (f'{label}; cited main article, PDF page {page or "not reported"}. '
                   f'Automatic caption-based category: {" and ".join(categories)}. '
                   'Paper-level evidence; no sample match is asserted.')
        public['figures'].append({'file': Path(str(fig.get('file') or '').replace('\\', '/')).name,
                                  'figure': label, 'page': page, 'categories': categories, 'caption': caption,
                                  **{k: fig[k] for k in ('source_pdf_sha256', 'render_tool', 'render_dpi', 'page_size_pdf_points',
                                                        'crop_box_pdf_points', 'pixel_size', 'asset_sha256') if k in fig}})
    return public


def cmd_build(a):
    import shutil
    src, out = Path(a.pairs), Path(a.out); (out / 'p').mkdir(parents=True, exist_ok=True)
    if (src / 'figures').is_dir(): shutil.copytree(src / 'figures', out / 'figures', dirs_exist_ok=True)
    docs = [json.loads(f.read_text(encoding='utf-8')) for f in sorted(src.glob('*.json'))]
    if not a.quotes: docs = [public_document(d) for d in docs]
    rows = []
    for d in docs:
        link = f'<a href="https://doi.org/{html.escape(d["doi"])}">{html.escape(d["doi"])}</a>' if d.get('doi') else ''
        body = [f'<h1>{html.escape(d.get("title") or d["id"])}</h1><p>{link} <span class="tag">{html.escape(a.label)}</span></p>']
        for kind, heading in (('structure', 'Structure figures'), ('property', 'Property figures'), ('other', 'Other figures')):
            figs = [f for f in d.get('figures') or [] if kind in (f.get('categories') or ['other'])]
            if figs: body.append(f'<h2>{heading}</h2>')
            for fig in figs:
                body.append(f'<figure class="card"><img src="../figures/{html.escape(fig["file"])}" alt="{html.escape(fig.get("figure", ""))}" style="max-width:100%">'
                            f'<figcaption>{html.escape(fig.get("caption", ""))}</figcaption></figure>')
        for n, p in enumerate(d.get('pairs') or [], 1):
            st, rc = p.get('structure') or {}, p.get('recipe') or {}
            body.append(f'<div class="card"><h2>{n}. {html.escape(p.get("product") or "product")}</h2><div class="wrap"><table>'
                        + ''.join(f'<tr><th>{f.replace("_", " ")}</th><td>{show(st.get(f))}</td></tr>' for f in STRUCTURE_FIELDS) + '</table></div>'
                        + '<h2>Recipe</h2><div class="wrap"><table>' + ''.join(f'<tr><th>{f.replace("_", " ")}</th><td>{show(rc.get(f))}</td></tr>' for f in RECIPE_FIELDS) + '</table></div>')
            if rc.get('chemicals'):
                body.append('<div class="wrap"><table><tr><th>chemical</th><th>role</th><th>amount</th></tr>' + ''.join(
                    f'<tr><td>{html.escape(c["name"])}</td><td>{html.escape(c.get("role", ""))}</td><td>{html.escape(str(c["amount"]) + " " + c.get("unit", "")) if "amount" in c else "<span class=nr>not reported</span>"}</td></tr>'
                    for c in rc['chemicals']) + '</table></div>')
            if rc.get('steps'):
                body.append('<ol>' + ''.join(
                    f'<li><b>{html.escape(s["action"])}</b> {html.escape(s.get("description", ""))}'
                    + (f' — {s["temperature"]} {html.escape(s.get("temperature_unit", ""))}' if "temperature" in s else '')
                    + (f', {s["time"]} {html.escape(s.get("time_unit", ""))}' if "time" in s else '') + '</li>' for s in rc['steps']) + '</ol>' + profile_svg(rc['steps']))
            body.append('</div>')
            rows.append(f'<tr><td><a href="p/{d["id"]}.html">{html.escape(p.get("product") or d["id"])}</a></td><td>{show(st.get("composition"))}</td>'
                        f'<td>{show(st.get("phase"))}</td><td>{show(st.get("size"))}</td><td>{show(rc.get("reaction_temperature"))}</td><td>{show(rc.get("reaction_time"))}</td><td>{link}</td></tr>')
        page = f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(d.get("title") or d["id"])}</title><style>{CSS}</style><main><p><a href="../index.html">All pairs</a></p>{"".join(body)}</main></html>'
        (out / 'p' / f'{d["id"]}.html').write_text(page, encoding='utf-8')
    public = [{k: v for k, v in d.items()} for d in docs]
    (out / 'pairs.json').write_text(json.dumps(public, ensure_ascii=False), encoding='utf-8')
    index = (f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MatterSyn pairs</title><style>{CSS}</style>'
             f'<main><h1>Synthesis–structure pairs</h1><p>{len(rows)} pairs from {len(docs)} papers. <span class="tag">{html.escape(a.label)}</span> <a href="pairs.json">Download data</a></p>'
             '<input id="q" placeholder="Filter: CdSe, zinc blende, 300 ..." aria-label="Filter pairs"><div class="wrap"><table id="t"><tr><th>product</th><th>composition</th><th>phase</th><th>size</th><th>temperature</th><th>time</th><th>source</th></tr>'
             + ''.join(rows) + '</table></div></main><script>const q=document.getElementById("q"),r=[...document.querySelectorAll("#t tr")].slice(1);'
             'q.oninput=()=>{const s=q.value.toLowerCase();r.forEach(x=>x.style.display=x.textContent.toLowerCase().includes(s)?"":"none")}</script></html>')
    (out / 'index.html').write_text(index, encoding='utf-8')
    print(f'site: {len(docs)} papers, {len(rows)} pairs -> {out / "index.html"}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('extract'); e.add_argument('papers', nargs='+'); e.add_argument('--out', default='work')
    e.add_argument('--base-url', default='http://127.0.0.1:8080/v1'); e.add_argument('--model', default='qwen3-32b')
    e.add_argument('--passes', type=int, default=2, choices=(0, 1, 2)); e.add_argument('--budget', type=int, default=40000)
    e.add_argument('--redo', action='store_true'); e.add_argument('--allow-remote', action='store_true'); e.set_defaults(fn=cmd_extract)
    f = sub.add_parser('figures'); f.add_argument('papers', nargs='+'); f.add_argument('--out', default='work')
    f.add_argument('--model', help='label captions with this local model instead of keywords'); f.add_argument('--base-url', default='http://127.0.0.1:8080/v1')
    f.add_argument('--dpi', type=int, default=200); f.add_argument('--all', action='store_true', help='also keep schemes and other figures'); f.set_defaults(fn=cmd_figures)
    c = sub.add_parser('check'); c.add_argument('work'); c.add_argument('--out', default='pairs'); c.set_defaults(fn=cmd_check)
    s = sub.add_parser('score'); s.add_argument('pairs'); s.add_argument('--records', required=True); s.add_argument('--details', help='write the values that did not match to this local file'); s.set_defaults(fn=cmd_score)
    b = sub.add_parser('build'); b.add_argument('pairs'); b.add_argument('--out', default='site')
    b.add_argument('--label', default='Machine-extracted, automatically checked'); b.add_argument('--quotes', action='store_true'); b.set_defaults(fn=cmd_build)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
