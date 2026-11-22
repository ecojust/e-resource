"""Draw the surveyed timber windows and their traced photographic corners in each real camera."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'source'))
sys.path.insert(0,str(P.parents[2]/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
import guiren_window_sashes as sash
from math import ceil
m=json.loads((P/'measurements/window-photo-observations.json').read_text())
b=Builder(sash.PALETTE);sash.add_windows(b,False)
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def face(size):return ImageFont.truetype(font,size)
sheet=Image.new('RGB',(1110,789),'#f8f5ee');s=ImageDraw.Draw(sheet)
s.text((27,14),'归仁里过街楼  ·  街面窗扇测绘',font=face(30),fill='#282b2a')
s.text((29,63),'模型采用各照片的原相机投影。金色十字为独立读取的窗扇或框口角点，原照片未嵌入。',font=face(16),fill='#5a5951')
ordered=[('left_upper','东侧清水砖楼 · 二层'),('gate_upper','主弄口上窗 · 外开124°'),('right_upper','西侧凸窗廊 · 六扇'),('left_lower','东侧清水砖楼 · 底层'),('wide','西侧窗廊 · 顶部十格通亮'),('right_lower','西侧窗廊 · 底层四扇')]
for j,(key,title) in enumerate(ordered):
    d=m['wide_upper_light'] if key=='wide' else m['windows'][key];camera=np.asarray(d['xyz_to_image'])
    eye=-np.linalg.solve(camera[:,:3],camera[:,3])
    kind=key if key!='wide' else 'right_upper'
    if key=='wide':quads=[d['quad']]
    elif key=='gate_upper':quads=[d['left_open_leaf']['quad'],d['right_closed_leaf']['quad']]
    else:quads=[d['six_sash_frame' if key=='right_upper' else 'fixed_frame']['quad']]
    panels=[]
    for part in b.parts:
        if not part['label'].startswith('Guiren Li | '+kind+' | '): continue
        if key=='wide' and 'upper band ' not in part['label'] and 'continuous upper light' not in part['label']:continue
        if key=='right_upper' and ('upper band ' in part['label'] or 'continuous upper light' in part['label']):continue
        xyz=np.asarray(part['vertices']);v=np.c_[xyz,np.ones(len(xyz))]@camera.T
        pix=v[:,:2]/v[:,2:]
        mat=part['material'];rgb=np.asarray(sash.PALETTE[mat]['color'])
        col=np.clip(np.where(rgb<.00313,rgb*12.92,1.055*rgb**(1/2.4)-.055)*255,0,255)
        for faceidx in part['triangles']:
            i=list(faceidx);norm=np.cross(xyz[i[1]]-xyz[i[0]],xyz[i[2]]-xyz[i[0]]);norm/=np.linalg.norm(norm)
            if norm@(eye-xyz[i].mean(axis=0))<=0:continue
            light=.80+.20*max(0.,norm@np.array([-.36,-.78,.50]))
            panels.append((v[i,2].mean(),pix[i],tuple((col*light).astype(int))))
    allxy=np.concatenate([i[1] for i in panels]+[np.array(x) for x in quads]);mn=allxy.min(axis=0);mx=allxy.max(axis=0)
    margin=17;ww,hh=340,255;factor=min((ww-margin*2)/(mx[0]-mn[0]),(hh-margin*2)/(mx[1]-mn[1]))
    def screen(v):return (np.asarray(v)-(mn+mx)/2)*factor+[ww/2,hh/2]
    frame=Image.new('RGB',(ww,hh),'#263033');d0=ImageDraw.Draw(frame)
    for depth,poly,color in sorted(panels,key=lambda x:-x[0]):
        d0.polygon([tuple(p) for p in screen(poly)],fill=color)
    for q in quads:
        for x,y in screen(q):
            d0.line((x-4,y,x+4,y),fill='#ffcf58',width=1);d0.line((x,y-4,x,y+4),fill='#ffcf58',width=1)
    x=28+363*(j%3);y=112+318*(j//3)
    sheet.paste(frame,(x,y));s.text((x,y+262),title,font=face(19),fill='#303531')
    src=d.get('date','');s.text((x,y+290),f'{src[:4]}年{int(src[4:6])}月影像',font=face(14),fill='#686967')
# Bind the comparative drawing to the actual published-size geometry that passed these rays.
destination=Path(sys.argv[1])
proof=destination.with_name('whole-building-sash-checks.json')
if proof.is_file():
    records=json.loads(proof.read_bytes())['exports']
    assert [r['file'] for r in records]==['raw.glb','decoded-full.glb','decoded-lod.glb']
    assert all(r['tests']==112 and not r['issues'] for r in records)
    tags='   ·   '.join(label+' '+r['sha256'][:10] for label,r in zip(('原网','解码近档','解码远档'),records))
    s.line((27,747,1080,747),fill='#c5c0b4')
    s.text((29,753),tags+'   ·   每档112项窗面及贯空核验',font=face(15),fill='#565a52')
sheet.save(destination,quality=90,subsampling=0)
