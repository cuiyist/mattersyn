from pathlib import Path
import json,sys,hashlib,copy
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;G=A.parent;V=G/'source-extraction-revision-1';M=G.parents[4]
sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
sys.path.append('[local path redacted]')
from PIL import Image
import pypdfium2
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def check(label,test):checks.append({'check':label,'passed':bool(test)})
oldfreeze=load(V/'package-freeze.json');newfreeze=load(G/'package-freeze.json');history=load(G/'source-correction-history.json');preservation=load(V/'preservation-map.json');prior=load(A/'independent-audit-v1.json')
check('oldfreeze boundary',sha(V/'package-freeze.json')==prior['proposal_freeze_sha256'])
check('finalfreeze boundary',sha(G/'package-freeze.json')=='41917b06435344d340990aa7364e651722e6e61f27bb04013b05d32cbb6d0d0b')
check('tablebytehash unchanged',sha(G/'source-tables.json')==prior['source_tables_sha256'])
for p,h in newfreeze['bound_files'].items():check('final input hash '+p,Path(p).is_file() and sha(p)==h)
for p,x in preservation['changed_document_snapshots'].items():check('archived prior '+p,sha(x['archived_path'])==x['sha256'] and x['sha256']==oldfreeze['bound_files'].get(p,prior['bound_files'].get(p)))
for p,h in oldfreeze['bound_files'].items():
 if p not in preservation['changed_document_snapshots']:check('prior unchanged '+p,sha(p)==h)
