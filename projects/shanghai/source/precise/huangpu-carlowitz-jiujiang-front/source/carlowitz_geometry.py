"""Jiujiang Road front, with the four-storey arcade and visible corner return."""
from math import cos, pi, sin
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

BRICK = 'oxblood face brick'
RED = 'ring brick'
MORTAR = 'pressed brick joints'
STONE = 'pale carved stone'
GLASS = 'dark grey glazing'
FRAME = 'charcoal sash'
ROOF = 'muted tile'
INNER = 'recessed red wall'
FLOOR = 'arcade paving'
PALETTE = {
    name: {'color': rgb, 'roughness': rough}
    for name, rgb, rough in [
        (BRICK, [.48, .205, .128], .91), (RED, [.55, .26, .155], .90),
        (MORTAR, [.34, .172, .126], .94), (STONE, [.75, .71, .60], .84),
        (GLASS, [.16, .22, .21], .38), (FRAME, [.17, .145, .136], .70),
        (ROOF, [.32, .17, .118], .89), (INNER, [.33, .15, .105], .88),
        (FLOOR, [.54, .51, .45], .90)
    ]
}

FRONT_WIDTH = 44.5552
BAY = FRONT_WIDTH / 14
WEST = -FRONT_WIDTH / 2
EAST = FRONT_WIDTH / 2
DEPTH = 4.65
LEVELS = [(4.93, 3.02), (8.68, 3.06), (12.42, 3.04)]
EAVE = 15.93
ARC_START = (EAST, 0.)
ARC_END = (24.87, 3.50)


def round_corner():
    """A short elliptical return through the two mapped endpoints, facing the crossroads."""
    x, y = ARC_START
    width, depth = ARC_END[0]-x, ARC_END[1]-y
    return [(x+width*sin(t*pi/2/6), y+depth*(1-cos(t*pi/2/6))) for t in range(7)]


def trim(f, u, z, width, height, depth, mat, label):
    f.box(u, z, width, height, depth, depth*.42, mat, label)


def arch_band(f, hole, sill, width, rise, thin, material):
    x0, z0, x1, z1 = hole.bounds
    outline = hole.buffer(thin, join_style='round').difference(hole)
    # At the springing, the moulding meets separate pale capitals and brick piers.
    head = outline.intersection(box(x0-thin*2, z1-rise-.035, x1+thin*2, z1+thin*2))
    if not head.is_empty:
        f.prism(head, .013, .105, material, 'arched head')
    for x in (x0-.05, x1+.05):
        trim(f,x,z1-rise-.06,.29,.135,.14,STONE,'springing stone capital')


def spindle(builder, x, y, z, lod):
    profile = [(0,.074),(.07,.085),(.15,.050),(.235,.083),(.31,.064),(.42,.044),(.47,.072)]
    if lod:
        simplified = [(.0,.074),(.15,.050),(.235,.083),(.42,.044),(.47,.072)]
        v = [(x+sign*r,y,z+h) for h,r in simplified for sign in (-1,1)]
        builder.add(v,[(i,i+1,i+3,i+2) for i in range(0,len(v)-2,2)],
                    STONE,'baluster elevation silhouette')
    else:
        builder.lathe((x,y),[(z+h,r)for h,r in profile],STONE,8,'turned pale balcony baluster')


def railing(f, u, z, width, lod, bowed=False):
    # The restored south elevation shows a pierced panel across each broad arch.
    def projection(t):
        return .12 + (.17*(1-t*t) if bowed else 0)
    if bowed:
        edges=[-1+i*.25 for i in range(9)]
        for height,thickness in ((.035,.11),(.54,.10)):
            outside=[f.point(u+t*width/2,z,projection(t)+.15)[:2] for t in edges]
            inside=[f.point(u+t*width/2,z,projection(t)-.12)[:2] for t in reversed(edges)]
            f.builder.plan_prism(Polygon(outside+inside),z+height-thickness/2,z+height+thickness/2,STONE,'bowed balcony rail')
    else:
        trim(f,u,z+.035,width+.06,.085,.27,STONE,'balcony low rail')
        trim(f,u,z+.54,width+.12,.095,.31,STONE,'balcony handrail')
    for j in range(9):
        t=2*(j+.5)/9-1
        x,y,_=f.point(u+width*t/2,z,projection(t))
        spindle(f.builder,x,y,z+.075,lod)


