"""Measured three-storey street front, curved south end and straight north return."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from materials import BASE, CEMENT, DARK, DENTIL, FRAME, GLASS, PLASTER, ROOF, SHADOW, WOOD
from numbered_entrance import add_entrance, openings
from rounded_bay import add_round_windows
from street_windows import floral_apron,photo_lights,sash

TANGENT=-6.53
RADIUS=1.82
NORTH=6.98
DEPTH=3.18
SOUTH=TANGENT-RADIUS
EAVE=10.26

def corner(r,n):
    return [(TANGENT-r*sin(i*pi/(2*n)),RADIUS-r*cos(i*pi/(2*n))) for i in range(n+1)]

def horizontal(f,shape,z0,z1,mat,label):
    f.b.prism(shape,z0,z1,lambda u,d,z:f.point(u,d,z),mat,f.label+' | '+label)

def corner_band(f,inner,outer,z0,z1,mat,label,n):
    shape=Polygon(corner(RADIUS+outer,n)+list(reversed(corner(RADIUS+inner,n))))
    horizontal(f,shape,z0,z1,mat,label)
    
def floor_edge(f,z0,z1,projection,mat,label,n,central_gap=False):
    runs=[(TANGENT,-2.55),(2.28,NORTH)] if central_gap else [(TANGENT,NORTH)]
    for left,right in runs:
        f.rect(left,right,z0,z1,.001,projection,mat,label)
    corner_band(f,0,projection,z0,z1,mat,label,n)
    for s,d0,p in [(SOUTH,RADIUS,-1),(NORTH,0,1)]:
        a,b=sorted((s,s+p*projection))
        horizontal(f,box(a,d0,b,DEPTH),z0,z1,mat,label+' | side return')

def side_wall(face,width,center,lod,qualifier):
    lights=[]
    for z0,z1 in [(3.91,5.94),(7.76,9.59)]:
        shape=box(center-.51,z0,center+.51,z1)
        lights.append(shape)
        sash(face,shape,[z0+(z1-z0)*i/3 for i in (1,2)],[center],qualifier)
    face.solid(box(0,0,width,EAVE).difference(unary_union(lights)),-.255,0,PLASTER,qualifier+' | side wall')
    face.rect(0,width,.02,.52,.003,.029,BASE,qualifier+' | plinth')

def add_body(f,lod=False):
    steps=12 if lod else 32
    lights=photo_lights(lod)
    retail=[(-5.48,-3.18),(3.60,5.72)]
    shop_openings=[box(a,.035,b,2.96) for a,b in retail]
    cut=unary_union([*openings(),*shop_openings,*[record[1] for record in lights]])
    f.solid(box(TANGENT,0,NORTH,EAVE).difference(cut),-.25,0,PLASTER,'continuous street wall with recessed openings')
    f.solid(box(TANGENT,.012,NORTH,.52).difference(cut),.001,.031,BASE,'washed gravel plinth')
    add_round_windows(f,TANGENT,RADIUS,EAVE,lod)
    corner_band(f,0,.03,.012,.52,BASE,'rounded south plinth',steps)
    for a,b in retail:
        u=(a+b)/2
        f.rect(a,b,.035,2.96,-.28,-.25,DARK,'occupied ground-floor opening | shadow')
        lights_shape=box(a+.075,.09,b-.075,2.88)
        sash(f,lights_shape,[.70,2.39],[u], 'occupied ground-floor glazed doors',trim=False)
        f.rect(a-.12,b+.12,2.99,3.18,.005,.22,WOOD,'street shop | fascia')
    for name,shape,rows,columns,head in lights:
        sash(f,shape,rows,columns,name,head)
    floral_apron(f,lod)
    add_entrance(f,lod)
    side_wall(f.face(NORTH,0,0,1),DEPTH,2.15,lod,'north return casement')
    south=f.face(SOUTH,DEPTH,0,-1)
    south.rect(0,DEPTH-RADIUS,0,EAVE,-.25,0,PLASTER,'short south return beyond surveyed curve')
    south.rect(0,DEPTH-RADIUS,.015,.52,.003,.029,BASE,'south return | plinth')
    rear=f.face(NORTH,DEPTH,-1,0)
    rear.rect(0,NORTH-SOUTH,0,EAVE,-.24,0,PLASTER,'inner limit of the documented street segment')
    outline=Polygon([(NORTH,0),*corner(RADIUS,steps),(SOUTH,DEPTH),(NORTH,DEPTH)])
    horizontal(f,outline,10.06,10.22,ROOF,'street block roof')
    horizontal(f,outline,.001,.035,BASE,'floor slab')
    for z0,z1,projection,mat,label,split in [
        (3.56,3.62,.072,CEMENT,'string course undercut',False),
        (3.62,3.72,.125,CEMENT,'string course fascia',False),
        (3.72,3.80,.19,DENTIL,'projecting street floor belt',False),
        (9.91,9.97,.08,CEMENT,'eaves bed moulding',True),
        (10.07,10.15,.145,CEMENT,'eaves crown | lower',True),
        (10.15,10.23,.23,DENTIL,'eaves crown | upper',True),
        (10.23,10.29,.26,ROOF,'eaves weathering',True)]:
        floor_edge(f,z0,z1,projection,mat,label,steps,split)
    for a,b in [(TANGENT,-2.55),(2.28,NORTH)]:
        x=a+.08
        while x+.085 < b:
            f.rect(x,x+.088,9.96,10.073,.013,.115,DENTIL,'eaves | individual dentils')
            x+=.22
    for i in range(13):
        th=(i+.5)*pi/26
        u=TANGENT-RADIUS*sin(th);d=RADIUS-RADIUS*cos(th)
        face=f.face(u,d,cos(th),-sin(th))
        face.rect(-.044,.044,9.96,10.073,.004,.113,DENTIL,'curved cornice | individual dentils')
