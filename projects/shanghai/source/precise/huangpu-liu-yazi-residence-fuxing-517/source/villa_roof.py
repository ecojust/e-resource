"""Villa 517 roof in survey metres, +X east and +Y north.

Section A-A fixes the high ridge and gutter. The reflected roof lines on the
fourth-floor plan, the overhead photograph 36 and garden photograph 35 fix
the four end gables, hips, valleys, roof door and chimney positions.
"""
from collections import defaultdict
from math import ceil, cos, floor, hypot, pi, sin

from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon, box

from villa_materials import ROUGH, colour

TILE = 'Terracotta field tile'
DARK_TILE = 'Weathered terracotta tile'
LIGHT_TILE = 'Sunburnt terracotta tile'
RIDGE = 'Terracotta ridge roll'
ZINC = 'Grey roof flashing'
TIMBER = 'Roof verge soffit'
BRICK = 'Chimney stock brick'
CAP = 'Stone chimney cap'
POT = 'Fired clay flue pot'
DARK = 'Flue interior'
DOOR = 'Honey stained attic door'
GLASS = 'Attic doorway glazing'
STONE = 'Attic terrace paving'
COPPER = 'Oxidised terrace upstand'
METAL = 'Attic bronze hardware'

ROOF_PALETTE = {
    TILE: colour((145, 87, 70), .88), DARK_TILE: colour((133, 78, 65), .89),
    LIGHT_TILE: colour((153, 91, 72), .85), RIDGE: colour((153, 97, 76), .83),
    ZINC: colour((94, 99, 104), .69, .18), TIMBER: colour((117, 105, 91), .86),
    BRICK: colour((151, 88, 68), .89), CAP: colour((152, 150, 141), .86),
    POT: colour((153, 149, 138), .84), DARK: colour((47, 43, 40), .96),
    DOOR: colour((163, 120, 67), .69), GLASS: colour((65, 76, 73), .27, .21),
    STONE: colour((202, 193, 179), .88), COPPER: colour((133, 74, 64), .70, .20),
    METAL: colour((116, 108, 82), .47, .55),
}

HALF_WALL = 8.854035
HALF_DEPTH = 5.451996
OUTSIDE = HALF_WALL + .638
END = HALF_DEPTH + .48
WING = 6.13
INSIDE = 3.48
WING_PEAK = 12.87
HIGH = 14.66
EAVE = 9.95
RIDGE_Y = 1.04
SOUTH_INSET = -3.34
NORTH_EAVE = 9.85
SLOPE = (WING_PEAK - EAVE) / (OUTSIDE - WING)
INNER_EAVE = WING_PEAK - (WING - INSIDE) * SLOPE
MAIN_HALF_RIDGE = WING - (HIGH - WING_PEAK) / SLOPE
DECK = 10.39
ROOF_SKIN = .145

# Top of render for each wing at either end of the building. The eave/tiles
# continue past these points. Do not continue this gable across the balcony.
GABLE_WALL_SECTIONS = {
    'west': ((-HALF_WALL, EAVE + (OUTSIDE-HALF_WALL)*SLOPE - ROOF_SKIN),
             (-WING, WING_PEAK - ROOF_SKIN), (-INSIDE, INNER_EAVE - ROOF_SKIN)),
    'east': ((INSIDE, INNER_EAVE - ROOF_SKIN), (WING, WING_PEAK - ROOF_SKIN),
             (HALF_WALL, EAVE + (OUTSIDE-HALF_WALL)*SLOPE - ROOF_SKIN)),
}

FRONT_PITCH = (HIGH-INNER_EAVE) / (RIDGE_Y-SOUTH_INSET)
BACK_PITCH = (HIGH-NORTH_EAVE) / (END-RIDGE_Y)
S_JOIN = RIDGE_Y - (HIGH-WING_PEAK) / FRONT_PITCH
N_JOIN = RIDGE_Y + (HIGH-WING_PEAK) / BACK_PITCH
N_INNER = WING - (WING_PEAK-NORTH_EAVE) / SLOPE
DOOR_HALF_ROOF, DOOR_PEAK, DOOR_EAVE = 1.00, 13.56, 12.73
DOOR_NOSE, DOOR_FACE = -3.83, -3.39
DOOR_RETURN = RIDGE_Y - (HIGH-DOOR_EAVE) / FRONT_PITCH
DOOR_RIDGE_END = RIDGE_Y - (HIGH-DOOR_PEAK) / FRONT_PITCH


