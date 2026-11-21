"""Three photographed adjoining faces of the octagonal bell tower at 349 Hangzhou Road."""
from math import cos,pi,sin,sqrt,tan
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade

RGB={'weathered grey render':(137,132,120),'recessed render':(100,98,88),'pale reveal':(154,146,129),
     'upper column stone':(152,144,128),'column joint':(132,124,108),'louvre upper face':(111,105,88),
     'louvre lower face':(69,69,61),'shaded belfry':(45,46,42)}
def linear(c):
    s=c/255
    return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
PALETTE={k:{'color':[linear(x)for x in c],'roughness':.88}for k,c in RGB.items()}
APOTHEM=2.10
HALF=APOTHEM*tan(pi/8)
R=.422
LOW=(.24,2.20)
UP=(2.61,4.29)
TOP=4.99

def curve(rx,rz,z,n):
    return [(rx*cos(pi*i/n),z+rz*sin(pi*i/n))for i in range(n+1)]
def fan(r,base,spring,n):
    return Polygon([(-r,base),(r,base)]+curve(r,r,spring,n))
def frame(angle):
    a=angle*pi/180
    normal=np.array([sin(a),-cos(a)]);tangent=np.array([cos(a),sin(a)])
    center=np.array([0,APOTHEM])+normal*APOTHEM
    return center,tangent
def make_blade(b,f,width,z,label):
    # The leading arris is lower than the back: each blade has real upper/underside polygons.
    vertices=[f.point(x,z+dz,d).tolist() for x in (-width/2,width/2) for d,dz in [(-.055,0),(-.055,.035),(-.242,.108),(-.242,.073)]]
    b.add(vertices,[(0,1,5,4),(1,2,6,5),(0,3,2,1),(4,5,6,7)],'louvre upper face',label+' upper arris')
    b.add(vertices,[(0,4,7,3),(3,7,6,2)],'louvre lower face',label+' underside')
def add_building(builder,lod=False):
    n=16 if lod else 40;corners={}
    for k,a in enumerate((-45,0,45)):
        center,t=frame(a);left=center-HALF*t;right=center+HALF*t
        f=Facade(builder,left,right,('Left','Centre','Right')[k]+' face')
        lower=box(-R,LOW[0],R,LOW[1]);upper=fan(R,UP[0],UP[1],n)
        arcade=fan(.726,.015,4.28,n)
        # A larger blind arch frames a recessed wall containing two separate openings.
        front=box(-HALF,.015,HALF,TOP).difference(arcade)
        f.prism(front,-.23,0,'weathered grey render','blind arch surround')
        f.prism(arcade.difference(unary_union([lower,upper])),-.235,-.062,'recessed render','inner arch field')
        for slot,name in [(lower,'lower'),(upper,'upper')]:
            surround=slot.buffer(.034,join_style=2).difference(slot)
            f.prism(surround,-.27,-.075,'pale reveal',name+' reveal')
            f.prism(slot,-.335,-.325,'shaded belfry',name+' recess back')
        # The lower window has a narrow threshold. The upper window has a curved projecting apron.
        f.prism(box(-R-.085,LOW[0]-.055,R+.085,LOW[0]+.01),-.20,.025,'pale reveal','lower sill')
        z=UP[0]-.012
        lower_edge=[(R*(1-2*i/n),z-.148*(1-((1-2*i/n)**2)))for i in range(n+1)]
        f.prism(Polygon([(-R,z+.018),(R,z+.018)]+lower_edge),-.18,-.035,'pale reveal','upper sill apron')
        for j in range(10):
            zz=LOW[0]+.11+j*.181
            make_blade(builder,f,2*R-.024,zz,f.label+' lower blade '+str(j+1))
            zz=UP[0]+.13+j*.202
            width=2*sqrt(max(0,R*R-max(0,zz+.108-UP[1])**2))-.024
            make_blade(builder,f,width,zz,f.label+' upper blade '+str(j+1))
        for pt in [left,right]:corners[tuple(np.round(pt,5))]=pt
    for i,xy in enumerate(corners.values()):
        stages=[(.015,.075),(.075,.089),(.113,.082),(.153,.068),(4.08,.064),(4.115,.089),(4.164,.107),(4.189,.096),(4.221,.133),(4.267,.135),(4.290,.105)]
        if lod:stages=[stages[j] for j in [0,1,3,4,6,8,9,10]]
        builder.lathe(xy,stages,'upper column stone',12 if lod else 28,'angle shaft and capital '+str(i+1))
