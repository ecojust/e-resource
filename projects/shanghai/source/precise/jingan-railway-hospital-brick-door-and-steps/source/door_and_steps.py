"""Street-court doorway in the two-storey tiled brick range, orbital view by Fayhoo."""
from pathlib import Path
from PIL import Image,ImageDraw
from shapely.geometry import box,Polygon
from math import pi,sin,cos
import numpy as np
ID='jingan-railway-hospital-brick-door-and-steps'
BRICK='Red-brown facing brick'; GRANITE='Weathered grey plinth'; LEDGE='Pale lintel'; FRAME='Dark brown door metal'; GLASS='Muted translucent door glazing'; HANDLE='Warm metal pulls'; STEP='Brick step edging'; TILE='Terracotta landing'; VOID='Dark ventilation opening'; MEDAL='Warm red glass markings'
PALETTE={k:dict(color=c,roughness=r,metallic=m) for k,c,r,m in [(BRICK,[1,1,1],.91,0),(GRANITE,[.505,.484,.42],.91,0),(LEDGE,[.76,.715,.59],.83,0),(FRAME,[.203,.142,.12],.67,.2),(GLASS,[.447,.44,.382],.34,.13),(HANDLE,[.66,.59,.41],.38,.64),(STEP,[.47,.25,.155],.94,0),(TILE,[.67,.41,.275],.88,0),(VOID,[.092,.085,.07],1,0),(MEDAL,[.44,.185,.14],.7,.04)]}
def texture():
    loc=Path(__file__).with_name('stretcher-brick.png')
    if not loc.is_file():
        # Thirty-two individually shaded courses fill a single clamp-to-edge texture atlas.
        rng=np.random.default_rng(643);pix=np.zeros((320,480,3),dtype=float);pix[:]=[132,110,92]
        for j in range(32):
            shift=(j%2)*20
            for i in range(-1,13):
                a=i*40+shift;b=a+40;base=np.array([153,92,64])+rng.normal(0,[8,6,5]);x0=max(0,a+1);x1=min(480,b-2)
                if x1>x0:
                    n=rng.normal(0,4,(9,x1-x0,1))
                    pix[j*10+1:j*10+10,x0:x1]=base+n
        Image.fromarray(pix.clip(0,255).astype('uint8')).save(loc)
    PALETTE[BRICK]['texture']=str(loc)
def convert(x,z,depth):return x,-depth,z
def add_building(b,far=False):
    texture()
    def face(x0,x1,z0,z1,back,front,mat,name):b.prism(box(x0,z0,x1,z1),back,front,convert,mat,name)
    def bar(x0,x1,z0,z1,front,mat,name,deep=.035):face(x0,x1,z0,z1,front-deep,front,mat,name)
    # The visible bay is cropped between the two neighbouring windows.
    wall=box(-1.42,.36,1.42,2.85).difference(box(-.714,.25,.714,2.595))
    b.prism(wall,-.34,0,convert,BRICK,'Brick surround with a recessed rectangular doorway')
    for sign in (-1,1):
        xmin,xmax=(-1.42,-.714)if sign<0 else(.714,1.42)
        vent=sign*1.244
        stone=box(xmin,-.06,xmax,.36).difference(box(vent-.055,.02,vent+.055,.088))
        b.prism(stone,-.34,.008,convert,GRANITE,'Plinth with a small dark rectangular vent')
        face(vent-.062,vent+.062,.014,.094,-.24,-.20,VOID,'Dark inner plane of plinth opening')
    for k in range(3):
        width=.83+(2-k)*.151;front=.305+(2-k)*.212;top=.079+k*.114
        face(-width,width,top-.114,top,-.172,front,STEP,'Three receding brick risers')
        for i in range(-3,3):
            x0=max(-width,i*.335);x1=min(width,(i+1)*.335)
            if x1>x0+.006:face(x0+.002,x1-.002,top,top+.009,-.144,front-.016,TILE,'Landing tile and joint')
        if not far:
            for x in np.arange(-width+.042,width-.02,.085):
                bar(x-.0011,x+.0011,top-.108,top-.005,front+.0012,GRANITE,'Visible short vertical riser joint',.003)
    face(-.716,.716,.305,.34,-.205,.176,LEDGE,'Door threshold')
    # Fixed transom is divided in two; the lower pair of leaf frames is separate.
    for lo,hi in [(-.694,-.018),(.018,.694)]:
        face(lo,hi,.351,2.141,-.229,-.189,GLASS,'Glazed paired door leaf')
        face(lo,hi,2.212,2.556,-.229,-.189,GLASS,'Transom glazing')
        for z0,z1 in [(.347,.386),(.69,.731),(1.25,1.282),(2.122,2.197)]:
            bar(lo,hi,z0,z1,-.146,FRAME,'Horizontal steel edging and leaf rail')
    for x in(-.694,0,.694):
        bar(x-.021,x+.021,.344,2.582,-.146,FRAME,'Dark vertical door stile')
    for z in(.346,2.195,2.577):
        bar(-.713,.713,z-.018,z+.018,-.145,FRAME,'Outer rectangular frame')
    face(-.835,.835,2.609,2.687,-.13,.116,LEDGE,'Shallow stone drip lintel')
    face(-.80,.80,2.597,2.61,-.082,.099,GRANITE,'Setback beneath lintel')
    for x in(-.052,.052):
        for z in(1.055,1.416):b.tube([(x,.146,z),(x,.079,z)],.011,HANDLE,sides=6 if far else 12,label='Short mounts for the pull')
        b.tube([(x,.08,1.054),(x,.072,1.078),(x,.072,1.389),(x,.08,1.414)],.012,HANDLE,sides=6 if far else 12,label='Pair of legible vertical pulls')
    for x in(-.367,.367):
        pts=[(x+.075*cos(t),1.692+.075*sin(t))for t in np.linspace(0,2*pi,15 if far else 37,endpoint=False)]
        b.prism(Polygon(pts),-.19,-.187,convert,MEDAL,'A muted red circular mark, writing unresolved')
    for part in b.parts:
        if part['material']==BRICK:part['texcoords']=[[(x+1.42+.03*y)/2.85,(z-.36)/2.49] for x,y,z in part['vertices']]
