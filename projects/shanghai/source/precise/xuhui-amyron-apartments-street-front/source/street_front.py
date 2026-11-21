"""Street corner of the Amyron Apartments on Gao'an Road and Kangping Road."""
from math import sqrt
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade

BRICK='warm ochre face tile'
DARK_TILE='shadowed tile in entrance'
GLASS='slightly grey window glass'
STEEL='dark painted sash'
WOOD='burgundy entrance timber'
GRANITE='grey threshold stone'
CAP='pale cement edging'
IRON='balcony rail'
ROOF='flat roof'
REAR='rear of modeled section'
PALETTE={
    BRICK:dict(color=[.654,.504,.393],roughness=.89),DARK_TILE:dict(color=[.492,.392,.331],roughness=.91),
    GLASS:dict(color=[.428,.5,.548],roughness=.26,metallic=.27),STEEL:dict(color=[.195,.212,.219],roughness=.61),
    WOOD:dict(color=[.398,.198,.167],roughness=.72),GRANITE:dict(color=[.478,.474,.442],roughness=.87),
    CAP:dict(color=[.797,.764,.692],roughness=.85),IRON:dict(color=[.281,.289,.28],roughness=.66,metallic=.32),
    ROOF:dict(color=[.49,.492,.48],roughness=.94),REAR:dict(color=[.611,.562,.492],roughness=.94)}
STOREY=3.28
CROWN=20.35
SIDE_TOP=16.83
HALF_BOW=3.76

def line(x):
    """Rising returns at the road junction follow the surveyed corner of source 3602."""
    v=abs(x)
    if v<=HALF_BOW:
        return .22+10.0-sqrt(100.0-x*x)
    return .22+10.0-sqrt(100.0-HALF_BOW**2)+(v-HALF_BOW)*(.59 if x>0 else .45)

def plate(b,outline,z,h,material,name):
    b.prism(outline,z,z+h,lambda x,y,z:(x,y,z),material,name)

def opening(f,shape,cols,rows,material=GLASS,label='window'):
    f.prism(shape,-.236,-.215,material,label+' / glass or wood')
    x0,z0,x1,z1=shape.bounds
    bars=[shape.difference(shape.buffer(-.048,join_style=2))]
    for i in range(1,cols):
        x=x0+(x1-x0)*i/cols;bars.append(box(x-.024,z0,x+.024,z1))
    for i in range(1,rows):
        z=z0+(z1-z0)*i/rows;bars.append(box(x0,z-.026,x1,z+.026))
    f.prism(unary_union(bars),-.152,-.101,STEEL,label+' / sashes')

def local_strip(points,back=2.02):
    return Polygon([*points,*[(x,y+back) for x,y in reversed(points)]])

def curved_windows(b,low):
    count=8 if low else 16
    xs=[-HALF_BOW+2*HALF_BOW*i/count for i in range(count+1)]
    points=[(x,line(x)) for x in xs]
    for i,(left,right) in enumerate(zip(points,points[1:])):
        f=Facade(b,left,right,'six-storey curved front')
        u=f.length/2
        holes=[]
        for level in range(2,6):
            z=level*STOREY
            # There is a continuous glazed horizontal ribbon between the end piers.
            lo=-u+(.16 if i==0 else -.001);hi=u-(.16 if i==count-1 else -.001)
            win=box(lo,z+.58,hi,z+2.13);holes.append(win)
            opening(f,win,1,2,label='curved steel ribbon')
            f.prism(box(-u,z+.52,u,z+.59),-.013,.065,CAP,'shallow continuous sill')
        f.prism(box(-u,2*STOREY,u,CROWN).difference(unary_union(holes)),-.28,0,BRICK,'curved banded wall')
        if not low:
            wall=box(-u,2*STOREY,u,CROWN).difference(unary_union(holes))
            courses=[box(-u,z-.010,u,z+.010) for z in (2*STOREY+.16+k*.222 for k in range(63)) if z<CROWN]
            mortar=unary_union(courses).intersection(wall)
            f.prism(mortar,-.004,.007,DARK_TILE,'horizontal tile joints')
    plan=local_strip(points,2.15)
    plate(b,plan,2*STOREY-.13,.14,DARK_TILE,'entrance / exposed head soffit')
    plate(b,plan,CROWN-.16,.16,ROOF,'curved corner / roof slab')
    trim=plan.difference(plan.buffer(-.116,join_style=2))
    plate(b,trim,CROWN-.04,.18,CAP,'curved corner / narrow parapet band')
    back=Facade(b,(points[-1][0],points[-1][1]+2.15),(points[0][0],points[0][1]+2.15),'center rear section')
    back.wall(2*STOREY,CROWN,thickness=.11,material=REAR)
    for x,y in (points[0],points[-1]):
        f=Facade(b,(x,y),(x,y+2.15),'center side return')
        f.wall(2*STOREY,CROWN,thickness=.10,material=BRICK)

