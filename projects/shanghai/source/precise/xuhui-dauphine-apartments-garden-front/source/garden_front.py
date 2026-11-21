"""Concrete balcony slabs, circular windows and rounded central steel windows on the south elevation."""
import math
from shapely.geometry import Point,Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade

CREAM='sand toned wall render'
WHITE='light rendered central bow'
STONE='grey balcony slabs'
CAP='pale concrete coping'
DARK='carefully recessed door'
GLASS='blue grey window glass'
IRON='dark metal sashes'
SOFFIT='warm cement soffit'
ROOF='flat grey roof finish'
CUT='neutral rear section'
PALETTE={
    CREAM:dict(color=[.702,.654,.553],roughness=.92),WHITE:dict(color=[.844,.837,.775],roughness=.86),
    STONE:dict(color=[.728,.697,.627],roughness=.87),CAP:dict(color=[.826,.813,.741],roughness=.83),
    DARK:dict(color=[.308,.275,.222],roughness=.62),GLASS:dict(color=[.306,.392,.414],roughness=.29,metallic=.31),
    IRON:dict(color=[.203,.225,.225],roughness=.55,metallic=.33),SOFFIT:dict(color=[.688,.663,.592],roughness=.94),
    ROOF:dict(color=[.509,.51,.476],roughness=.89),CUT:dict(color=[.612,.588,.535],roughness=.96)}
WIDTH=31.20
DEPTH=4.68
STOREY=3.22
TOP=9*STOREY
WALL_Y=1.36


def horizontal(b,plan,z0,z1,material,label):
    b.prism(plan,z0,z1,lambda x,y,z:(x,y,z),material,label)


def light(f,opening,columns,rows,low,round_window=False,door=False):
    """Opaque glazing sits behind a real wall opening and a separate metal sash."""
    x0,z0,x1,z1=opening.bounds
    f.prism(opening.buffer(.018,join_style=2),-.275,-.25,DARK if door else GLASS,'recessed opening')
    parts=[opening.difference(opening.buffer(-(.055 if round_window else .07),join_style=2))]
    if not round_window:
        for i in range(1,columns):
            x=x0+(x1-x0)*i/columns
            parts.append(box(x-.031,z0,x+.031,z1).intersection(opening))
        for i in range(1,rows):
            z=z0+(z1-z0)*i/rows
            parts.append(box(x0,z-.029,x1,z+.029).intersection(opening))
    elif not low:
        z=(z0+z1)/2
        parts.append(box(x0,z-.017,x1,z+.017).intersection(opening))
    f.prism(unary_union(parts),-.18,-.113,IRON,'rolled steel sash')
    if round_window or not low:
        ring=opening.buffer(.092,join_style=2).difference(opening)
        f.prism(ring,-.012,.09 if round_window else .02,CAP,'round bezel' if round_window else 'window surround')


def rear_wall_of_balconies(b,low):
    f=Facade(b,[-WIDTH/2,WALL_Y],[WIDTH/2,WALL_Y],'garden elevation')
    holes=[]
    for number in range(9):
        z=number*STOREY
        for sign in (-1,1):
            circle=Point(sign*5.08,z+1.78).buffer(.405,quad_segs=7 if low else 14)
            holes.append(circle);light(f,circle,1,1,low,round_window=True)
            for center,width in [(9.30,2.52),(13.40,2.52)]:
                q=box(sign*center-width/2,z+.62,sign*center+width/2,z+2.54)
                holes.append(q);light(f,q,3 if low else 4,2 if low else 3,low)
    f.prism(box(-WIDTH/2,0,WIDTH/2,TOP).difference(unary_union(holes)),-.37,0,CREAM,'wall between terrace openings')


def balcony_plan(sign,low):
    """Rounded exposed end of one cantilever, selected separately in the editable model."""
    x0,x1=3.92,WIDTH/2
    # Soft radius on the two exposed corners, square returns at the wall.
    outline=box(x0+.51,-.53,x1-.51,WALL_Y+.22).buffer(.51,quad_segs=5 if low else 10)
    outline=outline.intersection(box(x0,-1.04,x1,WALL_Y+.22))
    if sign<0:
        from shapely.affinity import scale
        outline=scale(outline,xfact=-1,yfact=1,origin=(0,0))
    return outline