def roof_z(x, y):
    """Finished roof-plane height before tiling; valid inside the roof outline."""
    outer = EAVE + (OUTSIDE-abs(x))*SLOPE
    inner = WING_PEAK - abs(abs(x)-WING)*SLOPE
    cross = HIGH + min((y-RIDGE_Y)*FRONT_PITCH, (RIDGE_Y-y)*BACK_PITCH)
    return max(inner, min(outer, cross))


def _faces():
    # Separate the surfaces at their true intersection. Each entry carries a
    # linear plane z=a*x+b*y+c so even clipped tiles retain the roof pitch.
    result = []
    def put(label, xy, a, b, c):
        result.append((label, Polygon(xy), a, b, c))
    for sg, side in ((-1,'west'), (1,'east')):
        def xs(points):
            return [(sg*x,y) for x,y in points]
        put(side+' outer slope', xs([(OUTSIDE,-END),(WING,-END),(WING,S_JOIN),
            (MAIN_HALF_RIDGE,RIDGE_Y),(WING,N_JOIN),(WING,END),(OUTSIDE,END)]),
            -sg*SLOPE, 0., EAVE+OUTSIDE*SLOPE)
        put(side+' garden gable inner slope', xs([(WING,-END),(INSIDE,-END),
            (INSIDE,SOUTH_INSET),(WING,S_JOIN)]), sg*SLOPE, 0., WING_PEAK-WING*SLOPE)
        put(side+' street gable inner slope',xs([(WING,N_JOIN),(N_INNER,END),
            (WING,END)]), sg*SLOPE, 0., WING_PEAK-WING*SLOPE)
    put('garden cross roof',
        [(-MAIN_HALF_RIDGE,RIDGE_Y),(MAIN_HALF_RIDGE,RIDGE_Y),(WING,S_JOIN),
         (INSIDE,SOUTH_INSET),(DOOR_HALF_ROOF,SOUTH_INSET),(DOOR_HALF_ROOF,DOOR_RETURN),
         (0,DOOR_RIDGE_END),(-DOOR_HALF_ROOF,DOOR_RETURN),(-DOOR_HALF_ROOF,SOUTH_INSET),
         (-INSIDE,SOUTH_INSET),(-WING,S_JOIN)], 0., FRONT_PITCH, HIGH-FRONT_PITCH*RIDGE_Y)
    put('street cross roof',[(-MAIN_HALF_RIDGE,RIDGE_Y),(MAIN_HALF_RIDGE,RIDGE_Y),
         (WING,N_JOIN),(N_INNER,END),(-N_INNER,END),(-WING,N_JOIN)],0.,-BACK_PITCH,HIGH+BACK_PITCH*RIDGE_Y)
    for sg, side in ((-1,'west'),(1,'east')):
        put('attic door '+side+' pitch',[(0,DOOR_NOSE),(sg*DOOR_HALF_ROOF,DOOR_NOSE),
            (sg*DOOR_HALF_ROOF,DOOR_RETURN),(0,DOOR_RIDGE_END)],
            -sg*(DOOR_PEAK-DOOR_EAVE)/DOOR_HALF_ROOF, 0., DOOR_PEAK)
    return result


def _polys(geom):
    if geom.is_empty:
        return
    if geom.geom_type == 'Polygon':
        if geom.area > 1e-8:
            yield geom
    elif geom.geom_type in ('MultiPolygon','GeometryCollection'):
        for part in geom.geoms:
            yield from _polys(part)


def _ccw(poly):
    return list(poly.exterior.coords)[:-1][::1 if poly.exterior.is_ccw else -1]


def _cover(b, poly, a, v, c, label):
    points, faces = [], []
    def vertex(x,y,offset):
        points.append((x,y,a*x+v*y+c+offset))
        return len(points)-1
    # Roof outlines can be concave around an intersecting gable or the doorway.
    # Triangulate only the interior. The outside ring gets its own visible fascia.
    for t in constrained_delaunay_triangles(poly).geoms:
        xy = _ccw(t)
        faces.append(tuple(vertex(x,y,0.) for x,y in xy))
        faces.append(tuple(vertex(x,y,-ROOF_SKIN) for x,y in reversed(xy)))
    b.add(points, faces, TIMBER, label+' roof boards')
    ring = _ccw(poly); points,faces=[],[]
    for p,q in zip(ring, ring[1:]+ring[:1]):
        faces.append((vertex(*p,0.),vertex(*p,-ROOF_SKIN),vertex(*q,-ROOF_SKIN),vertex(*q,0.)))
    b.add(points,faces,ZINC,label+' edge')


