"""Sun Garden's tiled Huashan Road arch, measured from two viewpoints in 2015."""
from math import cos, sin, pi, ceil
from pathlib import Path
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

WALL='Ochre lime render and bamboo marks'
SOFFIT='Ochre vault and window reveals'
BAND='Pale cement eave moulding'
SHADE='Weathered eave recess'
TILE='Weathered grey clay tiles'
TILE2='Warm grey fired clay tiles'
IRON='Dark iron window bars'
GREEN='Green street number'
TYPE='Pale lettering'
PAVER='Grey entry threshold'
BRONZE='Weathered metal plaque'
LEAF='Bamboo leaf half-tones'
PALETTE={key:{'color':rgb,'roughness':rough} for key,rgb,rough in [
    (WALL,[.80,.735,.586],.93),(SOFFIT,[.705,.622,.480],.95),
    (BAND,[.663,.618,.530],.91),(SHADE,[.35,.319,.266],.90),
    (TILE,[.286,.273,.235],.93),(TILE2,[.337,.298,.258],.93),
    (IRON,[.123,.130,.119],.73),(GREEN,[.086,.306,.233],.74),
    (TYPE,[.845,.856,.725],.79),(PAVER,[.574,.557,.516],.96),
    (BRONZE,[.417,.420,.388],.84),(LEAF,[.69,.631,.504],.93)]}
WIDTH=4.114
SPRING=1.88
CROWN=3.13
DEPTH=1.475
TOP=4.36
RIDGE_HALF=3.00
SIDE=4.54
WINDOWS=((-3.54,1.61,.53,.91),(3.50,1.60,.50,.88))

def hex_window(x,z,width,height):
    return Polygon([(x,z+height/2),(x+width/2,z+height*.224),(x+width/2,z-height*.224),
                    (x,z-height/2),(x-width/2,z-height*.224),(x-width/2,z+height*.224)])

def wing_outline():
    # The caps retreat into two curved shoulders, above the narrow side walls.
    rim=[]
    for sign in (1,-1):
        wing=[(sign*SIDE,2.83),(sign*3.77,2.83)]
        for step in range(13):
            a=-pi/2-pi/2*step/12
            wing.append((sign*(3.77+.78*cos(a)),3.61+.78*sin(a)))
        wing.append((sign*RIDGE_HALF,4.015))
        rim.extend(wing if sign==1 else reversed(wing))
    return Polygon([(-SIDE,.0),(SIDE,.0),*rim])

def roof_tile(builder,name,x,y,radius,length,z,direction,far,index):
    segments=5 if far else 9
    vertices=[]
    for offset in (0,length):
        for rad in (radius,radius-.015):
            for i in range(segments+1):
                theta=pi*i/segments
                vertices.append((x+rad*cos(theta),y+direction*offset,z-.22*offset+rad*sin(theta)))
    count=segments+1
    faces=[]
    for i in range(segments):
        for a,b in ((0,2*count),(3*count,count),(count,0),(2*count,3*count)):
            faces.append((a+i,a+i+1,b+i+1,b+i))
    faces.append((0,2*count,3*count,count))
    i=segments
    faces.append((count+i,3*count+i,2*count+i,i))
    if direction>0:faces=[tuple(reversed(face)) for face in faces]
    builder.add(vertices,faces,TILE if index%5!=2 else TILE2,name)

def drip_tiles(builder,label,left,right,z):
    n=round((right-left)/.175);dx=(right-left)/n;front=-.145;back=DEPTH+.12
    for idx in range(n):
        x=left+(idx+.5)*dx;middle=(front+back)/2
        for direction in (-1,1):
            for j in range(3):
                y=middle+direction*(back-front)*j/6
                length=(back-front)/6-.004
                roof_tile(builder,label,x,y,dx*.526,length,z-.22*abs(y-middle),direction,builder.gate_far,idx+j)

def leaf_relief(builder,face,far):
    from bamboo_plaster import pattern, WIDTH as TW, HEIGHT as TH
    vertices=[];faces=[]
    for _,leaves in pattern():
        for i,(leaf,color) in enumerate(leaves):
            if far and i%3:continue
            section=[(u*2*SIDE/TW-SIDE,(1-v/TH)*4.20)for u,v in leaf]
            polygon=Polygon(section)
            if not face.covers(polygon):continue
            if not polygon.exterior.is_ccw:section.reverse()
            n=len(vertices);vertices.extend([(x,-.0017,z)for x,z in section]);cx,cz=polygon.centroid.coords[0];vertices.append((cx,-.0038,cz))
            faces.extend([(n+i,n+(i+1)%4,n+4)for i in range(4)])
    if faces:builder.add(vertices,faces,LEAF,'Low bamboo-shaped plaster relief')

