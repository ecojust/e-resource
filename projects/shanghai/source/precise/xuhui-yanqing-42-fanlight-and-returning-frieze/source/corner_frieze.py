"""No. 42 Yanqing Road. Front fanlight, imposts and the continuing upper-floor frieze."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon,LineString
ID='xuhui-yanqing-42-fanlight-and-returning-frieze'
RENDER='Grey-blue roughcast';PIER='Grey-blue ashlar';MINT='Pale green arched reveal';STONE='Off-white cornice';SHADOW='Shadowed cornice bed';SASH='Cream window bars';PANE='Smoky fanlight glass';BAND='Blue grey impost bands';RELIEF='Raised roughcast ornament'
PALETTE={m:dict(color=c,roughness=r) for m,c,r in ((RENDER,[1,1,1],.94),(PIER,[.57,.62,.63],.91),(MINT,[.661,.734,.673],.91),(STONE,[.768,.762,.689],.90),(SHADOW,[.413,.447,.436],.89),(SASH,[.801,.790,.698],.78),(PANE,[.339,.367,.349],.39),(BAND,[.302,.354,.356],.86),(RELIEF,[.507,.552,.571],.9))}
SPRING=.42;RX=.655;RZ=.554;END=1.20;DEPTH=.93
def texture():
    f=Path(__file__).with_name('roughcast-and-painted-stone.png')
    if not f.exists():
        rng=np.random.default_rng(835)
        notes=np.asarray(Image.fromarray(rng.integers(0,255,(42,37),dtype='uint8')).resize((256,240),Image.Resampling.BILINEAR)).astype(float)*.047-6
        grains=np.array([142,153,156])+(notes+rng.normal(0,9,(240,256)))[:,:,None]
        finish=np.array([158,166,167])+rng.normal(0,3,(240,256,1))
        pixels=np.concatenate([grains,finish],axis=1)
        Image.fromarray(pixels.clip(0,255).astype('uint8')).quantize(112).save(f)
    for material in (RENDER,PIER):
        PALETTE[material]['color']=[1,1,1]
        PALETTE[material]['texture']=str(f)
def arc(radius,steps):
    return [(RX*radius*math.cos(i*math.pi/steps),SPRING+RZ*radius*math.sin(i*math.pi/steps)) for i in range(steps+1)]
def add_building(b,far=False):
    texture();s=19 if far else 63
    def face(poly,back,front,mat,name):b.prism(poly,back,front,lambda x,z,d:(x,-d,z),mat,name)
    def rect(x0,x1,y0,y1,z0,z1,material,name):b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=name)
    def ledge(side0,side1,low,top,mat,label):
        rect(-1.01,END+side1,-side1,-side0,low,top,mat,label+' across front')
        rect(END+side0,END+side1,-side0,DEPTH,low,top,mat,label+' on return')
    opening=Polygon(arc(1.08,s)+[(-RX*1.08,-.015),(RX*1.08,-.015)])
    face(box(-1.015,0,END,1.18).difference(opening),-.176,0,MINT,'Front spandrel and reveal surrounding the arch')
    rect(END-.145,END,0,DEPTH,0,1.18,MINT,'Short return across the corner')
    face(Polygon(arc(1.03,s)),-.192,-.174,PANE,'Arched glass across the door head')
    for outer,inner,mat,depth,label in [(1.09,1.018,MINT,.024,'Raised render lining at arch'),(1.023,.965,SASH,-.111,'Arched sash perimeter'),(.553,.500,SASH,-.115,'Elliptical inner glazing bar')]:
        face(Polygon(arc(outer,s)+arc(inner,s)[::-1]),-.18,depth,mat,label)
    for deg in (41,90,139):
        a=math.radians(deg);ends=[(RX*r*math.cos(a),SPRING+RZ*r*math.sin(a)) for r in (.018,1.003)]
        face(LineString(ends).buffer(.017,cap_style=2),-.172,-.102,SASH,'Straight radial fanlight bar')
    rect(-RX,RX,.087,.179,SPRING-.03,SPRING+.022,SASH,'Cream transom across lower lights')
    rect(-RX,RX,.196,.22,0,SPRING-.031,PANE,'Dark glass in upper part of rectangular lights')
    for x in (-.59,-.375,-.16,.075,.282,.564):
        rect(x-.012,x+.012,.109,.179,0,SPRING-.021,SASH,'Upright below fanlight')
    for lo,hi in [(-1.014,-.693),(.694,END)]:
        rect(lo,hi,-.040,.133,.04,.363,PIER,'Squared grey pier below impost')
        for i,(z,h,d) in enumerate([(.325,.043,.068),(.363,.028,.093),(.391,.033,.079),(.424,.043,.100),(.467,.028,.106)]):
            rect(lo-.012,hi+.014,-d,.035,z,z+h,BAND if i in (1,3) else PIER,'Stepped impost capital')
    for z,h,d,mat in [(1.132,.044,.038,SHADOW),(1.17,.043,.072,STONE),(1.207,.052,.126,STONE),(1.252,.045,.169,STONE),(1.291,.038,.156,SHADOW),(1.323,.033,.172,STONE)]:
        ledge(-.01,d,z,z+h,mat,'Continuous cornice')
    ledge(-.132,0,1.350,1.795,RENDER,'Textured frieze')
    for z,h,d,mat in [(1.35,.025,.016,RELIEF),(1.733,.021,.019,RELIEF),(1.775,.026,.032,PIER),(1.799,.023,.044,PIER)]:
        ledge(-.012,d,z,z+h,mat,'Raised moulding of frieze')
    def motif(center,side):
        def panel(poly,depth,name):
            if side:b.prism(poly,-.003,depth,lambda y,z,d:(END+d,y,z),RELIEF,name)
            else:face(poly,-.003,depth,RELIEF,name)
        for z,width,height in [(1.518,.067,.016),(1.539,.088,.020),(1.567,.104,.017)]:
            panel(Polygon([(center-width*.52,z+height),(center+width*.52,z+height),(center+width*.35,z),(center-width*.35,z)]),.014,'Stacked relief strokes in lower frieze')
        panel(box(center-.048,1.70,center+.048,1.734),.026,'Rectangular bead beneath frieze band')
    for x in np.arange(-.91,END-.12,.236):motif(x,False)
    for y in np.arange(.14,DEPTH,.236):motif(y,True)
    for part in b.parts:
        if part['material']==PIER:part['texcoords']=[(.505+.48*min(1,max(0,(x+y+1.1)/2.51)),z/1.82) for x,y,z in part['vertices']]
        if part['material']==RENDER:part['texcoords']=[(.01+.47*min(1,max(0,(x+y+1.1)/2.51)),(z-1.35)/.45) for x,y,z in part['vertices']]
