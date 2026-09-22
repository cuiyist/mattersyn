from pathlib import Path
import shutil
W=Path(__file__).resolve().parent;D=W.parents[1]/'recipe-atlas/dist'
shutil.copy2(W/'reader-code-review/reader-particle-proposal.mjs',D/'reader-particle.mjs')
p=D/'reader-structures.mjs';s=p.read_text(encoding='utf-8');s="import {mountParticleContext} from './reader-particle.mjs';\n"+s
start=s.index("  try{if(key==='particle'){");end=s.index("  const entries=",start)
s=s[:start]+"  try{if(key==='particle'){mountParticleContext(panel,r,presentation);return;}\n"+s[end:]
# Remove superseded function so there is only one specimen-art policy.
start=s.index('function particleArt(');end=s.index('export async function mountReaderStructures',start);s=s[:start]+s[end:];p.write_text(s,encoding='utf-8')
p=D/'reader-app.mjs';s=p.read_text(encoding='utf-8')
s=s.replace("p.data_links?.full_review||('paper-review.html?id='+encodeURIComponent(r.lineage.source_group))", "p.data_links?.full_review||recordURL(r.record_id)+'#evidence'")
s=s.replace("async function select(rid){const turn=++generation;", "async function select(rid){delete main.dataset.readerReady;const turn=++generation;")
s=s.replace("history.replaceState(null,'',url);}", "history.replaceState(null,'',url);main.dataset.readerReady=rid;}")
p.write_text(s,encoding='utf-8')
# Keep just five specimen facts expanded; retain additional facts in a disclosure.
p=D/'reader-particle.mjs';s=p.read_text(encoding='utf-8')
s=s.replace("for(const f of group.facts){", "for(const f of group.facts.slice(0,5)){")
s=s.replace("copy.append(dl,link(", "if(group.facts.length>5){const extra=el('dl',undefined,'reader-product-facts');for(const f of group.facts.slice(5)){const row=el('div');row.append(el('dt',f.label),el('dd',text(f.value)));if(f.qualifier)row.append(el('small',f.qualifier));extra.append(row);}copy.append(disclosure('Additional specimen observations',extra));}copy.append(dl,link(")
p.write_text(s,encoding='utf-8')
print('Particle contexts and source fallback corrections applied.')
