"""Garden elevation and intersecting clay-tile roofs seen in the 2010 and 2020 views."""
import math

from shapely import set_precision
from shapely.geometry import Polygon, box, LineString, Point
from shapely.ops import unary_union

from photo_architecture import Facade, pieces

WALL = 'grey pebble dash'
TRIM = 'pale stone fascia'
WOOD = 'red brown window timber'
RAIL = 'painted veranda timber'
GLASS = 'blue grey casement glass'
DARK = 'dark recess glazing'
CLAY = 'red clay roof tile'
LAP = 'weathered tile edge'
JOINT = 'recessed clay tile joints'
RIDGE = 'terracotta ridge'
IRON = 'dark stair iron'
STEP = 'grey garden steps'
BRICK = 'chimney brick'
PALETTE = {
    name: {'color': rgb, 'roughness': rough, 'metallic': metallic}
    for name, rgb, rough, metallic in [
        (WALL,[.45,.43,.385],.95,0), (TRIM,[.69,.65,.57],.85,0),
        (WOOD,[.236,.089,.060],.61,0), (RAIL,[.318,.111,.070],.65,0),
        (GLASS,[.16,.223,.234],.26,.17), (DARK,[.084,.103,.101],.37,.10),
        (CLAY,[.40,.167,.099],.87,0), (LAP,[.447,.208,.124],.88,0),
        (RIDGE,[.47,.201,.125],.81,0), (JOINT,[.287,.121,.079],.94,0), (IRON,[.11,.124,.117],.61,.35),
        (STEP,[.43,.43,.399],.91,0), (BRICK,[.41,.219,.153],.90,0)
    ]
}


def shallow_arch(half, bottom, shoulder, rise, segments):
    # The lower porch is almost rectangular, with a shallow curved head.
    arc = [(half*math.cos(math.pi*i/segments),
            shoulder+rise*math.sin(math.pi*i/segments)) for i in range(segments+1)]
    return Polygon([(-half,bottom),(half,bottom),*arc])


def gallery_frame(face, shape, sill, head, lod, label):
    """Four pairs of casements, transom lights and a lower solid timber sill."""
    min_x, _, max_x, _ = shape.bounds
    openings = []
    for group in range(4):
        l = min_x+(max_x-min_x)*group/4+.054
        r = min_x+(max_x-min_x)*(group+1)/4-.054
        for leaf in range(2):
            start = l+(r-l)*leaf/2+.023
            end = l+(r-l)*(leaf+1)/2-.023
            rail = sill+.91
            transom = head-.54
            for z0,z1 in ((sill+.08,rail-.033), (rail+.033,transom-.040),
                          (transom+.040,head+.20)):
                if z0 < rail or z0 > transom or lod:
                    openings.append(box(start,z0,end,z1))
                else:
                    width=(end-start)/2
                    for col in range(2):
                        for row in range(3):
                            za=z0+(z1-z0)*row/3+.013
                            zb=z0+(z1-z0)*(row+1)/3-.013
                            openings.append(box(start+col*width+.010,za,
                                                start+(col+1)*width-.010,zb))
    inside=shape.buffer(-.054,join_style=2)
    face.prism(shape.difference(inside.intersection(unary_union(openings))),
               -.292,-.207,WOOD,label+' grid')
    face.prism(shape.buffer(.009,join_style=2),-.365,-.347,GLASS,label+' glass')
    face.box(0,sill+.048,max_x-min_x,.096,.225,-.067,RAIL,label+' foot rail')
    face.box(0,sill+.93,max_x-min_x,.10,.148,-.013,RAIL,label+' handrail')
    for i in range(24):
        x=min_x+.16+i*(max_x-min_x-.32)/23
        face.box(x,sill+.486,.105,.80,.089,-.013,RAIL,label+' balusters')


