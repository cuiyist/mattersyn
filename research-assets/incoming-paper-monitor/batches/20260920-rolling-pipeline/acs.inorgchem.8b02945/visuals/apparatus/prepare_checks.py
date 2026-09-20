from pathlib import Path
A=Path(__file__).resolve().parent;T=A.parents[2]/'la8031286/visuals/apparatus'
s=(T/'render_and_check.mjs').read_text(encoding='utf-8').replace('Pati2009','Friedfeld2019').replace('pati2009','friedfeld2019').replace('Pati 2009','Friedfeld 2019').replace('Pati et al. 2009','Friedfeld et al. 2019').replace('/root/backlog_eta','/root/norberg2004_extract').replace('35','58')
s=s.replace("b.option_pointers.reduce((a,p)=>a+Object.keys(records.find(r=>r.record_id===b.record_id).condition_options[+p.split('/')[2]].parameters).length,0)","b.option_selections.reduce((a,p)=>a+p.keys.length,0)")
start=s.index("check(row('drip'");end=s.index('for(const s of scenes)for(const group',start)
s=s[:start]+'''check(new Set(scenes.map(s=>s.kind)).size===58,'Unique exact record-operation scenes');
check(new Set(scenes.map(s=>s.operation_id)).size===34,'All 34 source operations');
check(row('dry-flask','oven_temperature').value==='160 °C','Oven temperature');
check(row('dry-flask','drying_duration').value==='overnight','Qualitative duration preserved');
check(row('acid-cold-hold','cold_hold_temperature').value==='-76 °C','Cold bath temperature');
check(row('acid-ambient-hold','ambient_hold_duration').value==='8 h','Ambient duration');
check(row('acid-crystallize','crystallization_temperature').value==='0 °C','Zero temperature preserved');
check(row('acid-extract','ether_extraction_repetitions').value==='3 count','Neutral count unit');
check(row('acid-nmr-analyze','13c_frequency').value==='176 MHz','Nucleus-specific frequency');
check(scene('tga-analyze').rows.some(x=>x.label==='Atmosphere'&&x.value.startsWith('Not reported')),'TGA does not inherit reaction gas');
check(scene('dsc-analyze').rows.some(x=>x.label==='Atmosphere'&&x.value.startsWith('Unreported')),'DSC gas unknown');
check(scene('xrd-analyze').rows.some(x=>x.value.includes('no Cu Kα')),'No invented wavelength');
check(scene('tem-analyze').rows.some(x=>x.value.includes('not relabeled as an SAED')),'Local FFT scope');
check(scene('acid-condense').description.includes('static vacuum'),'Static vacuum reported');
check(scene('acid-quench').description.includes('dropwise'),'Dropwise methanol');
check(scene('distill-solvent').rows.some(x=>x.value.includes('distillate is not')),'Residue retained');
check(scene('transfer-purify').rows.some(x=>x.value.includes('separately reported fractions')),'Separate GPC fractions');
const varied=scenes.find(x=>x.record_id.endsWith('conversion-concentration')&&x.operation_id==='sonicate-msc');
check(varied.rows.find(x=>x.pointer?.endsWith('/condition_specific_msc_mass')).quantity.value===null,'No invented varied mass');
check(!varied.rows.some(x=>x.kind==='operation_parameter'&&x.quantity.value===20),'No representative 20 mg in varied branch');
const counts=new Map();
for(const ss of scenes)for(const g of ss.rows.filter(x=>x.kind==='alternative_schedule_group'))for(const q of g.quantities){const k=ss.record_id+q.pointer;counts.set(k,(counts.get(k)||0)+1);}
for(const r of records)for(const [i,opt]of (r.condition_options||[]).entries())for(const k of Object.keys(opt.parameters))check(counts.get(r.record_id+'/condition_options/'+i+'/parameters/'+k)===1,'Each alternative parameter appears once at relevant stage');
''' +s[end:]
s=s.replace("fs.writeFileSync(path.join(A,'svg',scene.kind+'.svg'),scene.svg);","fs.writeFileSync(path.join(A,'svg',scene.kind+'.svg'),scene.svg);fs.writeFileSync(path.join(A,'svg',scene.kind+'--art.svg'),scene.artSvg);")
s=s.replace("'Separate solvent routes, diagnostic fraction, drying order, calcination/TGA atmosphere and XPS exposure limits'","'Friedfeld source-specific cold holds, external coolant separation, fraction flow, variant mass missingness and analysis context checks'")
(A/'render_and_check.mjs').write_text(s,encoding='utf-8')
s=(T/'render_previews.py').read_text(encoding='utf-8').replace('/root/backlog_eta','/root/norberg2004_extract')
s=s.replace("images.append({'scene_id'", "art=A/'svg'/(s['kind']+'--art.svg');adoc=pymupdf.open(stream=art.read_bytes(),filetype='svg');aout=A/'previews'/(s['kind']+'--art.png');adoc[0].get_pixmap(matrix=pymupdf.Matrix(1.8,1.8),alpha=False).save(aout)\n images.append({'art_svg_path':str(art.relative_to(A)),'art_svg_sha256':sha(art),'art_png_path':str(aout.relative_to(A)),'art_png_sha256':sha(aout),'scene_id'")
s=s.replace("write(A/'preview-manifest.json'", "artcontacts=[]\nfor start in range(0,len(images),6):\n group=images[start:start+6];canvas=Image.new('RGB',(1800,1760),'#e6eef4');d=ImageDraw.Draw(canvas)\n for j,item in enumerate(group):\n  im=Image.open(A/item['art_png_path']);im.thumbnail((570,795));x=(j%3)*600+15;y=(j//3)*880+15;canvas.paste(im,(x,y));d.text((x,y+808),str(start+j+1)+' '+item['operation_id'],fill='#123047');d.text((x,y+827),item['record_id'],fill='#123047')\n out=A/'contacts'/f'art-contact-{start//6+1}.png';canvas.save(out);artcontacts.append(dict(path=str(out.relative_to(A)),sha256=sha(out),scene_ids=[x['scene_id']for x in group]))\nwrite(A/'preview-manifest.json'")
s=s.replace("'contacts':contacts,", "'contacts':contacts,'art_contacts':artcontacts,")
(A/'render_previews.py').write_text(s,encoding='utf-8')
print('Prepared private module execution and preview helpers.')
