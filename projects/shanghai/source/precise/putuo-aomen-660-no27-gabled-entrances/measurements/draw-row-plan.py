"""Plot the georeferenced door-number points and their registered map outlines in local metres."""
import json, math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

here=Path(__file__).absolute().parent
survey=json.loads((here/'address-row.json').read_bytes())
row=survey['row_27_to_37']
shapes=row['associated_city_shapes']
nums=[27,29,31,33,35,37]
lon,lat=survey['numbered_address_points']['31']['wgs84']
sx=111319.49*math.cos(math.radians(lat)); sy=111132.9
def project(pt):
    return (485+(pt[0]-lon)*sx*12.1,265-(pt[1]-lat)*sy*12.1)
def font(size,bold=False):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',size)
im=Image.new('RGB',(930,570),'#f4f2e9');d=ImageDraw.Draw(im)
for k,data in shapes.items():
    poly=[project(pt) for pt in data['geometry']['coordinates'][0]]
    d.polygon(poly,fill='#dfb98d'if k=='1475'else '#deded3',outline='#875f44' if k=='1475' else '#c7c6bb',width=2)
for num in nums:
    pt=survey['numbered_address_points'][str(num)]['wgs84'];x,y=project(pt)
    d.ellipse([x-5,y-5,x+5,y+5],fill='#8c362b'if num==27 else '#554738')
    d.text((x+10,y+1),str(num)+'号',font=font(16,num==27),fill='#4d3027',stroke_width=2,stroke_fill='#f0e6d4')
d.rectangle([0,0,930,77],fill='#f7f5ee')
d.text((24,16),'澳门路660弄  ·  27至37号住宅',font=font(30,True),fill='#3e352c')
d.text((24,87),'同一排住宅上的六个地址点',font=font(17),fill='#474135')
d.line([(74,205),(74,164)],fill='#464136',width=2);d.polygon([(74,155),(69,167),(79,167)],fill='#464136');d.text((65,125),'北',font=font(15),fill='#464136')
d.line([(35,463),(156,463)],fill='#4d463a',width=3)
for q in (35,156):d.line([(q,459),(q,467)],fill='#4d463a',width=2)
d.text((65,431),'10米',font=font(15),fill='#4d463a')
d.rectangle([0,504,930,570],fill='#f7f5ee')
d.text((24,511),'门牌位置据高德公开地址点，底图1475为原有排屋。27号至37号端距约27.0米。',font=font(18),fill='#41392e')
d.text((24,542),'各点为地址标注，门洞至墙体边线的距离尚待现场测绘。',font=font(15),fill='#6e6658')
im.save(here.parent/'study-views'/'27-37-row.png',optimize=True)
