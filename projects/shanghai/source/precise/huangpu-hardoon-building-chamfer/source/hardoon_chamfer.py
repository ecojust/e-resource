"""The photographed corner bay of the Fu Li Building above its retail frontage."""
import math

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade, opening


BRICK = 'grey pressed brick'
MORTAR = 'light grey bed joint'
PALE = 'weathered pale masonry'
ASH = 'stone ledges and shade'
RED = 'ochre red dormer and arch'
TIMBER = 'deep red painted window joinery'
GLASS = 'recessed grey glass'
IRON = 'dark balcony iron'
SEAM = 'dark roofing edge'
CUT = 'study return finish'
PALETTE = {
    name: {'color': color, 'roughness': roughness}
    for name, color, roughness in [
        (BRICK, [.47, .46, .43], .94), (MORTAR, [.57, .56, .52], .96),
        (PALE, [.73, .70, .63], .90), (ASH, [.51, .49, .45], .93),
        (RED, [.66, .40, .31], .86), (TIMBER, [.43, .26, .23], .76),
        (GLASS, [.34, .40, .39], .37), (IRON, [.19, .20, .19], .69),
        (SEAM, [.34, .34, .31], .76), (CUT, [.45, .43, .40], .92),
    ]
}
# The central edge follows the 5.023 m source chamfer. Both adjoining
# elevations stop 1.55 m beyond their corner, before the next full window bay.
HALF = 2.51157
LEFT = (-HALF, 0.)
RIGHT = (HALF, 0.)
LEFT_END = (-3.5800, 1.1210)
RIGHT_END = (3.5749, 1.1266)
EDGES = [(LEFT_END, LEFT), (LEFT, RIGHT), (RIGHT, RIGHT_END)]
FACE = .39


def sash(facade, hole, label, lod, rail_levels=()):
    x0, z0, x1, z1 = hole.bounds
    facade.prism(hole.buffer(.016, join_style=2), .054, .077, GLASS, label + ' glass')
    frame = hole.difference(hole.buffer(-.075, join_style=2))
    frame = frame.union(box(-.032, z0, .032, z1).intersection(hole))
    for z in rail_levels:
        frame = frame.union(box(x0, z-.028, x1, z+.028).intersection(hole))
    if not lod:
        frame = frame.union(box(x0, z0+.14, x1, z0+.173).intersection(hole))
    facade.prism(frame, .085, .135, TIMBER, label + ' frame and mullion')


def brick_courses(facade, mask, lod):
    # Both levels keep the coursing. The close mesh also retains the staggered
    # vertical joints and the lighter soldier bricks above the square window.
    pitch = .148 if not lod else .296
    left, bottom, right, top = mask.bounds
    row = 0
    z = bottom + pitch
    cuts = []
    while z < top:
        band = box(left+.025, z, right-.025, z+.010).intersection(mask)
        if not band.is_empty:
            cuts.append(band)
        if not lod:
            start = left + (.19 if row % 2 else .39)
            while start < right:
                joint = box(start, z-pitch+.012, start+.011, z).intersection(mask)
                if not joint.is_empty:
                    cuts.append(joint)
                start += .39
        row += 1
        z += pitch
    if cuts:
        facade.prism(unary_union(cuts), FACE+.002, FACE+.008, MORTAR, 'laid grey brick joints')


def upper_openings(facade, lod):
    lower = opening(0, .19, 3.02, 1.94, 1.03, segments=15 if lod else 38)
    middle = opening(0, 2.99, 1.79, 2.32, .15, segments=10 if lod else 24)
    upper = opening(0, 6.20, 1.75, 2.56, .82, segments=15 if lod else 38)
    holes = [lower, middle, upper]
    wall = box(-HALF, 0, HALF, 9.38).difference(unary_union(holes))
    facade.prism(wall, .09, FACE, BRICK, 'grey masonry with three openings')
    lower_panel = box(-1.85, .16, 1.85, 2.24).difference(lower)
    upper_ring = upper.buffer(.135, join_style=2).difference(upper)
    facade.prism(lower_panel, FACE-.02, FACE+.055, PALE, 'broad dressed lower arch surround')
    lower_trim = lower.buffer(.095, join_style=2).difference(lower)
    facade.prism(lower_trim, FACE+.046, FACE+.106, ASH, 'lower arch moulding')
    facade.prism(upper_ring, FACE-.018, FACE+.066, RED, 'upper arch brickwork')
    upper_lip = upper.buffer(.182, join_style=2).difference(upper.buffer(.132, join_style=2))
    facade.prism(upper_lip, FACE+.036, FACE+.105, PALE, 'outer rim of upper arch')
    for z in [2.99, 6.20]:
        facade.box(0, z-.023, 2.10, .078, .16, FACE+.016, ASH, 'door sill')
    sash(facade, lower, 'lower arched light', lod, [1.16])
    sash(facade, middle, 'middle balcony door', lod, [4.69])
    sash(facade, upper, 'upper arched door', lod, [7.90])
    facade.prism(middle.buffer(.073, join_style=2).difference(middle),
                 FACE-.014, FACE+.026, BRICK, 'shallow segmental brick lintel')
    brick_courses(facade, wall.difference(unary_union([lower_panel.buffer(.04), upper_ring.buffer(.03)])), lod)


