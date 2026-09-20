from pathlib import Path
p=Path(r'[local path redacted]')
t=p.read_text(encoding='utf-8')
def replace(a,b):
    global t
    assert t.count(a)==1,a[:100]
    t=t.replace(a,b)
replace("const grid=el('div',undefined,'guide-evidence-gallery');for(const f of [...c.figures,...(c.tables||[]).filter(t=>t.public_asset)])", "const grid=el('div',undefined,'guide-evidence-gallery'),cards=[];const scopeLabels=c.record_formulation_labels?.[r.record_id]||[];for(const f of [...c.figures,...(c.tables||[]).filter(t=>t.public_asset)])")
replace("const card=el('figure',undefined,'guide-figure'),a=link", "const card=el('figure',undefined,'guide-figure'),a=link")
replace("card.append(d);grid.append(card);}host.append(grid);", "card.append(d);const direct=(f.sample_links||[]).some(x=>(typeof x==='string'?x:x.record_id)===r.record_id),sameFormulation=(f.formulation_labels||[]).some(x=>scopeLabels.includes(x));cards.push({card,relevant:direct||sameFormulation});grid.append(card);}if(c.record_formulation_labels){const filter=el('select',undefined,'guide-route-select');filter.setAttribute('aria-label','Figure scope');for(const [value,label] of [['record','Selected formulation or procedure context'],['all','All original figures and tables in this paper']]){const option=el('option',label);option.value=value;filter.append(option);}const count=el('p',undefined,'source-evidence-count');count.setAttribute('aria-live','polite');const apply=()=>{let n=0;for(const item of cards){item.card.hidden=filter.value==='record'&&!item.relevant;if(!item.card.hidden)n++;}count.textContent=n+' of '+cards.length+' original figures/tables shown. Shared formulation context does not establish the same specimen or treatment state.';};filter.onchange=apply;apply();host.append(filter,count);}host.append(grid);")
replace("const target=intuitionTarget||host;target.replaceChildren();", "const target=intuitionTarget||el('section');if(intuitionTarget)target.replaceChildren();else host.append(target);")
replace("const target=document.getElementById('material-intuition-content')||document.getElementById('record-intuition-content')||host;target.replaceChildren();", "const separate=document.getElementById('material-intuition-content')||document.getElementById('record-intuition-content');const target=separate||el('section');if(separate)target.replaceChildren();else host.append(target);")
p.write_text(t,encoding='utf-8')
print('Source-specific figure filter and non-destructive intuition fallback added.')