def window(f, u, z, w, h, arch, lod):
    cut=opening(u,z,w,h,arch,10 if lod else 22)
    broad = w > 1.8
    f.window(cut,columns=4 if broad else 2,rows=1 if broad else 2,frame=FRAME,glass=GLASS,trim=False,label='recessed sash')
    if broad:
        # One high transom separates the curved fanlight from the four tall lower panes.
        f.box(u,z+h-arch-.21,w-.14,.055,.08,-.20,FRAME,'high transom')
        trim(f,u,z+h+.095,.26,.22,.13,RED,'projecting arch key')
    arch_band(f,cut,z,w,arch,.13,RED)
    return cut


def front_wall(f, lod):
    centres=[WEST+(i+.5)*BAY for i in range(14)]
    lower=[opening(u,-.025,BAY*.72,4.08,1.12,10 if lod else 22) for u in centres]
    all_openings = list(lower)
    for u,hole in zip(centres,lower):
        arch_band(f,hole,0.,BAY*.72,1.12,.16,RED)
    for z,h in LEVELS:
        cuts=[]
        for u in centres:
            width=BAY*.75
            hole=window(f,u,z,width,h,.67,lod)
            railing(f,u,z+.025,width*.99,lod,bowed=(z==8.68 and u>EAST-2*BAY))
            cuts.append(hole)
        # On the photographed high floors, paired engaged shafts meet a
        # broad pale carved impost. The intermediate square shafts remain brick.
        for i in range(1,14):
            x=WEST+i*BAY
            spring=z+h-.67
            for offset in (-.185,.185):
                u=x+offset
                lower=z+.70
                top=spring-.24
                if z==12.42 and i%2==1:
                    xx,yy,_=f.point(u,0,.018)
                    f.builder.lathe((xx,yy),[(lower,.117),(lower+.08,.14),(top-.10,.111),(top,.147)],
                                    STONE,8 if lod else 14,'paired pale engaged shaft')
                else:
                    f.box(u,(top+lower)/2,.245,top-lower,.105,.045,BRICK,'paired brick pilaster')
                trim(f,u,lower-.055,.31,.105,.16,STONE,'narrow shaft base')
                trim(f,u,spring-.118,.36,.26,.19,STONE,'carved capital block')
                if not lod:
                    for leaf in (-.085,0,.085):
                        leaf_tip=f.point(u+leaf,spring-.19,.189)
                        leaf_left=f.point(u+leaf-.048,spring-.085,.19)
                        leaf_right=f.point(u+leaf+.048,spring-.058,.19)
                        leaf_peak=f.point(u+leaf,spring-.095,.215)
                        f.builder.add([leaf_tip,leaf_left,leaf_right,leaf_peak],[(0,1,3),(0,3,2),(1,2,3)],STONE,'capital leaf relief')
            trim(f,x,spring+.032,.82,.075,.18,STONE,'shared impost cap')
        bottom=z-.42
        top=z+h+.35
        # Continuous wall through reveals and projecting horizontal bands.
        all_openings.extend(cuts)
        trim(f,0,bottom+.075,f.length,.16,.17,STONE,'continuous sill course')
        if not lod:
            # Mortar is restrained and confined to the brick face between real voids.
            interior=box(-f.length/2+.006,bottom,f.length/2-.006,top)
            solid=interior.difference(unary_union(cuts).buffer(.16))
            zz=bottom+.21
            while zz<top-.06:
                lines=solid.intersection(box(WEST,zz,EAST,zz+.015))
                if not lines.is_empty:f.prism(lines,.003,.010,MORTAR,'brick bed joint')
                zz+=.18
            # Short vertical joints alternate along the broad brick piers between openings.
            for bay in range(1,14):
                u=WEST+BAY*bay
                for j in range(17):
                    at=u+(.105 if j%2 else -.105)
                    low=bottom+.23+.18*j
                    if solid.covers(box(at-.006,low,at+.006,low+.145)):
                        vertices=[f.point(ux,hz,.012)for ux,hz in [(at-.007,low),(at+.007,low),(at+.007,low+.145),(at-.007,low+.145)]]
                        f.builder.add(vertices,[(0,1,2,3)],MORTAR,'staggered brick perpends')
    f.wall(.055,EAVE,all_openings,thickness=.49,material=BRICK)
    trim(f,0,4.69,f.length,.22,.26,STONE,'arcade top cornice')
    trim(f,0,EAVE-.015,f.length,.26,.31,STONE,'stone eaves')


