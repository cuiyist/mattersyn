"""Preserve canonical data while presenting reviewed Lian metadata readably."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
L=Path(__file__).resolve().parent;O=L/'site-integration-proposal';S=L.parents[4]/'recipe-atlas'
path=S/'scripts/build_dataset.py';before=path.read_text(encoding='utf8')
snapshot=O/'build-dataset-before-reader-presentation.py';assert not snapshot.exists();snapshot.write_text(before,encoding='utf8')
needle='def record_href(url):'
helper='''def material_reader_notes(material,record):
    # Retain historical extraction bookkeeping in the canonical JSON.
    return [n for n in dict.fromkeys(material['notes']) if not (record['lineage']['source_group']=='lian2021' and n=='Chemical/atomic visual binding is separately pending.')]

def product_reader_note(note,record):
    prefix='Source sample object: '
    if record['lineage']['source_group']!='lian2021' or not note.startswith(prefix):return '<p>'+esc(note)+'</p>'
    try: obj=json.loads(note[len(prefix):])
    except (ValueError,TypeError):return '<p>'+esc(note)+'</p>'
    if not isinstance(obj,dict):return '<p>'+esc(note)+'</p>'
    def display(value):
        if isinstance(value,list):return '; '.join(display(x) for x in value) if value else 'None listed'
        if isinstance(value,dict):return '; '.join(human(k)+': '+display(v) for k,v in value.items())
        if value is None:return 'Not reported'
        return str(value)
    rows=''.join('<div><dt>'+esc(human(k))+'</dt><dd>'+esc(display(v))+'</dd></div>' for k,v in obj.items())
    return '<details class="source-specimen-context"><summary>Source specimen context and provenance</summary><dl class="fact-list">'+rows+'</dl></details>'

'''
assert before.count(needle)==1
after=before.replace(needle,helper+needle)
old="for n in dict.fromkeys(m['notes'])";new="for n in material_reader_notes(m,r)"
assert after.count(old)==1;after=after.replace(old,new)
old="''.join('<p>'+esc(n)+'</p>' for n in prod['notes'])";new="''.join(product_reader_note(n,r) for n in prod['notes'])"
assert after.count(old)==1;after=after.replace(old,new)
compile(after,str(path),'exec');path.write_text(after,encoding='utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
delta={'author':'/root','at':datetime.now(timezone.utc).isoformat(),'scope':'Lian-only presentation: hide one independently superseded draft visual-status note; render exact source-sample JSON fields as readable details. Canonical scientific bytes unchanged.','file':'scripts/build_dataset.py','before_sha256':sha(snapshot),'after_sha256':sha(path),'canonical_mutation':False}
(O/'reader-presentation-delta.json').write_text(json.dumps(delta,indent=2)+'\n',encoding='utf8')
print(json.dumps(delta))
