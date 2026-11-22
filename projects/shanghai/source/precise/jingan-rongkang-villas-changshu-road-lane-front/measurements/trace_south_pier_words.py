"""Measure the Fangyou-period applied blue words against the two 2017 photographs."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union
from trace_shop_signs import ORIGINAL, masked_polygons, pieces

HERE = Path(__file__).resolve().parent
RECTIFIED = np.float32([[24,595],[146,595],[146,25],[24,25]])
SEPTEMBER = {
    'pier_left': [[464,321,481,342],[463,347,481,369],[464,374,481,396],[463,399,485,421]],
    'pier_right': [[653,315,671,336],[650,346,672,368],[650,375,673,400],[649,402,673,429]]}
NATIVE = {'pier_left':[[24,29,157,161],[21,168,164,301]],
          'pier_right':[[31,27,151,165],[25,173,150,307]]}
FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')


def scale_to(g,bounds):
    x,y,X,Y=g.bounds
    l,t,r,b=bounds
    return affinity.translate(affinity.scale(affinity.translate(g,-x,-y),(r-l)/(X-x),(b-t)/(Y-y),origin=(0,0)),l,t)


def minister():
    # Seven connected blue strips. The bicycle handle interrupts the lowest centre in August.
    strips=[[(41,331),(131,327),(129,342),(40,347)],
            [(41,336),(56,335),(54,434),(38,436)],
            [(80,340),(96,339),(95,366),(78,366)],
            [(43,364),(125,360),(123,376),(41,380)],
            [(109,367),(125,364),(122,401),(106,403)],
            [(43,391),(122,387),(122,403),(42,409)],
            [(73,401),(88,399),(86,429),(69,429)],
            [(38,426),(132,422),(131,435),(38,438)]]
    return unary_union([Polygon(p) for p in strips])


def data(photo,second):
    assert hashlib.sha256(photo.read_bytes()).hexdigest()==ORIGINAL
    original=cv2.imread(str(photo))
    panels=json.loads((HERE/'south-shop-pier-panels.json').read_bytes())['native_uv']
    glyph=Image.new('L',(300,300))
    ImageDraw.Draw(glyph).text((0,0),'信',font=ImageFont.truetype(str(FONT),255,index=2),fill=255,anchor='lt')
    faith=masked_polygons(np.asarray(glyph)>110,(0,0))
    result={}
    for col in NATIVE:
        H=cv2.getPerspectiveTransform(np.float32(panels[col]),RECTIFIED)
        wall=cv2.warpPerspective(original,H,(176,645))
        b,g,r=wall.astype(np.int16).transpose(2,0,1)
        blue=(b>r+17)&(b>g+10)&(r<60)
        shapes=[]
        for l,t,R,B in NATIVE[col]:
            polys=pieces(masked_polygons(blue[t:B,l:R],(l,t),minimum=85))
            shapes.append(max(polys,key=lambda p:p.area))
        # Periodic placement is measured independently on the unobstructed September fronts.
        # The bottom of the left September inscription is behind the rail, with three pixels estimated.
        if col=='pier_left':
            shapes.extend([scale_to(minister(),[39,322,150,444]), scale_to(faith,[29,464,159,587])])
        else:
            shapes.extend([minister(),scale_to(faith,[30,465,148,590])])
        result[col]=[]
        for c,shape in zip('易居臣信',shapes):
            item={'letter':c,'evidence':{'易':'August outline','居':'August outline, lower edge cross-checked in September',
                 '臣':'Measured right-column August outline and September parallel; lower centre traced across a bicycle handle',
                 '信':'September identifies and locates the character; fitted Noto Sans CJK SC Bold outline'}[c]}
            for name,tol in [('near',.66),('low',1.27)]:
                rings=[]
                for p in pieces(shape.simplify(tol,preserve_topology=True)):
                    group=[]
                    for ring in [p.exterior,*p.interiors]:
                        xy=np.asarray(ring.coords)[:-1]
                        coords=np.column_stack([(xy[:,0]-24)/122-.5,(595-xy[:,1])/570])
                        group.append(coords.round(6).tolist())
                    rings.append(group)
                item[name]=rings
            xy=np.array([i for p in item['near']for ring in p for i in ring])
            item['normalized_bounds']=[*xy.min(0),*xy.max(0)]
            result[col].append(item)
    return {'subject':'常熟路荣康别墅南口，2017年房友门面两柱蓝字','inscription':'易居臣信',
            'photographs':[{'date':'2017-08-19','photographer':'Antigng','license':'CC BY-SA 4.0',
                'url':'https://commons.wikimedia.org/wiki/File:荣康别墅.jpg','sha256':ORIGINAL},
                {'date':'2017-09-03','size':[900,690],'sha256':hashlib.sha256(second.read_bytes()).hexdigest(),
                 'measured_native_bounds_LTRB':SEPTEMBER,'private_source_pixels_included':False}],
            'rectification':{'august_corners':{k:panels[k]for k in NATIVE},'rectified_BL_BR_TR_TL':RECTIFIED.tolist()},
            'construction':'Physical front relief 6 mm, assumed. Both columns are measured independently; shape and colour approximate shaded painted blue. Opaque foreground covers the bottom letter in August. Lower September pixels are about 20–27 pixels per letter.',
            'font_for_partial_character':{'name':'Noto Sans CJK SC Bold','character':'信','license':'SIL Open Font License 1.1','url':'https://github.com/notofonts/noto-cjk','font_sha256':hashlib.sha256(FONT.read_bytes()).hexdigest()},
            'panels':result}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for arg in ('august','september','output'):parser.add_argument(arg,type=Path)
    args=parser.parse_args()
    args.output.write_text(json.dumps(data(args.august,args.september),ensure_ascii=False,separators=(',',':'))+'\n')
