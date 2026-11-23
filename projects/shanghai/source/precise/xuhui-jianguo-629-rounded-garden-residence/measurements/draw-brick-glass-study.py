"""Original schematic of visible garden-front ornament. No third-party pixels."""
import argparse
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

S = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(S/'source'))
from arch_brick_and_glass import pier_outline
from garden_letters import glyph


def draw(output):
    image = Image.new('RGB',(1180,830),'#f7f4ec')
    d = ImageDraw.Draw(image)
    regular = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    bold = regular.replace('Regular','Bold')

    def text(x,y,t,n=20,color='#2a302e',strong=False):
        d.text((x,y),t,fill=color,font=ImageFont.truetype(bold if strong else regular,n,index=2))

    def poly(shape, mapping, colour):
        for p in getattr(shape,'geoms',[shape]):
            d.polygon([mapping(x,z) for x,z in p.exterior.coords],fill=colour)
            for ring in p.interiors:
                d.polygon([mapping(x,z) for x,z in ring.coords],fill='#f7f4ec')

    text(42,23,'建国西路629号住宅 · 花园立面装饰',35,strong=True)
    text(43,82,'三层中央砖芯与窄窗的两份照片记录',22)
    d.line([(43,127),(1136,127)],fill='#bdb39d',width=2)
    text(48,144,'中央窗间砖芯',22,strong=True)
    text(318,144,'玻璃砖窄带',22,strong=True)
    text(538,144,'钢框窄窗',22,strong=True)
    text(800,144,'立面题字',22,strong=True)
    for x,t in [(48,'同层正投影'),(318,'2019年刊载'),(538,'2017年摄取'),(800,'按照片实际错列')]:
        text(x,180,t,16,color='#616967')
    layout = json.loads((S/'measurements/brick-and-glass-profiles.json').read_text())
    for i, row in enumerate(layout['levels']):
        top=235+164*i
        text(44,top+41,['上层','中层','下层'][i],17,color='#555d5a')
        x0,x1,z0,shoulder,z1=row['pier']
        sc=57.; transform=lambda x,z: (165+(x-(x1+x0)/2)*sc,top+130-(z-z0)*sc)
        outline=pier_outline(row['pier']); poly(outline,transform,'#a66650')
        mask=Image.new('1',image.size); md=ImageDraw.Draw(mask)
        md.polygon([transform(x,z) for x,z in outline.exterior.coords],fill=1)
        ink=Image.new('RGB',image.size,'#a66b53'); di=ImageDraw.Draw(ink)
        pitch=layout['course_height']*sc
        for k in range(55):
            y=round(top+130-k*pitch)
            di.line((100,y,235,y),fill='#935f48')
            for n in range(-5,7):
                x=round(165+(n+(k%2)*.5)*3.4*pitch)
                di.line((x,y,x,y+pitch),fill='#935f48')
        image.paste(ink,(0,0),mask)
        x0,x1,z0,z1=row['strip']
        width=(x1-x0)*sc
        for x,early in [(378,False),(611,True)]:
            lo=top+140
            zs=lambda z:lo-(z-z0)*sc
            d.rectangle((x-width/2-3,zs(z1)-3,x+width/2+3,lo+3),fill='#d1c6b3')
            d.rectangle((x-width/2,zs(z1),x+width/2,lo),fill='#aa7159')
            for l,h,rows in [(z0,row['brick_bottom'],row['courses'][1]),(row['brick_top'],z1,row['courses'][0])]:
                bounds=(x-width/2,zs(h),x+width/2,zs(l))
                d.rectangle(bounds,fill='#758384' if early else '#859999',outline='#333f3f' if early else '#aeb9ae',width=2)
                if not early:
                    for col in range(1,3):
                        xx=x-width/2+width*col/3
                        d.line((xx,zs(h),xx,zs(l)),fill='#c9cabe',width=1)
                    for k in range(1,rows):
                        yy=zs(l+(h-l)*k/rows)
                        d.line((x-width/2,yy,x+width/2,yy),fill='#c9cabe',width=1)
            for z in range(round(zs(row['brick_top']))+4,round(zs(row['brick_bottom'])),4):
                d.line((x-width/2,z,x+width/2,z),fill='#93644e')
    seq=[('立',986,245),('言',986,307),('立',986,408),('思',986,469),
         ('立',835,408),('行',835,469),('立',835,568),('志',835,629)]
    for ch,x,y in seq:
        g=glyph(ch);a,b,c,e=g.bounds
        poly(g,lambda u,v:(x+(u-a)/(c-a)*72,y+(e-v)/(e-b)*49),'#413d36')
    d.line((43,733,1137,733),fill='#bdb39d',width=2)
    text(45,750,'砖芯上层直楣，下两层浅弧。窄带两期均在上下透光段之间夹一块红砖。',18)
    text(45,786,'图据 Antigng 2017年8月2日照片及2019年3月11日刊载照片重绘。刊载照片的拍摄日期待考。',15,color='#616967')
    output.parent.mkdir(parents=True,exist_ok=True)
    image.save(output,optimize=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    draw(parser.parse_args().output)
