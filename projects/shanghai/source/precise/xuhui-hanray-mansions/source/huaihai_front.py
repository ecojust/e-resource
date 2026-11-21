"""Build the Huaihai Road side of Hanray Mansions in a measured local plan."""
from math import cos, pi, sin

from shapely import union_all
from shapely.geometry import LineString, Polygon, box

from photo_architecture import Facade

TILE = 'cream glazed brick'
FLUTE = 'fine grooved ochre tile'
JOINT = 'sand coloured joints'
STONE = 'pale artificial stone'
SASH = 'weathered window metal'
GLASS = 'blue grey window glass'
BASE = 'grey shop plinth'
ROOF = 'terrace paving'
SECTION = 'unexposed section'
PALETTE = {name: {'color': colour, 'roughness': rough, 'metallic': metal}
           for name, colour, rough, metal in [
               (TILE, [.72, .577, .395], .66, 0), (FLUTE, [.557, .414, .282], .76, 0),
               (JOINT, [.591, .482, .357], .85, 0), (STONE, [.749, .695, .609], .78, 0),
               (SASH, [.347, .367, .356], .49, .29), (GLASS, [.294, .389, .407], .29, .23),
               (BASE, [.376, .359, .331], .82, 0), (ROOF, [.556, .496, .412], .93, 0),
               (SECTION, [.648, .542, .409], .86, 0)]}

# Streetward changes of depth correspond to the two projecting window bands.
# The back plane truncates the model before the court and rooftop service rooms.
FRONT = [(-22.58, 2.74), (-17.79, 3.19), (-18.25, .00), (-5.70, .00),
         (-5.48, 2.74), (5.48, 2.97), (5.70, .00), (17.34, 1.60),
         (18.94, 4.79), (21.90, 3.88)]
CUT = 7.32
LEVELS = [4.15, 7.29, 10.43, 13.57, 16.71]
PARAPET = 20.25


def opening(u, w, z, height):
    return box(u - w / 2, z, u + w / 2, z + height)


def front_wall(f, holes, top, lod, bottom=.09):
    surface = f.wall(bottom, top, holes, .23, TILE)
    # Use shallow bed joints and interrupted soldier courses at the sills. Their
    # real apertures remain open across the cut wall, including window returns.
    l, _, r, _ = surface.bounds
    step = .56 if lod else .245
    for i in range(1, int((top - 4.12) / step) + 1):
        z = 4.12 + i * step
        lines = box(l + .018, z, r - .018, z + .016).intersection(surface)
        if lines.area > .0002:
            f.prism(lines, .002, .013, JOINT, 'bed joints')


def glaze(f, aperture, columns, rows, name):
    # The shop doors meet a stone threshold. Upper sashes have a shallow sill
    # modelled separately so the front elevation stays flush with its brickwork.
    left, low, right, high = aperture.bounds
    inner = aperture.buffer(-.085, join_style=2)
    bars = []
    for i in range(1, columns):
        x=left+(right-left)*i/columns
        bars.append(box(x-.028,low,x+.028,high))
    for i in range(1,rows):
        z=low+(high-low)*i/rows
        bars.append(box(left,z-.027,right,z+.027))
    panes = inner.difference(union_all(bars)) if bars else inner
    f.prism(aperture.buffer(.012,join_style=2),-.34,-.32,GLASS,name+'/glass')
    f.prism(aperture.buffer(-.025,join_style=2).difference(panes),-.27,-.16,SASH,name+'/metal frame')


def casement(f, aperture, cols, lod, tag='sash'):
    glaze(f, aperture, cols, 2, tag)
    x0, z0, x1, z1 = aperture.bounds
    f.box((x0+x1)/2, z0-.055, x1-x0+.085, .10, .19, .044, STONE, 'window sill')
    if not lod and cols > 1:
        for i in range(1, cols):
            if i % 2 == 0:
                x = x0 + (x1-x0)*i/cols
                f.box(x, (z0+z1)/2, .074, z1-z0, .102, -.105, SASH, 'paired outer stiles')


