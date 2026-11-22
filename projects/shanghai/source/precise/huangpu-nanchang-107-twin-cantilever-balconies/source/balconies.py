"""Two projecting balconies on the chamfered residential elevation in Fayhoo's 2014 photo."""
from math import pi,cos,sin
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

ID='huangpu-nanchang-107-twin-cantilever-balconies'
BRICK='Deep plum brown running-bond brick';STONE='Warm grey balcony stone';EDGE='Pale nosing and course';SHADE='Shaded underside'
FRAME='Weathered dark green joinery';GLASS='Window glass in shade';LIGHT='Window glass reflecting the sky'
IRON='Dark iron balustrade';CAP='Weathered top rail';REVEAL='Dark jamb reveal'
PALETTE={m:dict(color=c,roughness=r) for m,c,r in [
 (BRICK,[1,1,1],.94),(STONE,[.58,.55,.48],.91),(EDGE,[.73,.70,.62],.9),(SHADE,[.46,.43,.38],.94),
 (FRAME,[.19,.205,.157],.85),(GLASS,[.155,.19,.186],.34),(LIGHT,[.27,.34,.33],.31),(IRON,[.105,.115,.115],.7),(CAP,[.225,.235,.226],.66),(REVEAL,[.20,.185,.165],.9)]}
CENTERS=(-1.71,1.71)
FRONT=lambda x,z,depth:(x,-depth,z)
TOP=3.87
def texture():
    p=Path(__file__).with_name('dark-facing-brick.png')
    if not p.exists():
        rng=np.random.default_rng(507);height,width=432,736;yy,xx=np.indices((height,width));r=yy//8;offset=13*(r%2)
        col=(xx+offset)//26
        grain=rng.normal(0,2.9,(height,width));shift=rng.normal(0,10,(56,31))[r,col];violet=rng.normal(0,4,(56,31))[r,col]
        field=np.array([79,65,61],float)[None,None,:]+(shift+grain)[:,:,None]
        field[:,:,2]+=violet;field[:,:,0]-=violet*.35
        mask=(yy%8==0)|((xx+offset)%26==0)
        field[mask]=np.array([123,119,108])+grain[mask,None]*.9
        Image.fromarray(np.clip(field,0,255).astype('u1')).quantize(160).save(p)
    PALETTE[BRICK]['texture']=str(p)
def slab(b,shape,front,back,material,label):
    b.prism(shape,back,front,FRONT,material,label)
def rect(b,l,r,z0,z1,d,back,mat,label):
    slab(b,box(l,z0,r,z1),d,back,mat,label)
def plan(center,w,depth,radius,segments):
    """The outer long edge is straight with quarter-round ends returning to each jamb."""
    coords=[(center-w,0.),(center+w,0.),(center+w,-depth+radius)]
    for a in np.linspace(0.,-pi/2,segments+1):
        coords.append((center+w-radius+radius*cos(a),-depth+radius+radius*sin(a)))
    for a in np.linspace(-pi/2,-pi,segments+1):
        coords.append((center-w+radius+radius*cos(a),-depth+radius+radius*sin(a)))
    return Polygon(coords)
def shelf(b,c,far):
    levels=[(.368,.421,.935,.754,.145,SHADE),(.421,.492,.977,.797,.160,STONE),(.492,.531,.994,.806,.168,EDGE),(.531,.568,.971,.787,.155,STONE)]
    for z0,z1,w,d,r,m in levels:
        path=plan(c,w,d,r,5 if far else 12)
        b.prism(path,z0,z1,lambda x,y,z:(x,y,z),m,'Balcony slab with two softened front corners')
    section=Polygon([(0.,.08),(.12,.08),(.33,.158),(.535,.260),(.594,.367),(0.,.367)])
    for dx in (-.385,.385):
        b.prism(section,-(c+dx)-.089,-(c+dx)+.089,lambda d,z,s:(-s,-d,z),STONE,'Two tapered corbels under each slab')
