"""Documented Zhonghua Road clock bay and its immediately adjoining windows.

The 1999 heritage plaque and 2017/2019 street views identify the historic
architecture. Local X increases toward the west and Y points into the facade.
Only the public elevation, short structural section, and clock roof are included.
"""
from math import cos, sin, pi, copysign
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

WALL = 'Buff ochre render'
COAT = 'Light ochre quoins'
LIME = 'Pale sand limestone'
STONE = 'Weathered stone mouldings'
UNDER = 'Sheltered stone'
GLASS = 'Grey green window glass'
FRAME = 'Dark sash'
METAL = 'Patinated roof'
RIB = 'Dark roof seams'
DIAL = 'Clock enamel'
MARK = 'Raised clock marks'
WOOD = 'Entrance timber'
MATERIALS = {
    WALL: {'color': [.737, .642, .466], 'roughness': .84},
    COAT: {'color': [.804, .716, .541], 'roughness': .83},
    LIME: {'color': [.812, .753, .630], 'roughness': .76},
    STONE: {'color': [.636, .588, .502], 'roughness': .84},
    UNDER: {'color': [.416, .386, .315], 'roughness': .9},
    GLASS: {'color': [.249, .303, .304], 'roughness': .39, 'metallic': .10},
    FRAME: {'color': [.236, .238, .218], 'roughness': .72},
    METAL: {'color': [.402, .422, .419], 'roughness': .66, 'metallic': .25},
    RIB: {'color': [.266, .281, .286], 'roughness': .66, 'metallic': .25},
    DIAL: {'color': [.808, .800, .667], 'roughness': .54},
    MARK: {'color': [.159, .163, .147], 'roughness': .59, 'metallic': .19},
    WOOD: {'color': [.210, .215, .172], 'roughness': .76}
}
WIDTH = 22.12
CROWN_Y = 3.31
EAVE = 15.59


def disk(x, z, r, n):
    return Point(x, z).buffer(r, quad_segs=n)


def ellipse_ring(u, z, r, rz, thick, steps=30, start=0, end=pi):
    angles = [start+(end-start)*i/steps for i in range(steps+1)]
    return Polygon([(u+(r+thick)*cos(a), z+(rz+thick)*sin(a)) for a in angles] +
                   [(u+r*cos(a), z+rz*sin(a)) for a in reversed(angles)])


def cornice(face, level, width, label, coarse, depth=.30, material=LIME):
    for k, (h, offset, d) in enumerate([(.16, -.14, depth*.56), (.12, -.015, depth), (.08, .083, depth*1.18)]):
        if coarse and k == 1:
            continue
        face.box(0, level+offset, width, .001+h, d+.32, (d-.32)/2, material, label)


def panes(face, holes, x, sill, w, h, rise, coarse, label, cols=2, rows=3, depth=.27):
    op = opening(x, sill, w, h, rise, 14 if coarse else 26)
    holes.append(op)
    op_inner = op.buffer(-.049, join_style=2)
    bars = [box(x-w/2+w*i/cols-.027, sill, x-w/2+w*i/cols+.027, sill+h)for i in range(1, cols)]
    bars += [box(x-w/2, sill+(h-rise)*j/rows-.032, x+w/2, sill+(h-rise)*j/rows+.032)
             for j in range(1, rows)]
    if rise:
        bars.append(box(x-w/2, sill+h-rise-.040, x+w/2, sill+h-rise+.04))
    frame = op.difference(op_inner.difference(unary_union(bars)))
    face.prism(op.buffer(.009), -depth-.010, -depth, GLASS, label+' panes')
    face.prism(frame, -depth+.013, -depth+.079, FRAME, label+' sash')
    face.box(x, sill-.048, w+.13, .10, .39, -.035, STONE, label+' sill')


def curve(face, points, r, mat, name, segments):
    if len(points) == 2:
        face.line(points[0], points[1], r, mat, segments, name)
        return
    face.builder.tube([face.point(*p) for p in points], r, mat, segments, face.label+'/'+name)