def bow(radius_x, projection, base, count):
    return [(radius_x*math.cos(math.pi*i/count), base+projection*math.sin(math.pi*i/count))
            for i in range(count+1)]


def curved_balcony(facade, lod):
    count = 14 if lod else 32
    curve = bow(1.58, .60, FACE+.035, count)
    # Facade-local horizontal x/depth to the local city axes.
    outline = Polygon([(x, -d) for x, d in curve] + [(-1.58, -FACE+.055), (1.58, -FACE+.055)])
    for lo, hi, offset, material, label in [
        (2.63,2.73,-.035,ASH,'underside of bowed balcony'),
        (2.73,2.91,.035,PALE,'bowed balcony edge'),
        (2.91,2.99,.075,ASH,'curved balcony sill')]:
        facade.builder.prism(outline.buffer(offset, join_style=2),lo,hi,
                             lambda x,y,z:(x,y,z),material,label)
    # The white fascia in the street photo is pierced by a row of vase-shaped
    # solid balusters. Each follows the outward normal of the curved balcony.
    for left, right in zip(curve, curve[1:]):
        seg = LineString([(left[0],-left[1]), (right[0],-right[1])]).buffer(.071, cap_style=2)
        for z0,z1 in [(3.01,3.15),(3.59,3.70)]:
            facade.builder.prism(seg,z0,z1,lambda x,y,z:(x,y,z),PALE,'curved lower and upper handrails')
    for i in range(15 if lod else 19):
        t = math.pi*i/(14 if lod else 18)
        x,depth = 1.58*math.cos(t), FACE+.035+.60*math.sin(t)
        profile = [(3.13,.059),(3.20,.073),(3.28,.041),(3.41,.078),(3.48,.047),(3.59,.057)]
        nr = 5 if lod else 8
        verts = [(x+radius*math.cos(2*math.pi*j/nr), -depth+radius*math.sin(2*math.pi*j/nr), z)
                 for z,radius in profile for j in range(nr)]
        faces = []
        for k in range(len(profile)-1):
            for j in range(nr):
                a=k*nr+j;b=k*nr+(j+1)%nr
                faces.extend([(a,b,b+nr),(a,b+nr,a+nr)])
        facade.builder.add(verts,faces,PALE,'bowed balcony turned stone balusters')
    for x in [-.91,.91]:
        bracket = Polygon([(x-.19,2.67),(x+.19,2.67),(x+.10,2.24),(x-.10,2.24)])
        facade.prism(bracket, FACE+.02, FACE+.32, ASH, 'balcony stone corbels')


def straight_balustrades(facade,lod):
    width=3.40
    for z in [.31,.97]:
        facade.box(0,z,width,.043,.055,FACE+.26,IRON,'lower balcony rails')
    for i in range(9):
        x=(i/8-.5)*width
        facade.box(x,.64,.033,.65,.035,FACE+.26,IRON,'lower iron uprights')
        if i<8 and not lod:
            end=x+width/8
            facade.builder.tube([facade.point(x,.38,FACE+.26),facade.point(end,.89,FACE+.26)],.014,IRON,5,'diagonal ironwork')
            facade.builder.tube([facade.point(x,.89,FACE+.26),facade.point(end,.38,FACE+.26)],.014,IRON,5,'diagonal ironwork')
    for z in [6.24,6.80]:
        facade.box(0,z,2.42,.11,.22,FACE+.24,PALE,'upper balcony parapet')
    for i in range(10):
        facade.box((i/9-.5)*2.25,6.52,.09,.52,.13,FACE+.24,PALE,'upper low balustrade')


def miter_plan(point, first_normal, second_normal, back, front):
    """Connect adjoining offset wall planes through their true plan intersection."""
    ax, ay = first_normal[:2]
    bx, by = second_normal[:2]
    scale = 1. + ax*bx + ay*by
    dx, dy = (ax+bx)/scale, (ay+by)/scale
    x, y = point
    return Polygon([(x+ax*back,y+ay*back), (x+ax*front,y+ay*front),
                    (x+dx*front,y+dy*front), (x+bx*front,y+by*front),
                    (x+bx*back,y+by*back), (x+dx*back,y+dy*back)])