def add_gable(builder, x, lod):
    f=Facade(builder,(x-BAY,-.055),(x+BAY,-.055),'paired slit attic gable')
    # Curved shoulders rise to a short upright centre; source photos show two separate openings.
    half=BAY; z=EAVE+.02
    side=[(0,2.63),(.54,2.61),(.54,2.30),(.90,2.02),(1.29,1.83),(1.99,1.48),
          (2.35,1.60),(2.42,1.27),(2.77,.91),(half,.52),(half,0)]
    profile=[(-half,z),*[( -u,z+h) for u,h in side[-2::-1]],*[(u,z+h)for u,h in side[1:]],(half,z)]
    wall=Polygon(profile)
    holes=[window(f,u,z+.56,.56,.93,.28,lod)for u in(-.67,.67)]
    f.prism(wall.difference(unary_union(holes)),-.45,.015,BRICK,'curvilinear attic gable face')
    outline=[(-u,z+h)for u,h in side[::-1]]+[(u,z+h)for u,h in side[1:]]
    builder.tube([f.point(u,h,.075)for u,h in outline],.072,STONE,6 if lod else 10,'pale gable silhouette')
    for u in (-2.36,2.36):
        trim(f,u,z+.97,.15,1.30,.15,STONE,'slender shoulder pilaster')
        trim(f,u,z+1.67,.24,.12,.21,STONE,'shoulder finial')
    trim(f,0,z+2.66,1.12,.15,.24,STONE,'flat centre crest cap')


def roof_dormer(builder,x,lod):
    f=Facade(builder,(x-1.35,.82),(x+1.35,.82),'short Jiujiang roof dormer')
    z=EAVE+.14
    hole=opening(0,z+.12,1.85,.58,0)
    f.window(hole,columns=3,rows=1,frame=FRAME,glass=GLASS,trim=False)
    outline=Polygon([(-1.35,z),(1.35,z),(1.35,z+.88),(0,z+1.55),(-1.35,z+.88)])
    f.prism(outline.difference(hole),-.52,.01,RED,'triangular dormer head')
    for x1,x2,h1,h2 in ((-1.47,0,.87,1.61),(0,1.47,1.61,.87)):
        plane=[f.point(x1,z+h1,.15),f.point(x2,z+h2,.15),f.point(x2,z+h2,-1.43),f.point(x1,z+h1,-1.43)]
        builder.add(plane,[(0,1,2,3)],ROOF,'pitched dormer roof')


