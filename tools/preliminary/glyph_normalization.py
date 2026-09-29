"""Optional private punctuation-glyph evidence. Visual meaning remains an author check."""
from io import BytesIO
import hashlib
import json
import re
from preliminary_contract import _keys, _int, norm

SCHEMA = 'mattersyn-private-glyph-normalization/1'
VISUAL_SCHEMA = 'mattersyn-private-observed-glyph-evidence/1'
PUNCTUATION = frozenset('~()[]')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def font_codes(pdfraw, pages):
    """Exact PDF font names prevent consuming scientific digits after a code.

    This bounded version supports page-resource simple-font Differences only.
    Other encodings, nested-form-only fonts and ambiguous prefixes remain holds.
    """
    from pypdf import PdfReader
    document = PdfReader(BytesIO(pdfraw), strict=True)
    result = {}
    for page in pages:
        codes = set()
        resources = document.pages[page - 1].get('/Resources', {})
        resources = resources.get_object() if hasattr(resources, 'get_object') else resources
        for font in resources.get('/Font', {}).values():
            encoding = font.get_object().get('/Encoding')
            encoding = encoding.get_object() if hasattr(encoding, 'get_object') else encoding
            if isinstance(encoding, dict):
                codes.update(str(v) for v in encoding.get('/Differences', [])
                             if isinstance(v, str) and re.fullmatch(r'/H[0-9]{4,5}', v))
        if any(a != b and b.startswith(a) for a in codes for b in codes):
            raise ValueError('ambiguous PDF glyph-name prefix')
        result[page] = codes
    return result


def decode(text, codes, aliases):
    """Replace exact font-name prefixes only; all other characters stay identical."""
    pieces = []
    start = 0
    while True:
        pos = text.find('/H', start)
        if pos < 0:
            pieces.append(text[start:])
            return ''.join(pieces)
        matches = [code for code in codes if text.startswith(code, pos)]
        if len(matches) != 1 or matches[0] not in aliases:
            raise ValueError('unknown or unverified glyph in source quote')
        code = matches[0]
        replacement = aliases[code]
        if replacement not in PUNCTUATION:
            raise ValueError('glyph replacement is not permitted punctuation')
        pieces.extend((text[start:pos], replacement))
        start = pos + len(code)


