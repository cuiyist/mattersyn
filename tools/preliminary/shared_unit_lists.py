"""Literal shared units for bounded coordinated numeric lists, not sample assignment."""
import re

MAX_ITEMS = 8
# A trailing decimal point is excluded because it may terminate a sentence.
_NUMBER = r'[-+−]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?'
_ITEM = r'(?P<qualifier><=|>=|<|>|≤|≥|~|≈)?\s*(?P<number>'+_NUMBER+r')'
_BARE_ITEM = r'(?:<=|>=|<|>|≤|≥|~|≈)?\s*'+_NUMBER
_SEPARATOR = r'\s*(?:,\s*(?:and\s+)?|\band\s+)'
_ITEM_RE = re.compile(_ITEM)


def coordinated_quantity_spans(text, literal_unit_pattern):
    """Return (qualifier, number, literal unit) tuples for 2..8-item lists.

    The caller supplies the existing unit grammar and matching text view. No
    normalization, conversion, range expansion, or qualifier inheritance occurs.
    Ambiguous thousands punctuation and partial/mixed-unit lists fail closed.
    """
    pattern = re.compile(
        r'(?<![\w.+−–-])(?P<items>'+_BARE_ITEM+
        r'(?:'+_SEPARATOR+_BARE_ITEM+r')+)\s*'
        r'(?P<unit>'+literal_unit_pattern+r')(?![A-Za-z])')
    result = set()
    for match in pattern.finditer(text):
        left = text[:match.start()].rstrip()
        right = text[match.end():]
        # Do not recover a tail from digit grouping, a range, an oversized list,
        # or a coordinated expression whose earlier member already has a unit.
        if left and (left[-1] in ',.+−–-±' or left[-1].isdigit()
                     or re.search(r'\b(?:and|to)$', left)):
            continue
        if re.search(_NUMBER+r'\s*,\s*[A-Za-z][^,;.!?]*$', left):
            continue
        if re.match(_SEPARATOR+_BARE_ITEM, right):
            continue
        items_text = match['items']
        # 1,000 is not permission to manufacture separate 1 and 000 values.
        if re.search(r'\d,\s*\d{3}(?![\d.])', items_text):
            continue
        items = list(_ITEM_RE.finditer(items_text))
        if not 2 <= len(items) <= MAX_ITEMS:
            continue
        unit = re.sub(r'\s+', '', match['unit'])
        result.update((item['qualifier'] or '', item['number'], unit)
                      for item in items)
    return result
