from pathlib import Path
B=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent
old=(B.parent/'ja036811v/public-review-proposal/canonical_mapping.py').read_text(encoding='utf8')
head=old[:old.index('growth_ops=')].replace('13204+n','158+n')
body=old[old.index('rowlinks={}') :]
body=body.replace("Source-defined operation. Shared frameworks retain their source applicability; this does not establish independent batches, exact retained dopant concentrations or unreported conditions.","Source-defined operation. Aliquot quenching is distinct from bulk termination; common study identity does not resolve caption/body conflicts or unreported batch identity.")
body=body.replace("({'pure-kinetics':'pure-kinetics','pure-titration':'pure-titration','co-titration':'co-titration','dopant-series':'dopant-series'}.get(short) or stock_targets[stock['id']])","(route_stock.get(short) or stock_targets[stock['id']])")
body=body.replace("target=material_targets[component['material_id']]","target=route_stock.get(short) or material_targets[component['material_id']]")
body=body.replace('Undoped/doped ZnO, initial feed, internal/surface dopants, cleaned optical specimens, aggregates and author models are distinct contexts; common study identity does not establish a single physical batch.','Individual particles, spherical assemblies, wires, optical aliquots, electrical devices and models remain separate contexts. Common study identity does not establish a single physical batch or resolve source-ratio conflicts.')
(O/'canonical_mapping.py').write_text(head+'exec((O/\'canonical_targets.py\').read_text(encoding=\'utf8\'))\n'+body,encoding='utf8')
print('Canonical mapper prepared')
