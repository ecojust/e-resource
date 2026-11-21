"""The returned wall next to the green No. 8 address plate on the 2015 lane photograph."""
from math import cos, sin, pi
from pathlib import Path
from random import Random
from PIL import Image
from shapely.geometry import Polygon, box
from shapely import affinity

STONE='Speckled gray mineral finish'
FACE='Raised pale diamond'
SHADOW='Gray joint bedding'
PLINTH='Darker plinth'
CAP='Coping and staggered cornice'
SIGN='Deep green enamel'
EDGE='Folded green plate rim'
WHITE='Pale painted numeral'
PIN='Plate fixings'
PALETTE={name:dict(color=color,roughness=r) for name,color,r in [
    (STONE,[.83,.81,.77],.96),(FACE,[.99,.975,.95],.93),(SHADOW,[.25,.255,.245],.96),
    (PLINTH,[.52,.55,.51],.97),(CAP,[.54,.54,.50],.88),(SIGN,[.048,.255,.193],.45),
    (EDGE,[.10,.20,.16],.55),(WHITE,[.92,.92,.79],.7),(PIN,[.52,.52,.46],.68)]}
POST_X=.63
PLATE=(.59,1.95)
DIAMOND=(-.55,1.29)

def texture(file):
    """Create an original mineral grain photographically comparable to the gray wall finish."""
    rng=Random(419)
    out=Image.new('RGB',(256,256))
    for y in range(256):
        for x in range(256):
            n=rng.gauss(0,7)+3.9*cos(x*.078+sin(y*.036))+3.1*cos(y*.085+sin(x*.055))
            if rng.random()<.065:n-=rng.uniform(12,42)
            out.putpixel((x,y),tuple(min(255,max(0,round(c+n))) for c in (175,175,170)))
    out.save(file)

def plate_outline(lod):
    n=20 if lod else 56
    def oval(x,z,rx,ry):
        return Polygon([(x+rx*cos(2*pi*i/n),z+ry*sin(2*pi*i/n)) for i in range(n)])
    # Continuous, slightly narrow double-loop numeral, as on the enamel plate.
    upper=oval(0,.035,.028,.038)
    lower=oval(0,-.028,.031,.044)
    return upper.union(lower).difference(oval(0,.037,.016,.023)).difference(oval(0,-.029,.018,.028))

def prism(b,polygon,back,front,material,label):
    b.prism(polygon,back,front,lambda x,z,d:(x,-d,z),material,label)

def block(b,x0,x1,y0,y1,z0,z1,material,label):
    b.prism(box(x0,y0,x1,y1),z0,z1,lambda x,y,z:(x,y,z),material,label)

def beveled_course(b,x0,x1,y0,y1,z0,z1,inset,material,label):
    # A shallow drafted edge follows all four faces and casts its own shadow.
    def ring(x0,x1,y0,y1,z):
        return [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
    levels=[ring(x0+inset,x1-inset,y0+inset,y1-inset,z0),
        ring(x0,x1,y0,y1,z0+inset),ring(x0,x1,y0,y1,z1-inset),
        ring(x0+inset,x1-inset,y0+inset,y1-inset,z1)]
    v=sum(levels,[]);f=[(0,2,1),(0,3,2),(12,13,14),(12,14,15)]
    for j in range(3):
        for k in range(4):
            a=4*j+k;c=4*j+(k+1)%4
            f.extend([(a,c,c+4),(a,c+4,a+4)])
    b.add(v,f,material,label)

def add_building(b,lod):
    # Absolute dimensions are illustrative. Only the documented panel and pier are present.
    left,right=-1.37,.355
    block(b,left,right,-.028,.246,.00,.41,PLINTH,'Dark wall base')
    block(b,left,right,-.039,.252,.41,.456,CAP,'Raised edge on plinth')
    block(b,left,right,0,.238,.456,1.985,STONE,'Wall panel around relief')
    block(b,left-.013,right+.016,-.046,.274,1.985,2.105,CAP,'Continuous cap on enclosure wall')
    block(b,left-.013,right+.016,-.055,.274,2.082,2.119,STONE,'Light top fillet along wall')
    cx,cz=DIAMOND;dx,dz=.687,.611
    # The relief has an uninterrupted flat lozenge with a shallow perimeter bevel.
    v=[]
    for inset,front in [(0,.008),(.008,.031),(.025,.043)]:
        v.extend([(cx+dx-inset,-front,cz),(cx,-front,cz+dz-inset),(cx-dx+inset,-front,cz),(cx,-front,cz-dz+inset)])
    f=[(8,9,10),(8,10,11)]
    for j in range(2):
        for k in range(4):
            a=4*j+k;c=4*j+(k+1)%4
            f.extend([(a,c,c+4),(a,c+4,a+4)])
    b.add(v,f,FACE,'Raised lozenge and four bevels')
    x=POST_X
    block(b,x-.275,x+.275,-.204,.305,0,2.265,SHADOW,'Recessed pier joints')
    breaks=[0,.38,.83,1.26,1.69,2.145]
    for i,(lo,hi) in enumerate(zip(breaks,breaks[1:])):
        beveled_course(b,x-.283,x+.283,-.217,.318,lo+.004,hi-.004,.005,STONE,'Cut pier course '+str(i+1))
    layers=[(.295,.0035,2.142,2.196,SHADOW),(.325,.008,2.192,2.230,CAP),
            (.343,.005,2.227,2.260,STONE),(.367,.008,2.258,2.307,CAP),
            (.427,.006,2.306,2.369,CAP),(.413,.016,2.368,2.408,STONE)]
    for i,(h,ch,lo,hi,mat) in enumerate(layers):
        beveled_course(b,x-h,x+h,.05-h,.05+h,lo,hi,ch,mat,'Tier '+str(i+1)+' of gate pier coping')
    # The upper plaque has a single projecting folded rim and a green face.
    sx,sz=PLATE
    prism(b,box(sx-.115,sz-.134,sx+.115,sz+.134),.216,.229,EDGE,'Address plaque folded border')
    prism(b,box(sx-.109,sz-.127,sx+.109,sz+.127),.229,.232,SIGN,'Green enamel face')
    num=affinity.translate(plate_outline(lod),xoff=sx,yoff=sz+.018)
    prism(b,num,.232,.234,WHITE,'Number 8 with two open counters')
    n=6 if lod else 12
    for xx in [sx-.094,sx+.094]:
        for zz in [sz-.111,sz+.111]:
            pin=Polygon([(xx+.003*cos(2*pi*i/n),zz+.003*sin(2*pi*i/n)) for i in range(n)])
            prism(b,pin,.232,.235,PIN,'Small plaque fixing')
    for surface in (STONE,FACE,PLINTH,CAP):
        b.palette[surface]['texture']=str(Path(__file__).with_name('mineral-grain.png'))
    for part in b.parts:
        if part['material'] in (STONE,FACE,PLINTH,CAP):
            part['texcoords']=[[(x+1.39+.72*y)/2.68,.99-z/2.56] for x,y,z in part['vertices']]
