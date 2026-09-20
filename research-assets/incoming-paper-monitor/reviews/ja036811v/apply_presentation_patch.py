"""Prepare a minimal, strict material-guide patch; only parent may run --apply.

Default execution reads Site and writes the proposed module/diff/check report in B.
An explicit --apply writes Site only after every expected snippet matches once.
"""
from pathlib import Path
import argparse, hashlib, json, difflib

B=Path(__file__).resolve().parent
S=B.parents[3]/'recipe-atlas'
target=S/'dist/material-guide.mjs'
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
old=target.read_text(encoding='utf8');new=old
edits=[
('export async function mountEvidence(host,r){',
 'export async function mountEvidence(host,r,{materialFormula}={}){'),
("const scopeLabels=c.record_formulation_labels?.[r.record_id]||[];for(const f of",
 "const scopeLabels=c.record_formulation_labels?.[r.record_id]||[];const routeContexts=c.route_evidence_contexts?.[r.record_id]||[],contextIds=new Set(routeContexts);const assetFormula=c.material_original_asset_ids?.[materialFormula]?materialFormula:r.material?.formula,allowedAssetIds=c.material_original_asset_ids?.[assetFormula],allowedAssets=allowedAssetIds?new Set(allowedAssetIds):null;if(routeContexts.length){host.append(el('p',c.material_asset_scope_note||'Related source procedures and analytical specimens provide contextual evidence; they do not establish the same physical batch as this route.','guide-notice'));const contextDetails=el('details',undefined,'related-source-records');contextDetails.append(el('summary','Evidence contexts associated with this route'));for(const id of routeContexts){const entry=(c.recipe_inventory||[]).find(x=>(x.record_ids||[]).includes(id));contextDetails.append(link((entry?.label||id)+' →','records/'+id+'.html'));}host.append(contextDetails);}for(const f of"),
("const direct=(f.sample_links||[]).some(x=>(typeof x==='string'?x:x.record_id)===r.record_id),sameFormulation=(f.formulation_labels||[]).some(x=>scopeLabels.includes(x));cards.push({card,relevant:direct||sameFormulation});",
 "const direct=(f.sample_links||[]).some(x=>(typeof x==='string'?x:x.record_id)===r.record_id),sameFormulation=(f.formulation_labels||[]).some(x=>scopeLabels.includes(x)),contextual=(f.sample_links||[]).some(x=>contextIds.has(typeof x==='string'?x:x.record_id)),materialAllowed=!allowedAssets||allowedAssets.has(f.id||f.figure_id);cards.push({card,relevant:materialAllowed&&(direct||sameFormulation||contextual)});"),
("if(c.record_formulation_labels){const filter=", "if(c.record_formulation_labels||allowedAssets||routeContexts.length){const filter="),
("[['record','Selected formulation or procedure context'],['all','All original figures and tables in this paper']]",
 "[['record',routeContexts.length?'Selected material and source evidence contexts':'Selected formulation or procedure context'],['all','All original figures and tables in this paper']]"),
("await mountEvidence(figureHost,r);", "await mountEvidence(figureHost,r,{materialFormula:data.formula});")]
checks=[]
for i,(before,after) in enumerate(edits,1):
 count=new.count(before);checks.append({'edit':i,'expected_occurrences':1,'actual_occurrences':count})
 if count!=1:raise RuntimeError(f'Expected snippet {i} exactly once, found {count}; refusing any Site write.')
 new=new.replace(before,after,1)
proposal=B/'reader-assets/material-guide.proposed.mjs'
proposal.write_text(new,encoding='utf8')
(B/'reader-assets/material-guide-proposed.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(target),tofile=str(proposal))),encoding='utf8')
report={'status':'passed','applied':args.apply,'target':str(target),'original_sha256':hashlib.sha256(old.encode()).hexdigest(),'proposed_sha256':hashlib.sha256(new.encode()).hexdigest(),'checks':checks,'scope':'New optional source mappings apply only where supplied. All-source selection bypasses the contextual filter; existing sources without new fields retain prior relevance behavior.'}
if args.apply:target.write_text(new,encoding='utf8')
(B/'reader-assets/presentation-patch-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
