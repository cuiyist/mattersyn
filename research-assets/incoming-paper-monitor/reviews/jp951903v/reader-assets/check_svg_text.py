"""Bounded XML/text-edge check. Not a substitute for root browser layout QA."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from PIL import ImageFont
B=Path(__file__).resolve().parent
rows=[]
for f in sorted((B/'scene-previews').glob('*.svg')):
    root=ET.parse(f).getroot()
    for t in root.iter('{http://www.w3.org/2000/svg}text'):
        text=''.join(t.itertext()); size=int(t.attrib.get('font-size',18))
        font=ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if t.attrib.get('font-weight') else 'segoeui.ttf'),size)
        width=font.getlength(text); x=float(t.attrib['x']); y=float(t.attrib['y'])
        left=x-width/2 if t.attrib.get('text-anchor')=='middle' else x
        rows.append({'file':f.name,'text':text,'left':left,'right':left+width,'baseline':y,'font_size':size,'pass':left>=8 and left+width<=592 and y-size>=0 and y<=376})
bad=[x for x in rows if not x['pass']]
report={'status':'passed_XML_and_text_edges' if not bad else 'text_edge_findings','svg_files':len(list((B/'scene-previews').glob('*.svg'))),'text_nodes':len(rows),'findings':bad,'long_headings':[x for x in rows if x['font_size']==23],'limitation':'Segoe UI font metrics check text edges only. No claim of browser collision, image, mobile or source-to-view verification.'}
(B/'svg-text-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','svg_files','text_nodes','findings']},ensure_ascii=False))
