"""Courtyard double stair of the former Guangci maternity pavilion.

Photo right is +X, the building is +Y and the brick upper front is Y=0.
The underside of the central deck meets the brick door wall at Z=3.55.
"""
from math import cos, hypot, pi, sin

from shapely.geometry import Polygon

TREAD = 'Guangci worn brown stone treads'
PALE = 'Guangci grey limestone handrail'
SHADE = 'Guangci recessed pier panels'
EDGE = 'Guangci projecting coping and tread arrises'
BED = 'Guangci court stair stone base'
BRICK = 'Guangci stair cheek red brick'
JOINT = 'Guangci stair brick mortar'

def _stone(rgb, roughness):
    def linear(v):
        s = v / 255
        return s / 12.92 if s <= .04045 else ((s + .055) / 1.055) ** 2.4
    return {'color': [linear(c) for c in rgb], 'roughness': roughness}

STAIR_PALETTE = {
    TREAD: _stone((168, 144, 116), .9),
    PALE: _stone((166, 164, 150), .86),
    SHADE: _stone((142, 140, 128), .9),
    EDGE: _stone((177, 174, 159), .83),
    BED: _stone((139, 135, 120), .94),
    BRICK: _stone((158, 96, 71), .89), JOINT: _stone((174, 137, 112), .91),
}

DECK = 3.80
DECK_UNDERSIDE = 3.55
FRONT = -3.18
TURN = 2.20
INSIDE_X = 8.81
OUTSIDE_X = 12.14
FOOT_Y = -6.25
BACK_Y = -.27
UPPER_END_X = 6.58
RAIL_HEIGHT = .99

def _block(b, center, size, material, name):
    b.box(center, size, material, label=name)

def _post(b, x, y, base, width, name, lod):
    # Rectangular body, raised foot and the broad, slightly stepped square cap.
    scale = (1.51 if base == DECK else 1.69) / 1.175
    for low, high, w, mat in ((0,.10,width+.085,BED),(.10,.19,width+.035,PALE),
                              (.19,1.035,width,PALE),(1.035,1.095,width+.045,PALE),
                              (1.095,1.175,width+.155,EDGE)):
        _block(b,(x,y,base+(low+high)*scale/2),(w,w,(high-low)*scale),mat,name)
    if not lod:
        # A shallow, framed panel on the courtyard face. The panel has a small
        # reveal relative to its four surrounding strips, as in the 2018 close view.
        panel_width=width*.59
        panel_height=.66*scale
        cy=y-width/2-.006
        _block(b,(x,cy,base+.625*scale),(panel_width,.016,panel_height),SHADE,name+' inset panel')
        for sx in (-1,1):
            _block(b,(x+sx*(panel_width+.03)/2,cy-.012,base+.625*scale),(.03,.035,panel_height+.06),PALE,name+' inset surround')
        for sz in (-1,1):
            _block(b,(x,cy-.012,base+.625*scale+sz*(panel_height+.03)/2),(panel_width,.035,.03),PALE,name+' inset surround')

def _axis(a, b):
    x,y=a
    dx,dy=b[0]-x,b[1]-y
    distance=hypot(dx,dy)
    ux,uy=dx/distance,dy/distance
    # Positive width points to the right when walking in the ascending direction.
    return distance,lambda u,z,w:(x+ux*u+uy*w,y+uy*u-ux*w,z)

def _flight(b, start, end, bottom, top, width, count, name, lod):
    run,mapper=_axis(start,end)
    delta=(top-bottom)/count
    going=run/count
    profile=[(0,bottom)]
    for i in range(count):
        height=bottom+(i+1)*delta
        profile.extend([(i*going,height),((i+1)*going,height)])
    # The stonework is supported down to courtyard level. No wedge intrudes
    # below the elevated deck's central ground-floor door.
    if bottom:
        profile.extend([(run,0),(0,0)])
    else:
        profile.append((run,0))
    b.prism(Polygon(profile),-width/2,width/2,mapper,TREAD,name+' stepped flight')
    if not lod:
        for i in range(count):
            a=i*going
            z=bottom+(i+1)*delta
            # Small rounded-over lip above each actual vertical stone riser.
            nosing=Polygon([(a-.027,z-.034),(a-.030,z-.012),(a-.018,z),(a+.018,z),(a+.018,z-.034)])
            b.prism(nosing,-width/2+.017,width/2-.017,mapper,EDGE,name+' tread noses')

def _rail_course(b, a, z0, c, z1, width, low, high, mat, name):
    run,mapper=_axis(a,c)
    section=Polygon([(0,z0+low),(run,z1+low),(run,z1+high),(0,z0+high)])
    b.prism(section,-width/2,width/2,mapper,mat,name)