def shopfront(f, type_, lod):
    width = f.length
    if type_ == 'return':
        return []
    if type_ == 'centre':
        holes = [opening(0, 3.44, .10, 2.87)]
        for side in (-1, 1):
            holes.append(opening(side * 3.65, 2.22, .41, 2.34))
    else:
        span = width * (.80 if width > 7 else .57)
        holes = [opening(0, span, .42, 2.39)] if span > .7 else []
    for hole in holes:
        is_door = type_ == 'centre' and abs(hole.centroid.x)<.1
        glaze(f,hole,4 if hole.bounds[2]-hole.bounds[0]>6 else 2,
              2 if is_door else 1,'street entrance' if is_door else 'shop glazing')
    f.box(0, 3.39, width-.025, .51, .26, .035, STONE, 'continuous shop fascia')
    return holes


def ground_entrance(b, lod):
    # The central bank glazing turns onto the recessed doorway via curved cheeks.
    for sign in (-1, 1):
        profile = [(sign*(1.80+1.02*(1-cos(i*pi/16))),
                    2.74-.92*sin(i*pi/16)) for i in range(9)]
        for i, (a, end) in enumerate(zip(profile, profile[1:])):
            if sign < 0:
                a, end = end, a
            f = Facade(b, a, end, 'entry/curved return')
            f.wall(.10, 2.99, [], .12, BASE if i==0 else STONE)
    b.plan_prism(box(-1.79, 1.80, 1.79, 2.93), .01, .095, STONE, 'entry/threshold')


def stepped_terrace(b, label, left, right, front, radius, floor, wall_top, lod):
    # Round the two street corners of each floor, retaining its continuous parapet.
    resolution = 8 if lod else 17
    path=[]
    for i in range(resolution+1):
        angle=pi+i*pi/(2*resolution)
        path.append((left+radius+radius*cos(angle), front+radius+radius*sin(angle)))
    for i in range(resolution+1):
        angle=-pi/2+i*pi/(2*resolution)
        path.append((right-radius+radius*cos(angle), front+radius+radius*sin(angle)))
    line=[(left,CUT),*path,(right,CUT)]
    # Both terrace fronts terminate against the raised central street bay.
    axis=box(-5.46, -1, 5.46, CUT+.2)
    plan=Polygon(line).difference(axis)
    b.plan_prism(plan,floor-.25,floor,STONE,label+'/terrace slab')
    b.plan_prism(plan.buffer(-.08,join_style=2),floor-.015,floor+.05,ROOF,label+'/terrace paving')
    parapet=LineString(line).buffer(.125,cap_style=2,join_style=2).difference(axis)
    b.plan_prism(parapet,floor,wall_top,TILE,label+'/continuous curved parapet')
    coping=LineString(line).buffer(.17,cap_style=2,join_style=2).difference(axis)
    b.plan_prism(coping,wall_top,wall_top+.093,STONE,label+'/rounded coping')


def entrance_tower(b, street, lod):
    # The recessed bank entrance is at pavement level. Above the fascia the
    # central pier advances and continues past both terrace parapets.
    left=(-5.48,1.13)
    right=(5.48,1.36)
    face=Facade(b,left,right,'entrance tower')
    upper_levels=[*LEVELS,19.85,22.99]
    sashes=[opening(side*3.66,1.44,z+.29,1.86) for z in upper_levels for side in (-1,1)]
    lights=[opening(side*.41,.40,23.42,1.13) for side in (-1,1)]
    front_wall(face,[*sashes,*lights],25.03,lod,3.69)
    for hole in sashes:
        casement(face,hole,2,lod)
    for hole in lights:
        glaze(face,hole,1,1,'crown/vertical light')
    for side in (-1,1):
        for k in range(3 if lod else 6):
            u=.80+k*(.24 if lod else .12)
            face.box(side*u,14.47,.10,21.51,.20,.095,FLUTE,'continuous flutes')
        face.box(side*2.12,14.39,.27,21.31,.28,.12,STONE,'outer pale jamb')
    # A shallow round crest rising above the straight side parapets remains
    # visible against the upper roof in the oblique street photograph.
    curve=[(1.52*cos(i*pi/20),25.05+.66*sin(i*pi/20)) for i in range(21)]
    face.prism(Polygon([(-1.52,25.0),(1.52,25.0),*curve]),-.31,.23,TILE,'rounded crest')
    for start,end in [((left[0],5.82),left),(right,(right[0],5.82))]:
        Facade(b,start,end,'entrance tower/side return').wall(3.69,25.03,[],.22,TILE)
    cap=Polygon([left,right,(right[0],5.82),(left[0],5.82)])
    b.plan_prism(cap,24.98,25.08,ROOF,'entrance tower/cap')
    b.plan_prism(Polygon([left,right,tuple(street.b[:2]),tuple(street.a[:2])]),3.64,3.74,STONE,'entrance tower/soffit')