def foliage(face, side, coarse):
    # Paired hanging flower garlands flank the big arcade's crown. Their
    # visible overall fall and branches repeat symmetrically in the close-up.
    for path in ([(.41, 14.48), (.71, 14.62), (1.01, 14.61), (1.32, 14.46), (1.67, 14.40), (1.93, 14.53), (2.22, 14.61)],
                 [(1.29, 14.42), (1.49, 14.21), (1.75, 14.03), (1.99, 14.04), (2.17, 14.18)]):
        pts = [(side*x, z, .136)for x, z in path]
        curve(face, pts, .083 if coarse else .078, STONE, 'flower garland', 7)
        for i in range(1, len(path)):
            x, z = path[i]
            dx, dz = path[i-1]
            u = side*(.58*x+.42*dx)
            v = .58*z+.42*dz
            for direction in ([-1] if coarse else [-1, 1]):
                leaf = Polygon([(u-.040, v+.027), (u+side*.15, v+direction*.14),
                               (u+side*.227, v+direction*.176), (u+side*.116, v+direction*.014)])
                face.prism(leaf, .092, .235, STONE, 'carved garland leaves')
            if not coarse or i % 2:
                center_x = u+side*.02
                center_z = v-.040
                bead = Polygon([(center_x-.065, center_z), (center_x, center_z-.084),
                                (center_x+.070, center_z), (center_x, center_z+.057)])
                face.prism(bead, .166, .255, STONE, 'carved garland beads')
    for u, v in [(2.21, 14.59), (2.40, 14.31), (2.42, 13.88)]:
        for j in range(5):
            theta = 2*pi*j/5
            cx = side*u+.095*cos(theta)
            cz = v+.095*sin(theta)
            face.prism(disk(cx, cz, .090, 2 if coarse else 4), .105, .229,
                       STONE, 'carved flower clusters')
        face.prism(disk(side*u, v, .074, 6), .191, .273, LIME, 'carved flower buttons')


def upper_arc(face, holes, coarse):
    z = 11.99
    r = 2.0
    semi = opening(0, 11.75, 2*r, r+.24, r, 24 if coarse else 36)
    holes.append(semi)
    face.prism(semi.buffer(.008), -.427, -.415, GLASS, 'recessed upper three-part window')
    head = ellipse_ring(0, z, r, r, .19, 30 if coarse else 50)
    face.prism(head, -.033, .16, STONE, 'architrave around upper window')
    crown_fill = box(-.65, 13.61, .65, 14.03).intersection(semi)
    face.prism(crown_fill, -.425, .006, COAT, 'flat head of rectangular central light')
    face.box(0, 13.604, 1.29, .061, .16, -.052, STONE, 'top of central rectangular sash')
    for sign in (-1, 1):
        face.prism(box(sign*.756-.13, 11.73, sign*.756+.13, 14.00).intersection(semi), -.43, -.008,
                   COAT, 'two solid window piers')
        foliage(face, sign, coarse)
    for xpos in (0., -1.37, 1.37):
        bar = box(xpos-.023, 11.75, xpos+.023, 14.02).intersection(semi)
        face.prism(bar, -.390, -.333, FRAME, 'window mullions')
    face.prism(box(-r, 12.65, r, 12.711).intersection(semi), -.403, -.355, FRAME, 'window transom')
    for i in range(7 if coarse else 13):
        total = 7 if coarse else 13
        a = .18*pi+.64*pi*(i+.5)/total
        leaf = ellipse_ring(0, z, r+.181, r+.181, .069, 3, a-.022, a+.025)
        face.prism(leaf, .120, .223, STONE, 'short arch ornaments')
    key = Polygon([(-.15, 13.99), (.15, 13.99), (.23, 14.56), (-.23, 14.56)])
    face.prism(key, .125, .308, STONE, 'keystone')
    for x, w in ((0, .125), (-.132, .054), (.132, .054)):
        face.box(x, 14.32, w, .45, .205, .252, LIME, 'keystone flutes')
    face.box(0, 11.74, 4.71, .64, .63, .015, LIME, 'projecting window apron')
    face.box(0, 11.38, 4.88, .14, .77, .062, STONE, 'apron bedding course')
    for sign in (-1, 1):
        # Small exposed corbels below the balcony slab, visible from the public road.
        x = sign*2.02
        face.box(x, 10.98, .235, .64, .28, .11, STONE, 'outer window apron bracket')
        face.box(x, 11.15, .30, .31, .40, .14, LIME, 'bracket capital')
    for sign in [-1, 1]:
        face.box(sign*2.30, 12.14, .21, .44, .56, .024, STONE, 'apron end die')


