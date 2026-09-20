"""Preserve source revision 1 and apply only the four independent-audit corrections."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,copy
import pypdfium2
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
old=read(P/'package-freeze.json');assert old['revision']==1
assert sha(P/'package-freeze.json')=='835eccb1bec1e5c5a9aa55c6d0314a39a429b077c318aa5aee8a2a28aa12d12e'
for p,h in old['bound_files'].items():assert sha(p)==h,p
A=P/'source-extraction-revision-1';A.mkdir(exist_ok=False)
changed_binary={'reader-assets/figure-1.png','reader-assets/figure-s4.png'}|{f'private/crop-contact-{i:02}.png'for i in range(1,7)}
preserved={}
for p in [Path(x)for x in old['bound_files']]+[P/'package-freeze.json']:
 if p.parent==P or (p.is_relative_to(P)and p.relative_to(P).as_posix()in changed_binary):
  dst=A/p.relative_to(P);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
  assert sha(dst)==sha(p);preserved[str(p)]={'archived_path':str(dst),'sha256':sha(dst)}
write(A/'preservation-map.json',{'schema':'mattersyn-preserved-source-revision/1','preserved_at':datetime.now(timezone.utc).isoformat(),'original_freeze_sha256':sha(A/'package-freeze.json'),'changed_document_snapshots':preserved,'unchanged_large_files':'Original PDF/text/full-page files and the other 34 crops remain at their original paths with unchanged hashes.'})
replacements={'amplitude-weighted average lifetime':'the reported average lifetime computed from amplitude and lifetime coefficients','Amplitude-weighted average lifetime;':'Reported average lifetime computed from amplitude and lifetime coefficients;'}
deltas=[]
def replace(x,path=''):
 if isinstance(x,dict):return{k:replace(v,path+'/'+k)for k,v in x.items()}
 if isinstance(x,list):return[replace(v,path+'/'+str(i))for i,v in enumerate(x)]
 if isinstance(x,str):
  n=x
  for a,b in replacements.items():n=n.replace(a,b)
  if n!=x:deltas.append({'pointer':path,'before':x,'after':n})
  return n
 return x
for name in ['source-facts.json','source-inventory.json']:
 data=read(P/name);start=len(deltas);data=replace(data)
 if name=='source-facts.json':
  f=next(f for f in data['facts']if f['id']=='ghosh2012-no-added-amine')
  evidence=copy.deepcopy(f['quantities'][1]['evidence'][0]);assert evidence['pdf_page']==4
  assert len(f['evidence'])==1;f['evidence'].append(evidence)
  deltas.append({'pointer':'/facts/'+str(data['facts'].index(f))+'/evidence/1','before':None,'after':evidence})
 else:
  u=next(u for u in data['inventory_units']if u['id']=='fact:ghosh2012-no-added-amine')
  evidence=copy.deepcopy(next(f for f in read(P/'source-facts.json')['facts']if f['id']=='ghosh2012-no-added-amine')['evidence'][1]);u['evidence'].append(evidence)
  deltas.append({'pointer':'/inventory_units/'+str(data['inventory_units'].index(u))+'/evidence/1','before':None,'after':evidence})
 for d in deltas[start:]:d['file']=name
 write(P/name,data)
for name in ['source_author_data.py','build_extraction.py']:
 p=P/name;t=p.read_text(encoding='utf-8')
 for a,b in replacements.items():t=t.replace(a,b)
 if name=='build_extraction.py':
  marker="fb['no-added-amine']['quantities'][1]['evidence']=[ev('main',4,'Table 2 row 6 >6 ML faceting')]"
  assert t.count(marker)==1;t=t.replace(marker,marker+"\nfb['no-added-amine']['evidence'].append(ev('main',4,'Table 2 row 6 >6 ML faceting'))")
  for a,b in [("('figure-1','main',5,(.52,.226,.902,.434))","('figure-1','main',5,(.52,.226,.921,.434))"),("('figure-s4','si',3,(.116,.354,.518,.795))","('figure-s4','si',3,(.116,.354,.539,.795))")]:assert t.count(a)==1;t=t.replace(a,b)
 p.write_text(t,encoding='utf-8')
assets=read(P/'original-assets-manifest.json');payload=read(P/'complete-source-payloads.json');docs={d['document_id']:d for d in payload['documents']};crop_deltas=[]
for aid,right in [('figure-1',.921),('figure-s4',.539)]:
 a=next(a for a in assets['assets']if a['id']==aid);prior=copy.deepcopy(a);a['bbox_normalized'][2]=right
 pdf=pypdfium2.PdfDocument(docs[a['source_role']]['source_path']);pg=pdf[a['pdf_page']-1];bm=pg.render(scale=a['render_scale']);im=bm.to_pil();w,h=im.size
 rect=[round(v*(w if i%2==0 else h))for i,v in enumerate(a['bbox_normalized'])];crop=im.crop(rect);crop.save(a['path'])
 a['sha256']=sha(a['path']);a['bbox_pixels_at_render']=rect;a['pixel_dimensions']=list(crop.size)
 a['manual_visual_review']='Original crop right margin expanded after independent reviewer found a clipped final x-axis tick. Author final enlarged-crop visual review is recorded separately.'
 crop_deltas.append({'id':aid,'before':prior,'after':copy.deepcopy(a),'change':'Right padding only; same source page, scale and left/top/bottom bounds.'})
 crop.close();im.close();bm.close();pg.close();pdf.close()
write(P/'original-assets-manifest.json',assets)
for start in range(0,len(assets['assets']),6):
 subset=assets['assets'][start:start+6];out=Image.new('RGB',(2100,740*((len(subset)+1)//2)),'#e4e8ec');draw=ImageDraw.Draw(out)
 for j,a in enumerate(subset):
  im=Image.open(a['path']);im.thumbnail((1030,690));x=(j%2)*1050;y=(j//2)*740;out.paste(im,(x+(1050-im.width)//2,y+34));draw.text((x+10,y+8),a['id'],fill='black');im.close()
 out.save(P/'private'/f'crop-contact-{start//6+1:02}.png');out.close()
# Verify source quantities, table payloads and equations remain exact; wording is the only formula-context change.
before=read(A/'source-facts.json');after=read(P/'source-facts.json')
assert before['tables']==after['tables'] and before['counts']==after['counts']
assert [f['quantities']for f in before['facts']]==[f['quantities']for f in after['facts']]
assert [e['expression']for e in before['equations']]==[e['expression']for e in after['equations']]
for k in ['materials','stocks','samples','figures','schemes','references','conflicts','gaps','training_admission']:assert before[k]==after[k],k
assert sha(P/'source-tables.json')==sha(A/'source-tables.json')
unchanged={p:h for p,h in old['bound_files'].items()if p not in preserved}
for p,h in unchanged.items():assert sha(p)==h,p
write(P/'source-correction-history.json',{'schema':'mattersyn-source-correction-history/1','author':'/root/backlog_eta','requesting_independent_reviewer':'/root/norberg2004_extract','corrected_at':datetime.now(timezone.utc).isoformat(),'from_revision':1,'to_revision':2,'original_freeze_sha256':sha(A/'package-freeze.json'),'scientific_numeric_change':False,'deltas':deltas,'crop_deltas':crop_deltas,'invariance':['All 194 fact quantities exactly unchanged','All 272 table cells and source-tables.json bytes unchanged','All six equation expressions unchanged','Materials, stocks, samples, figures, schemes, references, conflicts, gaps and training gates unchanged','All four original sources, 19 text caches and full-page renders unchanged','Other 34 selected crop bytes unchanged'],'scope':'Four independent findings: missing fact-level Table 2 locator, conventional weighted-lifetime naming, and two clipped rightmost x-axis labels. No new inference or source value change.'})
print(json.dumps({'deltas':len(deltas),'crop_updates':len(crop_deltas),'history_sha256':sha(P/'source-correction-history.json'),'next':'Actually view both expanded crops, rerun validation and freeze revision 2.'}))
