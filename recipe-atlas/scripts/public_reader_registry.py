"""Public Reader physical parts; reuse the reviewed Source partition algorithm."""
import hashlib,json
from reader_presentation_registry import serialized_parts,_merge
from reader_presentation_registry import BASE as SOURCE_BASE,PART as SOURCE_PART,MARKER
BASE='reader-presentation.json'
PART='reader-presentation.part2.json'
MAX_PART_BYTES=80*1024*1024

def encoded(value):
    return (json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')

def public_parts(value,legacy_raw=None):
    if MARKER in value:raise ValueError('Reserved split marker is not logical display data')
    if any(not isinstance(value.get(k),dict) for k in ('records','materials','figures_by_source')):
        raise ValueError('Public Reader tables must remain objects')
    raw=encoded(value) if legacy_raw is None else legacy_raw
    if json.loads(raw)!=value:raise ValueError('Legacy public Reader bytes differ from logical data')
    if len(raw)<MAX_PART_BYTES:return {BASE:raw}
    # No alternate partitioner, truncation or record/figure rewriting.
    source=serialized_parts(value,split=True)
    base=json.loads(source[SOURCE_BASE]);part=source[SOURCE_PART]
    base[MARKER]['part']=PART
    payloads={BASE:encoded(base),PART:part}
    if any(len(raw)>=MAX_PART_BYTES for raw in payloads.values()):
        raise ValueError('Public Reader parts must each remain below80MiB')
    logical=dict(base);logical.pop(MARKER)
    if _merge(logical,json.loads(part))!=value:
        raise ValueError('Public Reader split semantic parity failed')
    if base[MARKER]['sha256']!=hashlib.sha256(part).hexdigest():
        raise ValueError('Public Reader part checksum differs')
    return payloads
