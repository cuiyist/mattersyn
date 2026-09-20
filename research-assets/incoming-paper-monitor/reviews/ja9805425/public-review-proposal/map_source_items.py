from pathlib import Path
import json
O=Path(__file__).resolve().parent;B=O.parent
read=lambda p:json.loads(p.read_text(encoding='utf8'))
units=read(B/'source-audit.json')['units']
mapping={}
def put(target,*uids):
 for uid in uids:mapping.setdefault(uid,[]).append(target)
put('article-identity','identity','m2-si-announcement')
put('historical-strategies','m1-context-01','m1-context-02','m1-context-03')
put('growth-background','m1-context-04')
put('tem-calibration-scope','m1-pl-01')
put('pl-size-assumptions','m1-pl-02','m1-pl-03','m1-pl-04')
put('distribution-moments','m1-pl-05')
for uid,target in {
 'to-po-charge':'cdse-medium','heat':'cdse-heat','stock':'cdse-stock','initial-injection':'cdse-injection','temperature-drop':'cdse-injection','aliquot':'cdse-growth','precipitate':'cdse-precipitate','purification':'cdse-precipitate','redissolve':'cdse-optical-preparation','optical-density':'cdse-optical-preparation','reinjection':'cdse-refeed','missing':'method-gaps'}.items():put(target,'m1-cdse-'+uid)
for uid,target in {
 'indium-stock':'inas-indium-stock','indium-storage':'stock-storage','top-charge':'inas-bath-and-solvent','heat':'inas-first-injection','stock':'inas-cold-stock','initial-injection':'inas-first-injection','drop':'inas-first-injection','growth':'inas-growth-temperature','aliquots':'inas-sampling','spectra':'inas-sampling','reinjection1':'inas-feeds','reinjection2':'inas-feeds','missing':'method-gaps'}.items():put(target,'m1-inas-'+uid)
for n,target in enumerate(['cdse-focusing-results','cdse-focusing-results','cdse-defocusing-results','cdse-refocusing-results','particle-number','monomer-concentration','qualitative-yield','nucleation-limits'],1):put(target,f'm1-growth-{n:02}')
put('gibbs-thomson','m1-eq1-expression','m1-eq1-symbols')
put('inas-kinetics','m1-growth-07')
put('cdse-spectra','m2-fig1-overview')
for u in units:
 if u['id'].startswith('m2-fig1-time-'):put('cdse-spectra',u['id'])
put('main-axis-metadata','m2-fig1-axes','m2-fig2-visible-axes')
put('cdse-focusing-results','m2-fig2-cdse')
put('inas-kinetics','m2-fig2-inas')
put('cdse-tem','m2-fig3-tem')
put('structural-scope','m2-fig3-characterization-scope')
put('cdse-tem','m2-fig3-characterization-scope')
put('growth-equation','m2-eq2-condition','m2-eq2-expression','m2-eq2-symbols')
put('model-figure4','m2-fig4','m2-intuition-01')
for n,target in [(2,'why-focusing'),(3,'why-defocusing'),(4,'why-refeeding'),(5,'concentration-control'),(6,'generality-limits'),(7,'automation-outlook')]:put(target,f'm2-intuition-{n:02}')
put('cdse-reduced-injection','m2-variant-lower-volume')
put('cdse-cd-rich-comparison','m2-variant-baseline-ratio','m2-variant-cd-rich')
put('cdse-cd-poor-comparison','m2-variant-lower-cd')
put('funding','m2-ack')
for n in range(1,23):put(f'reference-{n:02}',f'ref{n:02}')
put('si-cover-disposition','si-cover')
for material,count in [('cdse',16),('inas',20)]:
 put(material+'-calibration-overview','si-'+material+'-table')
 for n in range(1,count+1):put(f'{material}-calibration-row{n:02}',f'si-{material}-row{n:02}')
put('inas-pl-series','si-inas-spectra-overview')
for u in units:
 if u['id'].startswith('si-inas-spectra-abs'):put('inas-absorption-series',u['id'])
 if u['id'].startswith('si-inas-spectra-pl'):put('inas-pl-series',u['id'])
put('inas-reabsorption','si-inas-spectra-reabsorption')
put('si-axis-metadata','si-inas-spectra-axes')
for n,targets in enumerate([['cdse-stock','printed-ratios'],['structural-scope'],['cdse-optical-preparation','inas-sampling'],['tem-calibration-scope'],['cdse-injection','cdse-refeed','inas-first-injection','inas-feeds'],['cdse-tem'],['cdse-refeed','inas-feeds'],['inas-growth-temperature','cdse-injection','historical-strategies']],1):
 for t in targets:put(t,f'audit-gap-{n:02}')
assert set(mapping)=={u['id'] for u in units},sorted({u['id'] for u in units}-set(mapping))
(O/'source-item-mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Mapped',len(mapping),'source units')
