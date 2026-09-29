"""Explicit private, extractor-verified transcription; never an independent audit.

Software binds declarations to exact source/claim/render bytes. It cannot prove
that the extractor read the image correctly. Raw pages and claims stay intact.
"""
import hashlib
import json
import re
import struct
from preliminary_contract import _keys, _int, norm

SCHEMA = 'mattersyn-private-visual-transcription/1'
IDENTITY_POINTERS = frozenset(['/doi', '/title'])


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def text(value, maximum=4000):
    return isinstance(value, str) and 0 < len(value) <= maximum and bool(value.strip())


def rebuild(raw, edits):
    """Apply only the declared nonoverlapping spans inside this exact quote."""
    if not isinstance(edits, list) or not 1 <= len(edits) <= 64:
        raise ValueError('visual transcription edits missing or excessive')
    result = []; cursor = 0; previous_start = -1
    for edit in edits:
        if not _keys(edit, 'start end raw replacement'):
            raise ValueError('visual transcription edit keys invalid')
        start = edit['start']; end = edit['end']; replacement = edit['replacement']
        if not _int(start) or not _int(end) or not cursor <= start <= end <= len(raw) or start <= previous_start:
            raise ValueError('visual transcription edit outside span or overlapping')
        if not isinstance(edit['raw'], str) or raw[start:end] != edit['raw'] or not isinstance(replacement, str) or len(replacement) > 4000 or edit['raw'] == replacement:
            raise ValueError('visual transcription edit differs from declared raw span')
        if any(ord(c) < 32 and c not in '\n\r\t' for c in replacement):
            raise ValueError('visual transcription replacement contains control characters')
        result.extend([raw[cursor:start], replacement]); cursor = end; previous_start = start
    result.append(raw[cursor:])
    return ''.join(result)


def prepare(pin, entry, texts, claims, required, resolve, load):
    """Load an actual author receipt and bind every correction to one claim.

    Paths are resolved by the existing private loader and enter its rechecked
    dependency set. Render provenance is an author declaration, not a new image
    interpretation by this software. No renderer or evidence command is run.
    """
    if not _keys(pin, 'path sha256'):
        raise ValueError('visual transcription receipt pin malformed')
    receipt = json.loads(load(resolve(pin['path']), pin['sha256']))
    if not _keys(receipt, 'schema source_id document_sha256 author_visual_checked independent_scientific_audit accuracy training_ready pages transcriptions') or receipt['schema'] != SCHEMA or receipt['source_id'] != entry['source_id'] or receipt['document_sha256'] != entry['document_sha256']:
        raise ValueError('visual transcription source identity mismatch')
    if receipt['author_visual_checked'] is not True or receipt['independent_scientific_audit'] is not False or receipt['accuracy'] != 'unmeasured' or receipt['training_ready'] is not False:
        raise ValueError('visual transcription author/scope declaration invalid')
    if not isinstance(receipt['pages'], list) or not 1 <= len(receipt['pages']) <= len(texts):
        raise ValueError('visual transcription page inventory invalid')
    raw_pages = {}
    for row in receipt['pages']:
        if not _keys(row, 'page raw_text render') or not _int(row['page']) or row['page'] not in texts or row['page'] in raw_pages:
            raise ValueError('visual transcription page mismatch or duplicate')
        page = row['page']
        if not _keys(row['raw_text'], 'path sha256') or not _keys(row['render'], 'path sha256 document_sha256 page rendering'):
            raise ValueError('visual transcription page provenance malformed')
        render = row['render']
        if render['document_sha256'] != entry['document_sha256'] or not _int(render['page']) or render['page'] != page or not text(render['rendering'], 1000):
            raise ValueError('visual transcription render source/page mismatch')
        raw = load(resolve(row['raw_text']['path']), row['raw_text']['sha256']).decode('utf-8')
        # Exact bytes are pinned; offsets use the documented universal-newline view.
        raw = raw.replace('\r\n', '\n').replace('\r', '\n')
        if norm(raw) != texts[page]:
            raise ValueError('visual transcription raw page differs from actual PDF')
        png = load(resolve(render['path']), render['sha256'])
        if len(png) < 45 or png[:8] != bytes([137,80,78,71,13,10,26,10]) or png[12:16] != b'IHDR' or png[-8:-4] != b'IEND' or not all(struct.unpack('>II', png[16:24])):
            raise ValueError('visual transcription page PNG missing or malformed')
        raw_pages[page] = raw
    rows = receipt['transcriptions']
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000 or not isinstance(claims, list):
        raise ValueError('visual transcription span inventory invalid')
    prepared = {}; used_pages = set()
    for row in rows:
        if not _keys(row, 'pointer page raw_start raw_end raw_quote raw_quote_sha256 transcribed_quote transcribed_quote_sha256 edits author_visual_checked'):
            raise ValueError('visual transcription span keys invalid')
        ptr = row['pointer']; page = row['page']
        if not isinstance(ptr, str) or ptr in IDENTITY_POINTERS or ptr not in required or not _int(page) or page not in raw_pages or page not in required[ptr][1]:
            raise ValueError('visual transcription pointer/page ineligible')
        raw = row['raw_quote']; final = row['transcribed_quote']; start = row['raw_start']; end = row['raw_end']
        if not text(raw) or not text(final) or row['author_visual_checked'] is not True or not _int(start) or not _int(end) or not 0 <= start < end <= len(raw_pages[page]) or raw_pages[page][start:end] != raw:
            raise ValueError('visual transcription raw quote/offset mismatch')
        if digest(raw.encode('utf-8')) != row['raw_quote_sha256'] or digest(final.encode('utf-8')) != row['transcribed_quote_sha256']:
            raise ValueError('visual transcription span hash mismatch')
        if rebuild(raw, row['edits']) != final or raw == final:
            raise ValueError('visual transcription has undeclared/out-of-span substitutions')
        if re.search(r'/(?:H|C)\d+', final):
            raise ValueError('visual transcription retains unresolved glyph codes')
        normalized = norm(raw)
        position = texts[page].find(normalized)
        if position < 0 or texts[page].find(normalized, position + 1) >= 0:
            raise ValueError('visual transcription source occurrence ambiguous')
        matches = [c for c in claims if isinstance(c, dict) and c.get('pointer') == ptr and c.get('page') == page and isinstance(c.get('quote'), str) and norm(c['quote']) == normalized]
        if len(matches) != 1:
            raise ValueError('visual transcription lacks one exact matching claim')
        key = (ptr, page, normalized)
        if key in prepared:
            raise ValueError('duplicate visual transcription claim')
        prepared[key] = norm(final); used_pages.add(page)
    if used_pages != set(raw_pages):
        raise ValueError('unused visual transcription page provenance')
    return prepared


def quote(raw, page, pointer, prepared):
    """Return only an exact pointer/page/quote match; otherwise stay on raw path."""
    if prepared is None or pointer in IDENTITY_POINTERS:
        return None
    return prepared.get((pointer, page, norm(raw)))


def copy_check_texts(texts, prepared):
    # Additional copyright check only, never evidence for other claim pointers.
    result = dict(texts)
    if prepared is not None:
        result.update({'transcription-' + str(i): value for i, value in enumerate(prepared.values())})
    return result
