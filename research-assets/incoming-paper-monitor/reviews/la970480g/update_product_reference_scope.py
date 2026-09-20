from pathlib import Path
import json
R=Path(__file__).resolve().parent;P=R/'molecular-assets/product-reference-proposal.json';d=json.loads(P.read_text(encoding='utf8'))
excluded=['donnan-model-no-salt','donnan-model-salt','donnan-model-one-third-swelling','donnan-model-context','pretreatment-context']
bindings=d['productBindings']['yao-1998-characterization'];r=json.loads((R/'canonical-drafts/yao-1998-characterization.json').read_text(encoding='utf8'));products={q['sample_id']:q for q in r['products']}
for sid in excluded:
 assert products[sid]['composition']['value'] is None
 bindings.pop(sid,None)
d['excludedNonphysicalContexts']=[{'record_id':'yao-1998-characterization','sample_id':sid,'reason':'No physical CdS/polymer product composition is assigned; mathematical model or cited resin-transport context only.'} for sid in excluded]
d['validation']['checks'].append({'check':'Five composition-null model or cited-context entries excluded from product bindings','passed':all(sid not in bindings for sid in excluded)})
assert sum(len(x) for x in d['productBindings'].values())==22
P.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'record_references':len(d['references']),'physical_product_bindings':sum(map(len,d['productBindings'].values())),'excluded_contexts':len(excluded)}))
