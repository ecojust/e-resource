"""Richardson Hall's rear auditorium, from Ctny's 2017 interior and the district's broadside photograph."""
import math
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.affinity import scale

LEFT, RIGHT, NORTH = -16.2, 10.2, 52.3
WEST_JOIN, EAST_JOIN = 17.01, 22.94
HEIGHT = 8.75
GALLERY_FRONT = 25.79
WINDOW_CENTRES = (29.785, 35.5, 41.7)
WINDOW_HEIGHT_SCALE = .719
BRICK = 'grey ashlar'
PLASTER = 'warm ivory plaster'
RECESS = 'pale panel recess'
STONE = 'carved pale stone'
LEAD = 'charcoal lead and steel'
OAK = 'dark oak'
FLOOR = 'polished mottled floor'
ROOF = 'grey roof flashing'
SEAT = 'Hall | folded charcoal seat'
CLEAR = 'Hall | ivory leaded glass'
RED = 'Hall | ruby red border glass'
GOLD = 'Hall | amber border glass'
CYAN = 'Hall | turquoise medallion'
PALETTE = {
    SEAT:dict(color=[.032,.035,.031],roughness=.59),
    CLEAR:dict(color=[.78,.75,.56],roughness=.29),
    RED:dict(color=[.58,.052,.026],roughness=.31),
    GOLD:dict(color=[.85,.49,.072],roughness=.30),
    CYAN:dict(color=[.021,.48,.53],roughness=.28),
}


def arch(centre, half, sill, spring, peak, steps):
    """Two arcs meet at a point above the vertical jambs."""
    rise = peak-spring
    radius = (half*half+rise*rise)/(2*half)
    curve = [(centre-half+radius-math.sqrt(max(0,radius*radius-(rise*i/steps)**2)),
              spring+rise*i/steps) for i in range(steps+1)]
    return Polygon([(centre-half,sill), *curve, *[(2*centre-u,z) for u,z in reversed(curve[:-1])], (centre+half,sill)])


def disk(u,z,r,sides=8):
    return Polygon([(u+r*math.cos(i*math.tau/sides),z+r*math.sin(i*math.tau/sides)) for i in range(sides)])


def stripe(shape,width):
    return shape.difference(shape.buffer(-width,join_style=2))


def window_silhouette(y):
    return arch(y,1.63,1.19,6.15,7.60,10)


def rectangle_silhouette(y):
    return box(y-1.37,1.20,y+1.37,3.22)