def streetwall(builder, coarse):
    face = Facade(builder, (-WIDTH/2, 0), (WIDTH/2, 0), 'street')
    holes = []
    for side in (-1, 1):
        for i, x in enumerate((4.18, 6.91, 9.68)):
            u = side*x
            panes(face, holes, u, .76, 1.13, 3.15, .55, coarse, 'ground arch', 2, 3, .34)
            panes(face, holes, u, 6.07, 1.22, 2.69, 0, coarse, 'second floor', 2, 3)
            panes(face, holes, u, 11.05, 1.17, 2.18, 0, coarse, 'high sash', 2, 2, .25)
    upper_arc(face, holes, coarse)
    for x in (-.98, .98):
        panes(face, holes, x, 6.05, 1.35, 2.75, 0, coarse, 'street centre second floor', 2, 2)
    door = box(-1.18, .51, 1.18, 3.60)
    holes.append(door)
    face.prism(door.buffer(.004), -.419, -.408, WOOD, 'recessed double entrance')
    for side in (-1, 1):
        face.prism(box(side*.575-.455, 1.51, side*.575+.455, 3.16), -.39, -.353, GLASS, 'entrance panes')
        face.box(side*.56, 1.13, .92, .54, .112, -.336, WOOD, 'entrance door panels')
    face.box(0, 2.08, .064, 2.92, .145, -.321, WOOD, 'door central stile')
    face.prism(box(-WIDTH/2, 0, WIDTH/2, EAVE).difference(unary_union(holes)), -.58,
               0, WALL, 'three-storey street wall')
    # Ashlar courses on the ground floor are cut at the real arched windows.
    for i in range(1, 12):
        z = i*.419
        strip = box(-WIDTH/2, z-.015, WIDTH/2, z+.018).difference(unary_union(holes))
        face.prism(strip, .002, .018, UNDER, 'base stone joints')
    for z in (4.88, 9.55, EAVE-.02):
        cornice(face, z, WIDTH, 'storey cornices', coarse)
    face.box(0, 14.82, WIDTH, .145, .52, .06, STONE, 'under-eave shelf')
    n = 36 if coarse else 62
    for i in range(n):
        face.box((i-(n-1)/2)*(WIDTH-.40)/(n-1), 14.966, .152, .218, .274, .066, STONE, 'main cornice dentils')
    # At either end the fragment ends just beyond the last measured opening.
    for side in (-1, 1):
        for z in (4.88, 9.55, 15.55):
            builder.box((side*(WIDTH/2-.08), 1.40, z), (.16, 2.8, .18), STONE, label='cut cornice end')
    builder.box((0, 1.65, EAVE-.18), (WIDTH, 3.30, .26), UNDER, label='roof plane behind street cornice')
    # The short section against the retained building is deliberately unornamented.
    # It closes the cut faces without assigning openings to the unobserved rear.
    for side in (-1, 1):
        builder.box((side*(WIDTH/2-.08), 1.91, 7.69),
                    (.16, 2.78, 15.38), WALL, label='plain side section')
    builder.box((0, 3.19, 7.69), (WIDTH-.31, .21, 15.38), WALL, label='neutral rear section')
    builder.box((0, 4.39, 7.76), (4.76, 2.17, 15.52), WALL, label='plain clock base section')
    for k in range(4):
        depth = (4-k)*.28
        builder.box((0, -depth/2, k*.128+.064), (2.57, depth, .128), STONE, label='central exterior step')
    # Low stone cheek walls turn outward around the entrance steps, as visible in the frontal view.
    for side in (-1, 1):
        path = [(side*1.38, .03, .37), (side*1.40, -.45, .34),
                (side*1.51, -.85, .30), (side*1.82, -1.04, .28)]
        builder.tube(path, .085, STONE, 7 if coarse else 12, 'outer step coping')


