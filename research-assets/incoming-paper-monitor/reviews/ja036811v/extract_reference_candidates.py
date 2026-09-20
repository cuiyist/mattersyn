from pathlib import Path
import sys,re,json
sys.path.insert(0,'[local path redacted]')
import pymupdf
B=Path(__file__).resolve().parent
p=Path('[local path redacted]')
doc=pymupdf.open(p);rows=[]
for n,page in enumerate(doc,1):
 blocks=page.get_text('blocks')
 for left in [True,False]:
  col=[b for b in blocks if (b[0]<310)==left and b[1]<743 and b[2]-b[0]<300]
  starts=[b[1]for b in col if re.match(r'^\(\d+\)\s',b[4].strip())]
  if not starts:continue
  ymin=min(starts);chosen=sorted([b for b in col if b[1]>=ymin],key=lambda b:b[1]);text='\n'.join(b[4]for b in chosen)
  matches=list(re.finditer(r'^\((\d+)\)\s',text,re.M))
  for j,m in enumerate(matches):
   chunk=text[m.end():matches[j+1].start()if j+1<len(matches)else len(text)]
   rows.append({'number':int(m.group(1)),'page':n,'text':re.sub(r'\s+',' ',chunk).strip()})
(B/'reference-candidates.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
for r in rows:print(str(r['number'])+' p'+str(r['page'])+' '+r['text'])
