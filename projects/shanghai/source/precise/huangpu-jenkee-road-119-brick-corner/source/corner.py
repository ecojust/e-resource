"""Upper chamfer of the building at the former Jenkee Road, after Fayhoo's 2014 photograph."""
from math import cos, sin, pi, ceil
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ID='huangpu-jenkee-road-119-brick-corner'
BRICK='Rose brick masonry'; DARK='Shadow in the brick joints'; STONE='Cool dressed stone'
SOFFIT='Shadow under string courses'; EDGE='Pale weathered stone edge'
WINDOW='Brown window sash'; PANE='Glass in shade'; SKY='Cooler upper glass'; WOOD='Dark window reveal'
CLOTH='Weathered wine coloured canopy'; SEAM='Raised canopy seam'; HEM='Shadowed scalloped valance'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [
    (BRICK,[1,1,1],.94),(DARK,[.40,.28,.255],.95),(STONE,[.58,.575,.50],.94),
    (SOFFIT,[.365,.36,.325],.94),(EDGE,[.73,.72,.64],.91),(WINDOW,[.28,.23,.20],.8),
    (PANE,[.225,.27,.26],.33),(SKY,[.315,.395,.405],.33),(WOOD,[.20,.156,.135],.89),
    (CLOTH,[.44,.32,.33],.94),(SEAM,[.51,.39,.40],.87),(HEM,[.355,.245,.26],.93)]}
HALF=1.26
DEPTH=2.94
ANGLE=pi/4
LEVELS=(0.,2.66,5.32)
OPEN_HALF=.571
LEFT=lambda u,z,d: (-HALF+u*cos(ANGLE)-d*sin(ANGLE),-u*sin(ANGLE)-d*cos(ANGLE),z)
FACE=lambda u,z,d: (u,-d,z)
RIGHT=lambda u,z,d: (HALF+u*cos(ANGLE)+d*sin(ANGLE),u*sin(ANGLE)-d*cos(ANGLE),z)
PLANES=((LEFT,(-1.21,0.)),(FACE,(-HALF,HALF)),(RIGHT,(0.,1.21)))

def texture():
    p=Path(__file__).with_name('rose-brick.png')
    if not p.exists():
        w,h=840,1008
        rng=np.random.default_rng(499)
        yy,xx=np.indices((h,w));row=yy//9;col=(xx+(row%2)*20)//40
        tones=rng.normal(0,7.5,(113,23));stain=rng.normal(0,2.2,(h,w))
        brick=np.array([166,98,91])[None,None,:]+(tones[row,col%23]+stain)[:,:,None]
        joint=(yy%9==0)|((xx+row%2*20)%40==0)
        brick[joint]=np.array([147,116,108])+stain[joint,None]
        Image.fromarray(np.clip(brick,0,255).astype('u1')).quantize(158).save(p)
    PALETTE[BRICK]['texture']=str(p)

def profile(model,mapper,polygon,front,depth,mat,label):
    model.prism(polygon,front-depth,front,mapper,mat,label)

def rect(model,mapper,l,r,b,t,front,depth,mat,label):
    profile(model,mapper,box(l,b,r,t),front,depth,mat,label)

def aperture(base,count):
    l=OPEN_HALF; spring=base+1.97
    arc=[(l*cos(t),spring+.30*sin(t)) for t in np.linspace(0.,pi,count+1)]
    return Polygon([(-l,base+.44),(l,base+.44)]+arc)

def cornice(model,z,upper=False):
    sections=[(-.11,-.07,.065,SOFFIT),(-.07,-.012,.112,STONE),
              (-.012,.040,.147,EDGE),(.040,.074,.115,STONE),(.074,.11,.087,SOFFIT)]
    if upper: sections+= [( .11,.16,.14,STONE),(.16,.22,.19,EDGE)]
    for mapper,(l,r) in PLANES:
        for lo,hi,over,material in sections:
            # The end of a moulding is extended to the tangent of the adjoining plane.
            overlap=over*.4143
            rect(model,mapper,l-overlap,r+overlap,z+lo,z+hi,over,.28,material,'Stone stringcourse turning around the corner')

def canopy(model,z,far):
    spans=36 if far else 48
    rings=9
    half=.67;projection=.59;rise=.39
    vertices=[];faces=[]
    for j in range(rings):
        lat=j*(pi/2-.065)/(rings-1)
        for i in range(spans+1):
            t=i*pi/spans
            vertices.append((half*cos(t)*cos(lat),-.018-projection*sin(t)*cos(lat),z+rise*sin(lat)))
    for j in range(rings-1):
        for i in range(spans):
            k=j*(spans+1)+i
            faces.append((k+spans+1,k+spans+2,k+1,k))
    # The top of this fabric hood is pinned against the brick arch.
    peak=len(vertices);vertices.append((0,-.018,z+rise));off=(rings-1)*(spans+1)
    for i in range(spans):faces.append((peak,off+i+1,off+i))
    model.add(vertices,faces,CLOTH,'Panelled half-dome window awning')
    for i in range(7):
        t=i*pi/6
        points=[((half+.003)*cos(t)*cos(a),-.019-(projection+.003)*sin(t)*cos(a),z+(rise+.003)*sin(a))
                for a in np.linspace(0,pi/2-.04,rings)]
        model.tube(points,.005,SEAM,4 if far else 6,'Seam between awning panels')
    verts=[];fs=[]
    for i in range(spans+1):
        t=i*pi/spans;x=half*cos(t);y=-.018-projection*sin(t)
        verts.extend([(x,y,z+.008),(x,y,z-.055-.039*(1-cos(12*t))*.5)])
    for i in range(spans):fs.append((2*i,2*i+2,2*i+3,2*i+1))
    model.add(verts,fs,HEM,'Scalloped valance following the curved hood')