# Original narrow, round-ended numeral strokes. The 2019 frontal close-up
# shows upright Arabic numbers; both hands are fixed at the observed reading.
DIGITS = {
    '0': [(.52, 1), (.18, .95), (.03, .69), (.03, .30), (.18, .05), (.49, 0), (.69, .19), (.70, .78), (.52, 1)],
    '1': [(.11, .76), (.39, 1), (.39, .04)],
    '2': [(.03, .78), (.17, .96), (.47, 1), (.68, .80), (.65, .60), (.04, .04), (.70, .04)],
    '3': [(.05, .88), (.27, .99), (.55, .94), (.68, .75), (.58, .56), (.32, .49), (.56, .44), (.69, .26), (.62, .08), (.35, .0), (.08, .09)],
    '4': [(.52, 0), (.52, 1), (.015, .32), (.71, .32)],
    '5': [(.68, .97), (.14, .97), (.08, .52), (.42, .58), (.64, .47), (.68, .23), (.52, .035), (.22, .02), (.04, .13)],
    '6': [(.58, .98), (.32, .94), (.11, .66), (.05, .30), (.14, .08), (.40, .01), (.63, .12), (.68, .34), (.56, .54), (.30, .57), (.08, .41)],
    '7': [(.015, .98), (.69, .98), (.22, .02)],
    '8': [(.35, .51), (.13, .65), (.10, .86), (.29, .99), (.52, .96), (.66, .80), (.58, .63), (.35, .51), (.11, .38), (.05, .19), (.19, .04), (.48, .01), (.66, .15), (.64, .35), (.35, .51)],
    '9': [(.07, .10), (.28, .02), (.53, .14), (.66, .44), (.67, .78), (.56, .95), (.32, 1), (.12, .91), (.04, .70), (.17, .51), (.43, .49), (.65, .63)]
}


def clock(face, coarse):
    z = 17.82
    n = 20 if coarse else 36
    for radius, behind, ahead, material, name in [
        (1.122, .005, .114, STONE, 'carved outer clock surround'), (1.034, .105, .151, UNDER, 'bedded ring shadows'),
        (.969, .146, .219, LIME, 'carved inner clock rim'), (.846, .211, .242, MARK, 'dial bezel'),
            (.796, .238, .252, DIAL, 'cream circular dial')]:
        face.prism(disk(0, z, radius, n), behind, ahead, material, name)
    count = 18 if coarse else 32
    for i in range(count):
        a = 2*pi*i/count
        # Curled blocks stand proud of the two annular beds.
        A = ellipse_ring(0, z, .979, .979, .094, 4, a+.009, a+2*pi/count-.009)
        face.prism(A, .139, .216, STONE if i % 2 else LIME, 'clock border scrolls')
    for i in range(12):
        a = pi/2-2*pi*i/12.
        u = .703*cos(a)
        v = z+.703*sin(a)
        curve(face, [(.745*cos(a), z+.745*sin(a), .262), (.779*cos(a),
              z+.779*sin(a), .262)], .012, MARK, 'hour divisions', 5)
        digits = str(i or 12)
        h = .158 if len(digits) == 1 else .146
        advance = .80*h
        for j, char in enumerate(digits):
            x = u+(j-(len(digits)-1)/2)*advance-.34*h
            outline = [(x+h*px, v+h*(pz-.5), .264) for px, pz in DIGITS[char]]
            curve(face, outline, .014 if not coarse else .016, MARK, 'upright clock numerals', 5)
    for name, theta, length, width in [('hour', 2.11, .462, .048), ('minute', -.665, .660, .029)]:
        ex, ez = cos(theta), sin(theta)
        coords = [(-.093, -width), (length*.60, -width), (length, 0), (length*.52, width), (-.093, width)]
        pointer = Polygon([(s*ex-t*ez, z+s*ez+t*ex)for s, t in coords])
        face.prism(pointer, .277, .322, MARK, name+' hand')
    face.prism(disk(0, z, .069, 8), .317, .353, MARK, 'clock hand pin')


def tower_column(face, x, coarse):
    X, Y, _ = face.point(x, 0, .144)
    profile = [(15.99, .165), (16.06, .216), (16.18, .206), (16.26, .158),
               (16.35, .132), (17.67, .127), (18.93, .115), (19.00, .148), (19.085, .160), (19.20, .213)]
    face.builder.lathe((X, Y), profile, LIME, 9 if coarse else 16, 'clock tower paired corner shafts')
    face.box(x, 19.235, .51, .094, .47, .117, STONE, 'square capital slabs')
    for sign in (-1, 1):
        tip = x+sign*.127
        face.prism(disk(tip, 19.10, .077, 5 if coarse else 10), .237, .309,
                   STONE, 'capital corner volutes')
        face.prism(disk(tip, 19.10, .029, 4), .297, .32, LIME, 'volute eyes')
    for u in (-.065, .065):
        leaf = Polygon([(x+u, 18.98), (x+u-.043, 19.041), (x+u, 19.172), (x+u+.043, 19.047)])
        face.prism(leaf, .241, .289, STONE, 'capital leaves')


