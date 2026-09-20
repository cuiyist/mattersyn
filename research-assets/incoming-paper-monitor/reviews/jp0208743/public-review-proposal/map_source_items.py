from pathlib import Path
import json
O=Path(__file__).resolve().parent;B=O.parent
data='''
identity-title|identity
identity-authors|identity source-context
identity-journal|identity
identity-dates|identity
identity-administrative|source-context
abstract-material|embedded-product host-versus-qd
abstract-size-control|anneal-rationale model-comparison
abstract-aspl|pl-range
abstract-mechanism|two-photon-model
context-applications|laser-context
context-qw|laser-context
context-qd|laser-context
context-bohr|pbs-context
context-gap|pbs-context
context-telecom|pbs-context
context-aspl-definition|aspl-context
context-prior-aspl|aspl-context
context-three-models|candidate-mechanisms
context-ts-tpa|candidate-mechanisms
context-auger|candidate-mechanisms
context-phonon|candidate-mechanisms
context-prior-dots|aspl-context
context-priority|historical-priority
context-study-scope|scope-conclusion theory-boundary
chemical-glass-list|glass-composition
chemical-silica|silica
chemical-sodium-carbonate|carbonate
chemical-zinc-oxide|zinc-oxide
chemical-alumina|alumina
chemical-lead-dioxide|lead-oxide
chemical-boron-oxide|boron-oxide
chemical-sulfur|sulfur-source
chemical-purity|glass-composition
chemical-missing-formulation|glass-composition missing-recipe
chemical-crucible|crucible fusion
chemical-product|host-versus-qd embedded-product
preparation-mix|batch-preparation
preparation-melt|fusion
preparation-cool|quench
preparation-stress-relief|stress-anneal
preparation-growth|growth-overview anneal-rationale
preparation-sets|sample-boundary growth-overview
preparation-sg1|sg1-growth
preparation-sg2|sg2-growth
preparation-sg3|sg3-growth
preparation-sg4|sg4-growth
preparation-afm1|afm1-growth afm-versus-optical
preparation-afm2|afm2-growth
preparation-color|color
preparation-optical-finish|optical-preparation
preparation-afm-prep|afm-acquisition
preparation-missing|missing-recipe host-versus-qd growth-overview
optical-method-spectrometer|optical-instrument
optical-method-excitation|optical-instrument
optical-method-temperature|optical-temperature
optical-method-missing|optical-instrument power-acquisition pl-trend
absorption-sg1-peaks|absorption-sg1
absorption-sg2-peaks|absorption-sg2
absorption-features|absorption-sg1 absorption-sg2
absorption-assignment|absorption-assignments
absorption-broadening|absorption-assignments
absorption-time-shift|absorption-trend optical-size-sg4
absorption-surface-shift|absorption-trend absorption-sg1 absorption-sg2
absorption-merging|surface-broadening
absorption-dependence|absorption-trend
theory-simple|parabolic-model
theory-masses|parabolic-model
theory-four-band|four-band-model
theory-quantum-labels|four-band-model figure3-legend
theory-agreement|model-comparison
theory-strong-regime|confinement-regimes
theory-large-regime|confinement-regimes
theory-sg1-calibration|optical-size-sg1 absorption-sg1
theory-sg1-size|optical-size-sg1
theory-sg2-size|optical-size-sg2
theory-sg3-size|optical-size-sg3 optical-size-sg4
theory-size-ambiguity|size-radius-boundary
theory-no-structure|theory-boundary structural-limit
theory-prior-agreement|model-comparison
afm-purpose|afm-acquisition
afm-afm1-scan|afm-acquisition afm-panels
afm-afm1-size|afm1-size
afm-afm1-comparison|afm-versus-optical
afm-afm2-size|afm2-size
afm-metric-ambiguity|size-radius-boundary afm1-size afm2-size
afm-image-limit|structural-limit
aspl-glass-limit|passivation-losses
aspl-growth-control|passivation-losses
aspl-sg-series|pl-range figure5-window
aspl-time-trend|pl-trend
aspl-phonon-bottleneck|phonon-argument
aspl-phonon-exclusion|phonon-argument
aspl-auger-competition|auger-argument
aspl-low-excitation|auger-argument power-acquisition
aspl-power-law|power-law
aspl-auger-exclusion|auger-argument
aspl-two-step|two-photon-model
aspl-first-step|two-photon-model
aspl-second-step|two-photon-model
aspl-momentum|momentum-argument
aspl-photon-source|momentum-argument
aspl-sublinear-model|sublinear-rationale
aspl-support|sublinear-rationale
raman-sg1-main|near-excitation-line
raman-sg1-secondary|near-excitation-line
raman-alignment|near-excitation-line absorption-sg1 figure7-axes
raman-assignment|raman-boundary near-excitation-line
figure-1|figure1-axes absorption-sg1 absorption-sg2
figure-2|figure2-axes absorption-trend
figure3-panels|figure3-legend parabolic-model four-band-model
figure3-states-a|figure3-legend
figure3-states-b|figure3-legend four-band-model
figure3-spaces|figure3-legend
figure4-panels|afm-panels afm-acquisition
figure4-afm1-labels|afm1-size afm-panels
figure4-afm2-labels|afm2-size afm-panels
figure4-precision|afm1-size afm2-size size-radius-boundary
figure-5|figure5-window pl-trend
figure-6|figure6-context power-law power-acquisition
figure-6-inset|figure6-context two-photon-model
figure-7|figure7-axes near-excitation-line
conclusion-six-samples|sample-boundary scope-conclusion
conclusion-model-agreement|model-comparison afm-versus-optical size-radius-boundary
conclusion-aspl|scope-conclusion pl-range
conclusion-funding|acknowledgment
source-missing|coverage missing-recipe structural-limit data-precision theory-boundary
'''
mapping={'dantas2002-'+line.split('|')[0]:line.split('|')[1].split() for line in data.strip().splitlines()}
for n in range(1,22):mapping[f'dantas2002-reference-{n:02}']=[f'reference-{n:02}']
audit=json.loads((B/'source-audit.json').read_text(encoding='utf8'));assert set(mapping)=={u['id'] for u in audit['units']},set(mapping)^{u['id'] for u in audit['units']}
(O/'source-item-mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Mapped',len(mapping),'source units')