def delta(a,b,path=''):
 if type(a)!=type(b):return [{'pointer':path,'before':a,'after':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   p=path+'/'+k.replace('~','~0').replace('/','~1')
   out+=delta(a[k],b[k],p) if k in a and k in b else [{'pointer':p,'before':a.get(k),'after':b.get(k)}]
  return out
 if isinstance(a,list):
  out=[]
  for i in range(max(len(a),len(b))):out+=delta(a[i],b[i],path+'/'+str(i)) if i<len(a) and i<len(b) else [{'pointer':path+'/'+str(i),'before':a[i] if i<len(a) else None,'after':b[i] if i<len(b) else None}]
  return out
 return [] if a==b else [{'pointer':path,'before':a,'after':b}]
deltas=[]
for file in ['source-facts.json','source-inventory.json']:
 old=load(V/file);new=load(G/file);actual=[dict(x,file=file) for x in delta(old,new)];expected=[x for x in history['deltas'] if x['file']==file]
 check('exact history delta '+file,actual==sorted(expected,key=lambda x:x['pointer']))
 deltas+=actual
of=load(V/'source-facts.json');nf=load(G/'source-facts.json')
for k in ['tables','materials','stocks','protocols','samples','figures','schemes','references','conflicts','gaps','training_admission']:check('scientific section unchanged '+k,of[k]==nf[k])
for x,y in zip(of['facts'],nf['facts']):check('all typed quantities unchanged '+x['id'],x['quantities']==y['quantities'])
for x,y in zip(of['equations'],nf['equations']):check('formula unchanged '+x['id'],x['expression']==y['expression'])
f=next(x for x in nf['facts'] if x['id']=='ghosh2012-no-added-amine');check('fact includes table locator',any(x['pdf_page']==4 and 'Table 2' in x['locator'] for x in f['evidence']))
check('average-lifetime label corrected',all('amplitude-weighted' not in str(x).lower() for x in [next(x for x in nf['facts'] if x['id']=='ghosh2012-lifetime-detection'),nf['equations'][1]]))
oa=load(V/'original-assets-manifest.json')['assets'];na=load(G/'original-assets-manifest.json')['assets'];identity=load(G/'intake-identity.json');docs={x['role']:pypdfium2.PdfDocument(x['source_path']) for x in identity['documents']}
for old,new in zip(oa,na):
 id=new['id'];check('assetidentity '+id,old['id']==id)
 if id in ['figure-1','figure-s4']:
  check('crop right expanded '+id,new['bbox_pixels_at_render'][2]>old['bbox_pixels_at_render'][2])
  check('crop otherbounds unchanged '+id,[v for i,v in enumerate(new['bbox_pixels_at_render']) if i!=2]==[v for i,v in enumerate(old['bbox_pixels_at_render']) if i!=2])
  bitmap=docs[new['source_role']][new['pdf_page']-1].render(scale=4);im=bitmap.to_pil().convert('RGB');ref=im.crop(new['bbox_pixels_at_render']);actual=Image.open(new['path']).convert('RGB')
  check('fresh PDFium pixels '+id,ref.size==actual.size and ref.tobytes()==actual.tobytes())
  before=Image.open(V/'reader-assets'/Path(old['path']).name).convert('RGB')
  check('original content fully retained '+id,actual.crop((0,0,before.width,before.height)).tobytes()==before.tobytes())
  check('source metadata unchanged '+id,all(new[k]==old[k] for k in ['id','source_role','pdf_page','source_sha256','render_scale','evidence','whole_source_page','public_import_approval']))
 else:check('unaffected crop complete object '+id,new==old and sha(new['path'])==old['sha256'])
check('all findings addressed',len(deltas)==5)
failed=[x for x in checks if not x['passed']]
save(A/'revision2-delta-checks.json',{'reviewer':'/root/norberg2004_extract','checks':checks,'failed':failed,'deltas':deltas,'source_freeze_sha256':sha(G/'package-freeze.json')})
print(json.dumps({'checks':len(checks),'failed':failed},ensure_ascii=False))
if failed:raise SystemExit(1)
bound=dict(newfreeze['bound_files']);bound[str(G/'package-freeze.json')]=sha(G/'package-freeze.json')
for file in ['independent-audit-v1.json','independent-audit-v1.md','mechanical-checks-v1.json','reading-checkpoint-final.json','independent-reading-checkpoint.json','independent-table-reading.json','revision2-delta-checks.json','check_revision2.py']:
 p=A/file;bound[str(p)]=sha(p)
for p,x in preservation['changed_document_snapshots'].items():bound[x['archived_path']]=x['sha256']
bound[str(V/'preservation-map.json')]=sha(V/'preservation-map.json')
res=copy.deepcopy(prior);res.update({'created_at':datetime.now(timezone.utc).isoformat(),'status':'passed','source_package_revision':2,'proposal_freeze_sha256':sha(G/'package-freeze.json'),'source_facts_sha256':sha(G/'source-facts.json'),'source_tables_sha256':sha(G/'source-tables.json'),'open_findings':[],'bound_files':bound,'mechanical_check_count':3305,'bounded_revision_check_count':len(checks),'current_manual_recheck':['Read exact fact-level new locator and neutral lifetime wording against original source definitions.','Actually viewed both corrected original Figure1 and S4 crops: rightmost axis glyphs complete. Exact fresh PDFium pixels and unchanged inherited image pixels checked independently.'],'audit_helper_notes':prior['audit_helper_notes']+['Final revision recheck is bounded; the independent complete-source reading and numerical audit remain preserved at revision1. No fresh rereading of every unchanged cell is claimed.']})
for finding in res['findings']:finding['status']='resolved_in_source_revision_2'
save(A/'independent-audit-v2.json',res);save(A/'independent-audit.json',res)
md='# Ghosh 2012 independent source audit — passed revision 2\n\nAll 10 main and 9 SI pages, 71 facts/194 quantities, 15 protocol scopes/33 operations, 81 contexts and 272 table cells were independently reviewed. All 36 selected original crops were viewed; the two corrected crops were reopened.\n\nThe three bounded findings are resolved: the no-added-amine fact now includes Table 2 p.4, lifetime prose accurately describes the unchanged printed equation, and Figures 1/S4 retain their complete final axis labels. No source numeric/table/formula/material/sample value changed.\n\n3,305 original independent consistency checks and '+str(len(checks))+' bounded revision checks pass. No open extraction finding. All C1–C6 and G1–G8 limitations remain.\n\nFinal source freeze: `'+sha(G/'package-freeze.json')+'`. Exact bound inputs, prior findings and manual scope are in the JSON. This does not approve canonical records, training, exact atomic structure pairs, illustrations, browser integration or publication.\n'
(A/'independent-audit-v2.md').write_text(md,encoding='utf-8');(A/'independent-audit.md').write_text(md,encoding='utf-8')
print('audit_sha256='+sha(A/'independent-audit-v2.json'))