def rounded_return(builder,lod):
    path=round_corner();step=6
    # Define the front of each opening along its true circular curve, avoiding flat triangular plugs at its edges.
    floors = [(0.,4.03,1.03,.055,4.56), (4.93,3.02,.95,4.56,8.32),
              (8.68,3.06,.95,8.32,12.06), (12.42,3.04,.95,12.06,EAVE)]
    # The 2013 high-resolution photo shows a brick terminal pier with a
    # continuous pale impost and a separate ornamental frieze on the turning wall.
    end=Facade(builder,(EAST-.85,0),(EAST+.85,0),'east terminal pier')
    for dx in (-.25,-.01):
        end.box(dx,11.22,.165,6.79,.13,.045,BRICK,'two narrow terminal brick ribs')
    trim(end,-.07,14.69,.92,.32,.22,STONE,'wide east impost')
    trim(end,-.07,14.91,1.02,.09,.26,STONE,'east impost cap')
    for index,(a,b) in enumerate(zip(path,path[1:])):
        f=Facade(builder,a,b,'curved corner fascia')
        f.box(0,15.40,f.length+.003,.29,.12,.045,STONE,'shallow pale stone frieze')
        if not lod:
            for j in range(3):
                x=f.length*((j+.5)/3-.5)
                contour=[f.point(x-.058,15.40,.11),f.point(x,15.465,.11),f.point(x+.058,15.40,.11),f.point(x,15.344,.11)]
                peak=f.point(x,15.416,.145)
                builder.add([*contour,peak],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],STONE,'simplified fasces of the turning frieze')
    for z,h,w,bottom,top in floors:
        # Two curved jambs and a round soffit are cut parametrically, keeping the arch opening contiguous across facets.
        for i,(a,b)in enumerate(zip(path,path[1:])):
            f=Facade(builder,a,b,'rounded corner')
            u0=(i/step-.5)*3.7;u1=((i+1)/step-.5)*3.7
            segment=box(u0,bottom,u1,top)
            hole=opening(0,-.025 if z==0 else z,2*w,4.06 if z==0 else h,1.0 if z==0 else .6,16)
            from shapely.affinity import affine_transform
            m=f.length/(u1-u0);mapped=lambda poly:affine_transform(poly,[m,0,0,1,-(u1+u0)*m/2,0])
            wall=mapped(segment.difference(hole));f.prism(wall,-.46,0,BRICK)
            if z:
                glass=mapped(segment.intersection(hole))
                if not glass.is_empty:
                    f.prism(glass,-.35,-.32,GLASS,'glazed corner opening')
                trim(f,0,z+.52,f.length+.015,.10,.28,STONE,'curved balcony handrail')
                trim(f,0,z+.08,f.length+.015,.10,.23,STONE,'curved balcony base')
                for j in (-.25,.25):
                    xx,yy,_=f.point(f.length*j,z,.10);spindle(builder,xx,yy,z+.10,lod)
        if z:
            slab=LineString(path).buffer(.16,join_style='round',cap_style='flat')
            builder.plan_prism(slab,z-.42,z-.27,STONE,'curving corner band')


def add_building(builder,lod):
    f=Facade(builder,(WEST,0),(EAST,0),'Jiujiang Road')
    front_wall(f,lod)
    rounded_return(builder,lod)
    for u in (WEST+BAY,0,EAST-BAY):
        add_gable(builder,u,lod)
    for j in (2.9,4.9,9.1,11.1):
        roof_dormer(builder,WEST+BAY*j,lod)
    street=[(WEST,0),*round_corner()]
    outline=Polygon([*street,(ARC_END[0]-.05,DEPTH),(WEST-.10,DEPTH)])
    builder.plan_prism(outline,.015,.055,FLOOR,'courtyard-facing street gallery paving')
    builder.plan_prism(outline,4.46,4.56,STONE,'ceiling over street gallery')
    # The source ends at a shallow west return and the filmed east corner. The rear cut expresses the partial model.
    rear=Facade(builder,(ARC_END[0]-.05,DEPTH),(WEST-.10,DEPTH),'unrecorded stop')
    rear.wall(.055,EAVE,material=INNER)
    side=Facade(builder,(WEST-.10,DEPTH),(WEST,0),'west section')
    side.wall(.055,EAVE,material=INNER)
    back=Facade(builder,(WEST,2.22),(EAST,2.22),'shop wall behind gallery')
    holes=[]
    for i in range(14):
        u=WEST+(i+.5)*BAY
        hole=opening(u,.10,2.18,3.27,.30,10 if lod else 18);holes.append(hole)
        back.window(hole,columns=2,rows=2,frame=FRAME,glass=GLASS,trim=False)
    back.wall(.055,4.46,holes,thickness=.27,material=INNER)
    # The roof has a low visible pitch behind its gables. Rear roof pitch/chimneys have no assigned geometry.
    ring = [*street,(ARC_END[0]-.05,DEPTH),(WEST-.10,DEPTH)]
    roof = [(x,y,EAVE-.13+.345*y) for x,y in ring]
    builder.add(roof,[tuple(range(len(roof)))],ROOF,'visible tiled south roof plane')
    east_closure=Facade(builder,ARC_END,(ARC_END[0]-.05,DEPTH),'east section above arcade')
    east_closure.wall(4.56,EAVE,material=INNER)
    for (x0,y0),(x1,y1) in ((ring[-2],ring[-1]),(ring[-1],ring[0]),(ARC_END,ring[-2])):
        upper=[(x0,y0,EAVE-.15),(x1,y1,EAVE-.15),(x1,y1,EAVE-.13+.345*y1),(x0,y0,EAVE-.13+.345*y0)]
        builder.add(upper,[(0,1,2,3)],INNER,'plain roof section')