def _tilework(b, poly, a, v, c, label, lod):
    # u follows the eave. t runs uphill in plan; the course spacing is set on
    # the sloping surface. Near tiles have staggered joints, a shallow camber
    # and a projecting lower lip. The distant model retains the real courses.
    pitch = hypot(a,v)
    ux,uy = v/pitch,-a/pitch
    tx,ty = a/pitch,v/pitch
    plane = Polygon([(x*ux+y*uy,x*tx+y*ty) for x,y in poly.exterior.coords])
    umin,tmin,umax,tmax = plane.bounds
    step = .29/hypot(1,pitch)
    width = .205
    batches = defaultdict(lambda:([],[]))
    for row in range(floor(tmin/step),ceil(tmax/step)):
        base = row*step
        band = plane.intersection(box(umin-.1,base+.0015,umax+.1,base+step))
        if band.is_empty:
            continue
        stagger = (row%2)*.5
        indices = [0] if lod else range(floor(umin/width-stagger),ceil(umax/width-stagger))
        for col in indices:
            left = (col+stagger)*width
            cell = band if lod else band.intersection(box(left+.002,base-.001,left+width-.002,base+step+.001))
            shade = (row*19+col*37+(row+col)%5)%23
            mat = TILE if lod or shade>4 else (DARK_TILE if shade<2 else LIGHT_TILE)
            vertices, faces = batches[mat]
            for piece in _polys(cell):
                # A row can straddle an indentation. Triangulate those pieces
                # in plan instead of spanning valleys with a triangle fan.
                simple = abs(piece.convex_hull.area-piece.area)<1e-8
                parts = [piece] if simple else list(constrained_delaunay_triangles(piece).geoms)
                def vert(u,t,h):
                    x,y=u*ux+t*tx,u*uy+t*ty
                    vertices.append((x,y,a*x+v*y+c+h))
                    return len(vertices)-1
                for part in parts:
                    xy=_ccw(part)
                    contour=[vert(u,t,.009+.021*(1-(t-base)/step)) for u,t in xy]
                    if lod:
                        faces.append(tuple(contour))
                    else:
                        cen=part.centroid
                        middle=vert(cen.x,cen.y,.013+.021*(1-(cen.y-base)/step))
                        faces.extend((k,contour[(i+1)%len(contour)],middle) for i,k in enumerate(contour))
                    for i,(u,t) in enumerate(xy):
                        u1,t1=xy[(i+1)%len(xy)]
                        if abs(t-base-.0015)<.0001 and abs(t1-t)<.0001:
                            lo,lo1=vert(u,t,.004),vert(u1,t1,.004)
                            faces.append((contour[i],lo,lo1,contour[(i+1)%len(contour)]))
    for mat,(vertices,faces) in batches.items():
        if faces:b.add(vertices,faces,mat,label+' laid courses')


def _flashing(b,p,q,width,label):
    x,y,z=p;dx,dy,dz=(q[i]-p[i] for i in range(3));l=hypot(dx,dy)
    nx,ny=-dy/l*width/2,dx/l*width/2
    pts=[]
    for f,off in ((0,-1),(1,-1),(1,0),(0,0),(1,1),(0,1)):
        pts.append((x+f*dx+off*nx,y+f*dy+off*ny,z+f*dz+.046+.026*abs(off)))
    b.add(pts,[(0,1,2,3),(3,2,4,5)],ZINC,label)