def colored_window(b, y, wall, inward, pointed, lod, side, width_factor=1., lift=0.):
    """Positive section depth faces the audience on either wall."""
    label = 'Auditorium/'+side+(' paired lancets' if pointed else ' rectangular lights')
    def plate(poly,depth,thickness,mat,name):
        a=wall+inward*depth
        c=wall+inward*(depth+thickness)
        poly=scale(poly,xfact=width_factor,yfact=WINDOW_HEIGHT_SCALE if pointed else 1.,origin=(y,1.19))
        b.prism(poly,min(a,c),max(a,c),lambda u,z,d:(d,u,z+lift),mat,label+'/'+name)
    outer=window_silhouette(y) if pointed else rectangle_silhouette(y)
    sill=1.19 if pointed else 1.20
    lights=[]
    trefoils=[]
    for sign in (-1,1):
        mid=y+sign*(.81 if pointed else .66)
        if pointed:
            q=arch(mid,.633,sill+.10,5.23,5.98,8)
            for dx,dz,r in [(0,6.11,.187),(-.28,6.00,.102),(.28,6.00,.102),(0,6.41,.092)]:
                trefoils.append((mid+dx,dz,r))
        else:
            q=box(mid-.55,sill+.10,mid+.55,3.12)
        lights.append(q)
        # The coloured perimeter of each light and its dark lead are distinct, closed solids.
        plate(q,.135,.022,RED,'ruby perimeter')
        core=q.buffer(-.069,join_style=2)
        plate(core,.16,.019,GOLD,'amber perimeter')
        clear=core.buffer(-.082,join_style=2)
        plate(clear,.184,.018,CLEAR,'pale glass')
        top = 5.48 if pointed else 3.08
        cross = 3.76 if pointed else 2.51
        bars=[box(mid-.019,sill+.14,mid+.019,top),
              box(mid-.65,cross-.048,mid+.65,cross+.048)]
        rows=(1.65,2.08,2.53,2.98,3.38,4.70,5.12) if pointed else (1.53,1.94,2.74)
        for h in rows:
            bars.append(box(mid-.65,h-.016,mid+.65,h+.016))
        plate(q.intersection(unary_union(bars)),.219,.029,LEAD,'transom and leads')
        if not lod:
            lines=[]
            for h in ((1.71,2.63,4.71) if pointed else (1.70,2.64)):
                lines.append(LineString([(mid-.35,h+.20),(mid,h-.16),(mid+.35,h+.20),(mid,h+.56),(mid-.35,h+.20)]))
            plate(clear.intersection(unary_union(lines).buffer(.013,join_style=2,cap_style=2)),.205,.012,LEAD,'diamond leading')
        if pointed:
            med=disk(mid,4.27,.334,16 if not lod else 10)
            plate(med,.252,.018,CYAN,'turquoise central roundel')
            plate(stripe(med,.031),.274,.016,GOLD,'roundel rim')
            plate(disk(mid,4.27,.077),.276,.018,RED,'red roundel heart')
            for k in range(4 if lod else 8):
                theta=k*math.tau/(4 if lod else 8)
                plate(disk(mid+.182*math.cos(theta),4.27+.182*math.sin(theta),.048,6),.277,.011,GOLD,'roundel petals')
        else:
            for h in (1.52,2.83):
                for dx in (-.38,.38):
                    plate(disk(mid+dx,h,.088),.251,.016,CYAN,'turquoise border jewel')
    holes=list(lights)
    if pointed:
        for u,z,r in trefoils:
            circle=disk(u,z,r,12 if not lod else 8)
            holes.append(circle);plate(circle,.137,.028,GOLD,'crown jewel')
            if r>.15:plate(disk(u,z,r*.67,10),.174,.011,CYAN,'crown roundel')
        eye=disk(y,6.91,.415,24 if not lod else 12)
        holes.append(eye);plate(eye,.136,.025,LEAD,'oculus dark glass')
        for i in range(9 if not lod else 6):
            a=i*math.tau/(9 if not lod else 6)
            stations=[(.046,0),(.22,-.19),(.36,-.08),(.32,.14),(.15,.20)]
            petal=Polygon([(y+r*math.cos(a+da),6.91+r*math.sin(a+da)) for r,da in stations])
            plate(petal,.167,.014,RED,'oculus ruby petal')
    cut=outer.difference(unary_union(holes))
    plate(cut,.05,.077,PLASTER,'carved surround')
    plate(stripe(outer,.065),.131,.049,STONE,'outer moulding')
    b.box((wall+inward*.18,y,sill-.087+lift),(.48,(outer.bounds[2]-outer.bounds[0])*width_factor+.23,.157),STONE,label=label+'/projecting sill')


def rounded_opening(l,r,z,spring,top):
    radius=top-spring
    left=[(l+radius*(1-math.cos(a*math.pi/16)),spring+radius*math.sin(a*math.pi/16)) for a in range(9)]
    return Polygon([(l,z),*left,*[(l+r-u,h) for u,h in reversed(left)],(r,z)])


