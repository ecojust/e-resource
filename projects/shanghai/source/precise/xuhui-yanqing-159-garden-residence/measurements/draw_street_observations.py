"""Draw reference measurements beside an independently rendered street view."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
def draw(render,output):
    obs=json.loads((HERE/'north-street-window-intersections.json').read_text())['point_observations']
    fit=json.loads((HERE/'street-attic-height-comparison.json').read_text())['views'][1]
    px=Image.new('RGB',(950,650),(242,240,232))
    marks=ImageDraw.Draw(px)
    # Reference points were recorded in the street image. Only numbers and a
    # diagram generated from them are distributed, independent of photo rights.
    for key,tint in [('A',(45,111,102)),('B',(45,111,102)),('C',(45,111,102)),
                     ('B_attic',(151,101,60)),('C_attic',(151,101,60)),('front_high_vent',(167,68,55))]:
        top=obs[key+('_top' if key=='front_high_vent' else '_head')]['pixels_by_view'][1]
        low=obs[key+'_sill']['pixels_by_view'][1]
        if top and low:
            marks.line([tuple(top),tuple(low)],fill=tint,width=3)
            for x,y in (top,low):
                marks.line((x-12,y,x+12,y),fill=tint,width=3);marks.ellipse((x-3,y-3,x+3,y+3),fill=tint)
            if key in 'ABC':marks.text((top[0]-4,top[1]-21),key,fill=tint)
    ref=px.crop((265,-95,960,391))
    # Pale background extends above the source raster, where no measurements exist.
    ImageDraw.Draw(ref).rectangle((0,0,ref.width,94),fill=(242,240,232))
    model=Image.open(render).convert('RGB')
    size=(565,394);ref=ref.resize(size);model=model.resize(size)
    pad=18;sheet=Image.new('RGB',(2*size[0]+3*pad,size[1]+144),(247,246,240));d=ImageDraw.Draw(sheet)
    fam='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font=ImageFont.truetype(fam,23);small=ImageFont.truetype(fam,15);ink=(45,49,45)
    d.text((pad,6),'延庆路159号临街三组窗与东北角阁窗',font=font,fill=ink)
    sheet.paste(ref,(pad,48));sheet.paste(model,(size[0]+2*pad,48))
    y=52+size[1]
    d.text((pad,y),'2015年12月19日街景读数。短横线标出窗头和窗台。',font=small,fill=ink)
    d.text((2*pad+size[0],y),'按三组主窗配准的模型。房屋以外的遮挡物省略。',font=small,fill=ink)
    d.text((pad,y+31),'独立复核的东侧阁窗标成红色。此机位中，模型窗头、窗台与实景读数分别相差约7和4像素。',font=small,fill=ink)
    sheet.save(output,quality=90,optimize=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('render',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();draw(args.render,args.output)