def _ridges(b,lod):
    def roll(p,q,label):
        b.tube([p,q],.067,RIDGE,8 if lod else 12,label)
        if lod:return
        length=sum((q[i]-p[i])**2 for i in range(3))**.5
        for k in range(1,ceil(length/.39)):
            s=k*.39/length
            if s+.016/length >= 1:break
            b.tube([tuple(p[i]+(q[i]-p[i])*t for i in range(3)) for t in (s,s+.016/length)],
                   .074,RIDGE,10,label+' joint')
    def r(x,y):return (x,y,roof_z(x,y)+.047)
    roll(r(-MAIN_HALF_RIDGE,RIDGE_Y),r(MAIN_HALF_RIDGE,RIDGE_Y),'main cross ridge')
    for sg,side in ((-1,'west'),(1,'east')):
        for y, end, edge_x, edge_y, name in ((S_JOIN,-END,INSIDE,SOUTH_INSET,'garden'),
                                              (N_JOIN,END,N_INNER,END,'street')):
            junction=r(sg*WING,y)
            roll(junction,r(sg*WING,end),side+' '+name+' gable ridge')
            roll(junction,r(sg*MAIN_HALF_RIDGE,RIDGE_Y),side+' '+name+' hip')
            _flashing(b,junction,r(sg*edge_x,edge_y),.27,side+' '+name+' open valley')
        _flashing(b,(0,DOOR_RIDGE_END,DOOR_PEAK),(sg*DOOR_HALF_ROOF,DOOR_RETURN,DOOR_EAVE),
                  .19,'attic door roof valley')
    roll((0,DOOR_NOSE,DOOR_PEAK+.045),(0,DOOR_RIDGE_END,DOOR_PEAK+.045),'attic door ridge')


def _dormer(b):
    jamb=.625
    door_half=.423
    spring=12.67
    def front_shape(xz,label):
        # Face south, with a real reveal depth and a continuously open jamb.
        vv=[(x,y,z) for y in (DOOR_FACE,DOOR_FACE+.13) for x,z in xz];n=len(xz)
        ff=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
        ff.extend((i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n))
        b.add(vv,ff,ROUGH,label)
    for sg in (-1,1):
        left,right=sorted((sg*door_half,sg*jamb))
        front_shape([(left,DECK),(right,DECK),(right,spring),(left,spring)],'pebble dash attic door jamb')
        x=sg*jamb
        top=DOOR_PEAK-(DOOR_PEAK-DOOR_EAVE)*jamb-ROOF_SKIN
        back=RIDGE_Y-(HIGH-top)/FRONT_PITCH
        s=[(x,DOOR_FACE,DECK),(x,back,top),(x,DOOR_FACE,top)]
        b.add(s,[(0,1,2) if sg>0 else (2,1,0)],ROUGH,'attic door cheek')
    top=DOOR_PEAK-(DOOR_PEAK-DOOR_EAVE)*jamb-ROOF_SKIN
    front_shape([(-jamb,spring),(jamb,spring),(jamb,top),(0,DOOR_PEAK-ROOF_SKIN),(-jamb,top)],
                'attic door small pediment')
    head=12.64
    for x in (-door_half+.045,door_half-.045):
        b.box((x,DOOR_FACE+.027,(head+DECK)/2),(.09,.12,head-DECK),DOOR,label='door frame')
    for z in (DECK+.055,head-.055):
        b.box((0,DOOR_FACE+.027,z),(2*door_half,.12,.11),DOOR,label='door rail')
    b.box((0,DOOR_FACE+.103,(DECK+head)/2),(.66,.049,head-DECK-.16),GLASS,label='recessed glazed door')
    for x in (-.297,.297):
        b.box((x,DOOR_FACE+.069,(head+DECK)/2),(.058,.047,head-DECK-.18),DOOR,label='leaf stile')
    for z in (DECK+.22,head-.125):
        b.box((0,DOOR_FACE+.069,z),(.63,.047,.10),DOOR,label='leaf bottom and top rails')
    b.box((-.265,DOOR_FACE-.012,DECK+1.02),(.098,.075,.027),METAL,label='attic door lever')
    b.box((0,DOOR_FACE-.085,DECK+.027),(.90,.21,.054),CAP,label='attic door threshold')


def _terrace(b,lod):
    ymin,ymax=-7.13,SOUTH_INSET
    b.box((0,(ymin+ymax)/2,DECK-.11),(2*INSIDE,ymax-ymin,.18),CAP,label='south attic terrace slab')
    columns, rows = (4,3) if lod else (10,6)
    for i in range(columns):
        for j in range(rows):
            width,depth=2*INSIDE/columns,(ymax-ymin)/rows
            b.box((-INSIDE+(i+.5)*width,ymin+(j+.5)*depth,DECK-.014),
                  (width-.009,depth-.008,.028),STONE,label='terrace paving')
    for sg in (-1,1):
        b.box((sg*(INSIDE-.038),(ymax-END)/2,DECK+.125),(.076,END+ymax,.25),COPPER,label='side metal upstand')
        w=INSIDE-.65
        b.box((sg*(.65+w/2),ymax-.046,DECK+.12),(w,.092,.24),COPPER,label='back metal upstand')