def _baluster(b,x,y,z,name,lod):
    # Bottom plinth, convex lower body, thin neck, annular capital. The abacus
    # above the turned shaft remains square on both detail levels.
    stations=[(.18,.095),(.222,.095),(.245,.068),(.287,.071),(.350,.105),
              (.426,.125),(.481,.112),(.584,.066),(.643,.050),(.700,.049),
              (.729,.074),(.758,.070),(.783,.095),(.813,.095)]
    if lod:stations=[stations[i] for i in (0,2,5,8,10,13)]
    sides=6 if lod else 12
    verts=[(x+r*cos(2*pi*i/sides),y+r*sin(2*pi*i/sides),z+h*1.34)
           for h,r in stations for i in range(sides)]
    faces=[tuple(reversed(range(sides)))]
    for j in range(len(stations)-1):
        for i in range(sides):
            a=j*sides+i;c=j*sides+(i+1)%sides
            faces.append((a,c,c+sides,a+sides))
    faces.append(tuple(range(len(verts)-sides,len(verts))))
    b.add(verts,faces,PALE,name+' turned balusters')
    _block(b,(x,y,z+.163*1.34),(.224,.224,.062*1.34),EDGE,name+' square feet')
    _block(b,(x,y,z+.827*1.34),(.222,.222,.050*1.34),PALE,name+' square capitals')

def _railing(b,a,z0,c,z1,pieces,name,lod):
    run,point=_axis(a,c)
    for lo,hi,w,material,label in ((-.09,.097,.30,BED,' shoe'),(.097,.185,.33,PALE,' foot course'),
                                    (.80,.87,.278,PALE,' architrave'),(.87,.934,.313,PALE,' moulding'),
                                    (.934,RAIL_HEIGHT,.368,EDGE,' coping')):
        _rail_course(b,a,z0,c,z1,w,lo*1.34,hi*1.34,material,name+label)
    for i in range(pieces):
        t=(i+.5)/pieces;z=z0+t*(z1-z0)
        x,y,_=point(t*run,0,0)
        _baluster(b,x,y,z,name,lod)

def add_stairs(builder,lod):
    """Build the elevated deck, opposing L-shaped flights and open stone balustrades."""
    b=builder
    _block(b,(0,FRONT/2,(DECK+DECK_UNDERSIDE)/2),(2*UPPER_END_X,-FRONT,DECK-DECK_UNDERSIDE),TREAD,'Courtyard upper landing paving')
    _block(b,(0,FRONT-.040,DECK-.061),(2*UPPER_END_X+.06,.13,.122),EDGE,'Upper landing front nosing')
    posts=(-UPPER_END_X,-2.30,2.30,UPPER_END_X)
    for i,x in enumerate(posts):
        _post(b,x,FRONT,DECK,.60,'Upper landing panelled pier '+str(i+1),lod)
    for i,(left,right) in enumerate(zip(posts,posts[1:])):
        _railing(b,(left+.29,FRONT),DECK,(right-.29,FRONT),DECK,(9,10,9)[i],
                 'Upper landing front bay '+str(i+1),lod)
    for sign,side in ((-1,'Left'),(1,'Right')):
        center=(INSIDE_X+OUTSIDE_X)*.5
        depth=BACK_Y-FRONT
        width=OUTSIDE_X-INSIDE_X
        name=side+' courtyard stair'
        _flight(b,(sign*center,FOOT_Y),(sign*center,FRONT),0,TURN,width,12,name+' lower',lod)
        _block(b,(sign*center,(FRONT+BACK_Y)/2,TURN/2),(width,depth,TURN),TREAD,name+' quarter landing')
        _flight(b,(sign*INSIDE_X,(BACK_Y+FRONT)/2),(sign*UPPER_END_X,(BACK_Y+FRONT)/2),
                TURN,DECK,depth,9,name+' upper',lod)
        # A brick cheek below the sloping courtyard fascia. The masonry stops
        # at the outside upper pier and keeps the lower central door clear.
        end_z=DECK-.075
        cheek=Polygon([(0,.02),(INSIDE_X-UPPER_END_X,.02),(INSIDE_X-UPPER_END_X,TURN-.075),(0,end_z)])
        def cheek_point(u,z,d):
            return sign*(UPPER_END_X+u),FRONT-sign*d,z
        low,high=(0,.045) if sign>0 else (-.045,0)
        b.prism(cheek,low,high,cheek_point,BRICK,name+' brick stair cheek')
        if not lod:
            for course in range(2,int(end_z/.065)):
                z=course*.065
                reach=min(INSIDE_X-UPPER_END_X,(end_z-z)*(INSIDE_X-UPPER_END_X)/(DECK-TURN))
                if reach>.045:
                    _block(b,(sign*(UPPER_END_X+reach/2),FRONT-.047,z),(reach,.008,.006),JOINT,name+' cheek mortar courses')
        for xpos in (INSIDE_X,OUTSIDE_X):
            _post(b,sign*xpos,FOOT_Y,0,.49,name+(' inner' if xpos==INSIDE_X else ' outer')+' foot pier',lod)
            _railing(b,(sign*xpos,FOOT_Y+.23),.13,(sign*xpos,FRONT),TURN,10,
                     name+(' inner' if xpos==INSIDE_X else ' outer')+' sloping rail',lod)
        _railing(b,(sign*INSIDE_X,FRONT),TURN,(sign*(UPPER_END_X+.29),FRONT),DECK-.12,5,
                 name+' upper turned rail',lod)
        # The outer edge of the middle landing turns back toward the facade;
        # the short transverse rail is visible behind the lower flight.
        _railing(b,(sign*OUTSIDE_X,FRONT),TURN,(sign*OUTSIDE_X,BACK_Y),TURN,6,
                 name+' outer landing rail',lod)
        _railing(b,(sign*(OUTSIDE_X-.04),BACK_Y),TURN,(sign*INSIDE_X,BACK_Y),TURN,7,
                 name+' back landing rail',lod)
