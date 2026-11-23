"""Stepped upper street elevation and street-facing roof slopes seen behind the shuttered wing."""
import json
from math import cos,pi,sin
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

from materials import ASHLAR,BASE,DEEP,EAVE,GLASS,PALE,RIDGE,ROOF,SHADE,TRIM,WOOD
from photo_plane import hit,opening
from street_front import slab
from hipped_tiles import tile_roof

SURVEY=json.loads((Path(__file__).resolve().parents[1]/'measurements/rear-elevation-observations.json').read_text())
SECTION=2.30

def footprint(row):
    depth=row['d']
    a=hit(*row['left_jamb'],depth)[0]
    b=hit(*row['right_jamb'],depth)[0]
    return a,b,hit(*row['eave'],depth)[1],hit(*row['belt'],depth)[1]

def cutout(row,depth):
    return opening(*row['corners'],d=depth)

def window(f,row,hole):
    a,z,b,top=hole.bounds
    name='rear window | '+row['id']
    f.solid(hole,-.163,-.148,DEEP,name+' | dark reveal back')
    f.solid(hole.buffer(-.047,join_style=2),-.146,-.136,GLASS,name+' | recessed glazing')
    f.solid(hole.difference(hole.buffer(-.049,join_style=2)),-.147,-.097,WOOD,name+' | dark casement perimeter')
    vbars,hbars=row['bars']
    for t in vbars:
        u=a+(b-a)*t
        f.rect(u-.023,u+.023,z+.031,top-.031,-.133,-.091,WOOD,name+' | meeting stile')
    for t in hbars:
        h=top-(top-z)*t
        f.rect(a+.035,b-.035,h-.019,h+.019,-.136,-.101,WOOD,name+' | glazing rail')
    edge=.080
    trim=hole.buffer(edge,join_style=2).difference(hole)
    f.solid(trim,-.024,.061,TRIM,name+' | white window surround')
    f.rect(a-.104,b+.104,z-.084,z-.041,.004,.097,PALE,name+' | sill nose')
    if row.get('partial'):
        return
    for x,h0,h1,t,mat in [(.106,.058,.100,.09,TRIM),(.144,.100,.132,.137,SHADE),(.158,.132,.168,.16,PALE)]:
        f.rect(a-x,b+x,top+h0,top+h1,-.008,t,mat,name+' | projecting lintel')
    if row['id']=='low-narrow-upper':
        w=b-a;c=(a+b)/2
        outline=Polygon([(a-.105,z-.066),(b+.105,z-.066),(b+.105,z-.185),(c+.29*w,z-.185),
                         (c+.29*w,z-.312),(c-.29*w,z-.312),(c-.29*w,z-.185),(a-.105,z-.185)])
        f.solid(outline,.003,.084,PALE,name+' | stepped sill apron')
        f.rect(a-.073,b+.073,z-.113,z-.099,.084,.089,SHADE,name+' | apron groove')
        for direction in [-1,1]:
            pts=[]
            for j in range(17):
                ang=j*2.05*pi/16;r=.088-.066*j/16
                pts.append((c+direction*(.062+r*cos(ang)),-.090,z-.194+r*.58*sin(ang)))
            f.rail(pts,.010,TRIM,name+' | small apron curls',6)

def roof(f,a,b,top,lod,label):
    # The model only follows the shallow red roof plane visible from the street.
    overhang=.40
    x0,x1=a-.28,b+.28
    p0,p1=-overhang,SECTION
    for low,high,p,mat,name in [(-.098,-.027,.19,TRIM,'plaster bed'),(-.027,.024,.32,EAVE,'shadowed soffit'),(.024,.103,overhang,EAVE,'dark fascia')]:
        slab(f,box(x0,-p,x1,SECTION),top+low,top+high,mat,label+' | '+name)
    # A fit to the upper and lower red silhouette at 39 unoccluded columns constrains these planes.
    add,slope,hip=(.131,.591,1.105) if label=='upper low wing' else (.251,.601,1.172)
    slab(f,box(x0,-overhang,x1,SECTION),top+.103,top+.133+add,EAVE,label+' | fascia behind tile edge')
    tile_roof(f,x0,x1,p0,p1,top+.138+add,slope,hip,lod,label)

def band(f,a,b,z,label):
    for h0,h1,p,m in [(-.105,-.059,.08,TRIM),(.016,.055,.095,PALE),(.055,.122,.142,TRIM)]:
        f.rect(a-.048,b+.048,z+h0,z+h1,.006,p,m,label+' | floor belt')
    x=a+.115
    while x+.062<b:
        shape=Polygon([(x-.070,z+.016),(x+.070,z+.016),(x+.047,z-.035),(x+.012,z-.052),(x-.026,z-.052),(x-.055,z-.029)])
        f.solid(shape,.008,.080,PALE,label+' | pendant floor frieze')
        x+=.256

def add_rear_elevation(f,lod):
    for record in SURVEY['wings']:
        key,d=record['key'],record['d'];label='upper '+key+' wing'
        a,b,top,belt=footprint(record)
        front=f.face(0,d,1,0)
        rows=[r for r in SURVEY['openings'] if r['wing']==key]
        holes=[cutout(row,d) for row in rows]
        front.solid(box(a,0,b,top).difference(unary_union(holes)),-.18,0,ASHLAR,label+' | ruled plaster with apertures')
        for row,hole in zip(rows,holes):
            window(front,row,hole)
        band(front,a,b,belt,label)
        for end,origin,ydir in [(a,SECTION,-1),(b,0,1)]:
            side=front.face(end,origin,0,ydir)
            side.rect(0,SECTION,0,top,-.136,0,ASHLAR,label+' | shallow return')
        front.face(b,SECTION,-1,0).rect(0,b-a,0,top,-.14,0,BASE,label+' | rear cut plane')
        slab(front,box(a,0,b,SECTION),.003,.030,BASE,label+' | sectional base')
        roof(front,a,b,top,lod,label)