def prepare(pin, entry, pdfraw, texts, resolve, load):
    """Verify document/page/raw-quote/render pins; do not execute a renderer.

    PNG provenance and mapping meanings are factual author declarations. Their
    hashes are checked, but the software does not prove visual semantics.
    """
    if not _keys(pin, 'path sha256'):
        raise ValueError('glyph normalization pin malformed')
    spec = json.loads(load(resolve(pin['path']), pin['sha256']))
    if not _keys(spec, 'schema source_id document_sha256 visual_evidence pages') or spec['schema'] != SCHEMA or spec['source_id'] != entry['source_id'] or spec['document_sha256'] != entry['document_sha256']:
        raise ValueError('glyph normalization document identity mismatch')
    if not _keys(spec['visual_evidence'], 'path sha256'):
        raise ValueError('visual evidence pin malformed')
    visual = json.loads(load(resolve(spec['visual_evidence']['path']), spec['visual_evidence']['sha256']))
    if not isinstance(visual, dict) or visual.get('schema') != VISUAL_SCHEMA or visual.get('source_id') != entry['source_id'] or not isinstance(visual.get('source_pdf'), dict) or visual['source_pdf'].get('sha256') != entry['document_sha256'] or visual.get('independent_scientific_audit') is not False:
        raise ValueError('visual evidence identity/scope mismatch')
    if not isinstance(visual.get('pages'), list) or not all(isinstance(p, dict) for p in visual['pages']) or not isinstance(visual.get('mappings'), list) or not all(isinstance(m, dict) for m in visual['mappings']) or not isinstance(visual.get('quotes'), dict):
        raise ValueError('visual evidence inventory malformed')
    if not isinstance(spec['pages'], list) or not 1 <= len(spec['pages']) <= len(texts):
        raise ValueError('invalid glyph page inventory')
    codes = font_codes(pdfraw, texts)
    mappings = {}; approved = {}
    for row in spec['pages']:
        if not _keys(row, 'page aliases') or not _int(row['page']) or row['page'] not in texts or row['page'] in mappings:
            raise ValueError('invalid/duplicate glyph page')
        page = row['page']; aliases = row['aliases']
        approved[page] = set()
        if not isinstance(aliases, dict) or not 1 <= len(aliases) <= 16 or any(code not in codes[page] or replacement not in PUNCTUATION for code, replacement in aliases.items()):
            raise ValueError('glyph aliases require exact PDF font names and punctuation')
        matches = [p for p in visual['pages'] if p.get('page') == page]
        if len(matches) != 1:
            raise ValueError('visual page provenance missing/duplicate')
        source = matches[0]
        raw_text = load(resolve(source['raw_text_path']), source['raw_text_sha256']).decode('utf-8')
        # Observation offsets use Python's universal-newline text view; the pin
        # above still covers the original file bytes, including their newlines.
        raw_text = raw_text.replace('\r\n', '\n').replace('\r', '\n')
        if norm(raw_text) != texts[page]:
            raise ValueError('visual raw page differs from actual PDF extraction')
        png = load(resolve(source['render_path']), source['render_sha256'])
        if not png.startswith(bytes([137,80,78,71,13,10,26,10])) or not isinstance(source.get('rendering'), str) or not source['rendering'].strip():
            raise ValueError('actual page PNG/render provenance missing')
        for code, replacement in aliases.items():
            observed = [m for m in visual['mappings'] if m.get('raw_code') == code]
            if len(observed) != 1 or observed[0].get('visible_punctuation') != replacement or observed[0].get('visual_status') != 'confirmed':
                raise ValueError('glyph alias does not match visual evidence')
            if not isinstance(observed[0].get('observed_in'), list) or not all(isinstance(q, str) for q in observed[0]['observed_in']):
                raise ValueError('visual observation IDs malformed')
            found = False
            for quote_id in observed[0]['observed_in']:
                q = visual['quotes'][quote_id]
                if q['page'] != page:
                    continue
                raw = q['raw_text']; begin = q['raw_character_start']; end = q['raw_character_end']
                if not _int(begin) or not _int(end) or not 0 <= begin < end <= len(raw_text) or raw_text[begin:end] != raw or digest(raw.encode('utf-8')) != q['raw_utf8_sha256'] or norm(raw) != q['normalized_quote'] or digest(norm(raw).encode('utf-8')) != q['normalized_quote_sha256']:
                    raise ValueError('visual source quote/offset/hash mismatch')
                if code in raw:
                    # Unknown codes in a checked observation cannot be silently stripped.
                    decode(raw, codes[page], aliases)
                    observation = norm(raw)
                    at = texts[page].find(observation)
                    if at < 0 or texts[page].find(observation, at + 1) >= 0:
                        raise ValueError('ambiguous visual observation occurrence')
                    for match in re.finditer(re.escape(code), observation):
                        approved[page].add((at + match.start(), code))
                    found = True
            if not found:
                raise ValueError('glyph lacks visual observation on this page')
        mappings[page] = aliases
    return {'codes': codes, 'aliases': mappings, 'texts': texts, 'approved': approved}


def quote(text, page, prepared):
    if prepared is None:
        return text
    decoded = decode(text, prepared['codes'][page], prepared['aliases'].get(page, {}))
    if '/H' in text:
        normalized = norm(text); full = prepared['texts'][page]
        start = full.find(normalized)
        if start < 0 or full.find(normalized, start + 1) >= 0:
            raise ValueError('ambiguous glyph claim occurrence')
        for match in re.finditer('/H', normalized):
            code = next(c for c in prepared['codes'][page] if normalized.startswith(c, match.start()))
            if (start + match.start(), code) not in prepared['approved'].get(page, set()):
                raise ValueError('glyph occurrence lacks a visual observation')
    return decoded


def copy_check_texts(texts, prepared):
    # Additional detection only: never use partly decoded pages as claim evidence.
    result = dict(texts)
    if prepared is not None:
        for page, aliases in prepared['aliases'].items():
            text = texts[page]
            for code, replacement in aliases.items():
                text = text.replace(code, replacement)
            result['glyph-' + str(page)] = norm(text)
    return result
