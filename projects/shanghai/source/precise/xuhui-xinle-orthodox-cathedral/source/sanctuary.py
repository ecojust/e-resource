"""Street elevations and lower structure below the five domes on Xinle Road."""
from math import cos, sin, pi
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from cupolas import PALETTE, PLASTER, MOULDING, IRON, GLASS, COPPER, add_roof

STONE = 'grey threshold and plinth'
DOOR = 'dark green entrance doors'
ROOF = 'dark folded roof sheet'
PALETTE.update({
    STONE: {'color':[.52,.51,.47],'roughness':.87},
    DOOR: {'color':[.13,.185,.145],'roughness':.67},
    'green enamel address plate': {'color':[.033,.14,.105],'roughness':.44},
    'porcelain numerals': {'color':[.86,.85,.78],'roughness':.59},
    ROOF: {'color':[.265,.265,.25],'metallic':.21,'roughness':.69},
})

def silhouette(width, spring, rise, segments):
    left=-width/2
    return Polygon([(left,0),(-left,0),*[(width/2*cos(i*pi/segments),spring+rise*sin(i*pi/segments))for i in range(segments+1)]])

def arched_bay(b, endpoint_a, endpoint_b, lod, label, portal=False, central=False):
    face=Facade(b,endpoint_a,endpoint_b,label)
    width=face.length
    rise=3.2 if central else 1.72
    spring=14.25 if central else 12.9
    n=12 if lod else 28
    profile=silhouette(width,spring,rise,n)
    head=opening(0,10.7 if central else 10.2,width*(.43 if central else .49),
                 3.60 if central else 3.22,width*(.215 if central else .245),n)
    slender_width=.68 if central else .62
    positions=(-width*.377,width*.377) if portal else (-width*.20,width*.20)
    slots=[opening(x,1.28,slender_width,4.16,slender_width/2,n)for x in positions]
    lights=slots+[head]
    # The photographed north central portal has a fanlight and two recessed leaves.
    if portal:
        doorway=opening(0,.52,3.02,5.98,1.51,n)
        lights.append(doorway)
        for x in positions:
            lights.append(opening(x,7.04,.77,2.75,.385,n))
    face.wall(0,spring+rise,holes=lights,outline=profile,thickness=.47,material=PLASTER)
    for j,light in enumerate(lights):
        if portal and light.equals(doorway):continue
        face.window(light,columns=(5 if j==2 else 2),rows=(4 if j==2 else 3),frame=IRON,glass=GLASS,
                    trim=False,label='masonry light '+str(j+1))
        face.prism(light.buffer(.082,join_style='round').difference(light),-.025,.075,MOULDING,'raised window casing')
    border=[(width/2*cos(i*pi/n),spring+rise*sin(i*pi/n))for i in range(n+1)]
    # The rolled edge and its lower moulding trace the curved gable.
    for offset,radius in ((0,.11),(-.23,.066)):
        b.tube([face.point(x,z+offset,.13)for x,z in border],radius,MOULDING,6 if lod else 10,label+' / gable moulding')
    for u in (-width/2+.19,width/2-.19):
        face.box(u,spring*.51,.24,spring*.98,.16,.055,MOULDING,'edge pilaster')
        face.box(u,spring-.08,.49,.22,.26,.09,MOULDING,'impost')
    if not portal:return
    # The dated door photograph shows three fan spokes, a half ring and two
    # moulded circles on each green leaf. These details are cut as geometry.
    spring=4.99
    transom=doorway.intersection(box(-2,spring,2,6.52))
    face.prism(transom,-.34,-.32,GLASS,'fanlight glazing')
    edges=transom.difference(transom.buffer(-.085))
    fan=[edges,LineString([(1.50*cos(i*pi/n),spring+1.50*sin(i*pi/n))
                           for i in range(n+1)]).buffer(.044)]
    fan.append(LineString([(.62*cos(i*pi/n),spring+.62*sin(i*pi/n))
                           for i in range(n+1)]).buffer(.038))
    for angle in (pi/4,pi/2,3*pi/4):
        fan.append(LineString([(.62*cos(angle),spring+.62*sin(angle)),
                               (1.48*cos(angle),spring+1.48*sin(angle))]).buffer(.036))
    face.prism(unary_union(fan).intersection(transom),-.27,-.16,IRON,'curved and radial fanlight bars')
    for left,right in ((-1.5,-.025),(.025,1.5)):
        face.prism(box(left,.52,right,spring),-.32,-.245,DOOR,'paneled double door')
        x=(left+right)/2
        for radius in (.45,.775):
            ring=Point(x,2.91).buffer(radius,quad_segs=12 if lod else 26).boundary.buffer(.039)
            face.prism(ring.intersection(box(left+.045,.53,right-.045,spring)),-.245,-.196,DOOR,'concentric door moulding')
        for lower,upper in ((.83,2.10),(3.70,4.78)):
            panel=box(left+.13,lower,right-.13,upper)
            face.prism(panel.boundary.buffer(.042,join_style='mitre'),-.245,-.207,DOOR,'door stiles and rails')
    # The moulded frame in the frontal photograph has a broad outer arch
    # and successively narrower courses towards the leaves.
    for inside,outside,depth in ((.0,.18,.17),(.18,.37,.112),(.37,.56,.062)):
        outer=doorway.buffer(outside,join_style='round')
        inner=doorway if inside==0 else doorway.buffer(inside,join_style='round')
        band=outer.difference(inner).intersection(box(-3,.521,3,7.3))
        face.prism(band,-.018,depth,MOULDING,'stepped arched door frame')
    for u in (-1.80,1.80):
        face.box(u,.66,.61,.26,.19,.063,STONE,'door surround footing')
    face.box(0,.26,3.25,.52,.45,-.19,STONE,'inner threshold')
    for i in range(4):
        depth=.22*(4-i)
        height=.13*(i+1)
        face.box(0,height/2,6.38-i*.55,height,depth,depth/2,STONE,'street step')
    face.box(2.55,3.54,.38,.26,.065,.032,'green enamel address plate','enamel number plate')
    # Original digit outlines following the two white numerals on the 55 plate.
    for middle in (2.473,2.627):
        outline=[(.046,.078),(-.044,.078),(-.047,.012),(.017,.012),(.048,-.009),
                 (.048,-.051),(.026,-.074),(-.017,-.077),(-.051,-.058)]
        digit=LineString([(middle+u,3.54+v)for u,v in outline]).buffer(.010)
        face.prism(digit,.065,.074,'porcelain numerals','number 55')

