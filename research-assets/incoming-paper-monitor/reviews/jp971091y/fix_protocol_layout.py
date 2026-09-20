from pathlib import Path
p=Path(__file__).resolve().parent/'dabbousi-protocol.mjs'
s=p.read_text(encoding='utf-8')
s=s.replace('text-anchor="middle" font-size="${size}"','text-anchor="middle" font-family="Arial,sans-serif" font-size="${size}"')
s=s.replace("vial(391,211)+txt(459,157,'Transfer via',16)+txt(459,181,'syringe to',16)+txt(459,205,'addition funnel',16)","vial(355,211)+txt(479,157,'Transfer via',16)+txt(479,181,'syringe to',16)+txt(479,205,'addition funnel',16)")
s=s.replace("txt(453,123,'Pressure unknown',15)","txt(480,123,'Pressure unknown',14)")
s=s.replace("txt(460,166,polymer(r)?'Solvent removal':'Hexane removal',18)+txt(460,203,polymer(r)?'Viscous solution':'CdSe in TOPO/TOP',16)","txt(460,191,polymer(r)?'Solvent removal':'Hexane removal',18)+txt(460,224,polymer(r)?'Viscous solution':'CdSe in TOPO/TOP',16)")
s=s.replace("precipitation?'precipitate / exchange':'',14","precipitation?'Separate steps':'',14")
s=s.replace("wds?'Dry film ≈1 µm'","wds?'Dry film · 1 µm'")
s=s.replace("poly?'Cast the polymer composite':'Cast the concentrated dot dispersion'","poly?'Cast the polymer composite':wds?'Cast and dry the WDS film':'Cast the concentrated dot dispersion'")
s=s.replace("wds?'Dry film · 1 µm'","wds?'Final film · 1 µm'")
p.write_text(s,encoding='utf-8')