def entry(b,low):
    y=2.31
    for sx in (-1,1):
        # The pilasters frame the recess on both sides and carry the curved upper wall.
        x=3.42*sx
        pier=box(x-.42,.71,x+.42,y+.2)
        plate(b,pier,0,2*STOREY,BRICK,'two-storey porch / pier')
        plate(b,pier,0,.23,GRANITE,'two-storey porch / pier foot')
        for n in range(2 if low else 5):
            b.box((x-.32+n*(.64/(1 if low else 4)),.702,3.28),(.028,.024,5.96),DARK_TILE,label='porch / vertical tile reveals')
    f=Facade(b,(-3.82,y),(3.82,y),'recessed entrance')
    door=box(-1.19,.12,1.19,2.58);upper=box(-1.51,3.75,1.51,5.76)
    opening(f,door,2,1,WOOD,'entrance leaves');opening(f,upper,4,2,label='high vestibule windows')
    f.prism(box(-3.82,0,3.82,2*STOREY).difference(unary_union([door,upper])),-.25,0,DARK_TILE,'porch back')
    for x in (-.61,.61):
        f.prism(box(x-.36,.91,x+.36,2.28),-.19,-.153,GLASS,'inset glazed wood door')
    plate(b,box(-3.89,.16,3.89,y+.18),-.08,.19,GRANITE,'shallow exterior threshold')
    for sx in (-1,1):
        a=(sx*3.72,.76);z=(sx*3.72,y+.10)
        Facade(b,a,z,'porch side wall').wall(.10,6.54,thickness=.12,material=DARK_TILE)

def wings(b,low):
    for side,last in [(-1,11.10),(1,9.56)]:
        xs=sorted([side*HALF_BOW,side*6.69,side*last])
        for x0,x1 in zip(xs,xs[1:]):
            outer=abs((x0+x1)/2)>6.69
            # Open rounded balconies sit in front of the outside bay of each arm.
            pts=[(x0,line(x0)),(x1,line(x1))];f=Facade(b,*pts,'five-storey wing')
            u=f.length/2;holes=[]
            for level in range(5):
                z=level*STOREY
                if level==0:
                    left,right=(-u+.27,u-.27) if outer else (-u+.4,u-.4)
                    hole=box(left,z+.16 if outer else z+.89,right,z+2.55 if outer else z+2.02)
                    mat=WOOD if outer else GLASS
                else:
                    hole=box(-u+.15,z+.68,u-.15,z+2.41);mat=GLASS
                holes.append(hole);opening(f,hole,2 if low else 3,2,mat,'wing opening')
                if level:
                    f.prism(box(-u+.03,z+.62,u-.03,z+.69),-.016,.075,CAP,'wing window sills')
                if level and outer:
                    # The exposed ends of the slabs are rounded in all three dated photographs.
                    shelf=box(-u+.22,-.68,u-.22,.27).buffer(.23,quad_segs=4 if low else 10)
                    draw=lambda du,dy,h:f.point(du,h,-dy)
                    b.prism(shelf,z-.16,z+.015,draw,CAP,'outside balconies / rounded slab')
                    edge=shelf.difference(shelf.buffer(-.10)).intersection(box(-u-1,-1.1,u+1,.0))
                    b.prism(edge,z+.13,z+.55,draw,BRICK,'outside balconies / low parapet')
                    b.prism(edge,z+.91,z+.96,draw,IRON,'outside balconies / top rail')
                    for du in [-u+.35,0,u-.35]:
                        post=box(du-.035,-.868,du+.035,-.807)
                        b.prism(post,z+.5,z+.93,draw,IRON,'outside balconies / uprights')
            f.prism(box(-u,0,u,SIDE_TOP).difference(unary_union(holes)),-.25,0,BRICK,'wing masonry')
            plan=local_strip(pts,1.68)
            plate(b,plan,0,.10,GRANITE,'wing ground plate')
            plate(b,plan,SIDE_TOP-.18,.18,ROOF,'wing roof')
            Facade(b,(x1,line(x1)+1.68),(x0,line(x0)+1.68),'wing rear section').wall(.08,SIDE_TOP,thickness=.09,material=REAR)
        end=side*last;Facade(b,(end,line(end)),(end,line(end)+1.68),'outer cut').wall(.08,SIDE_TOP,thickness=.10,material=BRICK)

def make_front(b,low):
    curved_windows(b,low);entry(b,low);wings(b,low)
