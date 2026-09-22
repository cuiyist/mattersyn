"""Verify a normal rebuild retains current Reader pages and evidence archives."""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import json

WORK=Path(__file__).resolve().parent
SITE=WORK.parents[1]/'recipe-atlas'
spec=importlib.util.spec_from_file_location('build_reader_views',SITE/'scripts/build_reader_views.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
names=['material.html','cdse.html','murray-1993-method-1.html','murray-1993-method-2.html','alivisatos-2000.html','nakonechnyi-2017.html']
checks=[]
with TemporaryDirectory(prefix='mattersyn-reader-build-') as temp:
    root=Path(temp)
    (root/'dist').mkdir()
    (root/'templates').mkdir()
    (root/'templates/material-reader.html').write_bytes((SITE/'templates/material-reader.html').read_bytes())
    archives=[name.replace('.html','-evidence.html') for name in names[2:]]
    for archive in archives:
        (root/'dist'/archive).write_bytes(b'Unchanged scientific evidence sentinel')
    builder.ROOT=root
    builder.main()
    for name in names:
        generated=(root/'dist'/name).read_text(encoding='utf-8')
        current=(SITE/'dist'/name).read_text(encoding='utf-8')
        checks.append({'check':'Full rebuild matches deployed Reader: '+name,'passed':generated==current})
    for archive in archives:
        checks.append({'check':'Evidence archive preserved: '+archive,'passed':(root/'dist'/archive).read_bytes()==b'Unchanged scientific evidence sentinel'})
    first={p.name:p.read_bytes() for p in (root/'dist').iterdir()}
    builder.main()
    checks.append({'check':'Repeat build is stable','passed':first=={p.name:p.read_bytes() for p in (root/'dist').iterdir()}})
report={'status':'passed' if all(c['passed'] for c in checks) else 'failed','checks':checks,'scope':'Full reader builder executed twice in an isolated directory; no public site or scientific data changed.'}
(WORK/'reader-build-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(report['status']!='passed')
