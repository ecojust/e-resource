"""Brick corner tower above the southeast corner of the former Shanghai–Nanking Railway offices."""
from math import cos, pi, sin

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade, opening

BRICK = 'red stock brick'
ARCH = 'red arch voussoirs'
FADED = 'weathered ochre upper bricks'
PATCH = 'warm rose fired upper bricks'
JOINT = 'brick course shadow'
CORNICE = 'weathered projecting brick cornice'
GLASS = 'old blue grey glazing'
SASH = 'painted deep red sash'
IRON = 'dark wrought iron'
RECESS = 'deep opening shadow'
ROOF = 'dark roof coping'
CUT = 'study section'
PALETTE = {
    key: {'color': rgb, 'roughness': rough}
    for key, rgb, rough in [
        (BRICK, [.56,.25,.17], .94), (ARCH,[.65,.31,.20],.9), (JOINT,[.42,.235,.18],.97),
        (FADED,[.59,.39,.29],.95),(PATCH,[.52,.28,.20],.94),
        (CORNICE,[.36,.23,.19],.94), (GLASS,[.32,.41,.42],.32), (SASH,[.37,.19,.13],.78),
        (IRON,[.16,.15,.14],.65), (RECESS,[.17,.115,.095],.95), (ROOF,[.21,.19,.18],.91),
        (CUT,[.39,.26,.22],.96),
    ]
}
# The building lies to the north and west of the chamfer. South and east
# are the two visible street-facing sides. The other two walls close the study.
GROUND = Polygon([(-3.4,0),(-.94,0),(0,.94),(0,3.4),(-3.4,3.4)])


def slab(builder, plan, bottom, top, material, name):
    builder.prism(plan, bottom, top, lambda x,y,z:(x,y,z), material, name)


def facade_edges(builder, plan, name):
    points=list(plan.exterior.coords)
    if not plan.exterior.is_ccw:
        points.reverse()
    edges=[]
    for a,b in zip(points,points[1:]):
        if abs(a[1]-b[1])<1e-6 and a[1]<1: kind='south'
        elif abs(a[0]-b[0])<1e-6 and a[0]>-1: kind='east'
        elif abs(a[0]-b[0])>.0001 and abs(a[1]-b[1])>.0001: kind='chamfer'
        else: kind='section'
        edges.append((kind,Facade(builder,a,b,name+' '+kind)))
    return edges


def balcony(f, lod):
    width=1.68
    f.box(0,.62,width+.22,.14,.69,.29,CORNICE,'balcony slab')
    for sign in [-1,1]:
        u=sign*.58
        f.prism(Polygon([(u-.085,.06),(u+.085,.06),(u+.15,.54),(u-.15,.54)]),.055,.44,CORNICE,'balcony corbel')
    for z in [.75,1.10]:
        f.box(0,z,width,.035,.04,.61,IRON,'front handrail')
        for side in [-1,1]:f.box(side*width/2,z,.034,.036,.59,.33,IRON,'return handrail')
    for i in range(9):
        x=width*(i/8-.5)
        f.box(x,.92,.026,.36,.03,.61,IRON,'front railing baluster')
        if not lod and i<8:
            end=x+width/8
            f.builder.tube([f.point(x+.012,.80,.61),f.point((x+end)/2,.995,.61),f.point(end-.012,.80,.61)],.013,IRON,5,'balcony iron chevron')
    if not lod:
        for side in [-1,1]:
            for t in [.18,.35,.51]: f.box(side*width/2,.92,.031,.35,.031,t,IRON,'return railing baluster')


def lower_wall(f, kind, lod):
    detail=kind in ('south','east')
    hole=opening(0,.65,1.36,2.10,.69,segments=12 if lod else 28)
    wall=box(-f.length/2,0,f.length/2,3.25)
    if kind=='section':
        f.prism(wall,-.18,0,CUT,'rear cut face')
        return
    f.prism(wall.difference(hole) if detail else wall,-.21,0,BRICK,'red brick face')
    if detail:
        f.prism(hole,-.42,-.40,RECESS,'deep arch backing')
        outer=opening(0,.65,1.68,2.26,.84,segments=12 if lod else 28)
        arch=outer.difference(hole)
        f.prism(arch,-.03,.065,ARCH,'arched brick reveal')
        if not lod:
            # Radial mortar joints survive in the head of each arch.
            spring=.65+2.10-.69
            for j in range(17):
                t=pi*j/16
                f.builder.tube([f.point(.69*cos(t),spring+.69*sin(t),.069),
                                f.point(.82*cos(t),spring+.82*sin(t),.069)],.010,JOINT,4,'radial arch joint')
        balcony(f,lod)
    if not lod:
        for row in range(1,23):
            z=row*.138
            strips=box(-f.length/2+.012,z,f.length/2-.012,z+.009).difference(hole.buffer(.15) if detail else Polygon())
            if not strips.is_empty:f.prism(strips,.001,.006,JOINT,'fine brick bed joint')
        # Overly long cross-bed lines on the blank chamfer would turn it into a grid.
        if kind=='chamfer':
            for z in [.25,.52,.80,1.08,1.35,1.63,1.91,2.18,2.47,2.75,3.02]:
                f.box(.18 if int(z*10)%2 else -.19,z,.012,.12,.016,.008,JOINT,'staggered chamfer joints')


