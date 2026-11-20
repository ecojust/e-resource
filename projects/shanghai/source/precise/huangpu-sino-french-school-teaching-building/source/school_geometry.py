"""Three-storey teaching block of the Franco-Chinese School, viewed from its court."""
from math import cos, pi, sin
from pathlib import Path

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering

BRICK = 'rose red facing brick'
STONE = 'warm ivory rendered stone'
FRAME = 'dark stained window joinery'
GLASS = 'grey green glass'
RAIL = 'dark red gallery ironwork'
PAVING = 'grey terrazzo gallery'
ROOF = 'charcoal waterproofed roof'
GOLD = 'gilded school name'
PALETTE = {
    BRICK: dict(color=[.472, .181, .126], roughness=.95),
    STONE: dict(color=[.802, .755, .662], roughness=.83),
    FRAME: dict(color=[.106, .075, .065], roughness=.75),
    GLASS: dict(color=[.117, .159, .151], roughness=.35, metallic=.14),
    RAIL: dict(color=[.220, .099, .075], roughness=.66, metallic=.38),
    PAVING: dict(color=[.434, .426, .389], roughness=.87),
    ROOF: dict(color=[.166, .170, .158], roughness=.94),
    GOLD: dict(color=[.715, .452, .142], roughness=.49, metallic=.52),
}
# Each point is the frozen footprint projected onto the courtyard frame. The
# footprint remains asymmetric about the central bay, as seen on the ground.
PLAN = [
    (-42.43, .37), (-35.14, 0), (-34.03, 9.79), (-14.65, 9.41),
    (-14.37, .05), (14.37, -.05), (13.43, 10.23), (34.65, 10.05),
    (35.14, 0), (42.43, -.37), (40.85, 24.08), (-18.92, 24.32), (-41.51, 24.08)
]
FLOORS = (0., 4.72, 9.34)
CORNICE = 14.24
GALLERY_DEPTH = 2.52
FONT = Path(__file__).with_name('fonts') / 'GuangmingSchoolPlaque.otf'


def light(facade, shape, low, label):
    """A glazed recess in the wall, including its frame and upper transom."""
    left, bottom, right, top = shape.bounds
    cx = (left + right) / 2
    frame = shape.difference(shape.buffer(-.075, join_style='mitre'))
    bars = [frame, box(cx-.035, bottom, cx+.035, top),
            box(left, top-.68, right, top-.62)]
    if not low:
        bars.append(box(left, (top+bottom)/2-.025, right, (top+bottom)/2+.025))
    facade.prism(shape.buffer(.012, join_style='mitre'), -.33, -.30, GLASS, label+' glazing')
    facade.prism(shape.intersection(unary_union(bars)), -.28, -.202, FRAME, label+' timber')


def circular_head(u, z, width, height, top, low):
    return opening(u, z, width, height, width*.43 if top else 0, 8 if low else 20)


def corner_trim(f, u, low):
    f.box(u, CORNICE/2, .48, CORNICE, .23, .085, STONE, 'continuous ivory pilaster')
    for z, width, height, depth in [(.36,.67,.72,.35),(13.78,.66,.42,.31),(14.12,.82,.18,.42)]:
        f.box(u,z,width,height,depth,.11,STONE,'pilaster base and cap')
    if not low:
        f.box(u,7.02,.24,12.70,.072,.224,STONE,'pilaster face')


def cornice(f, low):
    for h, thickness, projection in [(13.78,.14,.19),(14.03,.18,.39),(14.32,.15,.48)]:
        f.box(0,h,f.length+.012,thickness,projection,.09,STONE,'parapet moulding')
    if not low:
        brackets = [box(u-.085,13.57,u+.085,13.85) for u in
                    [-f.length/2+.48+i*.72 for i in range(int((f.length-.44)/.72))]]
        if brackets:
            f.prism(unary_union(brackets),.045,.205,STONE,'cornice modillions')