def gallery(b,lod):
    spans=[(-15.54,-3.71),(-3.35,2.08),(2.44,9.57)]
    def mapping(u,h,d):return (u,GALLERY_FRONT-d,h)
    def post_mapping(u,h,d):return (u,GALLERY_FRONT-.918-d,h)
    screen=box(LEFT+.24,-.005,RIGHT-.24,3.39)
    openings=[rounded_opening(a,c,-.40,2.51,2.89) for a,c in spans]
    b.prism(screen.difference(unary_union(openings)),-.116,.118,post_mapping,PLASTER,'Auditorium/gallery three broad soffit openings')
    for q in openings:
        band=q.buffer(.075,join_style=1,quad_segs=3).difference(q).intersection(screen)
        b.prism(band,-.166,-.123,post_mapping,RECESS,'Auditorium/stepped soffit trim')
    # At the east the balcony abuts the shallower join of the transverse classroom wing.
    b.plan_prism(box(LEFT+.27,WEST_JOIN+.03,RIGHT-.27,GALLERY_FRONT+.125),3.19,3.42,PLASTER,'Auditorium/gallery deck')
    front=box(LEFT+.28,3.409,RIGHT-.28,4.829)
    b.prism(front,-.16,.09,mapping,PLASTER,'Auditorium/solid gallery parapet')
    slots=[]
    for i in range(35):
        mid=LEFT+.70+i*.737
        slots.append(stripe(arch(mid,.219,3.65,4.33,4.53,4 if lod else 7),.028))
    b.prism(unary_union(slots),-.206,-.172,mapping,RECESS,'Auditorium/gallery blind pointed panels')
    b.box(((LEFT+RIGHT)/2,GALLERY_FRONT+.17,4.84),(RIGHT-LEFT-.43,.28,.12),STONE,label='Auditorium/gallery top rail')
    for row in range(4):
        for lo,hi in ((LEFT+1.15,-1.1),(1.1,RIGHT-1.10)):
            b.box(((lo+hi)/2,GALLERY_FRONT-.72-row*.89,3.52+row*.15),(hi-lo,.85,.19+row*.30),FLOOR,label='Auditorium/upper seating rake')
            b.box(((lo+hi)/2,GALLERY_FRONT-.96-row*.89,4.01+row*.30),(hi-lo,.16,.61),SEAT,label='Auditorium/upper dark seat backs')


def stalls(b,lod):
    # Photographs establish two banks and an open centre aisle. Exact historic row/seat counts are unknown.
    banks=((LEFT+1.29,-.92),(.92,RIGHT-1.17))
    for j in range(18):
        y=45.04-j*1.08
        for lo,hi in banks:
            count=int((hi-lo)/.72)
            step=(hi-lo)/count
            # Each bank keeps its visible gaps and stepped silhouette at both resolutions.
            outline=[(0,0),(.39,0),(.39,.36),(.27,.36),(.15,.34),(.10,.79),(0,.79)]
            for i in range(count):
                xc=lo+step*(i+.5)
                b.prism(Polygon([(y+dy-.24,.075+h) for dy,h in outline]),xc-step*.447,xc+step*.447,lambda u,z,d:(d,u,z),SEAT,'Auditorium/stalls individual folded seat')
                if not lod and i in (0,count-1):
                    b.box((xc-step*.49+.018,y+.006,.49),(.048,.43,.075),OAK,label='Auditorium/aisle arm rest')


