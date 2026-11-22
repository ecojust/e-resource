"""One upper riverfront bay, Fuxin Flour Mill No. 1.

Brick ends and bed joints stop at the window reveal and the small ventilator
below its projecting sill. The independent red pier faces at either side are
retained. Dimensions are estimates taken from the documented streetscape.
"""
from math import ceil
import random
from shapely.geometry import box as polygon
def paint(rgb,rough=.88,metal=0):
    def linear(v):
        s=v/255
        return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
    return dict(color=[linear(c) for c in rgb],roughness=rough,metallic=metal)
PALETTE={
    'warm gray mortar':paint((142,129,115)), 'pier mortar':paint((155,123,112)),
    'red stretcher':paint((160,111,96)),'weathered pink brick':paint((166,119,103)),
    'red header':paint((151,102,90)),'gray-yellow brick':paint((154,144,126)),
    'smoke gray brick':paint((145,138,122)),'warmer ochre brick':paint((157,143,121)),
    'pale gray brick':paint((163,151,134)),'limestone sill':paint((144,136,125)),
    'painted window frame':paint((65,67,63),.63,.18),'steel casement':paint((77,81,75),.56,.23),
    'dusty glazing':paint((111,126,129),.36,.13),'blue-gray glazing':paint((97,113,122),.33,.18),
    'dark glazing':paint((89,100,104),.44,.16),'washed soldier brick':paint((151,127,112)),'shaded sill underside':paint((102,97,87)),'vent shadow':paint((61,53,46)),
}
BRICKS=('gray-yellow brick','smoke gray brick','warmer ochre brick','pale gray brick')
PIER=('red stretcher','weathered pink brick','red header')
WINDOW=(-.646,.646,1.170,2.477)
VENT=(-.158,.158,.896,1.049)
def solid(b,name,x0,x1,y0,y1,z0,z1,mat,flat=False):
    v=[(x,y,z)for z in(z0,z1)for y in(y0,y1)for x in(x0,x1)]
    f=[(0,1,5,4)] if flat else [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
    b.add(v,f,mat,name)
def layer(b,label,x0,x1,z0,z1,y0,y1,holes,mat):
    shape=polygon(x0,z0,x1,z1)
    for xa,xb,za,zb in holes:shape=shape.difference(polygon(xa,za,xb,zb))
    b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)
def fragments(left,right,lo,hi,cutouts):
    pieces=[(left,right,lo,hi)]
    for a,e,c,d in cutouts:
        after=[]
        for x,v,z,f in pieces:
            l,r=max(x,a),min(v,e);bt,tp=max(z,c),min(f,d)
            if l>=r or bt>=tp:after.append((x,v,z,f));continue
            after.extend(((x,v,z,bt),(x,v,tp,f),(x,l,bt,tp),(r,v,bt,tp)))
        pieces=[p for p in after if p[1]-p[0]>.005 and p[3]-p[2]>.005]
    return pieces
def courses(b,label,xmin,xmax,zmin,zmax,y,materials,holes,lod,seed):
    rng=random.Random(seed);bh=.069;bw=.197
    for j in range(ceil((zmax-zmin)/bh)):
        z=zmin+j*bh+.0025;top=min(zmax,zmin+(j+1)*bh-.0025)
        for i in range(-1,ceil((xmax-xmin)/bw)+1):
            x=xmin+(i+(.5 if j%2 else 0))*bw
            lo,hi=max(xmin,x+.0034),min(xmax,x+bw-.0034)
            if hi-lo<.006 or top-z<.005:continue
            mat=rng.choice(materials);front=y-(.0023+rng.random()*.0026)
            for l,r,bot,t in fragments(lo,hi,z,top,holes):
                solid(b,label+' course '+str(j+1),l,r,front,y+.001,bot,t,mat,flat=lod)
def add_building(b,lod=False):
    openings=[WINDOW,VENT]
    layer(b,'bonded facade wall',-1.44,1.44,0,3.10,0,.26,openings,'warm gray mortar')
    courses(b,'infill',-1.245,1.245,0,3.10,0,BRICKS,openings,lod,493)
    for i,(lo,hi)in enumerate(((-1.44,-1.245),(1.245,1.44))):
        solid(b,'projecting pier '+str(i),lo,hi,-.061,.018,0,3.10,'pier mortar')
        courses(b,'pier '+str(i),lo,hi,0,3.10,-.061,PIER,[],lod,28+i)
        for j in range(44):
            z=j*.069+.003
            # Small transverse faces show the red pier projecting beyond the infill.
            x=hi if i==0 else lo
            solid(b,'return at pilaster '+str(i),x-.003,x+.003,-.061,-.002,z,z+.063,PIER[j%3])
    # A narrow course steps out at the head of this upper bay.
    for z,w in ((2.902,.025),(2.971,.060),(3.037,.081)):
        solid(b,'stepped eaves band '+str(z),-1.245,1.245,-w,.006,z,z+.063,'red stretcher')
    lo,hi,bt,top=WINDOW
    solid(b,'stone lintel drip',lo-.073,hi+.073,-.071,.142,top-.026,top+.044,'limestone sill')
    for i in range(19):
        a=lo-.057+i*.074;solid(b,'soldier lintel brick',a,a+.069,-.015,.009,top+.048,top+.193,('washed soldier brick','red header','washed soldier brick')[i%3])
    solid(b,'continuous window sill',lo-.069,hi+.069,-.095,.124,bt-.081,bt+.009,'limestone sill')
    solid(b,'stone sill lower lip',lo-.061,hi+.061,-.083,.048,bt-.099,bt-.080,'shaded sill underside')
    a,z=VENT[0],VENT[2]
    solid(b,'back of ventilation recess',a,VENT[1],.215,.25,z,VENT[3],'vent shadow')
    for x in (lo,hi-.042):
        solid(b,'window jamb frame',x,x+.042,.098,.155,bt,top,'painted window frame')
    for z in (bt,top-.044):
        solid(b,'main frame rail',lo,hi,.096,.155,z,z+.044,'painted window frame')
    dx=(hi-lo-.09)/4;dz=(top-bt-.09)/4
    for i in range(4):
        for j in range(4):
            x=lo+.045+i*dx;z=bt+.045+j*dz
            solid(b,'glazed pane '+str(i*4+j),x,x+dx,.137,.147,z,z+dz,
                  ('blue-gray glazing','dusty glazing','dark glazing','dusty glazing')[(i*5+j*3)%4])
    for i in (1,2,3):
        x=lo+.045+i*dx;wide=.017 if i==2 else .009
        solid(b,'casement upright '+str(i),x-wide,x+wide,.103,.140,bt+.040,top-.040,'steel casement')
    for j in (1,2,3):
        z=bt+.045+j*dz
        solid(b,'casement crossbar '+str(j),lo+.040,hi-.040,.107,.141,z-.008,z+.008,'steel casement')
