from pathlib import Path
import json,subprocess,hashlib,math
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;D=json.loads((R/'source-manifest.json').read_text());S={d['role']:d for d in D}
P=Path(r'[local path redacted]')
items=[('main-graphical-abstract','main',1,[378,280,565,401]),('main-figure-1','main',3,[321,292,566,566]),('main-table-1','main',4,[59,292,302,423]),('main-figure-2','main',4,[322,64,566,245]),('main-figure-3','main',4,[322,570,566,765]),('main-figure-4','main',5,[321,65,566,380]),('main-figure-5','main',6,[321,63,566,441]),('main-kinetic-scheme','main',6,[61,323,300,382]),('main-figure-6','main',7,[321,63,566,378]),('si-figure-s1','si',2,[72,112,543,330]),('si-figure-s2','si',3,[72,312,543,707]),('si-table-s1','si',6,[72,268,540,470])]
(R/'crops').mkdir(exist_ok=True);out=[]
items[0]=('main-graphical-abstract','main',1,[353,280,566,382])
for id,role,page,bbox in items:
    x,y,x2,y2=[round(b*260/72) for b in bbox];dest=R/'crops'/id
    subprocess.run([str(P),'-f',str(page),'-l',str(page),'-singlefile','-r','260','-x',str(x),'-y',str(y),'-W',str(x2-x),'-H',str(y2-y),'-png',S[role]['source_path'],str(dest)],capture_output=True,check=True)
    path=dest.with_suffix('.png');im=Image.open(path)
    out.append({'id':id,'source_role':role,'pdf_page':page,'source_sha256':S[role]['sha256'],'bbox_pdf_points_top_left':bbox,'dpi':260,'pixel_dimensions':list(im.size),'path':str(path),'relative_path':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'kind':'original_pdf_native_crop','caption_included':id not in ['main-graphical-abstract','main-kinetic-scheme'],'visual_review':False})
(R/'crop-manifest.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for index,group in enumerate([out[:6],out[6:]],1):
    canvas=Image.new('RGB',(1500,1800),'white');draw=ImageDraw.Draw(canvas)
    for i,a in enumerate(group):
        im=Image.open(a['path']);im.thumbnail((720,535));x=(i%2)*750;y=(i//2)*600
        draw.text((x+10,y+5),a['id'],fill='black');canvas.paste(im,(x+10,y+35))
    canvas.save(R/f'crop-review-{index}.png')
print(f'Created {len(out)} original-native crops.')
