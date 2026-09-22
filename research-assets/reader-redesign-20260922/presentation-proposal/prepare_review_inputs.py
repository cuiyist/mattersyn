from pathlib import Path
import json
S=Path('[local path redacted]'); P=Path('[local path redacted]')
rr={p.stem:json.loads(p.read_bytes()) for p in (S/'data/paper-reviews').glob('*.json')}
a=[];b=[]
for sid,r in rr.items():
 for i,f in enumerate(r.get('figures',[])):a.append({'source':sid,'index':i,'id':f['id'],'label':f.get('label'), 'caption':f.get('caption_paraphrase'), 'scope':f.get('sample_scope'),'links':f.get('sample_links'),'asset':f.get('public_asset')})
 for si,s in enumerate(r.get('reader_sections',[])):
  if s.get('id')=='intuition':
   for ii,x in enumerate(s.get('items',[])):
    if x.get('text'):b.append({'source':sid,'pointer':f'/reader_sections/{si}/items/{ii}','id':x.get('id'),'title':x.get('title'),'text':x.get('text'),'claim_type':x.get('claim_type'),'evidence':x.get('evidence'),'canonical_links':x.get('canonical_links')})
(P/'figure-review-inputs.json').write_text(json.dumps(a,indent=2,ensure_ascii=False)+'\n','utf8');(P/'intuition-review-inputs.json').write_text(json.dumps(b,indent=2,ensure_ascii=False)+'\n','utf8')
print('figures',len(a),'intuition items',len(b))
for sid in ['feld2019','fu2007','gu2004','heath1996','littau1993','nakonechnyi2017','saha2019','stowell2005']:
 print('\n',sid)
 for f in a:
  if f['source']==sid:print(f['index'],f['id'],f['caption'])
for n in ['tessier2015','zhang2019']:
 p=S/'dist/data/recipe-figures'/f'{n}.json';d=json.loads(p.read_bytes());print('LEGACY',n,json.dumps(d,ensure_ascii=False)[:5500])
