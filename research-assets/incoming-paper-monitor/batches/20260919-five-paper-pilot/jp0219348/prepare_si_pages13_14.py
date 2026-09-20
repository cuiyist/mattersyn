"""Verify generation-2 source bytes, then extract only the final two native scans."""
from pathlib import Path
from datetime import datetime, timezone
import sys, json, hashlib, io
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image
B=Path(__file__).resolve().parent
M=B.parents[2]
read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ledger_path=M/'ledger.json'
ledger=read(ledger_path);group=ledger['groups']['10.1021_jp0219348']
assert group['generation']==2
resume_path=B.parent/'integration-resume-20260920T0116.json'
resume=next(x for x in read(resume_path)['source_fingerprints'] if x['group_id']=='10.1021_jp0219348')
assert resume['generation']==2
sources=[]
for key in group['files']:
    f=ledger['files'][key]
    folder=Path('[local path redacted]') if f['source_id']=='legacy' else Path('[local path redacted]')
    p=folder/f['relative_filename'];s0=p.stat();h=sha(p);s1=p.stat()
    assert (s0.st_size,s0.st_mtime_ns)==(s1.st_size,s1.st_mtime_ns)
    assert h==f['sha256']==resume['files'][key]
    sources.append({'key':key,'path':str(p),'role_as_audited':f['role'],'sha256':h,'size_bytes':s1.st_size,'mtime_ns':s1.st_mtime_ns})
assert len(sources)==4
fresh={'schema':'mattersyn-bounded-source-byte-verification/1','created_at':datetime.now(timezone.utc).isoformat(),
       'source_id':'heo2003','group_id':'10.1021_jp0219348','generation':2,
       'scope':'Actual incoming and legacy main/SI bytes compared read-only against the current generation2 ledger and retained resume fingerprint, before SI13-14 image reading.',
       'ledger_read_path':str(ledger_path),'ledger_sha256_at_read':sha(ledger_path),
       'prior_fingerprint_path':str(resume_path),'prior_fingerprint_sha256':sha(resume_path),'sources':sources,
       'unchanged':True,'ledger_modified':False}
O=B/'reader-assets/si-numerical-pages13-14';O.mkdir(exist_ok=False)
preserve={str(p):sha(p) for p in B.iterdir() if p.is_file() and p.suffix in ['.json','.tsv','.md'] and not p.name.startswith('si-pages13-14')}
for p in B.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(B).as_posix()
    if rel.startswith('si-pages') and '-13-14' not in rel and '13-14' not in rel:preserve[str(p)]=sha(p)
    if rel.startswith('reader-assets/si-') and '13-14' not in rel:preserve[str(p)]=sha(p)
d=read(B/'source-inventory.json')['source_documents']['si']
assert sha(d['path'])==d['sha256']=='3b2e262af1932ed04cfddd596958c92d89c37099ab9dad8c4ce1f11254d4acc6'
doc=pymupdf.open(d['path']);assert len(doc)==14
assets=[]
for page in [13,14]:
    pg=doc[page-1];embedded=pg.get_images(full=True);assert len(embedded)==1
    im=Image.open(io.BytesIO(doc.extract_image(embedded[0][0])['image'])).convert('L')
    rw,rh=Image.open(B/f'si-{page:02d}.png').size
    for label,box in [('native',None),('header',(190,180,895,235)),('left-top',(207,236,537,730)),
                      ('left-bottom',(207,708,537,1189)),('right-top',(570,236,895,730)),('right-bottom',(570,708,895,1189))]:
        bbox=None if box is None else [round(box[0]*im.width/rw),round(box[1]*im.height/rh),round(box[2]*im.width/rw),round(box[3]*im.height/rh)]
        crop=im if bbox is None else im.crop(bbox);p=O/f'si-{page:02d}-{label}.png';crop.save(p)
        assets.append({'id':p.stem,'path':str(p),'sha256':sha(p),'source_pdf_page':page,'printed_page':40+page,
                       'source_sha256':d['sha256'],'original_image_box':bbox,'original_image_size':[im.width,im.height],
                       'pixels':[crop.width,crop.height],'operation':'Lossless native embedded scan extraction and rectangular crop; no interpolation, numeral editing or reconstructed glyphs.'})
write(B/'si-pages13-14-source-verification.json',fresh)
write(B/'si-pages13-14-preserved-inputs.json',preserve)
write(B/'si-pages13-14-assets.json',{'schema':'mattersyn-si-numerical-evidence/1','author':'/root/peng1998_reader_assets',
      'created_at':datetime.now(timezone.utc).isoformat(),'source_id':'heo2003','source_path':d['path'],
      'source_sha256':d['sha256'],'source_generation':2,'assets':assets})
print(json.dumps({'source_copies_verified':len(sources),'generation':2,'pages':[13,14],
                  'assets':len(assets),'prior_files_preserved':len(preserve),'source_sha256':d['sha256']},indent=2))
