from pathlib import Path
import json,re
O=Path(__file__).resolve().parent;B=O.parent
old=B.parent/'cm0115416/public-review-proposal/validate_proposal.py'
s=old.read_text(encoding='utf8').replace('yi2002','banerjee2003').replace('range(1,28)','range(1,44)')
s=s.replace("ck('source hash',sha(Path(source['source_path'])),source['sha256']);ck('main page count',source['main_page_count'],5)","sources={d['role_candidate']:d for d in source['documents'] if d['role_candidate'] in {'main','si'}}\nfor role,d in sources.items():ck(role+' source hash',sha(Path(d['path'])),d['sha256'])\nck('main/SI page count',[sources[k]['page_count'] for k in ['main','si']],[9,1])")
s=s.replace("sorted('figure-'+str(n) for n in range(1,11))","sorted(['figure-'+str(n) for n in range(1,9)]+['si-infrared'])")
s=s.replace("a['source_sha256'],source['sha256']","a['source_sha256'],sources[a['source_role']]['sha256']")
a=s.index("ck('Figure 1 explicit 800 C cohort'");z=s.index('result=',a)
s=s[:a]+"""ck('Figure 1 precursor-only association',assets['figure-1']['sample_links'],['banerjee-2003-oxidation'])
ck('Figure 8 author mechanism',assets['figure-8']['sample_links'],['banerjee-2003-mechanisms'])
ck('SI precursor-only association',assets['si-infrared']['sample_links'],['banerjee-2003-infrared'])
ck('CdTe does not inherit precursor IR', 'banerjee-2003-infrared' not in r['material_evidence_records']['CdTe'])
ck('MWNT does not inherit free-particle comparator', 'banerjee-2003-free-nanocrystals' not in r['material_evidence_records']['MWNT'])
"""+s[z:]
(O/'validate_proposal.py').write_text(s,encoding='utf8')
m=B/'reader-assets/crop-manifest.json';d=json.loads(m.read_text(encoding='utf8'))
for a in d['assets']:a['visual_reviewed']=True
d['visual_inspection_note']='All 15 final 300 dpi PDFium crops individually inspected. Complete panels, original axes, captions, Symbol glyphs and excerpt continuation boundaries retained.'
m.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
f=O/'assets_metadata.py';s=f.read_text(encoding='utf8')
for a,b in {'a,b scales100,200nm':'a, b scales 100, 200 nm','c,d,e scales180,75,112nm':'c, d, e scales 180, 75, 112 nm','a and inset5nm each; b20nm,c5nm,d10nm':'a and inset 5 nm each; b 20 nm, c 5 nm, d 10 nm','a20nm,b10nm,c10nm':'a 20 nm, b 10 nm, c 10 nm','ticks2,4,6,8,10':'ticks 2, 4, 6, 8, 10','energy/eV; plotted ticks2–10':'energy / eV; plotted ticks 2–10','C1s,O1s,Te3d5/2,Cd3d5/2':'C 1s, O 1s, Te 3d₅/₂, Cd 3d₅/₂','energy405.22eV':'energy 405.22 eV','labels100/002/101,110,103,200':'labels 100/002/101, 110, 103, 200','MWNT002,101,004':'MWNT 002, 101, 004','XRD2θ ticks20–70°':'XRD 2θ ticks 20–70°','Topblue':'Top blue','bottomred':'bottom red','LO166cm−1':'LO 166 cm⁻¹','bulk170cm−1':'bulk 170 cm⁻¹','near1590,D1290–1320cm−1':'near 1590, D 1290–1320 cm⁻¹','labeled1000,2000,3000,4000':'labeled 1000, 2000, 3000, 4000','Lowerred':'Lower red','uppergreen':'upper green','labeled300–1000':'labeled 300–1000','labeled2000,1800,1600,1400,1200,1000,800':'labeled 2000, 1800, 1600, 1400, 1200, 1000, 800','35%HCl then10%HF':'35% HCl then 10% HF',';150°C':'; 150 °C','320°C':'320 °C','300°C':'300 °C','250°C/20min':'250 °C / 20 min','Cool50°C;5mL':'Cool to 50 °C; 5 mL',';0.2µm':'; 0.2 µm',';200µm':'; 200 µm',';785nm,10mW':'; 785 nm, 10 mW','oxidation~5–6atomic%O':'oxidation ~5–6 atomic % O','mild~1–2atomic%O':'mild ~1–2 atomic % O','Cd3d5/2':'Cd 3d₅/₂','Cd405.22eV':'Cd 405.22 eV','literalTeO3':'literal TeO₃','approximate350°C':'approximate 350 °C'}.items():s=s.replace(a,b)
f.write_text(s,encoding='utf8')
builder=O/'build_review_proposal.py';s=builder.read_text(encoding='utf8');line="exec((O/'material_mapping.py').read_text(encoding='utf8'))\n"
if line not in s:s=s.replace("if records and (O/'canonical_mapping.py').exists():",line+"if records and (O/'canonical_mapping.py').exists():")
builder.write_text(s,encoding='utf8');print('Prepared private validator and finalized crop inspection metadata')
