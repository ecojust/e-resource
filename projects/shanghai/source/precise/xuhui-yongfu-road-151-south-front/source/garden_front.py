"""The three distinct south-facing bays of the 1941–42 garden residence."""
import math

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade

STUCCO = 'warm ivory roughcast'
TRIM = 'carved pale plaster'
STONE = 'dressed buff terrace stone'
GLASS = 'shaded courtyard glazing'
FRAME = 'dark casement frames'
IRON = 'blackened balcony iron'
TILE = 'weathered brown clay coping'
RECESS = 'shadowed soffit plaster'

PALETTE = {
    STUCCO: {'color': [.80, .765, .671], 'roughness': .94},
    TRIM: {'color': [.859, .834, .757], 'roughness': .85},
    STONE: {'color': [.59, .551, .449], 'roughness': .83},
    GLASS: {'color': [.153, .203, .205], 'roughness': .27, 'metallic': .19},
    FRAME: {'color': [.147, .143, .121], 'roughness': .50, 'metallic': .14},
    IRON: {'color': [.139, .133, .114], 'roughness': .62, 'metallic': .29},
    TILE: {'color': [.36, .283, .208], 'roughness': .84},
    RECESS: {'color': [.557, .532, .458], 'roughness': .90},
}


def opened(x, lo, width, spring, rise, segments):
    right, left = x + width / 2, x - width / 2
    arc = [(x + width / 2 * math.cos(t), spring + rise * math.sin(t))
           for t in np.linspace(0, math.pi, segments + 1)]
    return Polygon([(left, lo), (right, lo), *arc])


def casement(face, shape, columns, bars, depth, prefix, arch_bar=None):
    x0, z0, x1, z1 = shape.bounds
    glass = shape.buffer(-.055, join_style=2)
    mullions = []
    for i in range(1, columns):
        x = x0 + (x1 - x0) * i / columns
        mullions.append(box(x - .023, z0, x + .023, z1))
    for z in bars:
        mullions.append(box(x0, z - .021, x1, z + .021))
    if arch_bar:
        spring, rise = arch_bar
        for t in (.26, .5, .74):
            face.line((x0+(x1-x0)*.5,spring,-depth+.018),
                      (x0+(x1-x0)*t,spring+rise*.70,-depth+.018),.014,FRAME,6,prefix+' fanlight radial')
    panes = glass.difference(unary_union(mullions)) if mullions else glass
    face.prism(shape, -depth-.04, -depth, GLASS, prefix+' glass')
    face.prism(shape.difference(panes), -depth+.006, -depth+.039, FRAME, prefix+' frame')


def rope_column(b, x, y, bottom, top, radius, lod, label):
    h = top - bottom
    body = [(0,bottom), (radius*1.21,bottom), (radius*1.21,bottom+.083),
            (radius*.93,bottom+.15), (radius*.84,top-.17),
            (radius*1.18,top-.12), (radius*1.18,top-.048), (radius*1.30,top-.048),
            (radius*1.30,top), (0,top)]
    b.lathe((x,y),[(z,r) for r,z in body],TRIM,16 if lod else 24,label+'/moulded shaft')
    turns = round((h-.27)/.49)
    for phase in (0, math.pi):
        points=[]
        for t in np.linspace(0,1,turns*(6 if lod else 11)+1):
            a=phase+2*math.pi*turns*t
            r=radius*(.90-.083*t)
            points.append((x+r*math.cos(a),y+r*math.sin(a),bottom+.135+(h-.27)*t))
        b.tube(points,radius*.19,TRIM,4 if lod else 6,label+'/spiral flute')


def balcony_iron(b, curve, segments, base, lod, label):
    pts=[curve(i/segments) for i in range(segments+1)]
    for z,r in [(base+.085,.029),(base+.80,.024),(base+.92,.043)]:
        b.tube([(x,y,z)for x,y in pts],r,IRON,6,label+'/continuous rail')
    for i,(x,y) in enumerate(pts):
        b.tube([(x,y,base+.065),(x,y,base+.925)],.023,IRON,5,label+'/vertical')
        if i==segments:continue
        loop=[]
        for angle in np.linspace(0,2*math.pi,6 if lod else 13):
            pos=(i+.5+.442*math.sin(angle))/segments
            xx,yy=curve(pos)
            loop.append((xx,yy,base+.45+.246*math.cos(angle)))
        b.tube(loop,.014,IRON,4 if lod else 5,label+'/oval ironwork')


def rounded_west_bay(b,lod):
    cx,cy,r=-5.94,2.98,2.88
    def point(t,radius=r):
        angle=math.pi+math.pi*t
        return (cx+radius*math.cos(angle),cy+radius*math.sin(angle))
    sweep=28 if lod else 52
    def deck(radius):return Polygon([point(t,radius)for t in np.linspace(0,1,sweep+1)])
    for lo,hi in [(.21,.43),(3.82,4.15),(7.34,7.75),(10.99,11.28)]:
        b.plan_prism(deck(r+.12),lo,hi,STUCCO,'West curved bay/banded floor or roof')
        b.plan_prism(deck(r+.162),hi-.098,hi-.025,TRIM,'West curved bay/drip moulding')
    for bottom,top in [(.43,3.82),(4.15,7.34),(7.75,10.99)]:
        for i in range(6):
            x,y=point(i/5)
            rope_column(b,x,y,bottom,top,.143,lod,'West curved bay')
        if bottom>7:
            back=Facade(b,(cx-r,cy-.01),(cx+r,cy-.01),'West upper loggia')
            opening=box(-1.83,bottom+.022,1.83,top-.38)
            back.wall(bottom,top,[opening],.19,STUCCO)
            casement(back,opening,4,[top-.95],.125,'recessed casement')
            balcony_iron(b,lambda t:point(t,r-.045),22,7.78,lod,'West upper balcony')
            continue
        for i in range(5):
            face=Facade(b,point(i/5,r-.055),point((i+1)/5,r-.055),'West lower glazed curve')
            sill=bottom+(.55 if bottom<1 else .77)
            pane=box(-face.length/2+.14,sill,face.length/2-.14,top-.18)
            face.wall(bottom,top,[pane],.22,STUCCO)
            casement(face,pane,2,[top-.65],.08,'faceted tall casement')
    for i,t in enumerate(np.linspace(0,1,25 if lod else 42)):
        a=point(t,r-.03);c=point(t,r+.11)
        b.tube([(a[0],a[1],11.34),(c[0],c[1],11.31)],.075,TILE,5 if lod else 8,'West crown/raised coping tile')