def build_auditorium(b,lod=False):
    b.palette.update(PALETTE)
    # Footprint comes from the north-hall map polygon. Face heights, stage depth and gallery rake are estimates.
    interior=box(LEFT,WEST_JOIN,RIGHT,NORTH)
    b.plan_prism(interior,-.175,-.009,FLOOR,'Auditorium/floor')
    b.plan_prism(box(-2.31,13.23,2.31,WEST_JOIN+.03),-.146,-.004,FLOOR,'Auditorium/vestibule connection')
    for wall,inward,start,side in ((LEFT,1,WEST_JOIN,'west'),(RIGHT,-1,EAST_JOIN,'east')):
        # Two rectangular banks by the rear gallery are visible both beneath and above its deck.
        rear=((26.37,1.,0.),(23.80,.54,0.),(23.80,.54,4.32))
        if side=='east':
            # Ctny's lower rectangular lights and the pair above the gallery use
            # the same inside plane as the plaster. The second bay straddles the
            # mapped joint with the classroom wing rather than cutting its exterior.
            rear=((26.37,1.,0.),(22.70,.77,-.04),(26.37,.91,3.89),(22.70,.77,4.05))
        apertures=[scale(window_silhouette(y),xfact=1.,yfact=WINDOW_HEIGHT_SCALE,origin=(y,1.19)) for y in WINDOW_CENTRES]
        for y,width,lift in rear:
            q=rectangle_silhouette(y)
            apertures.append(Polygon([(y+(u-y)*width,z+lift) for u,z in q.exterior.coords]))
        holes=unary_union(apertures)
        for low,high,mat,part in ((-.10,.16,BRICK,'ashlar outer faces'),(.165,.192,PLASTER,'plaster inner wall')):
            lining_start=17.18 if side=='east' and mat==PLASTER else start
            field=box(lining_start,-.02,NORTH,HEIGHT+.008).difference(holes) if lining_start!=start else box(start,0,NORTH,HEIGHT).difference(holes)
            a,c=wall+inward*low,wall+inward*high
            b.prism(field,min(a,c),max(a,c),lambda u,z,d:(d,u,z),mat,'Auditorium/'+side+' '+part)
        for y in WINDOW_CENTRES:colored_window(b,y,wall,inward,True,lod,side)
        for y,width,lift in rear:colored_window(b,y,wall,inward,False,lod,side,width,lift)
    b.box(((LEFT+RIGHT)/2,NORTH,HEIGHT/2),(RIGHT-LEFT+.19,.33,HEIGHT),BRICK,label='Auditorium/north rear wall')
    b.box(((LEFT+RIGHT)/2,NORTH-.183,HEIGHT/2),(RIGHT-LEFT-.36,.026,HEIGHT-.08),PLASTER,label='Auditorium/stage back')
    b.box(((LEFT+RIGHT)/2,49.31,.416),(RIGHT-LEFT-.55,5.53,.85),OAK,label='Auditorium/conditional stage apron')
    for i in range(3):
        b.box((.46,45.72+.265*i,.100+.10*i),(3.52,.255,.20+.20*i),OAK,label='Auditorium/stage steps')
    # South screen reconstructed on the hall side of the classroom joint. Its
    # ground-floor opening reveals the three existing vestibule doors at Y13.20.
    # In the audience photograph the balcony rail hides the foot of the upper openings.
    joint_y=17.18
    upper_door_left=rounded_opening(5.07,6.87,4.22,6.58,6.86)
    upper_door_right=rounded_opening(-7.53,-5.21,4.22,6.99,7.25)
    booth=box(-1.58,6.20,.81,7.21)
    passage=rounded_opening(-2.60,2.60,-.20,2.91,3.16)
    closure=box(LEFT+.02,-.06,RIGHT-.02,HEIGHT+.07)
    mapping=lambda u,z,d:(u,joint_y-d,z)
    openings=[passage,upper_door_left,upper_door_right,booth]
    b.prism(closure.difference(unary_union(openings)),-.108,.103,mapping,PLASTER,'Auditorium/south gallery back wall with central passage')
    for q,name in ((upper_door_left,'left upper recess'),(upper_door_right,'right upper recess')):
        b.prism(q,.35,.40,mapping,LEAD,'Auditorium/'+name+'/unmeasured dark rear')
        b.prism(stripe(q,.078),-.128,-.111,mapping,RECESS,'Auditorium/'+name+'/frame')
    b.prism(booth,.11,.15,mapping,LEAD,'Auditorium/upper horizontal dark glazing')
    b.prism(stripe(booth,.055),-.132,-.114,mapping,RECESS,'Auditorium/upper horizontal frame')
    for u in (-.76,.02):
        b.prism(box(u-.026,6.235,u+.026,7.17),-.095,-.071,mapping,LEAD,'Auditorium/upper window mullion')
    gallery(b,lod);stalls(b,lod)
    b.plan_prism(interior,HEIGHT+.10,HEIGHT+.23,ROOF,'Auditorium/conditional low weathering cover')
    b.plan_prism(box(LEFT+.19,WEST_JOIN+.018,RIGHT-.19,NORTH-.19),HEIGHT-.055,HEIGHT+.093,PLASTER,'Auditorium/plaster ceiling')
    for i in range(9):
        y=19.13+i*3.78
        b.box(((LEFT+RIGHT)/2,y,HEIGHT-.16),(RIGHT-LEFT-.37,.17,.19),PLASTER,label='Auditorium/transverse ceiling beams')
    for i in range(7):
        x=LEFT+1.82+i*3.73
        b.box((x,(WEST_JOIN+NORTH)/2,HEIGHT-.202),(.15,NORTH-WEST_JOIN-.35,.105),PLASTER,label='Auditorium/longitudinal coffer beams')
    return b