def cupola(builder, coarse):
    # Square plan with rounded, ribbed shoulders on four curved slopes.
    # The very top is a short flat plinth, visible below the terminal needle.
    N = 28 if coarse else 64
    rings = [(19.80, 2.40, 2.17, 7.), (19.98, 2.40, 2.17, 7.),
             (20.01, 2.33, 2.06, 6.), (20.14, 2.33, 2.06, 6.),
             (20.18, 2.24, 1.98, 5.), (20.28, 2.23, 1.96, 4.9),
             (20.57, 2.18, 1.88, 4.6), (20.86, 2.07, 1.75, 4.2),
             (21.08, 1.93, 1.59, 3.9), (21.27, 1.77, 1.43, 3.8),
             (21.41, 1.59, 1.32, 3.8), (21.49, 1.39, 1.13, 4.0),
             (21.53, 1.14, .86, 4.5)]

    def station(theta, profile):
        z, rx, ry, power = profile
        c = cos(theta)
        s = sin(theta)
        return (rx*copysign(abs(c)**(2/power), c), CROWN_Y+ry*copysign(abs(s)**(2/power), s), z)
    vs = [station(2*pi*i/N, row)for row in rings for i in range(N)]
    faces = []
    for h in range(len(rings)-1):
        for i in range(N):
            j = (i+1) % N
            faces.append((h*N+i, h*N+j, (h+1)*N+j, (h+1)*N+i))
    faces.append(tuple(range((len(rings)-1)*N, len(rings)*N)))
    faces.append(tuple(reversed(range(N))))
    builder.add(vs, faces, METAL, 'clock cupola folded roof')
    for i in range(8 if coarse else 16):
        a = 2*pi*i/(8 if coarse else 16)
        points = [station(a, (z+.014, rx+.010, ry+.010, pow))for z, rx, ry, pow in rings[2:]]
        builder.tube(points, .014 if not coarse else .024, RIB, 5, 'radial sheet ribs')
    for z, w, d, h in [(21.685, 1.27, 1.06, .31), (21.936, .99, .83, .20), (22.137, .74, .62, .21), (22.422, .45, .40, .37)]:
        builder.box((0, CROWN_Y, z), (w, d, h), RIB, label='stepped finial plinth')
    builder.lathe((0, CROWN_Y), [(22.60, .050), (22.79, .039),
                  (24.86, .017)], RIB, 8, 'slender clock finial')


def clock_stage(builder, coarse):
    half = 2.42
    cy = CROWN_Y
    depth = 2.0
    y0 = cy-depth
    y1 = cy+depth
    builder.box((0, cy, 17.63), (2*half, 2*depth, 4.03), WALL, label='square clock stage')
    f = Facade(builder, (-half, y0), (half, y0), 'clock')
    for side in (-1, 1):
        for x in (1.83, 2.17):
            tower_column(f, side*x, coarse)
        # Radial shallow joints in the flat stone surround.
        for a in (.30, .65, 1.0):
            curve(f, [(side*1.12*cos(a), 17.82+1.12*sin(a), .013),
                      (side*1.60*cos(a), 17.82+1.60*sin(a), .013)], .014, STONE, 'clock panel joints', 5)
    clock(f, coarse)
    # In both oblique views, dark vertical side glazing can be read at the upper stage.
    for x, side in [(-half, -1), (half, 1)]:
        sf = Facade(builder, (x, y1), (x, y0), 'east return') if side < 0 else Facade(
            builder, (x, y0), (x, y1), 'west return')
        sf.box(0, 17.59, 1.38, 2.23, .042, .04, FRAME, 'side sash')
        for dx in (-.33, .33):
            sf.box(dx, 17.60, .58, 1.92, .045, .074, GLASS, 'side sash lights')
        sf.box(0, 17.91, 1.28, .054, .088, .087, FRAME, 'side window transom')
    for z, w, d, h, mat in [(15.80, 5.26, 4.52, .19, STONE), (15.96, 5.03, 4.35, .14, LIME),
                            (19.40, 5.24, 4.54, .20, STONE), (19.57, 5.56, 4.79, .16, LIME), (19.74, 5.72, 4.95, .18, STONE)]:
        builder.box((0, cy, z), (w, d, h), mat, label='clock stage cornice')
    n = 16 if coarse else 30
    for i in range(n):
        f.box((i-(n-1)/2)*5.18/n, 19.36, .095, .17, .24, .28, STONE, 'clock dentils')
    cupola(builder, coarse)


def add_building(builder, distant):
    streetwall(builder, distant)
    clock_stage(builder, distant)