def number(f):
    x,z=2.73,1.833
    f.box(x,z,.315,.247,.031,.023,GREEN,'831 enamel plate')
    digits={'8':[(.34,.50),(.05,.49),(-.30,.36),(-.30,.21),(.27,-.15),(.25,-.39),(.04,-.5),(-.28,-.38),(-.27,-.17),(.30,.18),(.28,.39),(.06,.49)],
            '3':[(-.27,.38),(.00,.50),(.30,.37),(.28,.17),(.04,.02),(-.06,.01),(.19,-.04),(.3,-.21),(.25,-.42),(-.02,-.50),(-.29,-.36)],
            '1':[(-.24,.27),(.10,.48),(.10,-.48)]}
    for i,k in enumerate('831'):
        axis=x+(i-1)*.080
        curve=[(axis+xx*.081,z+zz*.147) for xx,zz in digits[k]]
        f.prism(LineString(curve).buffer(.0064,cap_style=2,join_style=2),.040,.044,TYPE,'Enamel number '+k)
    f.box(x,z-.46,.49,.49,.024,.018,BRONZE,'Rectangular heritage plaque')

def add_building(b,far):
    b.gate_far=far
    f=Facade(b,(-SIDE,0),(SIDE,0),'Street-facing gate')
    shape=wing_outline();void=opening(0,-.05,WIDTH,CROWN+.05,CROWN-SPRING,26 if far else 56)
    lights=[hex_window(*win)for win in WINDOWS];wall=shape.difference(unary_union([void,*lights]));
    # Two narrow exterior openings pierce the side wall, while the central arch has a deep vault.
    central=wall.intersection(box(-RIDGE_HALF,-.1,RIDGE_HALF,TOP));wings=wall.difference(box(-RIDGE_HALF,-.1,RIDGE_HALF,TOP))
    f.prism(central,-DEPTH,-.037,SOFFIT,'Deep arch and soffit');f.prism(wings,-.37,-.037,SOFFIT,'Wing window reveals')
    f.prism(wall,-.037,0.,WALL,'Continuous bamboo-plaster face');f.prism(central,-DEPTH-.02,-DEPTH,WALL,'Courtyard face')
    for hole in lights:
        xmin,zmin,xmax,zmax=hole.bounds
        strokes=[]
        for z1,z2 in [(zmin,zmax),(zmax,zmin)]:
            q=LineString([(xmin-.15,z1-.15*(1 if z2>z1 else -1)),(xmax+.15,z2+.15*(1 if z2>z1 else -1))]).buffer(.014,cap_style=2).intersection(hole)
            strokes.append(q)
        f.prism(unary_union(strokes),-.133,-.103,IRON,'Crossed iron hexagonal lights')
    for z,height,projection,mat,label in [(4.010,.071,.057,SHADE,'Dark underside'),(4.080,.069,.097,BAND,'Front lower fascia'),(4.156,.083,.133,BAND,'Upper projecting band')]:
        f.box(0,z,RIDGE_HALF*2+.12,height,projection+.065,projection/2-.032,mat,label)
    # The two visible intensity transects both show 27 troughs inside the crop.
    n=29;pitch=RIDGE_HALF*2/n
    for i in range(n):
        x=-RIDGE_HALF+(i+.5)*pitch
        scallop=opening(x,3.890,pitch*.82,.131,.072,7 if far else 12)
        block=box(x-pitch/2,3.929,x+pitch/2,4.011).difference(scallop)
        f.prism(block,-.018,.052,BAND,'Front scalloped eave band')
    b.prism(box(-RIDGE_HALF-.08,-.145,RIDGE_HALF+.08,DEPTH+.12),-.056,0,
            lambda x,y,d:(x,y,TOP-.08-.22*abs(y-(DEPTH-.025)/2)+d),TILE2,'Central tiled cap bed')
    drip_tiles(b,'Overlapping half-round grey roof tiles',-RIDGE_HALF-.08,RIDGE_HALF+.08,TOP-.072)
    for sign in (-1,1):
        x0,x1=sorted((sign*3.78,sign*SIDE)); f.box((x0+x1)/2,2.863,x1-x0,.064,.465,-.143,BAND,'Lower wall coping')
        count=round((x1-x0)/.175);step=(x1-x0)/count
        for i in range(count):roof_tile(b,'Lower wing tile',x0+(i+.5)*step,.17,step*.53,.397,2.949,-1,far,i)
    b.box((0,DEPTH/2,.018),(WIDTH+.04,DEPTH+.02,.036),PAVER,label='Archway paving')
    number(f)
    leaf_relief(b,wall,far)
    tex=Path(__file__).with_name('bamboo-plaster.png');b.palette[WALL]['texture']=str(tex)
    for part in b.parts:
        if part['material']==WALL:
            part['texcoords']=[[(x+SIDE)/(2*SIDE),1-z/4.20]for x,y,z in part['vertices']]
