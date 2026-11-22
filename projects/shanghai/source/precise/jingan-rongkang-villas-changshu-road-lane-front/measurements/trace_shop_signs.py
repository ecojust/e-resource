"""Trace the visible fronts of the four 2017 shop signs in calibrated native photograph pixels."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from scipy.ndimage import median_filter

ORIGINAL = '66bc99e23453d234029721aa78b6079bbca1e85ccf8c0aff573a11113d0c88be'
PANELS = {
    'south':[[-439.95, 2418.198], [2457.264, 2376.699], [2451.687, 2138.299], [-387.423, 2116.018]],
    'north_left':[[3250,2329],[3642,2335],[3635,2214],[3244,2202]],
    'north_middle':[[3698,2335],[4335,2344],[4329,2227],[3690,2214]],
    'north_right':[[4399,2343],[4870,2345],[4859,2235],[4387,2228]]}
UNIT = np.float32([[-.5,0],[.5,0],[.5,1],[-.5,1]])
def pieces(p):
    if p.is_empty:return []
    if p.geom_type=='Polygon':return [p]
    return [g for k in p.geoms for g in pieces(k)] if hasattr(p,'geoms') else []

def masked_polygons(mask,xy,minimum=6):
    mask=np.uint8(mask)*255
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((2,2),np.uint8))
    contours,h=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    shapes=[]
    for i,c in enumerate(contours):
        if h[0,i,3]!=-1 or cv2.contourArea(c)<minimum:continue
        outer=c.reshape(-1,2)+xy
        inner=[]
        j=h[0,i,2]
        while j>=0:
            if cv2.contourArea(contours[j])>3:
                inner.append(contours[j].reshape(-1,2)+xy)
            j=h[0,j,0]
        shapes.extend(pieces(Polygon(outer,inner).buffer(0)))
    return unary_union(shapes)

def trace(image, font_path):
    image=np.asarray(image,dtype=np.int16)
    result={k:[]for k in PANELS}
    def store(panel,label,shape,material,style='full native 2017 front outline'):
        mat=cv2.getPerspectiveTransform(np.float32(PANELS[panel]),UNIT)
        def transform(coords):
            a=np.c_[coords,np.ones(len(coords))]@mat.T
            return np.round(a[:,:2]/a[:,2:],6).tolist()
        specs=[]
        for lod,step in [('full',.75),('lod',1.45)]:
            polys=[]
            for poly in pieces(shape.simplify(step,preserve_topology=True)):
                if poly.area<4:continue
                polys.append([transform(np.asarray(r.coords)[:-1])for r in [poly.exterior,*poly.interiors]])
            specs.append(polys)
        xx=[p for comp in specs[0] for ring in comp for p in ring]
        if not xx:raise ValueError(label)
        from numpy import min as amin,max as amax
        result[panel].append({'lettering':label,'surface':material,'evidence':style,
            'normalized_bbox':[ *amin(xx,axis=0).tolist(),*amax(xx,axis=0).tolist()],
            'near':specs[0],'low':specs[1]})
    def pick(panel,label,rect,test,material):
        x,y,X,Y=rect; r,g,b=image[y:Y,x:X].transpose(2,0,1)
        p=masked_polygons(test(r,g,b),(x,y))
        if label=='厢':
            # Three large connected faces are the roof, wood radical and eye.
            # Small dark marks inside the eye openings are in the photographed background.
            p=unary_union([g for g in pieces(p) if g.area>52])
        store(panel,label,p,material)
    pink=lambda r,g,b:(r-g>57)&(b-g>32)&(r>110)
    white=lambda r,g,b:(np.minimum(np.minimum(r,g),b)>178)&(b>185)
    red=lambda r,g,b:g<25
    cream=lambda r,g,b:(g>47)&(np.abs(r-g)<23)&(np.abs(b-g)<17)
    for a,b,word in [(3255,3375,"Jill’s"),(3383,3498,'Nail'),(3504,3648,'Salon')]:
        pick('north_left',word,(a,2214,b,2312),pink,'pink')
    for a,b,word in [(3918,4008,'尚'),(4041,4147,'服'),(4182,4284,'饰')]:
        pick('north_middle',word,(a,2223,b,2333),white,'white')
    # The first character is clear at the September station; its August face lies behind foliage.
    glyph=Image.new('L',(190,190));pen=ImageDraw.Draw(glyph)
    pen.text((0,0),'风',font=ImageFont.truetype(str(font_path),153,index=2),fill=255,anchor='lt')
    p=masked_polygons(np.asarray(glyph)>100,(0,0));u,v,U,V=p.bounds
    p=affinity.translate(p,-u,-v)
    p=affinity.scale(p,85/(U-u),92/(V-v),origin=(0,0));p=affinity.translate(p,3778,2224)
    store('north_middle','风',p,'white','2017-09-03 and 2015 street photographs identify this character. The close August view is covered; its strokes use Noto Sans CJK SC Bold (SIL OFL 1.1), scaled between the observed letters.')
    for a,b,word in [(4429,4529,'红'),(4539,4639,'袖'),(4648,4743,'添'),(4767,4849,'厢')]:
        pick('north_right',word,(a,2234,b,2333),red,'wine')
    for a,b,word in [(700,850,'房'),(852,994,'友'),(1163,1238,'n'),(1239,1317,'g'),(1319,1393,'y'),(1394,1467,'o'),(1469,1544,'u'),(1546,1562,'.'),(1565,1607,'c'),(1607,1651,'o'),(1652,1711,'m')]:
        pick('south',word,(a,2240 if word=='n' else 2188,b,2316 if word=='n' else 2345),cream,'pale')
    # An unoccluded exposure shows the F has a smooth shoulder and a shorter middle arm.
    # Letter a has a closed oval counter and a right-hand descender ending at the baseline.
    f=[(1017,2312),(1024,2231),(1028,2219),(1034,2211),(1046,2206),(1077,2205),(1076,2221),(1053,2221),(1045,2224),(1040,2229),(1038,2247),(1073,2247),(1072,2261),(1036,2261),(1032,2312)]
    store('south','F',Polygon(f),'pale','2017-09-03 left unobscured; August native shoulder and lower stroke confirm form')
    def oval(x,z,rx,rz):return affinity.scale(Point(x,z).buffer(1,quad_segs=14),rx,rz,origin=(x,z))
    a=oval(1114,2280,32,33).difference(oval(1114,2280,17,18)).union(Polygon([(1133,2280),(1146,2280),(1146,2311),(1131,2311)]))
    store('south','a',a,'pale','2017-09-03 clear, August hidden by a street pole; reconstructed from approximately circular bowl and right stem in September')
    pick('south','blue chevron above u',(1460,2188,1554,2238),lambda r,g,b:(b>r+22)&(b>g+9)&(g>21),'blue')
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('original',type=Path);ap.add_argument('out',type=Path)
    ap.add_argument('--font',type=Path,default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'))
    args=ap.parse_args();assert hashlib.sha256(args.original.read_bytes()).hexdigest()==ORIGINAL
    geometry=trace(Image.open(args.original),args.font)
    evidence={'subject':'2017年常熟路荣康别墅南口相邻四块店招','camera':'5312 × 2988 原图，原点左上',
      'photograph':{'sha256':ORIGINAL,'author':'Antigng','date':'2017-08-19','license':'CC BY-SA 4.0','url':'https://commons.wikimedia.org/wiki/File:%E8%8D%A3%E5%BA%B7%E5%88%AB%E5%A2%85.jpg'},
      'secondary':{'date':'2017-09-03','north_station':'09000300121709030947260566A','role':'中牌首字与南牌灯杆所遮的 F、a 以另站识别；日期相近。','pixels_included':False},
      'supplemental_font':{'name':'Noto Sans CJK SC Bold','character':'风','license':'SIL Open Font License 1.1','upstream':'https://github.com/notofonts/noto-cjk','font_sha256':hashlib.sha256(args.font.read_bytes()).hexdigest()},
      'right_inscription':'红袖添厢，末字在近照片可见厂、木、目三个偏旁。','corners_native_BL_BR_TR_TL':PANELS,
      'coordinates':'Left = −0.5, right = +0.5, lower = 0, upper = 1. South board width follows the calibrated 10.55m fascia; its left end is outside August frame. North centre upper left and right board lower right extrapolated about 7/5 native px.',
      'colour_basis':'Photos record lit faces and shade. Material colours are estimates of daytime appearance. Front names are assigned by painted face appearance.',
      'panels':geometry}
    args.out.write_text(json.dumps(evidence,ensure_ascii=False,separators=(',',':'))+'\n')
