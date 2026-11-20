"""Model the street face and photographed returns of the Tai'an Road gate to Willow Garden."""
import math

import numpy as np
from shapely.geometry import Polygon,box
from photo_architecture import Facade

STUCCO='pale pebbled roughcast'
RED='fired red terracotta'
EDGE='orange relief highlights'
STONE='dusky rose plinth stone'
TILE='glazed red barrel tile'
IRON='dark entrance ironwork'
GREEN='green enamel address sign'
IVORY='cream enamel letters'
GILT='weathered brass fittings'
PALETTE={STUCCO:{'color':[.70,.652,.568],'roughness':.92},RED:{'color':[.544,.207,.116],'roughness':.76},
 EDGE:{'color':[.651,.279,.151],'roughness':.72},STONE:{'color':[.437,.337,.288],'roughness':.89},
 TILE:{'color':[.48,.173,.101],'roughness':.58},IRON:{'color':[.127,.146,.126],'metallic':.28,'roughness':.65},
 GREEN:{'color':[.033,.242,.141],'roughness':.50},IVORY:{'color':[.847,.838,.726],'roughness':.62},
 GILT:{'color':[.49,.392,.199],'roughness':.56,'metallic':.30}}
RADIUS=2.148
SPRING=2.73
RISE=1.88
HALF=3.31
HIGH=6.41
CROWN=5.79
DEPTH=.74


def arc(rx,rz,segments):
    return [(rx*math.cos(t),SPRING+rz*math.sin(t)) for t in np.linspace(0,math.pi,segments+1)]


def relief(f,points,radius,material,label,lod,depth):
    f.builder.tube([f.point(u,z,depth) for u,z in points],radius,material,5 if lod else 8,label)


def clay_drum(f,center,width,roof,lod):
    """Curved tile segments with individual open ends facing the street."""
    r=width*.53
    outer=[(center+r*math.cos(t),roof+r*math.sin(t)) for t in np.linspace(0,math.pi,7 if lod else 12)]
    inner=[(center+(r-.026)*math.cos(t),roof+(r-.026)*math.sin(t)) for t in np.linspace(math.pi,0,7 if lod else 12)]
    f.prism(Polygon(outer+inner),-.47,.095,TILE,'individual barrel tile')


def gateway(f,lod):
    count=28 if lod else 60
    top=[(-HALF,HIGH),(-1.63,HIGH),(-1.63,CROWN),(1.63,CROWN),(1.63,HIGH),(HALF,HIGH)]
    mass=Polygon([(-HALF,0),(-HALF,HIGH),*top[1:],(HALF,0)])
    clear=Polygon([(-RADIUS,-.1),(RADIUS,-.1),(RADIUS,SPRING),*arc(RADIUS,RISE,count)[1:]])
    f.prism(mass.difference(clear),-DEPTH,0,STUCCO,'stepped parapet and open vault')
    for sign in (-1,1):
        center=sign*(RADIUS+HALF)/2;w=HALF-RADIUS
        f.box(center,.255,w+.084,.51,DEPTH+.12,-DEPTH/2,STONE,'incised stone base')
        f.box(center,.535,w+.105,.085,DEPTH+.145,-DEPTH/2,STONE,'stone plinth lip')
        f.box(center,.053,w+.144,.106,DEPTH+.175,-DEPTH/2,STONE,'projecting base course')
        f.box(center,.275,.028,.385,.012,.065,RED,'plinth vertical joint')
        for z,height,ex in [(SPRING-.085,.085,.093),(SPRING+.018,.090,.15),(SPRING+.104,.070,.115)]:
            f.box(center,z,w+ex*1.22,height,DEPTH+ex*2,-DEPTH/2,RED,'impost molding')
        for row in np.linspace(.76,2.47,4):
            f.box(sign*(HALF-.10),row,.041,.30,.012,.002,STONE,'pier edge channel')
    surround=Polygon(arc(RADIUS+.29,RISE+.27,count)+list(reversed(arc(RADIUS,RISE,count))))
    f.prism(surround,-.014,.080,RED,'concentric terracotta architrave')
    for off,rad,depth in [(.034,.031,.082),(.16,.045,.082),(.267,.041,.075)]:
        relief(f,arc(RADIUS+off,RISE+off,count),rad,EDGE if off==.034 else RED,'Arch/separate rounded moldings',lod,depth)
    for i in range(1,12):
        theta=math.pi*i/12
        a=((RADIUS+.19)*math.cos(theta),SPRING+(RISE+.19)*math.sin(theta))
        c=((RADIUS+.28)*math.cos(theta),SPRING+(RISE+.28)*math.sin(theta))
        relief(f,[a,c],.0095,STONE,'Arch/radial joints',lod,.108)
    for x in np.linspace(-1.54,1.54,14):
        clay_drum(f,x,.222,CROWN,lod)
    f.box(RADIUS+.19,SPRING-.48,.30,.50,.043,.051,STONE,'pier notice')