def opening_details(model,base,far):
    shape=aperture(base,12 if far else 28)
    trim=shape.buffer(.045,join_style=2).difference(shape)
    profile(model,FACE,trim,.045,.14,BRICK,'Projecting brick rim of segmental opening')
    profile(model,FACE,shape,-.19,.025,WOOD,'Shadow behind street-facing opening')
    for j,(b,t) in enumerate([(base+.465,base+1.17),(base+1.17,base+1.96)]):
        for l,r in [(-.522,-.018),(.018,.522)]:
            rect(model,FACE,l,r,b,t,-.121,.022,SKY if j==1 else PANE,'Glazing below the hood')
    for x in (-.544,0.,.544):
        rect(model,FACE,x-.023,x+.023,base+.44,base+2.,-.064,.05,WINDOW,'Vertical wood sash')
    rect(model,FACE,-.545,.545,base+1.15,base+1.19,-.061,.05,WINDOW,'Horizontal meeting rail')
    for mat,b,t,over in [(STONE,.36,.405,.072),(EDGE,.405,.455,.11)]:
        rect(model,FACE,-.71,.71,base+b,base+t,over,.27,mat,'Sill beneath the opening')
    for x in (-1.04,1.04):
        rect(model,FACE,x-.16,x+.16,base+.13,base+2.39,.072,.20,BRICK,'Raised brick pilaster on the beveled bay')
        rect(model,FACE,x-.196,x+.196,base+.35,base+.43,.104,.25,EDGE,'Sill block of the brick pier')
        for step,(b,t,w,proj,mat) in enumerate([(2.34,2.39,.19,.107,SOFFIT),(2.39,2.47,.22,.13,STONE),(2.47,2.56,.258,.168,EDGE),(2.56,2.66,.274,.192,STONE)]):
            rect(model,FACE,x-w,x+w,base+b,base+t,proj,.29,mat,'Four stages of stone cap over brick pilaster')
    # Lower panel has a recessed brick field framed on three sides.
    for x in (-.64,.64):
        rect(model,FACE,x-.043,x+.043,base+.10,base+.35,.054,.105,BRICK,'Vertical return of the recessed apron')
    rect(model,FACE,-.68,.68,base+.08,base+.141,.054,.105,BRICK,'Brick apron ledge')
    # Successive radial bricks follow the segmental crown seen above the canopies.
    for i in range(11):
        a0=(i+.04)*pi/11.;a1=(i+.96)*pi/11.
        vertices=[(radius*cos(a),base+1.97+rise*sin(a)) for radius,rise,a in [(OPEN_HALF+.044,.331,a0),(OPEN_HALF+.044,.331,a1),(OPEN_HALF+.13,.411,a1),(OPEN_HALF+.13,.411,a0)]]
        profile(model,FACE,Polygon(vertices),.056,.102,STONE if i==5 else BRICK,'Keystone or radial crown brick')
    canopy(model,base+1.93,far)

def add_building(model,far=False):
    texture()
    voids=unary_union([aperture(level,12 if far else 28) for level in LEVELS])
    for mapper,(l,r) in PLANES:
        whole=box(l,.05,r,7.99)
        profile(model,mapper,whole.difference(voids) if mapper is FACE else whole,0,.245,BRICK,'Cut masonry around the corner openings')
        if mapper is not FACE:
            # Deep ruled lines in the returns are visible in the source photograph.
            for z in np.arange(.30,7.97,.29):
                rect(model,mapper,l,r,float(z),float(z)+.021,.012,.043,DARK,'Incised horizontal joint on the return')
    for base in LEVELS:
        cornice(model,base+.02);opening_details(model,base,far)
    cornice(model,7.89,upper=True)
    gable=Polygon([(-HALF,7.99),(-HALF,8.12),(-1.03,8.12),(-1.03,8.21),(-.84,8.21),(0,8.69),(.84,8.21),(1.03,8.21),(1.03,8.12),(HALF,8.12),(HALF,7.99)])
    profile(model,FACE,gable,.016,.25,STONE,'Stepped central gable above the corner')
    for part in model.parts:
        if part['material']==BRICK:
            part['texcoords']=[[(x+abs(y)*.32+2.55)/5.4,.012+z/9.11] for x,y,z in part['vertices']]