def barrel(b,start,end,width,spring,rise,lod,label):
    dx=end[0]-start[0];dy=end[1]-start[1];length=(dx*dx+dy*dy)**.5
    tx,ty=-dy/length,dx/length
    count=12 if lod else 28
    pts=[(u+tx*width/2*cos(pi*i/count),v+ty*width/2*cos(pi*i/count),spring+rise*sin(pi*i/count))
         for u,v in (start,end) for i in range(count+1)]
    faces=[(i,i+1,count+i+2,count+i+1)for i in range(count)]
    b.add(pts,faces,ROOF,label)
    for sign in (-1,1):
        wall_start=(start[0]+sign*tx*width/2,start[1]+sign*ty*width/2)
        wall_end=(end[0]+sign*tx*width/2,end[1]+sign*ty*width/2)
        if sign<0:wall_start,wall_end=wall_end,wall_start
        return_wall=Facade(b,wall_start,wall_end,label+' side wall')
        return_wall.wall(12.51,spring+.035,material=PLASTER)

def add_sanctuary(b,lod):
    span=10.0
    # Current ground outline sits within the frozen source. The old bishop's residence is outside this shell.
    body=unary_union([box(-10.85,-11.45,10.85,11.45),box(-span/2,-12.55,span/2,12.62),box(-11.66,-span/2,11.77,span/2)])
    # Only horizontal slabs span the building. Door and window cutouts in the perimeter remain open to their glazing.
    b.plan_prism(body,.005,.12,STONE,'street-level plinth')
    b.plan_prism(body.buffer(-.22,join_style='mitre'),12.38,12.59,ROOF,'lower terraces')
    ring=list(body.exterior.coords)
    if not body.exterior.is_ccw:ring.reverse()
    for a,c in zip(ring,ring[1:]):
        face=Facade(b,a,c,'perimeter returns');length=face.length
        centre=face.center
        is_north=abs(centre[1]-12.62)<.01
        is_east=abs(centre[0]-11.77)<.01
        is_south=abs(centre[1]+12.55)<.01
        is_west=abs(centre[0]+11.66)<.01
        if is_north or is_east:
            arched_bay(b,a,c,lod,'Xinle Road central doorway' if is_north else 'Xiangyang Road central bay',portal=is_north,central=True)
        elif is_south or is_west:
            face.wall(0,17.45,outline=silhouette(length,14.25,3.20,12 if lod else 28),material=PLASTER)
        elif length>4 and (centre[1]>11 or centre[0]>10.8):
            arched_bay(b,a,c,lod,'street flank bay')
            inner=face.center-face.n*2.55
            barrel(b,inner[:2],face.center[:2],length,12.87,1.72,lod,'flank roofs')
        else:
            face.wall(0,12.6,material=PLASTER)
    for a,c in [((0,3.5),(0,12.62)),((0,-3.5),(0,-12.55)),((3.5,0),(11.77,0)),((-3.5,0),(-11.66,0))]:
        barrel(b,a,c,span,14.21,3.22,lod,'barrel roofs above cross arms')
    b.plan_prism(box(-4.78,-4.78,4.78,4.78),12.55,20.42,PLASTER,'central crossing')
    for x in (-6.25,6.25):
        for y in (-7,7):
            core=box(x-2.51,y-2.51,x+2.51,y+2.51)
            b.plan_prism(core,12.55,15.87,PLASTER,'corner tower shoulders')
            b.plan_prism(core.buffer(.075,join_style='mitre'),15.64,15.82,MOULDING,'corner cornices')
    add_roof(b,lod)