def join_returns(facades, lod):
    # The street-facing and side wall planes sit ahead of the original city
    # wall. Their offset edges need a mitre at both real turns of the building.
    levels = [(0.,9.38,.09,FACE,BRICK), (0.,.11,.07,.45,ASH),
              (2.67,2.79,.07,.49,ASH),(2.80,2.92,.07,.51,PALE),
              (5.93,6.06,.07,.51,ASH),(6.06,6.20,.07,.55,PALE),
              (9.12,9.23,.07,.48,ASH),(9.32,9.46,.07,.57,PALE),
              (9.46,9.55,.07,.64,SEAM)]
    for index, point in enumerate([LEFT,RIGHT]):
        a, b = facades[index], facades[index+1]
        for lo, hi, back, front, mat in levels:
            plan=miter_plan(point,a.n,b.n,back,front)
            a.builder.prism(plan,lo,hi,lambda x,y,z:(x,y,z),mat,'mitred corner of street wall')
        pitch=.296 if lod else .148
        z=pitch
        joint=miter_plan(point,a.n,b.n,FACE,FACE+.008)
        while z<9.12:
            a.builder.prism(joint,z,z+.010,lambda x,y,h:(x,y,h),MORTAR,'mortar across corner')
            z+=pitch


def shoulders(facades,lod):
    for index, facade in enumerate(facades):
        if index!=1:
            wall=box(-facade.length/2,0,facade.length/2,9.38)
            facade.prism(wall,.09,FACE,BRICK,'short retained street-side return')
            brick_courses(facade,wall,lod)
        for bottom,top,depth,material,label in [
            (.0,.11,.45,ASH,'edge above retail fascia'), (2.67,2.79,.49,ASH,'lower balcony string'),
            (2.80,2.92,.51,PALE,'lower stone string'), (5.93,6.06,.51,ASH,'upper balcony lower course'),
            (6.06,6.20,.55,PALE,'upper balcony string'), (9.12,9.23,.48,ASH,'cornice lower band'),
            (9.32,9.46,.57,PALE,'projecting cornice'), (9.46,9.55,.64,SEAM,'cornice capping')]:
            facade.box(0,(top+bottom)/2,facade.length+.042,top-bottom,depth-.07,(depth+.07)/2,material,label)
        count=max(4,round(facade.length/.32))
        for k in range(count):
            x=(k+.5)*facade.length/count-facade.length/2
            facade.box(x,9.26,.12 if not lod else .14,.13,.20,FACE+.055,PALE,'dentil course')


def dormer(facade,lod):
    # Both photographs show the fan-shaped central panel, the two pilasters,
    # their short flat shoulder ledges and the roundels on the flared sides.
    count=12 if lod else 30
    arch_top=[(1.82*math.cos(math.pi*i/count),12.35+.68*math.sin(math.pi*i/count)) for i in range(count+1)]
    silhouette=Polygon([(-2.12,9.55),(2.12,9.55),(2.06,10.05),(1.77,10.32),
                        (1.65,11.07),(1.65,12.17),(1.82,12.35),*arch_top[1:],
                        (-1.65,12.17),(-1.65,11.07),(-1.77,10.32),(-2.06,10.05)])
    light=box(-.68,9.84,.68,11.42)
    facade.prism(silhouette.difference(light),-.38,.19,RED,'red dormer face and open light')
    facade.prism(light.buffer(.018,join_style=2),-.25,-.21,GLASS,'dormer recessed glass')
    frame=light.difference(light.buffer(-.066,join_style=2)).union(box(-.034,9.84,.034,11.42))
    facade.prism(frame,-.17,-.105,TIMBER,'dormer pair of window sashes')
    for sign in [-1,1]:
        x=sign*1.22
        facade.box(x,11.05,.31,2.13,.23,.19,PALE,'dormer pilaster')
        facade.box(x,12.13,.49,.12,.33,.205,ASH,'pilaster capital')
        facade.box(sign*1.40,12.31,.78,.12,.36,.214,RED,'flat dormer shoulder')
        ornament=roundel(sign*1.78,9.98,.16,count)
        facade.prism(ornament.buffer(.045).difference(ornament),.197,.258,PALE,'roundel on flared cheek')
    for x in [-.52,0,.52]:
        ribs=Polygon([(x*.53-.055,11.57),(x*.53+.055,11.57),(x*1.56+.095,12.70),(x*1.56-.095,12.70)])
        facade.prism(ribs,.195,.263,PALE,'splayed rib to dormer arch')
    curved=LineString(arch_top).buffer(.096,cap_style=2)
    facade.prism(curved,-.40,.31,PALE,'rounded layered pediment')
    facade.prism(LineString([(x,z+.080) for x,z in arch_top]).buffer(.041,cap_style=2),-.41,.34,ASH,'roof ridge lip')
    if not lod:
        for index in range(12):
            theta = math.pi*(index+.5)/12
            x=1.68*math.cos(theta);z=12.31+.52*math.sin(theta)
            facade.box(x,z,.095,.072,.13,.232,PALE,'small pediment dentils')


def roundel(x,z,radius,count):
    return Polygon([(x+radius*math.cos(2*math.pi*i/count),z+radius*math.sin(2*math.pi*i/count)) for i in range(count)])


def add_building(builder,lod):
    facades=[Facade(builder,a,b,label)for (a,b),label in zip(EDGES,['Nanjing shoulder','street corner','Sichuan shoulder'])]
    upper_openings(facades[1],lod)
    shoulders(facades,lod)
    join_returns(facades,lod)
    curved_balcony(facades[1],lod)
    straight_balustrades(facades[1],lod)
    dormer(facades[1],lod)
