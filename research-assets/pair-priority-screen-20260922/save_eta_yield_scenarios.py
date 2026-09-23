"""Record assumption-based planning scenarios, not inferred scientific yield."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
manifest_path = ROOT/'recipe-atlas/dist/data/dataset-manifest.json'
manifest = json.loads(manifest_path.read_bytes())
tasks = sorted({k for r in manifest['records'] for k in r['eligibility']})
counts = {k:sum(r['eligibility'].get(k,{}).get('eligible',False) for r in manifest['records']) for k in tasks}
rate = 9/12.868496328888888
scenario = {
    'at':datetime.now(timezone.utc).isoformat(),
    'status':'planning_scenarios_not_validated_forecasts',
    'fixed_scope':{'unfinished_provisional_groups':9500,'priority_candidate_groups':1140,
                   'atomic_evidence_groups':52,'phase_morphology_groups':1088},
    'measured_reference':{'source_closures':9,'elapsed_hours':12.868496328888888,
                          'closures_per_elapsed_hour':rate,
                          'limit':'Small selected past cohort, not active compute measurement or representative future throughput.'},
    'remaining_screening':{'planning_days':[3,7],
                           'assumption':'Existing runtime remains regularly available; format/source problems can remain explicitly unresolved rather than falsely reviewed.'},
    'priority_curation_scenario':{
        'deep_review_retention_assumption':[0.5,1.0],
        'equivalent_pipeline_hours_per_day_assumption':[12,16],
        'arithmetic_days_min':1140*0.5/(rate*16),
        'arithmetic_days_max':1140/(rate*12),
        'communication_range':'Approximately 2–5 months for the present priority pool; not complete curation of all 9,500 unfinished groups.',
        'initial_priority_release':'Planning target 3–4 weeks / October 22; subset scope only, not guaranteed full completion.'},
    'broad_descriptor_recipe_yield_scenario':{
        'candidate_groups':1088,'deduplication_and_eligibility_survival_assumption':0.5,
        'linked_recipe_variants_per_surviving_group_assumption':[1,3],
        'arithmetic_pairs':[544,1632],
        'communication_range':'Roughly 500–1,600 eventual descriptor–recipe examples, conditional on assumptions; not measured yield or a one-month deliverable promise.',
        'limits':['Unknown duplicate/eligibility fraction.','Distinct variants require explicit sample/product links.','Phase, size and morphology targets are not measured atomic-coordinate targets.','Do not count figures, citations or duplicate main/SI as data points.']},
    'exact_coordinate_recipe_yield':{'current_task_ready':counts.get('exact_structure_recipe',0),
        'forecast':None,'reason':'52 nominations include unavailable deposits, precursor or comparison structures and unresolved target links; no defensible usable-pair total yet.'},
    'current_export_task_counts':counts,
    'current_counts_not_additive':True,
    'dataset_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    'extra_paid_capacity_assumed':False,
}
path = HERE/'eta-yield-scenarios.json'
assert not path.exists(), 'Preserve dated planning history'
path.write_text(json.dumps(scenario,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
memory=ROOT/'MEMORY.md'
entry='''## 2026-09-22 — Requested ETA and training-yield update

User asked for the current finish estimate and usable synthesis–structure training-point count. Preserve the distinction between provisional paper groups, recipe variants, task-eligible examples and measured atomic-coordinate pairs. Current exports contain 95 precursor-selection, 120 partial-protocol, 15 size-conditioned-recipe and 95 optical-outcome entries, with zero exact-structure-recipe entries; these tasks overlap and must not be summed. The website's 675 records / 123 routes are not 675 or 123 verified structure–recipe pairs.

Planning allowance for remaining format recovery/source screening is approximately 3–7 days, subject to unresolved formats. An initial priority release in 3–4 weeks is a target for a subset. Deep curation of the present 1,140 candidate groups is approximately 2–5 months under an explicit scenario: 50–100% require full work, the past selected-cohort rate of 9 closures / 12.87 elapsed hours continues, and the local pipeline provides 12–16 equivalent hours/day. Arithmetic is 51–136 days before final contingency. This is not a measured forecast, guaranteed runtime, or completion estimate for all 9,500 unfinished scopes. One-month completion of the entire collection is not supported by current measured capacity.

For descriptor-conditioned recipe training, a conditional yield scenario is 1,088 phase/morphology nominations × 50% surviving duplicate/eligibility checks × 1–3 explicitly linked recipe variants = 544–1,632 examples (communicate roughly 500–1,600 eventual examples, not promised by October 22). Survival and variants are assumptions, not measurements. Exact sample-coordinate recipe yield has no defensible numerical forecast yet; the 52 atomic-evidence nominations include unavailable deposits, precursors and bulk/reference comparators. Current task-ready exact count remains zero. Save and revise this scenario after bounded source validation; do not select only successful experiments or invent joins to reach a numeric target.

Full assumptions and current manifest hash: research-assets/pair-priority-screen-20260922/eta-yield-scenarios.json. No paid processing or new source acquisition was authorized. The interrupted PDF render preparation completed a local manifest; rendered pages are not yet visually screened and must not close source holds.

'''
memory.write_text(entry+memory.read_text(encoding='utf8'),encoding='utf8')
print(json.dumps({'current_task_counts':counts,'priority_days':[scenario['priority_curation_scenario']['arithmetic_days_min'],scenario['priority_curation_scenario']['arithmetic_days_max']], 'broad_pair_scenario':[544,1632], 'exact_forecast':None}))
