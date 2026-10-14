"""Two fixed reviewed Reader source files; values remain opaque and unchanged."""
import hashlib,json,os
from pathlib import Path
BASE='reader-presentation-reviewed.json'
PART='reader-presentation-reviewed.part2.json'
MARKER='_reader_registry_split'
TABLES=('records','materials','figures_by_source')
MAX_PART_BYTES=80*1024*1024

def _path(path):
    path=Path(path)
    if path.name!=BASE or path.parent.name!='data':
        raise ValueError('Use the exact Reader source path under data')
    return path

def _encoded(value):
    return (json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')

def _read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def _merge(base,part):
    value=dict(base)
    if set(part)!=set(TABLES):
        raise ValueError('Unexpected second Reader source fields')
    for name in TABLES:
        left,right=value.get(name),part[name]
        if not isinstance(left,dict) or not isinstance(right,dict):
            raise ValueError('Reader source tables must remain objects')
        if set(left)&set(right):
            raise ValueError('Duplicate Reader source keys across parts')
        value[name]={**left,**right}
    return value

def _inputs(path):
    path=_path(path);base=_read(path);marker=base.get(MARKER)
    if marker is None:
        if path.with_name(PART).exists():
            raise ValueError('Orphan second Reader source; do not ignore it')
        return (path,),base,None
    if (not isinstance(marker,dict) or set(marker)!={'schema','part','sha256'}
            or marker['schema']!='reader-presentation-two-part/1'
            or marker['part']!=PART):
        raise ValueError('Invalid fixed Reader split marker')
    part=path.with_name(PART);raw=part.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=marker['sha256']:
        raise ValueError('Reader second source checksum differs')
    return (path,part),base,raw

def source_paths(path):
    return _inputs(path)[0]

def load_reviewed_reader(path):
    paths,base,raw=_inputs(path)
    if len(paths)==1:return base
    base.pop(MARKER)
    return _merge(base,json.loads(raw.decode('utf-8-sig')))

def serialized_parts(value,split=False):
    if MARKER in value:raise ValueError('Reserved split marker is not display data')
    if not split:return {BASE:_encoded(value)}
    if any(not isinstance(value.get(name),dict) for name in TABLES):
        raise ValueError('Reader source tables must remain objects')
    entries=[(name,key,item,len(_encoded((key,item))))
             for name in TABLES for key,item in value[name].items()]
    half=sum(row[3] for row in entries)/2
    base=dict(value);part={name:{} for name in TABLES}
    for name in TABLES:base[name]={}
    used=0
    for name,key,item,weight in entries:
        target=base if used<half else part
        target[name][key]=item
        used+=weight
    if _merge(base,part)!=value:
        raise ValueError('Reader split semantic parity failed')
    raw=_encoded(part)
    base[MARKER]={'schema':'reader-presentation-two-part/1','part':PART,
                  'sha256':hashlib.sha256(raw).hexdigest()}
    result={BASE:_encoded(base),PART:raw}
    if any(len(raw)>MAX_PART_BYTES for raw in result.values()):
        raise ValueError('Two Reader source parts exceed the bounded byte limit')
    return result

def write_reviewed_reader(path,value,split=None):
    path=_path(path)
    if split is None:split=len(source_paths(path))==2 if path.exists() else False
    payloads=serialized_parts(value,split)
    if not split and path.with_name(PART).exists():
        raise ValueError('Explicit collapse must preserve/review the second source')
    path.parent.mkdir(parents=True,exist_ok=True)
    # The primary pins the secondary. An interrupted pair write fails checksum.
    names=[PART,BASE] if split else [BASE]
    for name in names:
        target=path.with_name(name);tmp=target.with_name(target.name+'.reader-tmp')
        tmp.write_bytes(payloads[name]);os.replace(tmp,target)