def terraces(b,low):
    for side in (-1,1):
        plan=balcony_plan(side,low)
        # The open rail across the balcony is a low concrete parapet, with returns at the ends.
        rail=plan.difference(plan.buffer(-.14)).intersection(box(-20,-1.05,20,WALL_Y-.035))
        side_label='east balconies' if side>0 else 'west balconies'
        for i in range(1,9):
            z=i*STOREY
            horizontal(b,plan,z-.17,z+.045,STONE,side_label+'/slabs')
            horizontal(b,rail,z+.04,z+.77,CREAM,side_label+'/low rendered parapets')
            if not low:
                horizontal(b,rail.buffer(.027,quad_segs=2),z+.745,z+.805,CAP,side_label+'/parapet caps')
        horizontal(b,plan,TOP-.18,TOP+.09,STONE,side_label+'/top slab')
        horizontal(b,rail,TOP+.08,TOP+.49,WHITE,side_label+'/roof edge')


def projecting_center(b,low):
    half=3.96
    # The shaft has two folded corner-window faces, divided by a tall central cement pier.
    pts=[[-half,WALL_Y],[-half,.26],[-3.10,-.19],[-2.57,-.34],[-1.04,-.37],
         [1.04,-.37],[2.57,-.34],[3.10,-.19],[half,.26],[half,WALL_Y]]
    plan=Polygon([*pts,[half,DEPTH],[-half,DEPTH]])
    for index,(a,c)in enumerate(zip(pts,pts[1:])):
        f=Facade(b,a,c,'central bay '+str(index+1));holes=[]
        for floor in range(1,9):
            z=floor*STOREY
            if index==4:continue
            width=f.length
            left,right=-width/2+.019,width/2-.019
            q=box(left,z+.76,right,z+2.50)
            holes.append(q);light(f,q,1 if (low or width<1.4) else 2,2 if low else 3,low)
        if index==4:
            q=box(-.882,.14,.882,2.63);holes.append(q);light(f,q,2,2,low,door=True)
        f.prism(box(-f.length/2,0,f.length/2,TOP+.55).difference(unary_union(holes)),-.286,0,WHITE,'curved window bands and raised center')
    horizontal(b,plan,TOP+.40,TOP+.55,ROOF,'central bay/roof')
    pier=box(-.91,-.40,.91,.31)
    horizontal(b,pier,2.66,TOP+.86,WHITE,'central bay/continuous raised pier')
    horizontal(b,pier.buffer(.045,join_style=2),TOP+.83,TOP+.93,CAP,'central bay/pier cap')
    # Photographs show a shallow bow-front awning with a rendered rim, clear beneath.
    canopy=Point(0,-.36).buffer(2.65,quad_segs=10 if low else 22)
    from shapely.affinity import scale
    canopy=scale(canopy,yfact=.71,origin=(0,-.36)).intersection(box(-3,-3,3,.13))
    horizontal(b,canopy,2.78,2.98,SOFFIT,'entrance/rounded canopy')
    rim=canopy.difference(canopy.buffer(-.09)).intersection(box(-3,-3,3,-.38))
    horizontal(b,rim,2.96,3.24,WHITE,'entrance/fascia')
    if not low:horizontal(b,rim.buffer(.023),3.205,3.267,CAP,'entrance/fascia coping')


def make_front(b,low):
    rear_wall_of_balconies(b,low);terraces(b,low);projecting_center(b,low)
    shell=box(-WIDTH/2,WALL_Y,WIDTH/2,DEPTH)
    center_floor=box(-3.86,0,3.86,WALL_Y+.03)
    horizontal(b,shell.union(center_floor),0,.12,STONE,'main building/floor strip')
    horizontal(b,shell,TOP-.18,TOP,ROOF,'main building/roof strip')
    for start,end,label in [([-WIDTH/2,DEPTH],[-WIDTH/2,WALL_Y],'west end'),([WIDTH/2,WALL_Y],[WIDTH/2,DEPTH],'east end'),([WIDTH/2,DEPTH],[-WIDTH/2,DEPTH],'rear cut')]:
        f=Facade(b,start,end,label);f.wall(.08,TOP+.04,thickness=.11,material=CUT)