def garden_bay(b,lod):
    front=Facade(b,(-3.54,0),(3.54,0),'garden bay')
    arch=shallow_arch(2.25,-.03,1.81,.46,16 if lod else 38)
    lower=box(-2.86,3.25,2.86,6.02)
    upper=shallow_arch(2.86,6.61,8.76,.67,18 if lod else 36)
    wall=box(-3.54,0,3.54,10.13).difference(unary_union([arch,lower,upper]))
    front.prism(wall,-.30,0,WALL,'three masonry reveals')
    for z,h,d,width in ((.25,.13,.19,7.13),(2.72,.13,.23,7.24),
                        (6.30,.17,.35,7.48),(6.43,.062,.38,7.51)):
        band=box(-width/2,z-h/2,width/2,z+h/2)
        front.prism(band.difference(arch),-.291,d,TRIM,'projecting string courses')
    gallery_frame(front,lower,3.25,6.02,lod,'lower gallery')
    gallery_frame(front,upper,6.61,9.43,lod,'upper gallery')
    for x in (-3.54,3.54):
        frm=((x,2.58),(x,0)) if x < 0 else ((x,0),(x,2.58))
        edge=Facade(b,*frm,'gallery return')
        edge.wall(0,10.12,thickness=.22,material=WALL)
        for z,h in ((2.72,.13),(6.30,.17),(6.43,.062)):
            edge.beam(z,h,.13,TRIM,label='return fascia')
    back=Facade(b,(-3.54,2.43),(3.54,2.43),'porch rear')
    door=box(-1.14,.11,1.14,2.32)
    back.prism(box(-3.54,0,3.54,2.65).difference(door),-.18,0,WALL,'door recess')
    back.prism(door,-.08,-.06,DARK,'glazed inner doors')
    bars=[box(-1.14,.11,1.14,.30),box(-1.14,1.32,1.14,1.38)]
    for x in (-1.105,-.56,0,.56,1.105):
        bars.append(box(x-.037,.11,x+.037,2.32))
    back.prism(unary_union(bars),-.045,.005,WOOD,'inner door stiles')
    b.box((0,1.23,.048),(7.08,2.45,.096),STEP,label='porch paving')
    b.box((0,1.35,2.57),(7.08,2.54,.16),TRIM,label='porch soffit')
    for x in (-2.36,2.36):
        b.box((x,1.31,1.19),(.23,2.24,2.38),WALL,label='porch jamb return')


def side_wings(b,lod):
    for west in (True,False):
        x=-5.205 if west else 5.205
        face=Facade(b,(x-1.67,2.36),(x+1.67,2.36),'west wing' if west else 'east wing')
        mid=box(-.81,3.33,.63,5.11)
        top=[box(c-.32,6.88,c+.32,7.56) for c in (-.83,.75)]
        cellar=box(-.98,1.12,.07,1.70)
        face.wall(0,8.13,[mid,cellar,*top],thickness=.24,material=WALL)
        for w in [cellar,*top]:
            face.prism(w,-.22,-.20,DARK,'recessed side window')
            border=w.difference(w.buffer(-.047,join_style=2))
            face.prism(border,-.17,-.10,WOOD,'small timber frame')
        for z in (1.32,1.50):
            face.box(-.455,z,1.04,.034,.036,-.105,IRON,'lower window bars')
        face.prism(mid,-.23,-.21,DARK,'shutter back')
        leave_width=(.63+.81)/2
        for c in (-.81+leave_width/2,-.81+1.5*leave_width):
            panel=box(c-leave_width/2+.008,3.33,c+leave_width/2-.008,5.11)
            rim=panel.difference(panel.buffer(-.077,join_style=2))
            face.prism(rim,-.14,-.09,WOOD,'shutter stiles')
            count=12 if lod else 24
            step=1.62/count
            for i in range(count):
                z=3.41+(i+.5)*step
                b.box((x+c,2.485,z),(leave_width-.15,.055,step*.86),RAIL,
                      [(1,0,0),(0,.914,-.406),(0,.406,.914)],'wing/louvre blades')
        face.box(-.09,3.26,1.61,.13,.42,.025,TRIM,'shutter sill')
    # Narrow external stone stair visible left of the porch rises toward the house.
    for i in range(12):
        z=(i+1)*.176
        b.box((-6.58+(i+.5)*.225,1.91,z/2),(.225,.84,z),STEP,label='west/stair treads')
    p1=(-6.48,1.51,1.04); p2=(-3.98,1.51,3.00)
    b.tube([p1,p2],.026,IRON,5 if lod else 9,'west/sloping handrail')
    for i in (0,3,6,9,11):
        x=-6.58+(i+.5)*.225; z=(i+1)*.176
        b.tube([(x,1.51,z),(x,1.51,z+.87)],.018,IRON,5 if lod else 8,'west/stair uprights')


