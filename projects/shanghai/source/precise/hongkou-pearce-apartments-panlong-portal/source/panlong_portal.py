"""Street-side entrance of Pearce Apartments, after the photograph captioned Panlong Street 26."""
from math import cos, sin, pi
from pathlib import Path
import json
from shapely.affinity import scale, translate
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

STONE='pale grey cement'
BEAD='pale cast moulding'
FOOT='grey base render'
SHADOW='grey recessed moulding'
FRAME='oxblood painted timber'
PANEL='recessed wooden panel'
GLASS='dark reflected glass'
INK='red title enamel'
GREEN='green enamel address'
WHITE='ivory address figures'
PALETTE={m:dict(color=c,roughness=r) for m,c,r in (
    (STONE,[.53,.51,.455],.94),(BEAD,[.63,.60,.535],.87),(FOOT,[.28,.285,.265],.94),
    (SHADOW,[.33,.324,.285],.92),(FRAME,[.206,.076,.059],.72),(PANEL,[.155,.051,.045],.81),
    (GLASS,[.05,.055,.053],.24),(INK,[.324,.058,.043],.61),(GREEN,[.021,.180,.12],.52),(WHITE,[.87,.87,.73],.68))}
R=1.48
RISE=.70
SPRING=2.77
H=4.86
SIDE=.70

def face(b,poly,y0,y1,mat,name):
    if not poly.is_empty:
        b.prism(poly,-y1,-y0,lambda x,z,d:(x,-d,z),mat,name)

def block(b,x,z,w,h,front,back,material,name):
    face(b,box(x-w/2,z-h/2,x+w/2,z+h/2),front,back,material,name)

def arc(rx,rz,z,n):
    return [(rx*cos(pi*i/n),z+rz*sin(pi*i/n)) for i in range(n+1)]

def opening(rx,rz,base,n):
    return Polygon([(-rx,0),(rx,0),(rx,base),*arc(rx,rz,base,n)[1:]])

def outline(b,a,c,front,back,material,label,n):
    """A narrow curved bead with two vertical legs, continuous around the photographed opening."""
    geom=opening(R+c,RISE+c,SPRING,n).difference(opening(R+a,RISE+a,SPRING,n))
    face(b,geom,front,back,material,label)

def horizontal_profile(b,name,z,width,profile,mat):
    for i,(bottom,top,d,w) in enumerate(profile):
        block(b,0,z+(bottom+top)/2,width+2*w,top-bottom,-d,.10,mat,name+' course '+str(i+1))

def small_lights(b,cx,side):
    left=cx-SIDE/2;right=cx+SIDE/2
    face(b,box(left+.024,.93,right-.024,SPRING-.041),.169,.185,GLASS,side+' sidelight glazing')
    inner=box(left+.095,.137,right-.095,.815)
    face(b,box(left,0,right,.932).difference(inner),.075,.155,FRAME,side+' solid lower rail and stiles')
    face(b,inner,.098,.158,PANEL,side+' inset lower panel field')
    surround=box(left+.074,.113,right-.074,.838).difference(inner)
    face(b,surround,.034,.077,FRAME,side+' lower panel bead')
    for x in (left+.027,right-.028):
        block(b,x,(.932+SPRING)/2,.054,SPRING-.932,.058,.153,FRAME,side+' tall outside stile')
    for k in (-1,1):
        block(b,cx+k*.195,(.932+SPRING)/2,.022,SPRING-.932,.075,.158,FRAME,side+' narrow vertical glazing bars')
    for z in (1.019,SPRING-.159):
        block(b,cx,z,SIDE-.051,.026,.070,.157,FRAME,side+' transverse glazing bars')

def sign(b,lod):
    records=json.loads(Path(__file__).with_name('letter-contours.json').read_text())
    for item in records:
        g=shape(item['geometry'])
        if lod:g=g.simplify(.0012,preserve_topology=True)
        for poly in getattr(g,'geoms',[g]):
            if not isinstance(poly,Polygon):continue
            face(b,poly,item['front'],item['front']+.017,item['material'],item['group'])

def add_portal(b,lod=False):
    n=26 if lod else 64
    # A full-height cut through the entrance. The rear courtyard and the central passage remain open.
    wall=box(-1.98,0,1.98,4.58).difference(opening(R,RISE,SPRING,n))
    face(b,wall,.017,.412,STONE,'Street entrance render with open passage')
    for signx,side in ((-1,'Left'),(1,'Right')):
        foot=box(signx*1.74-.251,0,signx*1.74+.251,.429)
        face(b,foot,-.014,.416,FOOT,side+' grey plinth')
        small_lights(b,signx*(R-SIDE/2),side)
    outline(b,.004,.078,-.028,.055,STONE,'Inner curved cement reveal',n)
    outline(b,.078,.102,-.064,.01,BEAD,'Inner rounded moulding',n)
    outline(b,.119,.155,-.043,.04,BEAD,'Second stepped arch',n)
    outline(b,.165,.201,-.026,.038,BEAD,'Outer narrow arch fillet',n)
    face(b,Polygon(arc(R,RISE,SPRING,n)),.164,.18,GLASS,'Segmental dark transom glass')
    horizontal_profile(b,'Arch spring timber',SPRING,2*R,[(-.055,.047,-.051,0)],FRAME)
    for j,theta in enumerate((.115,.235,.365,.48,.59,.73,.865)):
        a=theta*pi
        path=[(r*R*cos(a),.093,SPRING+r*RISE*sin(a)) for r in (.247,.993)]
        b.tube(path,.014 if lod else .016,FRAME,6 if lod else 9,'Radial transom bars')
    for rr in (1.,.247):
        path=[(x,.079,z) for x,z in arc(R*rr,RISE*rr,SPRING,n)]
        b.tube(path,.022 if rr==1 else .017,FRAME,6 if lod else 10,'Arched timber fanlight and small hub')
    for t in (-.265,.27):
        b.tube([(0,.092,SPRING+.025),(t*.247*R,.092,SPRING+.165)],.010,FRAME,6,'Small fanlight hub spokes')
    # Slightly tapered central crown block above the fanlight.
    key=Polygon([(-.105,3.58),(.105,3.58),(.133,3.87),(-.133,3.87)])
    face(b,key,-.077,.017,BEAD,'Square projecting crown stone')
    horizontal_profile(b,'Lower moulded nameboard ledge',3.845,3.94,[(0,.037,.075,.018),(.037,.081,.052,0)],BEAD)
    block(b,0,4.132,3.87,.406,-.026,.093,STONE,'Nameboard face')
    for i in range(39):
        block(b,(i-19)*.101,4.398,.055,.079,-.124,.041,BEAD,'Dentils below nameboard cornice')
    horizontal_profile(b,'Dentilled cornice',4.432,3.97,[(0,.031,.115,.025),(.031,.061,.163,.059),(.061,.092,.19,.077),(.092,.152,.242,.102),(.152,.196,.235,.108),(.196,.233,.265,.124),(.233,.270,.289,.137)],BEAD)
    block(b,R-.282,2.33,.229,.177,.009,.051,GREEN,'Street number 26 enamel plate')
    sign(b,lod)
