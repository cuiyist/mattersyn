from pathlib import Path
import json,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=ROOT/'recipe-atlas';D=S/'dist'
# Reusable generator retains the independently checked projection logic.
generator=(W/'presentation-proposal/generate_presentation.py').read_text(encoding='utf-8')
generator=generator.replace("HERE = Path(__file__).resolve().parent\nSITE = Path('[local path redacted]')", "SITE = Path(__file__).resolve().parents[1]\nHERE = SITE.parent/'research-assets/reader-metadata-build'\nHERE.mkdir(parents=True,exist_ok=True)")
generator=generator.replace("'presentation_proposal_only'", "'integrated_reader_metadata'").replace("f'records/{rid}/'", "f'records/{rid}.html?view=data'").replace("'alivisatos-2000.html' if sid=='peng2000'", "'alivisatos-2000-evidence.html' if sid=='peng2000'")
generator=generator.replace("write('reader-presentation.json',output)", "write('reader-presentation.json',output)\n(SITE/'dist/data/reader-presentation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\\n',encoding='utf-8')")
(S/'scripts/build_reader_metadata.py').write_text(generator,encoding='utf-8')
# Short visible provenance; complete scientific qualifications remain in the disclosure.
p=D/'reader-structures.mjs';s=p.read_text(encoding='utf-8')
s=s.replace("if(phaseScope)host.append(el('p',phaseScope,'reader-note reader-phase-scope'));", "if(phaseScope){const brief=phaseScope.match(/^.{1,350}?[.](?:\\s|$)/)?.[0]?.trim();host.append(el('p',brief||phaseScope,'reader-note reader-phase-scope'));}")
s=s.replace("if(ref.scope&&ref.scope!==phaseScope)details.append", "if(phaseScope)details.append(el('p',phaseScope));if(ref.scope&&ref.scope!==phaseScope)details.append")
s=s.replace("+' Å. '+(n===1?", "+' Å; α = '+model.cell.alpha+'°, β = '+model.cell.beta+'°, γ = '+model.cell.gamma+'°. '+(n===1?")
p.write_text(s,encoding='utf-8')
p=D/'reader.css';p.write_text(p.read_text(encoding='utf-8')+'\n.reader-method-card:only-child{grid-column:1/-1}\n',encoding='utf-8')
print('Prepared reusable reader generator and final presentation refinements.')