def _pot(b,x,y,z,h,opened,lod):
    n=10 if lod else 20
    profile=[(.143,0),(.139,.08*h),(.115,.80*h),(.128,.84*h),(.127,h),(.079,h)]
    if opened:profile.extend([(.077,h-.13),(.073,h-.27)])
    verts=[(x+r*cos(2*pi*i/n),y+r*sin(2*pi*i/n),z+t) for r,t in profile for i in range(n)]
    faces=[]
    for j in range(len(profile)-1):
        for i in range(n):
            k=(i+1)%n
            faces.append((j*n+i,j*n+k,(j+1)*n+k,(j+1)*n+i))
    b.add(verts,faces,POT,'tapered flue with rolled lip')
    b.add(verts[-n:],[tuple(range(n))],DARK if opened else POT,'open flue throat' if opened else 'closed flue crown')


def _chimney(b,name,x,y,w,l,cap_z,pot_z,opened,lod):
    low=min(roof_z(x+i*w/2,y+j*l/2) for i in (-1,1) for j in (-1,1))-.10
    b.box((x,y,(low+cap_z-.20)/2),(w,l,cap_z-.20-low),ROUGH,label=name+' roughcast chimney')
    # Step flashing follows the actual roof at all four corners.
    corners=[(x+w*i/2,y+l*j/2) for i,j in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    vertices=[(px,py,roof_z(px,py)+.14) for px,py in corners]
    vertices.extend((x+(px-x)*(1+.22/w),y+(py-y)*(1+.22/l),
                     roof_z(x+(px-x)*(1+.22/w),y+(py-y)*(1+.22/l))+.05) for px,py in corners)
    b.add(vertices,[(i,i+4,(i+1)%4+4,(i+1)%4) for i in range(4)],ZINC,name+' lead apron')
    for offset,width,depth,thickness,mat in ((-.94,.022,.024,.14,BRICK),(-.26,.055,.065,.14,BRICK),
        (-.160,.115,.125,.090,BRICK),(-.066,.22,.23,.132,CAP)):
        b.box((x,y,cap_z+offset),(w+width,l+depth,thickness),mat,label=name+' corbelled courses')
    n=len(opened)
    for i,open_flue in enumerate(opened):
        cy=y+(i-(n-1)/2)*min(.395,(l-.12)/(n-.1))
        _pot(b,x,cy,cap_z,pot_z-cap_z,open_flue,lod)


def _rooflight(b):
    x0,y0=.0,2.02
    for w,h,elevation,mat,label in ((1.02,.67,.046,ZINC,'rooflight weather curb'),
        (.82,.48,.077,GLASS,'single street-pitch rooflight')):
        points=[]
        for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            x,y=x0+dx*w/2,y0+dy*h/2
            points.append((x,y,roof_z(x,y)+elevation))
        b.add(points,[(0,1,2,3)],mat,label)


def add_roof(builder,lod,d):
    """Add all pitched coverings, attic terrace/door and the three stacks."""
    for label,poly,a,b,c in _faces():
        _cover(builder,poly,a,b,c,label)
        _tilework(builder,poly,a,b,c,label,bool(lod))
    # The door roof projects past its rendered cheeks. Continue the main tiles
    # under those overhangs to the cheek so there is a closed weathering plane.
    for sign in (-1,1):
        x1,x2=sorted((sign*.625,sign*DOOR_HALF_ROOF))
        apron=box(x1,SOUTH_INSET,x2,DOOR_RETURN)
        c=HIGH-FRONT_PITCH*RIDGE_Y
        _cover(builder,apron,0.,FRONT_PITCH,c,'attic side underlap')
        _tilework(builder,apron,0.,FRONT_PITCH,c,'attic side underlap',bool(lod))
    _ridges(builder,bool(lod))
    _terrace(builder,bool(lod))
    _dormer(builder)
    _rooflight(builder)
    _chimney(builder,'west eaves',-8.82,2.85,.54,1.34,13.86,14.40,[True]*3,lod)
    _chimney(builder,'inner west',-3.68,-.59,.57,2.13,15.99,16.65,[True]*6,lod)
    _chimney(builder,'east eaves',8.82,-.68,.55,1.99,13.56,14.08,[False,True,False,False],lod)
