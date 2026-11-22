"""No. 1, Shanghai Jingju Training Hall. Door head and dry-dash pebble finish."""
from pathlib import Path
import math
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import box,Point
ID='xuhui-yueyang-168-jingju-pebble-dash-doorhead'
DASH='Dry-dash pebble wall';STONE='Cool grey rendered door dressings';PROFILE='Pale stepped mouldings';JOINT='Stone-coloured bed joints';SHADOW='Sheltered doorhead soffit';DOOR='Recess beyond the door head';BOSS='Round shallow relief discs'
GRAINS=['Warm sandstone pebble','Brown river pebble','Cool grey pebble','Pale quartz pebble','Dark rounded pebble']
COLOURS=[[.64,.52,.40],[.45,.379,.331],[.53,.58,.61],[.78,.78,.71],[.332,.348,.375]]
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(DASH,[1,1,1],.98),(STONE,[.638,.666,.659],.93),(PROFILE,[.727,.745,.735],.9),(JOINT,[.453,.483,.476],.94),(SHADOW,[.456,.465,.444],.93),(DOOR,[.21,.165,.154],.87),(BOSS,[.726,.739,.72],.84)]}
PALETTE.update({k:dict(color=c,roughness=.91) for k,c in zip(GRAINS,COLOURS)})
def texture():
    path=Path(__file__).with_name('mixed-pebble-dash.png')
    if not path.exists() or Image.open(path).size!=(1360,1190):
        rng=np.random.default_rng(775)
        im=Image.new('RGB',(416,416),(143,139,126));d=ImageDraw.Draw(im)
        for _ in range(7100):
            x,y=rng.integers(0,416,2);rx=rng.uniform(.9,3.75);ry=rx*rng.uniform(.49,.92)
            j=rng.choice(5,p=[.16,.21,.31,.16,.16])
            c=np.array(COLOURS[j])*255+rng.normal(0,11);c=np.clip(c,35,230).astype(int)
            for dx in ((0,416) if x<4 else (0,-416) if x>411 else (0,)):
                for dy in ((0,416) if y<4 else (0,-416) if y>411 else (0,)):
                    xx=x+dx;yy=y+dy
                    d.ellipse((xx-rx,yy-ry,xx+rx,yy+ry),fill=tuple(c))
                    if rx>2:d.line((xx-rx*.45,yy-ry*.53,xx+rx*.46,yy-ry*.53),fill=tuple(np.clip(c+13,0,255)))
        tile=im.resize((170,170),Image.Resampling.LANCZOS)
        atlas=Image.new('RGB',(170*8,170*7))
        for iy in range(7):
            for ix in range(8):atlas.paste(tile,(ix*170,iy*170))
        atlas.quantize(132).save(path)
    PALETTE[DASH]['texture']=str(path)
def relief_grains():
    rng=np.random.default_rng(751775)
    for row in range(47):
        for col in range(14):
            x=.234+(col+rng.random()*.73)*.036
            z=.018+(row+rng.random()*.79)*.031
            yield (row,col,x,z,rng.uniform(.0031,.0089),rng.uniform(.0025,.0058),rng.uniform(.0016,.0048),int(rng.integers(5)))
def add_building(b,far=False):
    texture()
    def panel(poly,lo,hi,m,name):b.prism(poly,lo,hi,lambda x,z,d:(x,-d,z),m,name)
    def rect(x,r,z,t,lo,hi,m,name):panel(box(x,z,r,t),lo,hi,m,name)
    opening=box(-.859,-.015,-.287,.571)
    panel(box(-.861,0,.752,1.49).difference(opening),-.156,0,DASH,'Dry-dash wall beside the doorway')
    rect(-.859,-.287,0,.59,-.228,-.216,DOOR,'Recess above the entrance leaf')
    rect(-.859,-.286,.216,.332,-.194,-.172,SHADOW,'Return inside door')
    rect(-.307,-.252,0,.578,-.209,.067,SHADOW,'Deep right-hand reveal')
    rect(-.284,.174,0,.956,.0005,.094,STONE,'Pale return of the door surround')
    rect(-.28,-.002,0,.949,.086,.137,STONE,'Shallow pilaster at the doorway')
    for j in [.318,.607,.902]:
        rect(-.281,-.002,j,j+.005,.137,.139,JOINT,'Horizontal joints across pilaster face')
        rect(.003,.175,j+.004,j+.008,.094,.095,JOINT,'Set-back joint across adjacent return')
    rect(-.861,-.275,.567,.783,-.097,.075,STONE,'Flat frieze inside the opening')
    for height,depth,thick in [(.574,.132,.014),(.601,.108,.015),(.789,.135,.022),(.814,.142,.016)]:
        rect(-.86,-.223,height,height+thick,.061,depth,PROFILE,'Parallel projecting bands enclosing the pair of bosses')
    for x in [-.710,-.380]:
        panel(Point(x,.688).buffer(.051,resolution=9 if far else 24),.074,.103,BOSS,'Independent circular ornament on the frieze')
    layers=[(.917,.947,.205),(.947,.961,.239),(.961,.986,.221),(.986,1.014,.201),(1.014,1.035,.215),(1.035,1.064,.255)]
    for z,top,depth in layers:
        rect(-.86,.197,z,top,.040,depth,PROFILE,'Successive steps above the pilaster capital')
    rect(-.86,.163,1.061,1.218,.043,.175,STONE,'Plain fascia above the centre mouldings')
    for z,t,right,dep in [(1.213,1.244,.213,.208),(1.244,1.268,.248,.245),(1.268,1.294,.266,.273),(1.294,1.324,.299,.307),(1.324,1.346,.310,.323),(1.346,1.372,.319,.330),(1.372,1.393,.327,.339)]:
        rect(-.86,right,z,t,-.010,dep,PROFILE,'Stepped crown and corner return')
    # A sparse raised layer supplements the much denser original material tile.
    batches={k:([],[]) for k in GRAINS}
    for row,col,x,z,rx,rz,height,j in relief_grains():
        if (.92<z<1.064 and x<.23) or (1.214<z<1.395 and x<.34):continue
        if far and (row+3*col)%3:continue
        v,f=batches[GRAINS[j]];base=len(v);n=5 if far else 9
        for i in range(n):
            t=2*math.pi*i/n;v.append((x+rx*math.cos(t),-.0004,z+rz*math.sin(t)))
        v.append((x+rx*.12,-height,z+rz*.14))
        f.extend((base+i,base+(i+1)%n,base+n)for i in range(n))
    for mat,(v,f) in batches.items():b.add(v,f,mat,'Raised grains of the '+mat)
    for part in b.parts:
        if part['material']==DASH:part['texcoords']=[[(x+.862)/(8*.224),z/(7*.224)]for x,y,z in part['vertices']]
