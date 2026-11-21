"""Reconstruct the five round arches visible in two Yangpu District photographs."""
from math import sin, cos, pi
from pathlib import Path
import json
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import affinity

STONE='pale grey ashlar'
DARKSTONE='grey stone course'
RING='dressed arch face'
WEATHERED='weathered arch stone'
FINE='cool grey ashlar'
PATINA='inscription mounting and dark edge'
BEAD='raised arch edging'
JOINT='dark joints'
SHADOW='porch interior stone'
DOOR='patinated door frames'
GLASS='deep green glazing'
GRILLE='stone window grille'
TEXT='aged metal inscription'
FLOOR='stone porch floor'
PALETTE={name:dict(color=color,roughness=roughness) for name,color,roughness in [
    (STONE,[.50,.476,.421],.94),(DARKSTONE,[.383,.374,.347],.94),
    (WEATHERED,[.505,.491,.453],.92),(FINE,[.468,.460,.430],.91),(PATINA,[.14,.16,.157],.71),(RING,[.591,.564,.509],.92),(BEAD,[.654,.624,.558],.87),
    (JOINT,[.243,.235,.208],.96),(SHADOW,[.242,.248,.211],.95),
    (DOOR,[.043,.062,.055],.68),(GLASS,[.071,.105,.091],.4),
    (GRILLE,[.354,.376,.325],.93),(TEXT,[.71,.708,.675],.70),
    (FLOOR,[.435,.402,.342],.94)]}
BAYS=[-5.04,-2.52,0.,2.52,5.04]
PIERS=[-6.30,-3.78,-1.26,1.26,3.78,6.30]
SPRING=2.04
INNER=.98
OUTER=1.26
def block(b,x0,x1,y0,y1,z0,z1,material,name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=name)

def face(b,geom,front,back,material,name):
    if geom.is_empty:return
    for poly in getattr(geom,'geoms',[geom]):
        if poly.geom_type=='Polygon' and poly.area>1e-7:
            b.prism(poly,-back,-front,lambda x,z,t:(x,-t,z),material,label=name)

def pt(x,r,a):
    return (x+r*cos(a),SPRING+r*sin(a))

def sector(x,outer,inner,a0,a1,n):
    angles=[a0+(a1-a0)*i/n for i in range(n+1)]
    return Polygon([pt(x,outer,a) for a in angles]+[pt(x,inner,a) for a in reversed(angles)])

def void(x,r,segments):
    arc=[pt(x,r,pi*i/segments) for i in range(segments+1)]
    return Polygon([(x-r,-1.),(x+r,-1.),*arc])

