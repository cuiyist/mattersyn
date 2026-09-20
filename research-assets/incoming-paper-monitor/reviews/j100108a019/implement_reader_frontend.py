"""Integrate reusable source evidence and display categories in the existing Site."""
from pathlib import Path
ROOT=Path(r'[local path redacted]')
def replace(relative,old,new):
    p=ROOT/relative;t=p.read_text(encoding='utf-8')
    if old not in t:
        assert new in t,(relative,old[:80]);return
    assert t.count(old)==1,(relative,old[:80]);p.write_text(t.replace(old,new),encoding='utf-8')

replace('dist/material-hub.mjs',
    "const response=await fetch('data/materials/'+entry.id+'.json'",
    "const displayCategories=await(await fetch('data/measurement-display.json')).json();const structural=m=>displayCategories.structural_properties.includes(m.property)||displayCategories.structural_property_fragments.some(part=>m.property.includes(part));\n const response=await fetch('data/materials/'+entry.id+'.json'")
replace('dist/material-hub.mjs',
    "(new Set(['diameter','diameter_spread','particle_size','particle_size_spread','characteristic_size','edge_length','edge_length_spread','length','width','crystal_phase','lattice_parameter','interplanar_spacing']).has(m.property)||/shell_thickness|crystallite_size|lattice_parameter|interplanar_spacing/.test(m.property))===isStructure",
    "structural(m)===isStructure")
replace('dist/dataset-app.mjs',
    "(type==='recipes'&&r.record_type!=='procedure')",
    "(type==='recipes'&&!['procedure','observation'].includes(r.record_type))||(type==='observation'&&r.record_type==='observation')")
replace('dist/dataset-app.mjs',
    "(type==='reviewed'&&r.collection!=='published_benchmark'&&r.record_type!=='procedure')",
    "(type==='reviewed'&&r.collection==='reviewed_literature')")
replace('scripts/catalog_view.py',
    '<option value="procedure">Shared procedures</option>',
    '<option value="procedure">Shared procedures</option><option value="observation">Contextual observations</option>')
replace('scripts/catalog_view.py',
    'Shared preparation, characterization and assay procedures are separate records.',
    'Shared preparation, characterization and assay procedures are separate records. Contextual observations without a reconstructed synthesis are counted separately and have no enabled training tasks.')
replace('dist/material-guide.mjs',
    "import {mountCrystalReferences}",
    "import {sourceItemCard} from './source-evidence.mjs';\nimport {mountCrystalReferences}")
replace('dist/material-guide.mjs',
    "for(const f of c.figures)",
    "for(const f of [...c.figures,...(c.tables||[]).filter(t=>t.public_asset)])")
replace('dist/material-guide.mjs',
    "const interpretations=[c.chemical_intuition",
    "const sourceIntuition=c.reader_sections?.find(s=>s.id==='intuition');if(sourceIntuition?.items?.length){const target=intuitionTarget||host;target.replaceChildren();target.append(el('p','Author explanations and models retain their source and sample scope; they do not supply missing experimental labels.','guide-notice'));for(const item of sourceIntuition.items)target.append(sourceItemCard(item,{compact:true,sourceDoi:c.doi,sourceId:c.paper_id}));return;}\n const interpretations=[c.chemical_intuition")
replace('dist/material-guide.mjs',
    "const c=await res.json();host.append",
    "const c=await res.json();if(c.reader_sections?.length){const context=el('nav',undefined,'source-record-links');context.setAttribute('aria-label','Complete source evidence');for(const s of c.reader_sections)context.append(link(s.title+' →','paper-review.html?id='+c.paper_id+'#source-'+s.id));host.append(context);const related=el('details',undefined,'related-source-records');related.append(el('summary','Supporting procedures and contextual specimens'));for(const item of c.recipe_inventory||[])for(const id of item.record_ids||[])if(id!==r.record_id)related.append(link((item.label||id)+' →','records/'+id+'.html'));host.append(related);}host.append")
replace('scripts/build_atlas.py',
    "NAMES={'CdSe'",
    "NAMES={'Si/SiOx':'Surface-oxidized silicon nanocrystal colloids','Si':'Silicon cores in surface-oxidized colloids','SiOx':'Silicon oxide surface layer · stoichiometry unresolved','CdSe'")
print('Reader context, characterization categories and observation counts integrated.')