def bezier(points,count):
    p=np.asarray(points,dtype=float)
    return [tuple((1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]) for t in np.linspace(0,1,count)]


def leaf(f,x,z,dx,dz,width,sign,lod):
    """A pointed acanthus blade, with raised center rib and a shadowed folded return."""
    n=math.hypot(dx,dz);tx,tz=dx/n,dz/n;nx,nz=-tz*sign,tx*sign
    def pos(t,offset):
        return (x+dx*t+nx*width*offset,z+dz*t+nz*width*offset)
    # The outer margin rolls back before the tip; the shorter folded margin
    # returns on the other side of the raised midrib.
    outer=bezier([pos(0,0),pos(.10,1.08),pos(.54,1.22),pos(.80,.63)],9)
    tip=bezier([outer[-1],pos(.93,.46),pos(.95,.76),pos(1,.92)],6)
    inner=bezier([tip[-1],pos(.79,-.18),pos(.39,-.63),pos(0,0)],10)
    f.prism(Polygon(outer+tip[1:]+inner[1:-1]),.062,.119,RED,'hand-shaped acanthus lobe')
    vein=bezier([pos(0,0),pos(.32,.11),pos(.72,.02),pos(.93,.60)],5 if lod else 9)
    relief(f,vein,.014,EDGE,'Relief/raised leaf rib',lod,.127)


def spiral(f,cx,cz,r,start,sign,lod,depth):
    sweep=np.linspace(0,math.pi*1.70,11 if lod else 23)
    rads=np.linspace(r,r*.16,len(sweep))
    curve=[(cx+sign*rr*math.cos(start+a),cz+rr*math.sin(start+a)) for a,rr in zip(sweep,rads)]
    relief(f,curve,.043,RED,'Relief/coiled scroll',lod,depth)


def oval(f,x,z,rx,rz,depth,lod,label,material):
    # A low relief ellipsoid with the greatest protrusion at its center.
    rr=8 if lod else 12;bands=3 if lod else 5;vertices=[];faces=[]
    vertices.append(f.point(x,z,.090+depth))
    for u in range(1,bands+1):
        theta=math.pi/2*u/bands
        for i in range(rr):
            t=2*math.pi*i/rr
            vertices.append(f.point(x+rx*math.sin(theta)*math.cos(t),z+rz*math.sin(theta)*math.sin(t),.08+depth*math.cos(theta)))
    for i in range(rr):faces.append((0,1+i,1+(i+1)%rr))
    for u in range(bands-1):
        off=1+u*rr
        for i in range(rr):
            j=(i+1)%rr;faces.extend([(off+i,off+rr+i,off+rr+j),(off+i,off+rr+j,off+j)])
    f.builder.add(vertices,faces,material,label)


def decoration(f,lod):
    for sign in (-1,1):
        mirror=lambda pts:[(sign*x,z) for x,z in pts]
        for control in [[(2.91,3.08),(2.77,3.60),(2.95,4.26),(2.84,5.18)],
                        [(2.81,4.35),(2.25,4.03),(1.85,5.16),(.75,5.12)],
                        [(1.79,4.72),(1.44,5.14),(.98,5.31),(.40,5.08)]]:
            relief(f,mirror(bezier(control,10 if lod else 23)),.055,RED,'Relief/spreading acanthus branches',lod,.094)
        for x,z,dx,dz,w in [(2.89,3.17,-.28,.40,.105),(2.87,3.29,.28,.36,.11),
          (2.83,3.54,-.32,.38,.13),(2.86,3.71,.28,.40,.13),(2.84,3.98,-.39,.22,.14),
          (2.85,4.19,.24,.47,.14),(2.86,4.45,-.31,.37,.13),(2.84,4.57,.14,.48,.12),
          (2.51,4.36,.02,.36,.12),(2.30,4.46,-.36,.13,.14),
          (2.13,4.60,.12,.39,.105),(1.91,4.73,-.32,.20,.13),(1.68,4.88,.05,.32,.10),
          (1.46,5.01,-.30,.14,.12),(1.17,5.11,-.28,.18,.10),(.89,5.11,-.15,.23,.10)]:
            leaf(f,x*sign,z,dx*sign,dz,w,sign,lod)
        for x,z,r,start in [(2.85,3.52,.17,.0),(2.77,4.74,.20,-1.2),(1.92,5.10,.18,-.8),(.68,5.24,.25,-.3)]:
            spiral(f,x*sign,z,r,start,sign,lod,.136)
        # Grape clusters hang below two curled leaves on each pier; the
        # individual grapes taper toward the bottom of the relief.
        cx=sign*2.73
        relief(f,[(cx-.25,2.44),(cx,2.38),(cx+.23,2.45)],.036,RED,'Pier/pendant hanger',lod,.11)
        for dx in (-.37,.37):
            d=1 if dx>0 else -1
            leaf(f,cx+dx*.24,2.39,dx,.16,.12,d,lod)
            spiral(f,cx+dx*.77,2.30,.115,.57,d,lod,.114)
        for z,cols in [(2.28,3),(2.14,4),(2.00,3),(1.87,2),(1.74,1),(1.55,3),(1.42,2),(1.30,1)]:
            for i in range(cols):
                xx=cx+(i-(cols-1)/2)*.102+.025*math.cos(z*14)
                oval(f,xx,z,.069,.085,.062,lod,'Pier/grape relief',EDGE if i%3==0 else RED)
        for idx in (-1,0,1):
            relief(f,[(cx,1.23),(cx+idx*.06,1.12),(cx+idx*.076,1.03)],.014,RED,'Pier/tassel',lod,.12)
    # Central shell and two scrolling branches above the molded archivolt.
    oval(f,0,5.07,.28,.295,.115,lod,'Crown/central foliate cartouche',RED)
    for j in range(-3,4):
        phi=math.radians(90+j*17)
        leaf(f,0,4.91,.38*math.cos(phi),.49*math.sin(phi),.068,1 if j<0 else -1,lod)
    # The central relief has visible flutes across the shell. These must
    # project beyond the boss so the radial carving reads from the street.
    for k in range(-3,4):
        a=k*.061
        rib=bezier([(a*.19,4.91),(a*.58,5.013),(a*1.05,5.159),(a*.94,5.24-abs(k)*.016)],8 if lod else 13)
        relief(f,rib,.016,EDGE,'Crown/fluted shell ridges',lod,.211-abs(k)*.010)
    for side in (-1,1):
        spiral(f,.42*side,5.38,.22,-.2,side,lod,.13)
        leaf(f,.49*side,5.46,-.11*side,.19,.075,side,lod)