def upper_brick_patches(f, kind, holes, lod):
    # Discontinuous fired red rectangles follow the weathered lighter masonry photographed in 2015.
    void=unary_union(holes).buffer(.055) if holes else Polygon()
    for course in range(2,15):
        z=3.46+course*.133
        for bond in range(-6,7):
            x=(bond+(course%2)*.5)*.245
            if abs(x)+.117>f.length/2-.025:continue
            index=(course*11+bond*17+(3 if kind=='south' else 7))%19
            if index>(3 if lod else 8): continue
            piece=box(x-.113,z-.051,x+.113,z+.051).difference(void)
            if not piece.is_empty:f.prism(piece,.001,.007,PATCH if index%3 else BRICK,'individual weathered red bricks')


def lantern_wall(f, kind, lod):
    field=box(-f.length/2,3.47,f.length/2,5.53)
    if kind=='section':
        f.prism(field,-.16,0,CUT,'rear cut face')
        return
    if kind=='chamfer':
        f.prism(field,-.16,0,FADED,'blank upper corner panel')
        upper_brick_patches(f,kind,[],lod)
        f.box(0,4.66,.105,1.21,.07,.04,ARCH,'slender brick panel ornament')
        f.box(0,5.26,.16,.074,.08,.05,ARCH,'raised ornament cap')
        return
    centers=[-.415,.415];holes=[opening(u,3.77,.63,.83)for u in centers]
    f.prism(field.difference(unary_union(holes)),-.17,0,FADED,'pierced upper brick wall')
    upper_brick_patches(f,kind,holes,lod)
    for u,hole in zip(centers,holes):
        f.prism(hole,-.155,-.14,GLASS,'rectangular paired light')
        f.prism(hole.buffer(.057,join_style=2).difference(hole),-.025,.046,SASH,'window frame')
        f.box(u,4.18,.64,.041,.03,-.095,SASH,'horizontal sash')
        if not lod:f.box(u,4.18,.026,.85,.032,-.096,SASH,'vertical sash')
    f.box(0,5.13,f.length-.20,.069,.075,.035,ARCH,'upper brick lintel line')


def add_building(builder,lod):
    for kind,f in facade_edges(builder,GROUND,'arched storey'):lower_wall(f,kind,lod)
    slab(builder,GROUND,0,.11,CUT,'underside study closure')
    slab(builder,GROUND,3.05,3.16,BRICK,'arch crown masonry')
    upper=GROUND.buffer(-.16,join_style=2)
    # Individual projecting courses are continuous through the three visible faces.
    for lo,hi,pad,mat in [(1.81,1.90,.044,CORNICE),(3.16,3.25,.09,ARCH),
                          (3.25,3.36,.18,CORNICE),(3.36,3.47,.25,ROOF)]:
        if lo==1.81:
            for kind,f in facade_edges(builder,GROUND,'belt'):
                if kind=='chamfer':f.box(0,(lo+hi)/2,f.length+.018,hi-lo,.068,.031,CORNICE,'continuous brick string on pier')
                if kind in ('south','east'):
                    length=(f.length-1.67)/2
                    for side in [-1,1]:f.box(side*(f.length-length)/2,(lo+hi)/2,length,hi-lo,.065,.030,CORNICE,'brick string terminating at arch')
        else:slab(builder,GROUND.buffer(pad,join_style=2),lo,hi,mat,'belt cornice course')
    for kind,f in facade_edges(builder,upper,'lantern'):lantern_wall(f,kind,lod)
    for lo,hi,pad,mat in [(5.49,5.55,.045,ARCH),(5.55,5.64,.10,CORNICE),(5.64,5.76,.18,ROOF)]:
        slab(builder,upper.buffer(pad,join_style=2),lo,hi,mat,'lantern coping')