def window_wall(f, bay_count, low, *, pairs=False, west_portal=False, quiet=False):
    panel = box(-f.length/2, 0, f.length/2, CORNICE)
    grid = f.length/bay_count
    holes = []
    sills = []
    for index in range(bay_count):
        midpoint = -f.length/2 + (index+.5)*grid
        portal = west_portal and index == bay_count//2
        positions = [midpoint-.76,midpoint+.76] if pairs and not portal else [midpoint]
        for floor,level in enumerate(FLOORS):
            for x in positions:
                width = (1.05 if len(positions)==2 else min(1.82,grid*.57))
                if portal and floor==0:
                    op=box(x-1.21,.05,x+1.21,3.57)
                else:
                    width = 2.10 if portal and floor==2 else width
                    op=circular_head(x,level+.62,width,3.20,floor==2 and not quiet,low)
                holes.append(op)
                light(f,op,low,'west door' if portal and floor==0 else 'casement')
                if not portal or floor:
                    l,b,r,_=op.bounds
                    sills.append(box(l-.12,b-.13,r+.12,b-.014))
                if floor==2 and not quiet:
                    head=op.buffer(.14,join_style='round').difference(op)
                    f.prism(head.intersection(box(x-width,level+2.2,x+width,level+4.2)),.01,.15,STONE,'arched head')
    f.prism(panel.difference(unary_union(holes)),-.28,0,BRICK,'red masonry with real reveals')
    f.prism(unary_union(sills),.005,.15,STONE,'window sills')
    if not quiet:
        for k in range(bay_count+1):
            u=min(f.length/2-.15,max(-f.length/2+.15,-f.length/2+k*grid))
            corner_trim(f,u,low)
        cornice(f,low)


def gallery_rail(f, u, width, z, low):
    half=width/2-.095
    f.box(u,z+.96,2*half,.06,.11,-.185,RAIL,'gallery handrail')
    f.box(u,z+.15,2*half,.044,.07,-.185,RAIL,'gallery foot rail')
    divisions=max(4,round(2*half/(.45 if low else .29)))
    bars=[box(u-half+i*(2*half/divisions)-.019,z+.15,u-half+i*(2*half/divisions)+.019,z+.96)
          for i in range(divisions+1)]
    if not low:
        for i in range(1,divisions):
            x=u-half+i*2*half/divisions
            a=min(.19,half/divisions)
            bars.append(LineString([(x-a,z+.73),(x,z+.90),(x+a,z+.73)]).buffer(.017))
    f.prism(unary_union(bars),-.22,-.155,RAIL,'open gallery balusters')


def opening_with_soft_corners(u, bottom, width, h, upper, low):
    if not upper:
        return box(u-width/2,bottom,u+width/2,bottom+h)
    radius=.37
    rounded=box(u-width/2+radius,bottom+radius,u+width/2-radius,bottom+h-radius).buffer(
        radius,quad_segs=3 if low else 8)
    return rounded.union(box(u-width/2,bottom,u+width/2,bottom+h-radius))


def gallery(f, spans, low):
    total=sum(spans)
    edges=[-f.length/2]
    for span in spans:
        edges.append(edges[-1]+f.length*span/total)
    holes=[]
    recesses=[]
    for level_index,base in enumerate(FLOORS):
        for left,right in zip(edges,edges[1:]):
            u=(left+right)/2
            width=right-left-.64
            lower=base+.03 if level_index==0 else base+.14
            op=opening_with_soft_corners(u,lower,width,3.84,level_index==2,low)
            holes.append(op)
            if level_index:
                gallery_rail(f,u,width,base,low)
            if level_index==2:
                frame=op.buffer(.138,join_style='round').difference(op)
                f.prism(frame.intersection(box(left,base+3.0,right,base+4.22)),.015,.146,STONE,'gallery arch moulding')
            # The photographed inner wall is visible beyond the railing.
            recesses.append(circular_head(u,base+.43,min(2.05,width*.61),3.13,True,low))
    panel=box(-f.length/2,0,f.length/2,CORNICE)
    f.prism(panel.difference(unary_union(holes)),-.36,0,BRICK,'open arcade wall')
    for u in edges:
        corner_trim(f,min(f.length/2-.11,max(-f.length/2+.11,u)),low)
    cornice(f,low)
    left,right=[f.point(u,0,-GALLERY_DEPTH)[:2] for u in (-f.length/2,f.length/2)]
    rear=Facade(f.builder,left,right,f.label+' inner wall')
    rear.prism(panel.difference(unary_union(recesses)),-.27,0,STONE,'rendered room wall')
    for op in recesses:
        light(rear,op,low,'inner door or transom')
    floor=Polygon([f.a[:2],f.b[:2],right,left])
    for h in FLOORS:
        f.builder.plan_prism(floor, max(-.006,h-.16),h+.026,PAVING,f.label+'/gallery floor')
    for a,b in [(f.a[:2],left),(right,f.b[:2])]:
        wall=Facade(f.builder,a,b,f.label+' return')
        wall.prism(box(-wall.length/2,0,wall.length/2,CORNICE),-.16,0,BRICK,'return wall')


