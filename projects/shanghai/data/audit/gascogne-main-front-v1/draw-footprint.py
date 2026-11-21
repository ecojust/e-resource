"""Draw the independently listed garden tower and five-storey street building from the frozen coordinates."""
from pathlib import Path
import json
import math
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import shape

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
record=json.loads((PROJECT/'source/precise/xuhui-gascogne-apartments-main-building/footprint-review.json').read_bytes())
font_file='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font=lambda size:ImageFont.truetype(font_file,size,index=2)
anchor=record['author_frame']['anchor']
lat=anchor['lat'];lon=anchor['lng'];k=6371008.8*math.radians(1);east=k*math.cos(math.radians(lat))
scale=6.05
def project(lng,lat_):return (342+(lng-lon)*east*scale,248-(lat_-lat)*k*scale)
image=Image.new('RGB',(760,688),'#f9f8f4');d=ImageDraw.Draw(image)
styles={107:('#eac285','#805a31'),4703:('#bedee5','#3e7582')}
rows=sorted(record['owners'],key=lambda r:r['local_id']in styles)
for r in rows:
    id=r['local_id'];g=shape(r['geometry']);pts=[project(x,y)for x,y in g.exterior.coords]
    fill,border=styles.get(id,('#e6e6df','#b5b5ad'))
    d.polygon(pts,fill=fill);d.line(pts,fill=border,width=3 if id in styles else 1)
    if id in styles:
        x,y=project(g.centroid.x,g.centroid.y)
        text='十三层主楼' if id==107 else '五层辅楼'
        d.text((x,y-5),text,anchor='mm',fill='#31332e',font=font(19))
        d.text((x,y+17),'107'if id==107 else'4703',anchor='mm',fill='#464943',font=font(14))
ring=record['original_geometry_wgs84']['coordinates'][0]
d.line([project(*ring[j])for j in (8,7,6)],fill='#a94129',width=5)
d.text((355,323),'前院',font=font(19),fill='#555b4a')
d.text((505,548),'淮海中路',font=font(21),fill='#71524c')
d.rectangle((0,0,759,59),fill='#f9f8f4');d.text((24,14),'淮海公寓两份保护登记的地块关系',font=font(25),fill='#24312b')
d.line((692,113,692,75),fill='#465149',width=3);d.polygon([(692,71),(686,87),(698,87)],fill='#465149')
d.text((692,54),'北',anchor='mm',font=font(15),fill='#465149')
d.rectangle((0,600,759,687),fill='#f9f8f4')
d.line([(28,624),(60,624)],fill='#a94129',width=5)
d.text((72,608),'本次制作的主楼南面  ·  1202号，市登记2D003',font=font(18),fill='#333a33')
d.text((28,643),'沿街辅楼为1204至1218号，市登记3D003。底图来源为OpenStreetMap及Overture Maps。',font=font(14),fill='#535b53')
image.save(HERE/'registered-buildings.png',optimize=True)
