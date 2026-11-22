"""Garden front of 492 Middle Fuxing Road in the documented 2 August 2017 view."""
from math import cos,sin,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box
from shapely.ops import unary_union

ID='huangpu-fuxing-492-curved-window-bay'
WALL='Ivory stucco'; TRIM='Cream dressed plaster'; STONE='Weathered pale stone'
JOINT='Shadow below stringcourse'; GLASS='Garden glazing'; METAL='Dark window framing'
RAIL='Rounded cream baluster'; COLUMN='Pale attached column'; FLOOR='Shadowed reveal'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [
    (WALL,[1,1,1],.96),(TRIM,[.84,.81,.73],.91),(STONE,[.679,.652,.582],.95),
    (JOINT,[.512,.500,.451],.94),(GLASS,[.17,.235,.245],.41),
    (METAL,[.237,.253,.245],.71),(RAIL,[.749,.725,.656],.89),
    (COLUMN,[.820,.80,.720],.94),(FLOOR,[.31,.315,.281],.96)]}
SIDES=[((-2.48,.32),(-.91,-.27)),((-.91,-.27),(.91,-.27)),((.91,-.27),(2.48,.32))]
def texture():
    p=Path(__file__).with_name('plaster.png')
    if not p.exists():
        rng=np.random.default_rng(575)
        rough=Image.fromarray(rng.integers(0,255,(55,46),dtype='u1')).resize((468,501),Image.Resampling.BICUBIC)
        delta=(np.asarray(rough,float)-127)*.051+rng.normal(0,1.65,(501,468))
        Image.fromarray(np.clip([211,207,192]+delta[:,:,None],0,255).astype('u1')).quantize(96).save(p)
    PALETTE[WALL]['texture']=str(p)
def frame(a,e):
    a=np.asarray(a);span=np.asarray(e)-a;length=np.linalg.norm(span);u=span/length;n=np.array([u[1],-u[0]])
    def pos(x,z,d):
        px,py=a+x*u+d*n;return px,py,z
    return length,pos
def lathe(b,x,y,z,profile,sides,mat,label):
    vertices=[(x+rad*cos(2*pi*i/sides),y+rad*sin(2*pi*i/sides),z+h) for h,rad in profile for i in range(sides)]
    faces=[]
    for layer in range(len(profile)-1):
        for i in range(sides):
            j=(i+1)%sides; a=layer*sides+i; f=layer*sides+j
            faces.append((a,f,f+sides,a+sides))
    faces.extend([tuple(reversed(range(sides))),tuple((len(profile)-1)*sides+i for i in range(sides))])
    b.add(vertices,faces,mat,label)
def add_building(b,far=False):
    texture()
    for side,(a,e)in enumerate(SIDES):
        span,point=frame(a,e);mid=span/2
        def part(u0,u1,z0,z1,back,front,mat,label):
            b.prism(box(u0,z0,u1,z1),back,front,point,mat,label)
        window=.96 if side!=1 else 1.27
        lo,hi=mid-window/2,mid+window/2
        openings=[box(lo,.52,hi,1.18),box(lo,1.39,hi,3.34)]
        shape=box(0,0,span,4.26).difference(unary_union(openings))
        b.prism(shape,-.36,0,point,WALL,'Three joined garden-facing bays with real openings')
        part(lo,hi,1.39,3.34,-.251,-.243,GLASS,'Garden window glass behind frame')
        part(lo,hi,.51,1.18,-.36,-.352,FLOOR,'Recess seen between the balusters')
        for u in (lo+.017,hi-.017,mid):
            part(u-.017,u+.017,1.39,3.34,-.249,-.157,METAL,'Narrow window stile')
        for z in (1.411,2.831,3.314):
            part(lo,hi,z-.018,z+.018,-.25,-.151,METAL,'Horizontal sash rail')
        part(lo-.052,hi+.052,1.18,1.293,-.038,.097,TRIM,'Balustrade coping below each window')
        part(lo-.063,hi+.063,.444,.528,-.03,.096,STONE,'Recessed base sill of balustrade')
        count=5 if side==1 else 3
        for u in np.linspace(lo+.104,hi-.104,count):
            x,y,_=point(u,0,.005)
            silhouette=[(0,.059),(.049,.07),(.093,.045),(.18,.039),(.265,.068),(.326,.077),(.378,.075),(.45,.056),(.53,.035),(.609,.039),(.650,.06)]
            lathe(b,x,y,.526,silhouette,10 if far else 22,RAIL,'Turned bottle-shaped baluster')
        for z,thick,depth,mat in [(.17,.055,.07,JOINT),(.226,.087,.126,TRIM),(3.806,.062,.087,JOINT),(3.867,.098,.132,TRIM),(4.046,.102,.19,TRIM),(4.150,.105,.215,STONE)]:
            part(-.005,span+.005,z,z+thick,-.096,depth,mat,'Stepped band following the three faces')
        for u in np.arange(.091,span-.034,.147):
            part(u-.035,u+.035,3.972,4.045,.061,.147,TRIM,'Short projecting dentil')
    for x in (-.91,.91):
        y=-.44
        b.box((x,y,.39),(.48,.46,.27),STONE,label='Square plinth at front of angled bay')
        lathe(b,x,y,.526,[(0,.231),(.062,.242),(.105,.197),(.168,.18),(.22,.16),(3.075,.144),(3.14,.17),(3.19,.196),(3.225,.196)],14 if far else 36,COLUMN,'Tapering round column with ring necking')
        b.box((x,y,3.795),(.442,.397,.097),TRIM,label='Square abacus below cornice')
        if not far:
            for off in (-.133,.133):
                th=np.linspace(.28,1.75*pi,15)
                pts=[(x+off+.040*cos(t),y-.158,3.718+.031*sin(t)) for t in th]
                b.tube(pts,.012,TRIM,sides=7,label='Small scroll on capital face')
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+2.5)/5.0,z/4.3]for x,y,z in part['vertices']]