def wing_top(x):
    if 6.50<x<9.35:
        return 2.77-.42*math.sin((x-6.50)/2.85*math.pi)**2
    return 2.77


def wings(f,lod):
    for l,r in ((-7.28,-HALF),(HALF,9.60)):
        xs=list(np.linspace(l,r,45 if r>6.5 else 5))
        poly=Polygon([(l,0),(r,0)]+[(x,wing_top(x)) for x in reversed(xs)])
        f.prism(poly,-.37,-.06,STUCCO,'visible garden boundary wall')
        f.prism(box(l,.015,r,.206),-.39,-.036,STONE,'wall base')
        for x in np.arange(l+.7,r,1.08):
            f.box(x,(wing_top(x)+.20)/2,.012,wing_top(x)-.27,.017,-.054,STONE,'wall panel joint')
        for z in (.00,.082):
            rail=[(x,wing_top(x)+z) for x in xs]
            relief(f,rail,.043,RED,'Boundary/undulating clay coping',lod,-.018)
        for x in np.arange(l+.09,r-.075,.17):
            clay_drum(f,float(x),.168,wing_top(x)+.079,lod)
    f.box(3.91,2.44,.58,.169,.035,-.020,GREEN,'enamel lane address')
    # Seven-stroke numerals on the small lane marker in the dated photograph.
    strokes=[[(0,-.04),(0,.045)], [(-.03,.035),(.005,.045),(.027,.021),(.015,0),(-.032,-.04),(.033,-.04)],
             [(-.023,-.033),(-.030,.022),(-.015,.043),(.018,.042),(.028,.019),(.027,-.027),(.012,-.043),(-.023,-.033)]]
    for pos,path in zip([3.80,3.91,4.015],strokes):
        relief(f,[(pos+x,2.442+z)for x,z in path],.0056,IVORY,'Address/120',lod,.008)


def folded_leaf(b,s,lod):
    """Open gate leaves lie against the inner reveals, leaving the path usable."""
    x=s*(RADIUS-.052);ya,yb=.20,1.77;z0=.107;top=2.24
    for z in (z0,z0+.20,top-.19,top):
        b.tube([(x,ya,z),(x,yb,z)],.022,IRON,7,'Open gates/rails')
    for y in np.linspace(ya,yb,10):
        b.tube([(x,y,z0),(x,y,top+.05)],.014,IRON,6,'Open gates/uprights')
    for y in np.linspace(ya+.2,yb-.20,4):
        ys=np.linspace(0,2*math.pi,13 if lod else 23)
        b.tube([(x-s*.018,y+.125*math.cos(a),1.03+.27*math.sin(a)) for a in ys],.012,GILT,6,'Open gates/rings')


def model(b,lod):
    f=Facade(b,(-10,0),(10,0),'Tai’an Road')
    gateway(f,lod);decoration(f,lod);wings(f,lod)
    for sign in (-1,1):
        folded_leaf(b,sign,lod)
