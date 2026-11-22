"""Two unequal round-headed windows of the residential frontage at 17 Yongjia Road."""
from math import sin,cos,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box,LineString
from shapely.ops import unary_union
ID='huangpu-yongjia-17-round-headed-window'
WALL='Light garden stucco';STONE='Pale outer arch';LIP='Sunlit arch step';DARK='Deep moulding shadow';JAMB='Weathered jamb face';BAR='Pale vertical glazing bar';GLASS='Dark garden glass';GLASS2='Reflected green in fanlight';SOLE='Pale stone sill';JOINT='Fine jamb shadow'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(WALL,[1,1,1],.97),(STONE,[.747,.730,.655],.91),(LIP,[.852,.832,.746],.87),(DARK,[.463,.445,.396],.95),(JAMB,[.694,.675,.592],.95),(BAR,[.673,.680,.614],.71),(GLASS,[.133,.169,.143],.36),(GLASS2,[.183,.226,.189],.38),(SOLE,[.638,.627,.566],.94),(JOINT,[.444,.436,.384],.94)]}
def texture():
    p=Path(__file__).with_name('plaster.png')
    if not p.exists():
        rng=np.random.default_rng(559);v=np.asarray(Image.fromarray(rng.integers(0,255,(59,54),dtype='u1')).resize((511,472),Image.Resampling.BICUBIC),float)
        a=(v-128)*.069+rng.normal(0,2.1,v.shape);Image.fromarray(np.clip([197,194,172]+a[:,:,None],0,255).astype('u1')).quantize(128).save(p)
    PALETTE[WALL]['texture']=str(p)
def panel(b,p,back,front,mat,name):b.prism(p,back,front,lambda x,z,d:(x,-d,z),mat,name)
def rect(b,x0,x1,z0,z1,back,front,m,n):panel(b,box(x0,z0,x1,z1),back,front,m,n)
def opening(c,r,spring,bottom,far):
    arc=[(c+r*cos(t),spring+r*sin(t))for t in np.linspace(0,pi,19 if far else 52)]
    return Polygon([(c-r,bottom),(c+r,bottom)]+arc)
def arch(b,c,r,z,thick,back,front,m,lod,desc):
    a=np.linspace(0,pi,19 if lod else 52)
    shell=Polygon([(c+(r+thick)*cos(t),z+(r+thick)*sin(t))for t in a]+[(c+r*cos(t),z+r*sin(t))for t in a[::-1]])
    panel(b,shell,back,front,m,desc)
CASES=[(-.492,1.00,2.623,.166),(1.532,.392,2.324,.852)]
def add_building(b,far=False):
    texture();holes=[opening(*v,far)for v in CASES];panel(b,box(-2.19,0,2.18,4.35).difference(unary_union(holes)),-.311,0,WALL,'Light finished wall behind the two unequal windows')
    for index,(c,r,sp,lo)in enumerate(CASES):
        small=.62 if index else 1.;glass=opening(c,r-.009,sp,lo+.013,far)
        panel(b,glass,-.224,-.210,GLASS,'Deep dark window glass and interior shadow')
        panel(b,glass.intersection(box(c-1.1,sp+.021,c+1.1,4.14)),-.210,-.204,GLASS2,'Darker fanlight set above the straight transom')
        for offset,thickness,depth,mat in [(.005,.063,.047,DARK),(.067,.054,.111,LIP),(.120,.083,.092,STONE),(.198,.039,.151,LIP)]:
            arch(b,c,r+offset*small,sp,thickness*small,-.015,depth*small,mat,far,'Concentric curve of the moulded archivolt')
        for side in (-1,1):
            x=c+side*(r+.077*small)
            rect(b,x-.066*small,x+.066*small,lo,sp-.051*small,-.023,.041*small,JAMB,'Straight jamb carried to spring line')
            rect(b,x-.109*small,x+.109*small,sp-.1*small,sp-.065*small,-.018,.150*small,DARK,'Shadow beneath springer cap')
            rect(b,x-.129*small,x+.129*small,sp-.066*small,sp-.010*small,-.019,.162*small,LIP,'Short horizontal impost over projecting jamb')
            if not far:
                rect(b,x-.089*small,x+.089*small,sp-.156*small,sp-.145*small,.038*small,.047*small,JOINT,'Slim joint in lower impost')
        rect(b,c-r,c+r,sp-.059*small,sp+.004*small,-.211,-.142,BAR,'Straight transom below semi-circular fanlight')
        if not index:rect(b,c-.027,c+.027,lo,sp-.054,-.219,-.145,BAR,'One vertical bar in the lower two-leaf window')
        rect(b,c-r-.101*small,c+r+.103*small,lo-.073*small,lo+.015*small,-.131,.107*small,SOLE,'Projecting bottom sill')
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+2.21)/4.42,z/4.36]for x,y,z in part['vertices']]
