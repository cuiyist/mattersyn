"""Record partial implementation without advancing paper or publication status."""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[3]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

validation={
    'checked_at':datetime.now(timezone.utc).isoformat(),
    'scope':'Partial reader implementation, not a completed Littau source-to-view audit.',
    'review_scope_regressions':{'tests':5,'status':'passed'},
    'apparatus_module_tests':{'tests':10,'status':'passed','scope':'Five scene types across 13 private drafts; source guards and explicit stage conditions. Integrated browser QA remains pending.'},
    'existing_dataset_build':{'records':155,'status':'passed'},
    'existing_site_checks':{'pages':169,'canonical_public_hashes':155,'optical_export_rows':95,'status':'passed'},
    'existing_atlas_checks':{'material_hubs':13,'paper_groups':4176,'status':'passed'},
    'existing_matched_main_si_scopes':{'sources':5,'pages':74,'status':'preserved'},
    'browser_interactions_checked':False,
    'littau_canonical_records_imported':0,
    'littau_published':False,
}
write(BASE/'reader-preparation-validation.json',validation)
c=read(BASE/'checkpoint.json')
c['site_implementation_status']='Partial local changes: explicit main-only versus matched-main/SI review scopes, readers and inventory validation; source-scoped continuous-flow SVG module integrated into the protocol renderer. Existing build/link/data checks passed. No Littau canonical records, source-review ledger, molecular registry additions or figure galleries imported yet; browser/source-to-view audit and publication remain.'
c['private_molecular_assets']={'new_entries':19,'reused_existing_entries':5,'new_2d_models':10,'illustrative_3d_models':7,'record_material_bindings':38,'validation_checks':569,'imported':False}
c['current_work_items']=[
    {'label':'Evidence coverage and reader context','status':'independent reconciliation in progress','scope':'All staged source items, 13 private records, original figures and Table I. Source-to-view closure remains pending.'},
    {'label':'Continuous-flow apparatus','status':'candidate integrated locally; browser inspection pending','scope':'Five source-scoped scenes, two furnaces and serial EG bubblers. Ten module tests pass; conflicts and residence-time distinctions retained.'},
    {'label':'Chemical models and bindings','status':'private package complete; import pending','scope':'19 additions, 5 reused identities, 10 2D and 7 illustrative 3D models, 38 material bindings. 569 package checks pass; root and asset agent inspected contact sheets.'},
    {'label':'Review scope and publication counts','status':'implemented locally; independent check in progress','scope':'Five regression tests and existing build/link/inventory checks pass. Main-only reading cannot silently be labeled matched-SI coverage. No new publication.'},
]
c['next_action']='Read updated NEXT_ACTION.md; finish reader-evidence and coverage-ledger handoff, then import the 13 audited canonical records under existing identity, merge private molecular assets, add all figures/Table I and contextual evidence, classify structural measurements correctly, inspect protocol/molecule/evidence interactions and source joins, reconcile inventory and publish. Explicit main-only/SI-unverified scope; current paper remains active.'
write(BASE/'checkpoint.json',c)
m=read(BASE/'milestones.json')
m['integrate']={'status':'partial','evidence':[str(BASE/'reader-preparation-validation.json'),str(BASE/'reader-assets/HANDOFF.md'),str(BASE/'molecular-assets/validation-report.json')],'note':c['site_implementation_status']}
write(BASE/'milestones.json',m)

n=BASE/'NEXT_ACTION.md'
t=n.read_text(encoding='utf-8')
t=t.replace('Current Site version11 is still the published site; this paper has not modified Site files.','Current Site version11 is still the published site. Local Site changes now add explicit review scopes and a source-scoped aerosol apparatus renderer; they are not published and Littau records are not yet imported.')
t=t.replace("The renderer's blanket complete-main/SI label requires source-scope handling before publishing this main-only contribution.","The renderer now has explicit review-scope handling: use `review_scope=\"supplied_main_only_si_unverified\"` for Littau, plus the explicit supporting-information availability note. Existing five matched-main/SI ledgers were migrated from the audited inventory and remain separate; independent scope audit is in `reader-assets` when complete.")
t=t.replace('No records or assets have been imported to the Site.','No Littau records, chemical registry entries or original figures have been imported to the Site. The reviewed continuous-flow module is now in `dist/aerosol-protocol.mjs` and connected in `protocol-visuals.mjs`; run integrated browser QA before publication.')
append='''
## Reader preparation checkpoint

The private `molecular-assets/README.md` is the stable merge handoff: 19 additions, 5 reused references, 38 bindings, 10 2D and 7 illustrative 3D models. `propose_merge.py` only writes a private merged proposal. Preserve parsed-record equality and update binding byte hashes only after justified canonical quality metadata changes; no training promotion comes from molecular assets.

`reader-assets/HANDOFF.md` describes five source-scoped flow scenes. Root copied the module into the Site and connected its explicit condition grid and source notes; ten module tests pass. Desktop/mobile sizing and real protocol-control interaction still require inspection. Main-only scope support passes five regression tests; existing dataset/atlas/inventory/link checks pass at 155 records / 13 hubs / five matched-SI ledgers / 74 pages. No Littau public contribution or deployment yet. Preserve these edits instead of restarting them.

Structural-field classification still needs extension: core/total/HPLC/coherence/shell dimensions currently fall outside the record renderer's short structural whitelist. Avoid counting the contextual observation as a synthesis recipe when importing. Source figures, tables, qualitative evidence and author models need source-specific reader sections and links to supporting records, with every evidence item accounted for. `reader-evidence.json` and `coverage-ledger.json` are the independent handoff when present; an extraction disposition is not yet a source-to-render audit.
'''
if '## Reader preparation checkpoint' not in t:t+='\n'+append
n.write_text(t,encoding='utf-8')

memory=PROJECT/'MEMORY.md'
text=memory.read_text(encoding='utf-8')
heading='## 2026-09-18 — reader assets and explicit review scope prepared'
paragraph='''
Continued the active Littau contribution while answering the user's rough-ETA question. Three same-paper subtasks prepared the continuous-flow apparatus, validated molecular assets and an item-coverage reconciliation. The stable private apparatus module has five stage-specific scenes and ten passing tests. Root integrated it locally with stage-specific condition rows; actual desktop/mobile interaction still needs inspection. The molecular package has19new entries,5reused references,10two-dimensional models,7illustrative conformers and38bindings across13drafts, with569checks passed and both contact sheets visually inspected by the asset agent and root. Missing identities retain nonmolecular cards. No paper downloads occurred.

Root implemented explicit source-review scopes in Site builders/readers/inventory: supplied_main_and_matched_si versus supplied_main_only_si_unverified. The existing five formal main+matchedSI ledgers preserve their74pages. Five regression tests, existing155-record build,169-page link/hash/export checks and13-hub/4,176-group atlas checks passed. No new Littau canonical record, source-review ledger, molecular registry or original-figure gallery has yet been imported; source-to-view validation/publication remain pending. The current claim remains active, integration is partial and public version11 is unchanged. See the review checkpoint, reader-preparation-validation.json and NEXT_ACTION.md. Do not treat asset preparation or a passing old-corpus build as paper completion.

Latest saved scan counted12,499document copies (7,373legacy+5,126incoming) and8,397provisional review units; these are not verified unique-paper totals. The ETA remains a planning allowance, not a measured processing rate or promised calendar deadline; quality-first and existing-backlog-first preferences are unchanged.

'''
if heading not in text:memory.write_text(heading+'\n\n'+paragraph+text,encoding='utf-8')
print('Saved partial reader implementation and asset preparation; paper claim/publication unchanged.')