def central_bay(b,lod):
    a,z=-3.13,3.62
    face=Facade(b,(a,2.19),(z,2.19),'Central recessed bay')
    lo,hi=-face.length*.50,face.length*.50
    profile=[(lo,.33),(hi,.33),(hi,11.09),(2.99,11.17),(2.78,11.47),(2.52,11.45),
             (2.22,11.35),(1.83,11.40),(.96,11.65),(.39,11.63),(-.02,11.88),(-.53,11.66),
             (-.94,11.61),(-1.68,11.38),(-2.20,11.37),(-2.44,11.50),(-2.75,11.31),(lo,11.17)]
    ap=[box(-2.51,.49,2.52,3.36),box(-2.48,4.36,2.49,6.87)]
    top=[opened(x,7.77,2.05,9.63,.23,10 if lod else 19) for x in(-1.06,1.06)]
    face.wall(.33,11.9,[*ap,*top],.33,STUCCO,Polygon(profile))
    for i,o in enumerate(ap):casement(face,o,4,[o.bounds[3]-.57],.12,'glazed central opening '+str(i+1))
    for o in top:casement(face,o,3,[8.64,9.39],.10,'paired upper casement')
    for (x0,z0),(x1,z1) in zip(profile[2:-1],profile[3:]):
        face.line((x0,z0,.015),(x1,z1,.015),.05,TRIM,6,'crest ridge')
    for z0 in (3.84,7.37):
        b.plan_prism(box(a-.06,.59,z+.03,2.19),z0,z0+.26,STUCCO,'Central bay/cantilevered balcony')
        b.plan_prism(box(a-.09,.53,z+.05,2.20),z0+.17,z0+.25,TRIM,'Central bay/floor edge')
        balcony_iron(b,lambda t:(a+.07+(z-a-.14)*t,.64),24,z0+.26,lod,'Central bay balcony')
        for x in (a+.07,z-.07):
            balcony_iron(b,lambda t:(x,.64+1.52*t),5,z0+.26,lod,'Central bay return')
    for i in range(3):
        inset=.245*i
        terrace=box(a-.18+inset,-.62+inset,z+.17-inset,2.24).buffer(.21,quad_segs=6)
        b.plan_prism(terrace,.013+i*.13,.145+i*.13,STONE,'Central bay/terrace tread')


def eastern_arcades(b,lod):
    face=Facade(b,(3.60,1.14),(8.78,1.14),'Eastern two-level arcade')
    aps=[]
    for bottom,spring in ((.65,2.53),(4.52,6.00)):
        for x in(-1.54,0,1.54):aps.append(opened(x,bottom,1.24,spring,.61,10 if lod else 21))
    face.wall(.34,8.25,aps,.34,STUCCO)
    for i,shape in enumerate(aps):
        z0=shape.bounds[1]
        spr=2.53 if i<3 else 6.00
        casement(face,shape,2,[spr],.135,'arcade casement '+str(i),arch_bar=(spr,.61))
        lip=shape.buffer(.062,join_style=1).difference(shape)
        face.prism(lip,-.035,.055,TRIM,'shallow arch archivolt')
    for level in ((.38,3.31),(4.17,6.8)):
        for x in (-2.30,-.77,.77,2.30):
            pp=face.point(x,0,.013)
            rope_column(b,pp[0],pp[1],level[0],level[1],.108,lod,'Eastern arcade')
    for z in (.43,3.60,4.08,7.61,8.22):
        face.box(0,z,face.length+.13,.13,.38,.018,TRIM,'horizontal cornice')
    for x in np.linspace(-2.3,2.3,13):
        face.prism(Polygon([(x-.094,3.53),(x+.094,3.53),(x+.025,3.34),(x-.04,3.34)]),-.02,.055,TRIM,'lower cornice corbel')
    for x in np.linspace(-2.06,2.06,5):
        face.prism(Polygon([(x-.13,7.65),(x,7.78),(x+.13,7.65),(x,7.53)]),-.015,.043,STONE,'five diamond insets')
    for x in np.linspace(-2.47,2.47,21 if lod else 36):
        face.line((x,8.30,-.25),(x,8.25,.10),.073,TILE,7,'clay coping roll')
    b.plan_prism(box(3.55,1.13,8.80,2.25),8.12,8.26,STUCCO,'Eastern bay/visible top return')


def model(b,lod):
    rounded_west_bay(b,lod)
    central_bay(b,lod)
    eastern_arcades(b,lod)
    # Shallow returns end the published elevation at the depth of the curved bay.
    for x, y, top, label in [(3.60,1.14,8.25,'East arcade/west pier return'),
                              (8.78,1.14,8.25,'East arcade/east pier return'),
                              (-3.09,2.19,11.08,'Central bay/west parapet return'),
                              (3.62,2.19,11.08,'Central bay/east parapet return')]:
        b.plan_prism(box(x-.087,y,x+.085,3.13),.36,top,STUCCO,label)
