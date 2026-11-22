"""Plot published numeric observations and mesh residuals without reproducing the district photograph."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).absolute().parent;r=json.loads((p/'independent-roof-silhouette.json').read_bytes())
v=r['models']['full']['samples'];canvas=Image.new('RGB',(860,545),'#faf9f5');d=ImageDraw.Draw(canvas)
font=lambda n: ImageFont.truetype('DejaVuSans.ttf',n)
ink='#27343a';blue='#28536c';orange='#a5532e'
d.text((32,21),'Lane 865, Yuyuan Road',fill=ink,font=font(23))
d.text((32,55),'Eave profile in the district photograph, 58 held-out columns',fill=ink,font=font(16))
x=lambda u:72+(u-186)*3.15
y=lambda val:95+(val-76)*1.52
for val in (100,150,200,250):
    d.line((68,y(val),823,y(val)),fill='#d5d6cf');d.text((32,y(val)-8),str(val),font=font(12),fill=ink)
coords=[(x(row['u']),y(row['projected_v']))for row in v];d.line(coords,fill=blue,width=3)
for row in v:
    a,b=x(row['u']),y(row['v']);d.ellipse((a-2,b-2,a+2,b+2),fill=orange)
d.text((555,98),'Model edge',fill=blue,font=font(14));d.text((555,120),'Observed sky edge',fill=orange,font=font(14))
d.text((32,391),'Vertical difference in source pixels',font=font(15),fill=ink)
for delta in (-4,0,4):
    z=466-10*delta;d.line((68,z,823,z),fill='#bac1bc' if delta==0 else '#e0e0db');d.text((39,z-7),str(delta),font=font(12),fill=ink)
d.line([(x(q['u']),466-10*q['error_px']) for q in v],fill=blue,width=2)
for u in (200,250,300,350,400):
    a=x(u);d.text((a-12,517),str(u),font=font(12),fill=ink)
canvas.save(p.parent/'study-views/roof-profile.png',optimize=True)
