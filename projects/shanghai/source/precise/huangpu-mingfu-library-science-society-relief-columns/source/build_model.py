"""Model the two decorated hall piers of the former Science Society of China."""
from pathlib import Path
import argparse,os
from math import cos,pi,sin
import sys
from shapely.geometry import Polygon
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
import package_architectural_model as package
sys.path.insert(0,str(SOURCE.parents[1]/'huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
package.Builder=AggregateBuilder
from photo_architecture import Facade
from shaft_stone import shaft,SHAFT
from medallion import relief,BRASS,LIGHT,BLUE,AGED,PANEL
ID='huangpu-mingfu-library-science-society-relief-columns'
META={'id':ID,'name':'明复图书馆明复楼门厅中国科学社社徽双柱','viewer_page':'mingfu-library-science-society-relief-columns.html',
      'scope':'明复楼门厅正对入口的两个方柱、社徽板、扭绳角饰、线脚、相应梁头与后壁。切至2018年正面照可见范围。展柜、电子屏和导视牌为非固定陈设。',
      'status':'photographed-interior-architectural-fragment','heritage_group':'4C022','heritage_address':'陕西南路235号',
      'photographic_assumptions':'柱身宽假定0.64米，其余尺度从两张照片比量。蓝色、黄铜色和白色按两种光照取近似色。两柱相向侧的社徽重复关系按单柱角部近照推定。',
      'coordinate_convention':'Local metres. +Z is up from the cropped lower shaft edge and +Y is away from the lobby camera. The photo does not show the feet of the columns.',
      'reference_dates':'明复图书馆1929年11月奠基，1931年1月1日开放。'}
WALL='Soft white plaster';EDGE='Lime white mouldings';RECESS='Shadow in plaster';SKIRT='Dark timber wall trim';CUT='Neutral section finish'
def swatch(rgb,roughness,metallic=0):
 def linear(c):
  q=c/255
  return q/12.92 if q<=.04045 else ((q+.055)/1.055)**2.4
 return dict(color=[linear(c)for c in rgb],roughness=roughness,metallic=metallic)
PALETTE={BRASS:swatch((183,150,86),.53,.38),LIGHT:swatch((221,192,122),.39,.43),BLUE:swatch((57,75,88),.59,.20),AGED:swatch((112,98,69),.64,.31),
         SHAFT:dict(color=[1.,1.,1.],roughness=.68,texture=str(SOURCE/'hall-stone.png')),WALL:swatch((225,222,206),.88),EDGE:swatch((233,229,211),.82),
         RECESS:swatch((191,188,171),.85),SKIRT:swatch((77,67,55),.78),CUT:swatch((172,169,155),.9)}
SPACING=2.08
WIDTH=.64
ZMEDAL=3.13
R=WIDTH/2
LO=ZMEDAL-PANEL/2
HI=ZMEDAL+PANEL/2
REAR=.54


def tapered_square(b,cx,levels,mat,name):
    verts=[]
    for z,half in levels:
        for x,y in [(-half,-half),(half,-half),(half,half),(-half,half)]:verts.append((cx+x,y,z))
    faces=[(3,2,1,0)]
    for level in range(len(levels)-1):
        for k in range(4):
            i=level*4+k;j=level*4+(k+1)%4
            faces.append((i,j,j+4,i+4))
    faces.append(tuple(range(len(verts)-4,len(verts))))
    b.add(verts,faces,mat,name)


def twist(b,x,y,lod,name):
    slices=44 if lod else 116
    sides=10 if lod else 24
    pts=[]
    for j in range(slices+1):
        t=j/slices
        for k in range(sides):
            theta=2*pi*k/sides
            r=.040+.006*cos(3*theta-2*pi*9*t)+.0018*cos(6*theta-4*pi*9*t)
            pts.append((x+r*cos(theta),y+r*sin(theta),LO+t*PANEL))
    faces=[tuple(reversed(range(sides)))]
    for j in range(slices):
        for k in range(sides):
            a=j*sides+k;c=j*sides+(k+1)%sides
            faces.append((a,c,c+sides,a+sides))
    faces.append(tuple(range(len(pts)-sides,len(pts))))
    b.add(pts,faces,BRASS,name+' twisting corner mould')


def hall_pier(b,cx,sign,lod):
    name='Left pier' if sign<0 else 'Right pier'
    shaft(b,cx,R,LO,name)
    tapered_square(b,cx,[(LO-.049,R),(LO-.040,R+.037),(LO-.019,R+.037),(LO-.015,R+.060),(LO,R+.060)],LIGHT,name+' lower metal ledge')
    b.box((cx,0,ZMEDAL),(WIDTH,WIDTH,PANEL),AGED,label=name+' relief block')
    relief(Facade(b,(cx-R,-R),(cx+R,-R),name+' front'),ZMEDAL,lod)
    x=cx-sign*R
    # These two inner faces are the exposed returns into the gap between the piers.
    relief(Facade(b,(x,sign*R),(x,-sign*R),name+' return'),ZMEDAL,lod)
    for x in (-1,1):
        for y in (-1,1):twist(b,cx+x*(R-.037),y*(R-.037),lod,name)
    tapered_square(b,cx,[(HI,R+.046),(HI+.016,R+.055),(HI+.046,R+.054),(HI+.054,R+.043)],BRASS,name+' top metal fillet')
    tapered_square(b,cx,[(HI+.054,R+.042),(HI+.065,R+.079),(HI+.089,R+.086),(HI+.104,R+.086),
                          (HI+.155,R+.068),(HI+.165,R+.105),(HI+.205,R+.106),
                          (HI+.214,R+.127),(HI+.237,R+.131),(HI+.251,R+.114)],EDGE,name+' stepped plaster capital')
    b.box((cx,.045,HI+.315),(WIDTH+.086,WIDTH+.09,.130),WALL,label=name+' square neck above cornice')
    b.box((cx,.20,HI+.425),(.52,1.16,.13),WALL,label=name+' ceiling beam end')


def add_building(b,lod):
    for side in (-1,1):hall_pier(b,side*SPACING/2,side,lod)
    b.box((0,REAR+.054,1.915),(4.44,.108,3.83),WALL,label='Lobby wall behind both piers')
    b.box((0,REAR-.006,.785),(4.44,.051,.105),SKIRT,label='Wall dado dark horizontal band')
    b.box((0,REAR-.022,.849),(4.44,.057,.034),AGED,label='Wall dado upper bead')
    for i in range(105 if not lod else 61):
        step=4.44/(105 if not lod else 61)
        b.box((-2.22+(i+.5)*step,REAR-.041,.787),(.017,.022,.070),AGED,label='Short brass dado flutes')
    b.box((0,REAR-.035,3.75),(4.44,.15,.079),EDGE,label='Shallow band below lintel')
    b.box((0,REAR-.046,3.81),(4.44,.18,.045),EDGE,label='Upper projecting plaster band')
    # Avoid a fabricated floor level. The document camera ends midway down the shafts.
    for x in (-2.22,2.22):
        b.box((x,REAR+.054,1.915),(.009,.108,3.83),CUT,label='Cropped edges of photographed wall')


if __name__=='__main__':
    cli=argparse.ArgumentParser(add_help=False)
    cli.add_argument('--blender',default='blender')
    options,rest=cli.parse_known_args()
    os.environ['MINGFU_HALL_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'native_blender.py')]
    package.build(SOURCE,META,PALETTE,add_building)
