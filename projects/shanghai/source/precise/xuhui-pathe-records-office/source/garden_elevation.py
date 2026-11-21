"""Garden elevation of the former Pathé building, modeled from the 2021 and 2024 garden photographs."""
import math

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union


BRICK = 'Pathe red stretchers'
STONE = 'Warm dressed stone'
WHITE = 'Warm white enamel'
FRAME = 'Dark window frames'
GLASS = 'Daylit glazing'
REVEAL = 'Inner opening'
TILE = 'Old roof clay'
EAVES = 'Dark eaves timber'
IRON = 'Forged metal'


def arched(center, sill, width, height, rise, segments):
    spring = sill + height - rise
    points = [(center - width / 2, sill), (center + width / 2, sill)]
    points.extend((center + width * .5 * math.cos(math.pi * i / segments),
                   spring + rise * math.sin(math.pi * i / segments))
                  for i in range(segments + 1))
    return Polygon(points)


def fenestration(wall, hole, surface, columns, rails, name, trim=.055):
    """Recess separate glazing and connected framing inside each real wall cut."""
    left, sill, right, head = hole.bounds
    opening = hole.buffer(-trim, join_style=2)
    bars = []
    for i in range(1, columns):
        u = left + (right-left) * i / columns
        bars.append(box(u-.016, sill, u+.016, head))
    for fraction in rails:
        z = sill + (head-sill)*fraction
        bars.append(box(left, z-.018, right, z+.018))
    frame = hole.difference(opening.difference(unary_union(bars)))
    wall.prism(hole, surface-.205, surface-.180, GLASS, name+' glass')
    wall.prism(frame, surface-.17, surface-.115, FRAME, name+' frames')
    reveal = hole.buffer(.025, join_style=2).difference(hole.buffer(-.012, join_style=2))
    wall.prism(reveal, surface-.205, surface+.005, REVEAL, name+' inner reveal')


def plan_solid(b, wall, polygon, low, high, material, name):
    # The planar source uses (along the garden face, out toward the garden).
    ring = [tuple(wall.point(u, 0, d)[:2]) for u,d in polygon.exterior.coords]
    b.plan_prism(Polygon(ring), low, high, material, name)


def column_pair(b, wall, center, d, foot, head, lod, label):
    radius = .114
    profile = [(foot, .15), (foot+.045, .15), (foot+.074, .143),
               (foot+.096, .125), (foot+.15, radius), (head-.27, .101),
               (head-.245,.119), (head-.205,.119), (head-.16,.137)]
    for i,axis in enumerate((center-.151,center+.151),1):
        b.lathe(wall.point(axis,0,d)[:2],profile,WHITE,10 if lod else 20,
                f'{label} shaft {i}')
        if not lod:
            for side in (-1,1):
                turns = []
                for step in range(17):
                    angle = math.tau*.97*step/16
                    rad = .071-.052*step/16
                    turns.append((axis + side*(.095+rad*math.cos(angle)),
                                  head-.116+rad*math.sin(angle)))
                curl = LineString(turns).buffer(.015)
                wall.prism(curl,d+.085,d+.139,WHITE,f'{label} capital scroll {i} {side}')
        wall.box(axis,head-.099,.32,.11,.31,d,WHITE,f'{label} abacus {i}')
    wall.box(center,head-.029,.69,.058,.36,d,STONE,label+' joined cap')


def pedestal(wall, u, d, low, high, width, depth, name):
    wall.box(u,(low+high)/2,width,high-low,depth,d,STONE,name+' body')
    wall.box(u,low+.055,width+.052,.11,depth+.046,d,STONE,name+' foot')
    wall.box(u,high-.046,width+.066,.092,depth+.058,d,WHITE,name+' cap')


def stone_rail(b,wall,a,z,d,left,right,lod,name):
    """A solid curb with individual lathed balusters and open air between them."""
    width = right-left
    wall.box((left+right)/2,a+.105,width,.21,.23,d,STONE,name+' curb')
    wall.box((left+right)/2,z-.055,width,.11,.245,d,WHITE,name+' cap rail')
    wall.box((left+right)/2,z-.125,width,.045,.182,d,STONE,name+' throat')
    base = a+.205
    top = z-.143
    count = max(1,round(width/.212))
    for i in range(count):
        u = left+(i+.5)*width/count
        heights = [(0,.067),(.09,.067),(.19,.049),(.36,.033),(.48,.039),
                   (.65,.064),(.79,.068),(.92,.047),(1,.059)]
        if lod:
            heights = [heights[k] for k in (0,2,3,6,8)]
        profile = [(base+(top-base)*h,r) for h,r in heights]
        b.lathe(wall.point(u,0,d)[:2],profile,WHITE,6 if lod else 12,
                f'{name} vase {i+1}')