def plaque(f, low):
    shoulder=14.38
    chord=2.98
    heights=[(chord*cos(i*pi/20),shoulder+.38+.90*sin(i*pi/20)) for i in range(21)]
    shape=Polygon([(-chord,shoulder),(chord,shoulder),*heights])
    f.prism(shape,-.35,.1,STONE,'curved school plaque')
    f.prism(LineString(heights).buffer(.092,cap_style='square'),-.08,.22,STONE,'plaque top coping')
    add_facade_lettering(f,'學中明光',0,14.99,4.50,.47,.103,.153,GOLD,label='school name right to left',font=FONT)
    for i in range(5):
        x=(i-2)*.48
        r=.23 if i==2 else .105
        z=15.33+.15*(1-abs(i-2)/2)
        pts=[(x+(r if n%2==0 else r*.41)*cos(pi/2+n*pi/5),
              z+(r if n%2==0 else r*.41)*sin(pi/2+n*pi/5)) for n in range(10)]
        f.prism(Polygon(pts),.108,.155,GOLD,'gold stars')


def make_school(builder,low=False):
    edges=[Facade(builder,a,b,l) for a,b,l in zip(PLAN,PLAN[1:]+PLAN[:1],[
        'West wing south','West wing court return','West recessed gallery','Central west return',
        'Central projection','Central east return','East recessed gallery','East wing court return',
        'East wing south','East end','North east rear','North west rear','West street end'])]
    window_wall(edges[0],2,low)
    window_wall(edges[1],2,low)
    gallery(edges[2],[.50,1.02,1.36,1.02,.50],low)
    window_wall(edges[3],2,low)
    mid=edges[4]
    widths=[7.04,mid.length-14.08,7.04]
    left=-mid.length/2
    for label,width in zip(['west pair','school name','east pair'],widths):
        face=Facade(builder,mid.point(left,0)[:2],mid.point(left+width,0)[:2],'Central '+label)
        if label=='school name':
            gallery(face,[1,1.5,1],low)
            plaque(face,low)
        else:
            window_wall(face,2,low)
        left+=width
    window_wall(edges[5],2,low)
    gallery(edges[6],[.50,1.02,1.36,1.02,.50],low)
    window_wall(edges[7],2,low)
    window_wall(edges[8],2,low)
    window_wall(edges[9],5,low,pairs=True)
    window_wall(edges[10],12,low,quiet=True)
    window_wall(edges[11],5,low,quiet=True)
    window_wall(edges[12],5,low,pairs=True,west_portal=True)
    plan=Polygon(PLAN)
    builder.plan_prism(plan,-.018,.020,PAVING,'Envelope/ground slab')
    builder.plan_prism(plan,13.87,14.04,ROOF,'Roof/terrace')
    parapet=plan.difference(plan.buffer(-.21,join_style='mitre'))
    builder.plan_prism(parapet,14.01,14.34,BRICK,'Roof/brick parapet')
    for i,(l,b,r,t,height) in enumerate([(-3.8,14.6,2.8,19.3,1.10),(8.5,20.5,32.2,23.65,.70)]):
        footprint=box(l,b,r,t)
        builder.plan_prism(footprint,14.03,14.03+height,STONE,f'Roof/low service volume {i+1}')
        builder.plan_prism(footprint.buffer(.10,join_style='mitre'),14.03+height,14.12+height,ROOF,'Roof/service coping')