def clipped_halfplane(domain, a, b, c):
    """Keep points in a*x+b*y+c >= 0 using a polygon enclosing the local house."""
    vertices=[(-64.,-64.),(64.,-64.),(64.,64.),(-64.,64.)]
    keep=[]
    previous=vertices[-1]
    for current in vertices:
        old=a*previous[0]+b*previous[1]+c
        new=a*current[0]+b*current[1]+c
        if (old>0)!=(new>0):
            t=old/(old-new)
            keep.append(tuple(p+t*(q-p) for p,q in zip(previous,current)))
        if new>=0:
            keep.append(current)
        previous=current
    if len(keep)<3:
        return Polygon()
    return domain.intersection(Polygon(keep))


def roof_planes(bounds,form):
    xmin,ymin,xmax,ymax=bounds
    domain=box(*bounds)
    result=[]
    for plane in form:
        roof=domain
        for other in form:
            if other!=plane:
                roof=clipped_halfplane(roof,*[q-p for p,q in zip(plane,other)])
        result.append((plane,roof))
    return result


def clay_tile_joints(builder, footprint, axis_x, height, pitch):
    """Short, staggered laps between adjacent tiles, aligned with each roof pitch."""
    inner=footprint.buffer(-.055)
    if inner.is_empty:
        return
    u0,v0,u1,v1=inner.bounds if axis_x else (inner.bounds[1],inner.bounds[0],inner.bounds[3],inner.bounds[2])
    vertices=[]; faces=[]
    def xy(u,v):
        return (u,v) if axis_x else (v,u)
    for course in range(math.floor(u0/pitch),math.ceil(u1/pitch)):
        start=course*pitch+.035
        end=(course+1)*pitch-.026
        offset=(course%2)*.104
        for tile in range(math.floor((v0-offset)/.208),math.ceil((v1-offset)/.208)+1):
            center=tile*.208+offset
            # Keep the clipped hips clean. Perimeter pieces do not acquire a
            # full-length joint which would project beyond the tile surface.
            outline=[xy(start,center-.009),xy(end,center-.006),
                     xy(end,center+.006),xy(start,center+.009)]
            if not all(inner.contains(Point(p)) for p in outline):
                continue
            if not axis_x:
                outline.reverse()
            base=len(vertices)
            vertices.extend((x,y,height(x,y)+z) for z in (.001,.007) for x,y in outline)
            faces.extend(tuple(base+n for n in face) for face in
                         [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    if vertices:
        builder.add(vertices,faces,JOINT,'roof/staggered joints between individual tiles')


def tile_roofs(b,lod):
    # The high 2020 oblique shows a lateral gable, a transverse southern bay
    # with a clipped hip, and a separate short hip to the rear.
    main=[(0,.76,8.14-.76*2.01),(0,-.76,8.14+.76*12.14)]
    bay=[(.49,0,10.13+.49*3.79),(-.49,0,10.13+.49*3.79),(0,.86,10.13+.86*.34)]
    rear=[(0,.77,8.14-.77*8.38),(0,-.77,8.14+.77*15.48),
          (.77,0,8.14+.77*7.31),(-.77,0,8.14+.77*7.10)]
    assemblies=[roof_planes((-7.41,2.01,7.06,12.14),main),
                roof_planes((-3.79,-.34,3.79,7.075),bay),
                roof_planes((-7.31,8.38,7.10,15.48),rear)]
    for idx,patches in enumerate(assemblies):
        for plane,patch in patches:
            a,c,d=plane
            for j,others in enumerate(assemblies):
                if j==idx:
                    continue
                for other,other_patch in others:
                    hiding=clipped_halfplane(other_patch,*[q-p for p,q in zip(plane,other)])
                    patch=patch.difference(hiding)
            roof=set_precision(patch,.00005)
            height=lambda x,y:a*x+c*y+d
            for poly in pieces(roof):
                if poly.area < .003:
                    continue
                project=lambda x,y,z:(x,y,height(x,y)+z)
                b.prism(poly,-.14,0,project,CLAY,'roof/intersecting clay planes')
                # Batten-parallel lines follow the fall of each individual slope.
                xfall=abs(a)>abs(c)
                pitch=.52 if lod else .265
                if not lod:
                    clay_tile_joints(b,poly,xfall,height,pitch)
                low=poly.bounds[0 if xfall else 1]; high=poly.bounds[2 if xfall else 3]
                for k in range(math.ceil(low/pitch),math.ceil(high/pitch)):
                    t=k*pitch
                    line=LineString([(t,-24),(t,28)] if xfall else [(-24,t),(24,t)])
                    intersection=line.intersection(poly.buffer(-.018))
                    for item in getattr(intersection,'geoms',[intersection]):
                        if item.geom_type!='LineString' or item.length<.15:
                            continue
                        endpoints=[(x,y,height(x,y)+.010) for x,y in (item.coords[0],item.coords[-1])]
                        b.tube(endpoints,.019,LAP,4 if lod else 7,'roof/tile course lips')
    for x1,y1,z1,x2,y2,z2 in [(-7.41,7.075,11.9894,7.06,7.075,11.9894),
                                 (0,1.8194,11.9871,0,7.075,11.9871),
                                 (-3.76,11.93,10.873,3.55,11.93,10.873),
                                 (-3.79,-.34,10.13,0,1.8194,11.9871),
                                 (3.79,-.34,10.13,0,1.8194,11.9871)]:
        b.tube([(x1,y1,z1+.025),(x2,y2,z2+.025)],.071,RIDGE,7 if lod else 12,'roof/ridge and hip caps')
    # Lateral gable returns join the retained street-side wall at the eaves.
    for west in (True,False):
        ends=((-7.22,12.05),(-7.00,2.10)) if west else ((6.88,2.1),(6.95,12.05))
        side=Facade(b,*ends,'street gable' if west else 'east gable')
        half=side.length/2
        triangle=Polygon([(-half,8.06),(half,8.06),(0,11.88)])
        side.prism(triangle,-.20,0,WALL,'gable masonry')
    # Wall between the garden projection's eaves and the end of the main pitch.
    for x in (-3.54,3.54):
        edge=Facade(b,(x,6.32),(x,2.36),'bay cheek') if x<0 else Facade(b,(x,2.36),(x,6.32),'bay cheek')
        edge.prism(box(-1.98,8.06,1.98,10.13),-.18,0,WALL,'high return')
    for x,y,base,top,w,h,pots in [(1.46,7.65,11.40,13.05,.69,.55,2),
                                  (-1.02,12.14,10.48,11.57,1.03,.51,3)]:
        b.box((x,y,(base+top)/2),(w,h,top-base),BRICK,label='chimney/stack')
        b.box((x,y,top),(w+.12,h+.10,.105),TRIM,label='chimney/coping')
        for i in range(pots):
            px=x+(i-(pots-1)/2)*.235
            b.lathe((px,y),[(top+.045,.085),(top+.275,.084),(top+.30,.096),
                             (top+.353,.096)],RIDGE,8 if lod else 14,'chimney/clay flues')


def add_house(builder,lod=False):
    garden_bay(builder,lod)
    side_wings(builder,lod)
    tile_roofs(builder,lod)