def steps(b,wall,axis,front,landing,halfwidth,lod):
    # In 2024 the center of each tread reads nearly straight, with broad curved ends.
    for n in range(4):
        r = 3-n
        half = halfwidth + .108*r
        run = .22+.267*r
        crown = .078+.016*r
        sides = 12 if lod else 28
        outline = [(axis-half,front-.012),(axis+half,front-.012)]
        outline.extend((axis+half*math.cos(math.pi*k/sides),
                        front+run+.5*crown*(1-math.cos(2*math.pi*k/sides)))
                       for k in range(sides+1))
        plan_solid(b,wall,Polygon(outline),landing*n/4,landing*(n+1)/4,
                   STONE,f'South stair curved tread {n+1}')


def terrace_lattice(wall, left, right, base, d, lod, name):
    """Rectangular openings and the photographed interrupted horizontal lattice band."""
    width=right-left
    wall.box((left+right)/2,base+.045,width,.09,.145,d,STONE,name+' plinth')
    wall.box((left+right)/2,base+.68,width,.085,.17,d,WHITE,name+' cap')
    wall.box((left+right)/2,base+.29,width,.052,.098,d,STONE,name+' crossing rail')
    count=max(2,round(width/.235))
    for i in range(1,count):
        u=left+i*width/count
        wall.box(u,base+.35,.045,.64,.098,d,STONE,f'{name} stave {i}')
    if not lod:
        for i in range(count):
            u=left+(i+.5)*width/count
            if i%3!=1:
                wall.box(u,base+.184,.037,.20,.083,d,STONE,f'{name} short stave {i}')