def model(b,lod=False):
    steps=22 if lod else 55
    openings=unary_union([void(x,INNER,steps)for x in BAYS])
    strip=box(-6.62,.052,6.62,4.24)
    # Both arch faces have a void extending all the way to the porch floor.
    face(b,strip.difference(openings),.045,.58,JOINT,'Five openings through the street wall')
    arches=unary_union([void(x,OUTER,steps)for x in BAYS])
    for row in range(10):
        low=.055+row*.427
        if low>=4.24:break
        step=1.20 if row%2 else 1.33
        xs=[-6.62]+[i*step+.33*(row%2) for i in range(-8,9) if -6.56<i*step+.33*(row%2)<6.56]+[6.62]
        for col,(left,right) in enumerate(zip(xs,xs[1:])):
            panel=box(left+.003,low+.004,right-.003,min(4.24,low+.423)).difference(arches)
            mat=DARKSTONE if low>3.44 else FINE if (row+2*col)%5<2 else STONE
            face(b,panel,.023,.050,mat,'Horizontal jointed ashlar')
    for i,x in enumerate(BAYS):
        for k in range(11):
            a0=k*pi/11+.0035;a1=(k+1)*pi/11-.0035
            tone=WEATHERED if (k+2*i)%5 in (1,4) else RING
            face(b,sector(x,OUTER-.034,INNER,a0,a1,2 if lod else 5),-.012,.10,tone,'Eleven stone voussoirs per opening')
        face(b,sector(x,OUTER,OUTER-.039,0,pi,steps),-.040,.045,BEAD,'Projecting semicircular hood')
        # Dark recessed returns can be seen from the oblique photograph direction.
        face(b,sector(x,INNER+.022,INNER-.008,0,pi,steps),.077,.584,SHADOW,'Vaulted soffit in each opening')
    for x in PIERS:
        for j in range(4):
            block(b,x-.232,x+.232,-.012,.577,.080+j*.504,.079+(j+1)*.504,STONE,'Squared pier shaft courses')
        block(b,x-.278,x+.278,-.054,.595,.053,.625,DARKSTONE,'Stone pier base')
        block(b,x-.265,x+.265,-.065,.598,.626,.689,RING,'Base cap')
        block(b,x-.31,x+.31,-.080,.61,1.376,1.636,STONE,'Projecting waist band')
        block(b,x-.269,x+.269,-.025,.585,1.643,2.042,STONE,'Pier above waist band')
    block(b,-6.64,6.64,-.065,.63,4.235,4.33,DARKSTONE,'Horizontal coping')
    block(b,-6.62,6.62,.575,1.82,3.756,4.235,SHADOW,'Arcade ceiling')
    block(b,-6.64,6.64,-.30,1.84,0.,.052,FLOOR,'Threshold and arcade floor')
    # Set-back glazed door sets occupy the three centre openings.
    for x in BAYS[1:4]:
        block(b,x-1.264,x-.932,1.73,1.82,.054,3.76,SHADOW,'Wall beside recessed doorway')
        block(b,x+.932,x+1.264,1.73,1.82,.054,3.76,SHADOW,'Wall beside recessed doorway')
        block(b,x-.934,x+.934,1.73,1.82,2.90,3.76,SHADOW,'Door head backing')
        block(b,x-.937,x+.937,1.686,1.74,.055,2.90,GLASS,'Recessed entrance glazing')
        for dx in (-.916,0.,.916):
            block(b,x+dx-.024,x+dx+.024,1.633,1.69,.057,2.90,DOOR,'Paired door stiles')
        for z in (.118,1.238,2.133,2.755,2.874):
            block(b,x-.935,x+.935,1.637,1.69,z-.024,z+.024,DOOR,'Rails and rectangular transom')
        for dx in (-.43,.43):
            block(b,x+dx-.014,x+dx+.014,1.650,1.69,2.15,2.88,DOOR,'Transom glazing bars')
    for x in (BAYS[0],BAYS[-1]):
        window=box(x-.414,1.43,x+.414,2.70)
        panel=box(x-1.27,.052,x+1.27,3.76)
        face(b,panel.difference(window),1.72,1.82,SHADOW,'Back wall of end bay')
        face(b,window,1.79,1.82,GLASS,'Glazing behind diamond grille')
        for z in (1.61,2.17,2.73):
            diamond=Polygon([(x,z-.28),(x+.28,z),(x,z+.28),(x-.28,z)])
            strokes=diamond.boundary.buffer(.038,join_style=2,cap_style=2).intersection(window)
            face(b,strokes,1.657,1.725,GRILLE,'Diamond lattice at outer bays')
    for side in (-1,1):
        x=side*6.51
        block(b,x-.11,x+.11,.576,1.82,.054,3.756,SHADOW,'Porch end return')
    # Typeset approximation of the photographed three-character inscription.
    for letter in json.loads(Path(__file__).with_name('inscription.json').read_text()):
        for shell,*holes in letter['polygons']:
            # The type source is finer than the stone face and must retain its counters.
            glyph=Polygon(shell,holes)
            if lod:glyph=glyph.simplify(.0028,preserve_topology=True)
            face(b,affinity.translate(glyph,xoff=.012,yoff=-.016),.002,.025,PATINA,'Inscription relief edge')
            face(b,glyph,-.027,.006,TEXT,'Inscription '+letter['text'])
