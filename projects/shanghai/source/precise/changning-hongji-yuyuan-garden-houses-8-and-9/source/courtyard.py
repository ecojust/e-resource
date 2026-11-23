"""Lawn, paving and the low planted margins that locate the two facing houses."""
from math import cos, pi, sin
from random import Random

from shapely.affinity import affine_transform
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from garden_fabric import EARTH, FOLIAGE, FOLIAGE_DARK, GRASS, PAVING, TREAD
from garden_shells import footprint
import house_eight_entrances


def garden_frame(shape,frame):
    e,n=frame['left_wall_projection']['garden_ENU_m']
    vx,vy=frame['local_X_unit_EN'],frame['local_Y_unit_EN']
    return affine_transform(shape,[vx[0],vy[0],vx[1],vy[1],e,n])


def lawn_outline():
    # Four approximate corners read in the north-up 660 px orbital canvas.
    # The northern margin lies below tree canopy. Paths at the fronts of the
    # houses and the clear southern lawn edge can be seen in both ground views.
    d=.25534237788840086
    return Polygon([((x-410)*d,(170-y)*d) for x,y in
                    [(326,157),(393,153),(397,206),(330,210)]])


def shrub(b,rng,x,y,w,d,h,mat,label,lod):
    n=8 if lod else 13
    points=[(x,y,-.008)]
    rings=[]
    irregular=[.87+.23*rng.random() for _ in range(n)]
    for level,rad in [(0.,.68),(.25,1.),(.72,.97),(.93,.74)]:
        ring=[]
        for j in range(n):
            a=2*pi*j/n
            ring.append(len(points))
            points.append((x+cos(a)*w*.5*rad*irregular[j],y+sin(a)*d*.5*rad*irregular[j],
                           .016+h*(level+(.04*rng.random() if level else 0))))
        rings.append(ring)
    top=len(points);points.append((x,y,.016+h))
    faces=[(0,rings[0][(j+1)%n],rings[0][j]) for j in range(n)]
    for a,c in zip(rings,rings[1:]):
        faces.extend((a[j],a[(j+1)%n],c[(j+1)%n],c[j]) for j in range(n))
    faces.extend((rings[-1][j],rings[-1][(j+1)%n],top) for j in range(n))
    b.add(points,faces,mat,label)


def planted_edges(local,number,lod):
    rng=Random(110700+number)
    if number==8:
        rows=[(.18,6.95,-.88,.74,.87),(8.10,10.62,-1.01,.63,.55)]
    else:
        rows=[(-2.97,7.02,-.74,.69,.58)]
    for row,(left,right,y,depth,h) in enumerate(rows,1):
        local.plan_prism(box(left-.13,y-depth*.59,right+.13,y+depth*.59),-.065,.003,
                         EARTH,'garden soil margin '+str(row))
        count=max(2,round((right-left)/(.76 if lod else .52)))
        for j in range(count):
            x=left+(right-left)*(j+.5)/count
            fac=.90+.16*rng.random()
            shrub(local,rng,x,y+.075*(rng.random()-.5),
                  (right-left)/count*1.29,depth*fac,h*(.92+.20*rng.random()),
                  FOLIAGE_DARK if rng.random()<.22 else FOLIAGE,'clipped lawn hedge',lod)
    if number==9:
        # The south walk has taller planting below the sashes. Only its
        # photographed edge is represented, giving the entrance its clear path.
        for j in range(15 if not lod else 9):
            y=.90+(20.8*(j+.5)/(15 if not lod else 9))
            shrub(local,rng,-3.40,y,1.08,1.85 if not lod else 2.65,1.22+.55*rng.random(),
                  FOLIAGE_DARK if j%3==0 else FOLIAGE,'south walk planting',lod)


def add_garden(b,layouts):
    borders=[]
    for num in (8,9):
        layout=layouts[str(num)]
        plan=footprint(num,layout)
        if num==8:
            occupied=house_eight_entrances.occupied_footprints(layout)
            plan=unary_union([plan,*(box(*occupied[k])for k in
                            ('numbered_red_wing','lawn_white_terrace','north_faceted_porch'))])
        else:
            plan=unary_union([plan,box(7.46,-.32,11.66,3.17)])
        borders.append(garden_frame(plan.buffer(1.52,join_style=2),layout['garden_transform']))
    lawn=lawn_outline()
    # The court connects both front paths. The crop ends beyond the houses,
    # before the neighbouring red factory and number 7.
    corridor=Polygon([(-29.30,5.29),(.7,6.65),(2.2,-12.91),(-27.65,-14.48)])
    whole=unary_union([corridor,*borders])
    b.plan_prism(whole,-.195,-.085,EARTH,'Garden | ground')
    b.plan_prism(whole.difference(lawn),-.085,-.046,PAVING,'Garden | paths around the lawn')
    b.plan_prism(lawn,-.085,-.014,GRASS,'Garden | central lawn')
    rim=lawn.buffer(.068,join_style=2).difference(lawn)
    b.plan_prism(rim,-.046,-.013,TREAD,'Garden | stone lawn edge')
