"""Create an original plan of the four blocks at the circular intersection."""
import json
import math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
register=json.loads((HERE.parents[2]/'source/precise/huangpu-metropole-hotel/footprint-review.json').read_bytes())
heading=math.radians(register['author_frame']['runtime_heading_deg'])
c,s=math.cos(heading),math.sin(heading)
size=850
im=Image.new('RGB',(size,670),'#faf7ef');draw=ImageDraw.Draw(im)
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
face=lambda n:ImageFont.truetype(font,n)

def xy(x,y):
    return (int(429+(x*c+y*s)*5.8),int(310-(-x*s+y*c)*5.8))

def polygon(row):return [xy(*v)for v in row['geometry_model_xy_m']]

def label(wgs,name,dy=0):
    v=polygon(wgs);cx=sum(a[0]for a in v[:-1])/(len(v)-1);cy=sum(a[1]for a in v[:-1])/(len(v)-1)
    draw.multiline_text((cx,cy+dy),name,font=face(15),anchor='mm',align='center',spacing=1,fill='#282a22',stroke_width=2,stroke_fill='#f5efe3')

rows={r['local_id']:r for r in register['owners']}
for r in rows.values():draw.polygon(polygon(r),fill='#d9d8cc',outline='#a5a89b',width=1)
for road in register['map_crosscheck']['streets'].values():draw.line([xy(*v)for v in road['geometry_local_m']],fill='#a6ada3',width=2)
for i,color in [(1554,'#c6d5bc'),(1844,'#b3c8d0'),(1708,'#b6c9b0'),(724,'#b7b3ab'),(358,'#ce9b63')]:draw.polygon(polygon(rows[i]),fill=color,outline='#534d41',width=2)
for i,t,dy in [(358,'都城饭店\n180号 · 358',-28),(724,'沿街邻楼\n724',0),(1844,'汉弥尔登大楼\n170号 · 1844',9),(1708,'金城银行\n200号 · 1708',-8)]:label(rows[i],t,dy)
draw.multiline_text((113,310),'原工部局大楼\n1554',font=face(15),anchor='mm',align='center',fill='#313a2e')
# Match the actual ground-boundary points of the curved façade.
a=rows[358]['geometry_model_xy_m'];draw.line([xy(*v)for v in a[:5]],fill='#aa381c',width=5)
# Unobtrusive street names in the margins, with a direct line to the road.
for title,start,end in [('江西中路',(110,181),(330,214)),('福州路',(652,415),(603,400))]:
    draw.line([start,end],fill='#666b61',width=1);draw.text(start,title,font=face(17),fill='#53594b',anchor='mm',stroke_width=3,stroke_fill='#faf7ef')
draw.rectangle([0,0,size,54],fill='#faf7ef');draw.text((24,10),'江西中路与福州路圆形路口',font=face(26),fill='#282a22')
draw.rectangle([0,620,size,670],fill='#faf7ef');draw.text((24,631),'向北为上　红线为都城饭店的内凹街面　·　© OpenStreetMap contributors / Overture Maps',font=face(15),fill='#44483c')
draw.line([(742,594),(800,594)],fill='#484b42',width=3);draw.text((771,577),'10 m',font=face(15),fill='#484b42',anchor='mm')
im.save(HERE/'street-blocks.png')
