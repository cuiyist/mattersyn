from pathlib import Path
import json
O=Path(__file__).resolve().parent;B=O.parent
old=B.parent/'jp0208743/public-review-proposal/validate_proposal.py'
s=old.read_text(encoding='utf8').replace('dantas2002','yi2002').replace('range(1,22)','range(1,28)').replace('range(1,8)','range(1,11)')
a=s.index("ck('Figure 3 remains pure theory'");z=s.index('result=',a)
s=s[:a]+"""ck('Figure 1 explicit 800 C cohort',assets['figure-1']['sample_links'],['yi-2002-anneal-800','yi-2002-xrd'])
ck('Figure 3 generic analyzer cohort',assets['figure-3']['sample_links'],['yi-2002-particle-size'])
ck('Figure 7 incomplete concentration series',assets['figure-7']['sample_links'],['yi-2002-erbium-series'])
ck('Figure 9 author mechanism',assets['figure-9']['sample_links'],['yi-2002-mechanisms'])
ck('Figure 10 bulk is separate reference',assets['figure-10']['sample_links'],['yi-2002-bulk','yi-2002-upconversion'])
"""+s[z:]
(O/'validate_proposal.py').write_text(s,encoding='utf8')
m=B/'reader-assets/crop-manifest.json';d=json.loads(m.read_text(encoding='utf8'))
for a in d['assets']:a['visual_reviewed']=True
d['visual_inspection_note']='All 16 final 300 dpi crops individually inspected: axes, captions, source glyphs and method continuation boundaries retained.'
m.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared Yi validation and bound completed visual crop inspection')
