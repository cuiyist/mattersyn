from pathlib import Path
import json,sys
O=Path(__file__).resolve().parent;F=O.parents[1];M=F.parents[4];V=O.parent/'molecules';D=O.parent/'molecules-correction-v2';A=O/'consumer-fixture'
assert not (O/'package-freeze.json').exists()
sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'));import pymupdf
read=lambda p:json.loads(p.read_text('utf8'))
def copy(src,rel):p=A/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(src.read_bytes())
copy(D/'registry-additions.json','registry-additions.json')
for n in ['bindings-proposal.json','solution-components-proposal.json','stock-component-map.json']:copy(O/n,n)
for e in read(D/'registry-additions.json')['entries']:
 for k in ['svgPath','model2dPath','model3dPath']:
  if e.get(k):copy(D/e[k] if (D/e[k]).exists() else V/e[k],e[k])
copy(M/'recipe-atlas/dist/chemical-viewer.mjs','reference-snapshots/chemical-viewer.mjs')
script=(F.parent/'la8031286/visuals/molecules/check_consumer.mjs').read_text('utf8')
script=script.replace("A=O,P=path.join(A,'../..')","A=path.join(O,'consumer-fixture'),P=path.join(O,'../..')")
script=script.replace('canonical-proposal/v1/record-manifest.json','canonical-proposal/draft-v2/record-manifest.json')
script=script.replace("slots===45,'All 45 slots executed'","slots===77,'All 77 slots executed'")
script=script.replace("stockTransitions===12&&contextTransitions===12,'All 24 component transitions executed'","stockTransitions===16&&contextTransitions===16,'All 32 component transitions executed'")
script=script.replace("dialogs===20&&threeD===6,'All 20 identities including 6 reference-geometry entries'","dialogs===39&&threeD===21,'All 39 identities including 21 reference-geometry entries'")
script=script.replace("author:'/root/peng1998_reader_assets'","author:'/root'")
(O/'check_consumer.mjs').write_text(script,'utf8')
p=O/'stock-svg/friedfeld2019-msc-injection-varied.svg';doc=pymupdf.open(stream=p.read_bytes(),filetype='svg');(O/'previews').mkdir(exist_ok=True);doc[0].get_pixmap(alpha=False).save(str(O/'previews/msc-injection-varied.png'));doc.close()
print('Effective corrected model fixture and varied stock preview ready.')