def top_storey(b, label, left, right, front, top, bottom, lod):
    f = Facade(b,(left,front),(right,front),label+'/recessed rooms')
    bays=max(3, round((right-left)/4.4));step=(right-left)/bays
    holes=[opening(-f.length/2+step*(i+.5),step*.70,bottom+.49,1.73) for i in range(bays)]
    f.wall(bottom,top,holes,.23,TILE)
    for o in holes:casement(f,o,3,lod)
    for a,end in [((left,CUT),(left,front)),((right,front),(right,CUT))]:
        wall=Facade(b,a,end,label+'/return')
        if wall.length > 2.2:
            o=opening(0,wall.length*.46,bottom+.49,1.73);wall.wall(bottom,top,[o],.23,TILE);casement(wall,o,2,lod)
        else:wall.wall(bottom,top,[],.23,TILE)
    b.plan_prism(box(left,front,right,CUT),top-.16,top,ROOF,label+'/flat roof')
    Facade(b,(right,CUT),(left,CUT),label+'/section').wall(bottom,top,[],.20,SECTION)


def build_front(b, lod):
    for i,(start,end) in enumerate(zip(FRONT, FRONT[1:])):
        typ = 'centre' if i==4 else 'wide' if i in (2,6) else 'end' if i in (0,8) else 'return'
        f = Facade(b,start,end,'street/%s %d'%(typ,i))
        holes=shopfront(f,typ,lod);windows=[]
        if typ=='centre':
            front_wall(f,holes,3.70,lod)
            entrance_tower(b,f,lod)
            continue
        for z in LEVELS:
            if typ=='wide':
                # Repeated broad bands separated by narrow brick posts, including the outer pair.
                for u,w,cols in [(-.29,.25,3),(.085,.41,5),(.395,.14,2)]:
                    windows.append((opening(f.length*u,f.length*w,z+.39,1.82),cols))
            elif typ=='end':windows.append((opening(0,f.length*.38,z+.36,1.75),2))
            elif f.length>2.5:windows.append((opening(0,1.0,z+.4,1.76),1))
        front_wall(f,[*holes,*[o for o,_ in windows]],PARAPET,lod)
        for o,n in windows:casement(f,o,n,lod)
    main=Polygon([*FRONT,(FRONT[-1][0],CUT),(FRONT[0][0],CUT)])
    b.plan_prism(main,.045,.12,BASE,'body/plinth')
    b.plan_prism(main,PARAPET-.28,PARAPET,ROOF,'body/roof below terraces')
    for a,end in [((FRONT[0][0],CUT),FRONT[0]),(FRONT[-1],(FRONT[-1][0],CUT)),((FRONT[-1][0],CUT),(FRONT[0][0],CUT))]:
        Facade(b,a,end,'body/section').wall(.06,PARAPET,[],.19,SECTION)
    ground_entrance(b,lod)
    stepped_terrace(b,'floor 7',-19.95,19.3,1.05,3.1,20.42,21.40,lod)
    top_storey(b,'floor 7',-16.72,16.5,3.56,23.22,20.42,lod)
    stepped_terrace(b,'floor 8',-15.80,15.7,3.24,2.23,23.30,24.17,lod)
    top_storey(b,'floor 8',-11.25,11.23,5.72,25.93,23.30,lod)