def rails(b,c,far):
    # The photo shows fine vertical rods, two heavier corner posts and a double horizontal top.
    # Profile and number of narrow rods are estimates.
    n=5 if far else 8
    trace=[(c-.833,-.055),(c-.833,-.600)]
    for a in np.linspace(pi,1.5*pi,7 if far else 13)[1:]:
        trace.append((c-.714+.119*cos(a),-.600+.119*sin(a)))
    trace.append((c+.714,-.719))
    for a in np.linspace(-pi/2,0.,7 if far else 13)[1:]:
        trace.append((c+.714+.119*cos(a),-.600+.119*sin(a)))
    trace.append((c+.833,-.055))
    for z,rad,mat in [(1.574,.021,CAP),(1.476,.013,IRON),(.652,.016,IRON)]:
        b.tube([(x,y,z)for x,y in trace],rad,mat,n,'Continuous guard rail around the rounded returns')
    for x in np.linspace(-.712,.712,17):
        b.tube([(c+x,-.719,.633),(c+x,-.719,1.553)],.0105,IRON,n,'Slim vertical iron rod across balcony front')
    for sign in (-1,1):
        for y in (-.11,-.247,-.382,-.521,-.615):
            b.tube([(c+sign*.833,y,.633),(c+sign*.833,y,1.553)],.0105,IRON,n,'Return of iron railing to wall')
        for x,y in ((.715,.719),(.833,.102)):
            b.tube([(c+sign*x,-y,.526),(c+sign*x,-y,1.576)],.022,IRON,n,'Anchored guard post')
def door(b,c):
    # Transom over two glazed casements/doors; lower detail behind the guard is indistinct.
    rect(b,c-.632,c+.632,.52,2.78,-.16,-.195,REVEAL,'Back of door recess')
    for i in range(2):
        for j,(z0,z1) in enumerate([(.58,1.54),(1.54,2.21),(2.21,2.68)]):
            l=c-.536+i*.536;r=l+.536
            rect(b,l+.023,r-.023,z0+.028,z1-.026,-.136,-.164,LIGHT if (i+j)%3==1 else GLASS,'Recessed glazed panel')
    for x in (-.559,0.,.559):
        rect(b,c+x-.024,c+x+.024,.533,2.721,-.087,-.158,FRAME,'Two-leaf frame')
    for z in (.56,1.54,2.21,2.704):
        rect(b,c-.583,c+.583,z-.024,z+.024,-.083,-.159,FRAME,'Door sash rail or transom')
    for off in (-.626,.626):rect(b,c+off-.027,c+off+.027,.53,2.826,.028,-.188,STONE,'Narrow reveal of door')
    rect(b,c-.658,c+.658,2.788,2.836,.035,-.188,EDGE,'Narrow light lintel across balcony opening')
    rect(b,c-.63,c+.63,2.73,2.784,-.018,-.16,FRAME,'Dark upper face of lintel')
def add_building(b,far=False):
    texture()
    front=box(-3.17,0.,3.17,TOP);holes=unary_union([box(c-.602,.522,c+.602,2.79) for c in CENTERS])
    slab(b,front.difference(holes),0.,-.22,BRICK,'Two openings in the dark brick wall of the clipped corner')
    for sign in (-1,1):
        a=pi/4
        def wing(u,z,d):return (sign*3.17+u*cos(a)+sign*d*sin(a),sign*u*sin(a)-d*cos(a),z)
        b.prism(box(min(0,sign*.45),0.,max(0,sign*.45),TOP),-.22,0.,wing,BRICK,'Short return of the chamfer to the street elevation')
    for lo,hi,d,mat in [(3.35,3.39,.069,SHADE),(3.39,3.435,.112,STONE),(3.435,3.523,.145,EDGE),(3.523,3.554,.122,STONE)]:
        rect(b,-3.17-.414*d,3.17+.414*d,lo,hi,d,-.22,mat,'Continuous light course over the pair of balcony openings')
        for sign in (-1,1):
            def wing(u,z,d):return (sign*3.17+u*.707107+sign*d*.707107,sign*u*.707107-d*.707107,z)
            b.prism(box(min(-sign*.414*d,sign*.45),lo,max(-sign*.414*d,sign*.45),hi),-.22,d,wing,mat,'Stone course returns at the corner')
    for c in CENTERS:door(b,c);shelf(b,c,far);rails(b,c,far)
    for part in b.parts:
        if part['material']==BRICK:
            part['texcoords']=[[(x+.28*y+3.62)/7.24,.017+z/4.06]for x,y,z in part['vertices']]