def build_garden_face(b,wall,D,lod):
    """Make the southern wall, recessed openings, open colonnade and eastern arched bay."""
    width = D['width']
    west,east=-width*.5,width*.5
    split=east-D['garden_east_width']
    porch=split-west
    depth=D['porch_depth']
    wing=D.get('garden_wing_projection',depth)
    eave=D['wall_eave']
    floor=D.get('garden_landing_height',.62)
    lower=D['ground_sill']
    upper=D['upper_sill']
    deck=upper-.47
    eastmid=(split+east)*.5
    brickthick=.235
    axes=[west+porch*t for t in (.166,.350,.537,.878)]
    # Four openings per floor. At terrace level only the second axis is the main doorway.
    wall_holes=[]
    apertures=[]
    for level in (0,1):
        for i,x in enumerate(axes):
            is_door=level==0 and i==1
            sill=(floor if is_door else lower) if level==0 else upper-.12
            head=(lower+1.67 if level==0 else eave-1.23)
            w=porch*(.125 if is_door else (.111 if i==3 else .103))
            h=box(x-w/2,sill,x+w/2,head)
            wall_holes.append(h)
            apertures.append((h,is_door,f'South {"upper" if level else "veranda"} opening {i+1}'))
    solid=box(west,0,split,eave).difference(unary_union(wall_holes))
    # The sheltered wall visible beneath the deck is finished in warm pale render.
    # It meets the exposed second-storey brickwork behind the terrace edge.
    lower_body=solid.intersection(box(west,0,split,deck))
    upper_body=solid.intersection(box(west,deck,split,eave))
    wall.prism(lower_body,-brickthick,0,STONE,'Garden / rendered lower wall')
    wall.prism(upper_body,-brickthick,0,BRICK,'Garden / exposed upper brick')
    for i in range(12):
        z=deck+.145+.285*i
        if z+.141>eave:break
        span=.25 if i%2==0 else .13
        wall.box(west+span/2,z,span,.274,.064,.023,STONE,'Garden / upper west quoins')
    for h,is_door,name in apertures:
        fenestration(wall,h,0,2 if is_door else 3,(.31,.64,.83),name)
        ring=h.buffer(.041,join_style=2).difference(h)
        wall.prism(ring,-.036,.025,STONE,name+' slim surround')
    # The projecting eastern bay has stacked round-headed openings and a distinct apron.
    arch_width=(east-split)*.475
    spring_rise=arch_width*.43
    lower_arch=arched(eastmid,lower,arch_width,deck-lower-.20,spring_rise,10 if lod else 28)
    upper_arch=arched(eastmid,deck+.15,arch_width,eave-deck-.41,spring_rise,10 if lod else 28)
    wingwall=box(split,0,east,eave).difference(unary_union([lower_arch,upper_arch]))
    wall.prism(wingwall,wing-brickthick,wing,BRICK,'East garden bay with stacked arches')
    for i,hole in enumerate((lower_arch,upper_arch),1):
        fenestration(wall,hole,wing,4,(.24,.46,.68,.80),f'South arched bay {i}')
        ring=hole.buffer(.116,join_style=1).difference(hole)
        wall.prism(ring,wing-.012,wing+.106,STONE,f'South arched bay {i} architrave')
    # Both returns end on the primary house skin. These are wall thicknesses, not filled rooms.
    for edge,side in ((split,1),(east,-1)):
        wall.box(edge+side*brickthick/2,eave/2,brickthick,eave,wing,wing/2,BRICK,
                 'Garden wing return '+('west' if edge==split else 'east'))
        for k in range(int(eave/.285)):
            span=.29 if k%2==0 else .155
            wall.box(edge+side*span/2,.16+k*.285,span,.271,.066,wing+.022,
                     STONE,f'Garden wing quoin {edge==split}')
            turn=.16 if k%2==0 else .27
            wall.box(edge+side*.018,.16+k*.285,.066,.271,turn,wing-turn/2,
                     STONE,f'Garden quoin return {edge==split}')
    # The 2024 frontal view shows a pale, uninterrupted apron between the
    # arches. Its curved sill follows the outside of the black balcony rail.
    waist_half=arch_width/2+.11
    wall.box(eastmid,deck-.005,2*waist_half,.303,.121,wing+.033,
             STONE,'Garden bay / stone apron between arches')
    guard_half=arch_width*.535
    along=[-1+2*i/(12 if lod else 28) for i in range((12 if lod else 28)+1)]
    for name,z0,z1,rim in [('apron ledge',deck+.117,deck+.170,.017),
                           ('balcony coping',deck+.170,deck+.203,.045)]:
        front_curve=[(eastmid+guard_half*t,wing+.096+.29*(1-t*t)+rim) for t in along]
        slab=Polygon([(eastmid-guard_half,wing-.025),(eastmid+guard_half,wing-.025),
                      *reversed(front_curve)])
        plan_solid(b,wall,slab,z0,z1,STONE,'Garden bay / '+name)
    # Ground-floor deck stays open to the garden from the door, up the four steps.
    front=depth+.08
    westfront=west-.08
    wall.box((westfront+split)/2,floor/2,split-westfront,floor,front+.03,front/2-.015,
             STONE,'South colonnade floor')
    beamlow=deck-.215
    wall.box((westfront+split)/2,deck-.100,split-westfront,.20,front+.035,front/2-.014,
             WHITE,'South colonnade ceiling and terrace slab')
    wall.box((westfront+split)/2,deck-.105,split-westfront+.10,.17,.17,front+.004,
             EAVES,'South terrace front fascia')
    wall.box((westfront+split)/2,deck-.006,split-westfront+.13,.065,.25,front+.020,
             TILE,'South narrow tile drip')
    toe=floor+.77
    column_d=front-.175
    for i,t in enumerate((.033,.690),1):
        column_pair(b,wall,west+porch*t,column_d,toe,beamlow,lod,
                    f'South paired Ionic group {i}')
    dooraxis=axes[1]
    half=porch*.113
    leftj,rightj=dooraxis-half,dooraxis+half
    leftend=westfront+.02
    for i,(l,r) in enumerate(((leftend,leftj-.11),(rightj+.11,split-.04)),1):
        stone_rail(b,wall,floor,toe,column_d,l,r,lod,f'South veranda railing {i}')
    for i,x in enumerate((leftj-.16,rightj+.16),1):
        pedestal(wall,x,column_d,floor,toe+.063,.29,.34,f'South stair post {i}')
    steps(b,wall,dooraxis,front,floor,half,lod)
    # The upper balcony in the 2021 photos has a rectangular stone grille.
    piers=[west+porch*t for t in (.044,.239,.478,.689,1.)]
    for i,(left,right) in enumerate(zip(piers,piers[1:]),1):
        terrace_lattice(wall,left+.13,right-.13,deck,front-.09,lod,f'South upper rail {i}')
    for i,x in enumerate(piers[:-1],1):
        pedestal(wall,x,front-.09,deck,deck+.78,.28,.29,f'South terrace pier {i}')
    # A shallow, curved, open iron guard spans the projecting bay's second-floor window.
    zl=deck+.20
    q=arch_width*.535
    m=10 if lod else 24
    for z in (zl+.067,zl+.85):
        rail=[wall.point(eastmid+q*t,z,wing+.096+.29*(1-t*t))
              for t in [-1+2*i/m for i in range(m+1)]]
        b.tube(rail,.024,IRON,6 if lod else 10,'East bay guard continuous rail')
    for i in range(12):
        t=-1+2*i/11
        d=wing+.096+.29*(1-t*t)
        profile=[wall.point(eastmid+q*t,zl+h,d+delta)
                 for h,delta in ((.075,0),(.24,.035),(.45,.058),(.64,.012),(.85,0))]
        b.tube(profile,.016,IRON,5 if lod else 8,f'East bay iron guard stave {i+1}')
    # The roof body is provided by the main house builder; the visible attic front has real glazing.
    aw=(east-split)*.60
    atticbase=eave-.04
    attichead=eave+D.get('garden_attic_front_height',1.17)
    atticglass=box(eastmid-aw*.39,atticbase+.18,eastmid+aw*.39,attichead-.15)
    surface=box(eastmid-aw/2,atticbase,eastmid+aw/2,attichead).difference(atticglass)
    wall.prism(surface,wing-.25,wing-.012,STONE,'Garden bay attic face')
    fenestration(wall,atticglass,wing-.012,5,(.5,), 'Garden bay attic window')
    return dict(south_openings=[4,4],paired_columns=[2,2],eastern_arches=2,steps=4,
                east_wing_face_depth=wing,attic_top=attichead,attic_center=eastmid)
