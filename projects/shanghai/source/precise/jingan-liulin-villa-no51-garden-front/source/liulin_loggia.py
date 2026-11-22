"""No. 51 central garden loggia. Coordinates in metres, +Y towards the house.

The original source images, two-camera fit and measured silhouettes are documented
in ../measurements. The separately authored garden door, terrace brickwork, two
side bays and window enclosure meet this component in the shared house datum.
"""
import math
import numpy as np

PREFIX = 'No.51 loggia | '
PLASTER = PREFIX + 'warm ivory lime plaster'
EDGE = PREFIX + 'painted stone fillets'
REVEAL = PREFIX + 'sheltered mouldings'
FLOOR = PREFIX + 'grey cement wearing surface'
PLINTH = PREFIX + 'pale stone pedestal'
APRON = PREFIX + 'shadowed floor edge'


def finish(rgb, roughness):
    srgb = np.array(rgb) / 255
    linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb + .055) / 1.055)**2.4)
    return dict(color=linear.tolist(), roughness=roughness)


PALETTE = {
    PLASTER: finish((200, 194, 180), .84), EDGE: finish((209, 203, 190), .76),
    REVEAL: finish((176, 170, 156), .88), FLOOR: finish((150, 145, 132), .91),
    PLINTH: finish((186, 180, 167), .85), APRON: finish((161, 154, 141), .87),
}
COLUMNS = np.array([[-3.0691, .0224], [-2.7020, .0177], [2.6653, -.1015], [3.0678, .0958]])
# Median of four native scan heights, optical axis intersected at each spindle's mid-depth.
RAIL_X = (
    -3.725, -3.535, -3.323, -2.383, -2.140, -1.921, -1.687, -1.461, -1.231,
    -1.011, -.789, -.553, -.319, -.079, .167, .415, .649, .895, 1.127, 1.368,
    1.571, 1.844, 2.072, 2.310, 3.391, 3.629, 3.823,
)
LEFT, RIGHT = -4.36, 4.28


def rail_y(x):
    return -.41797645 + .01207329*x + .03755177*x*x


def terrace_y(x):
    return -.49874407 - .00252176*x + .04703376*x*x


def from_sections(builder, rings, material, label):
    """Loft consistently wound, convex sections with a closed cap at each end."""
    rings = np.asarray(rings)
    n = len(rings[0])
    faces = [tuple(reversed(range(n)))]
    for k in range(len(rings)-1):
        for i in range(n):
            j = (i+1) % n
            a = k*n
            faces.append((a+i, a+j, a+n+j, a+n+i))
    faces.append(tuple(range((len(rings)-1)*n, len(rings)*n)))
    builder.add(rings.reshape((-1, 3)), faces, material, PREFIX+label)


def turned(builder, xy, levels, sides, material, label, angle=0.):
    theta = angle + np.arange(sides)*2*math.pi/sides
    circle = np.column_stack([np.cos(theta), np.sin(theta)])
    rings = [np.column_stack([xy+radius*circle, np.full(sides, z)]) for z, radius in levels]
    from_sections(builder, rings, material, label)


def rectangular(builder, xy, rotation, levels, material, label):
    local = np.array([[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]])
    rings = []
    for z, width, depth in levels:
        plan = xy + (local*[width, depth]) @ rotation.T
        rings.append(np.column_stack([plan, np.full(4, z)]))
    from_sections(builder, rings, material, label)


def rotated(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s], [s, c]])


def sweep(builder, x, front, section, material, label, back=None):
    """Sweep a convex depth/elevation section along the bow, cutting its two ends."""
    rings = []
    for value in x:
        yz = [(back if depth is None else front(value)+depth, z) for depth, z in section]
        rings.append([[value, y, z] for y, z in yz])
    from_sections(builder, rings, material, label)


def strip(builder, x, front, lower, upper, material, label, back=None):
    # At fixed X the sequence is CCW in the YZ plane (normal towards +X).
    z0, outer0, inner0 = lower
    z1, outer1, inner1 = upper
    sweep(builder, x, front, [(outer0, z0), (inner0, z0), (inner1, z1), (outer1, z1)],
          material, label, back)


def add_decks(builder, x, low):
    flat = lambda value: -.38
    strip(builder, [LEFT, RIGHT], flat, (.11, .015, None), (.485, .015, None),
          PLINTH, 'raised garden landing under entrance', back=2.45)
    strip(builder, [LEFT, RIGHT], flat, (.485, 0., None), (.523, 0., None),
          FLOOR, 'landing meeting the third photographed tread', back=2.45)

    # Recess, bevel and bead elevations read across the two column capitals and
    # the centre of the rectified curved fascia. Bands are continuous to the wings.
    for label, shape, levels in [
        ('first balcony', rail_y, [(4.25, .155), (4.282, .155), (4.311, .077),
            (4.353, .077), (4.405, .022), (4.499, .014), (4.54, -.009),
            (4.577, -.010), (4.625, -.051), (4.653, -.067), (4.736, -.067), (4.768, -.045)]),
        ('roof terrace', terrace_y, [(8.172, .230), (8.211, .225), (8.24, .182),
            (8.304, .175), (8.355, .085), (8.409, .067), (8.482, -.014),
            (8.551, -.015), (8.591, -.058), (8.716, -.058), (8.740, -.040)]),
    ]:
        start, end = levels[0][0], levels[-1][0]
        strip(builder, x, shape, (start, .230, None), (end-.035, .230, None),
              REVEAL, label+' slab and soffit', back=2.48)
        strip(builder, x, shape, (end-.035, .230, None), (end, .230, None),
              FLOOR, label+' walking surface', back=2.48)
        if low:
            levels = [levels[0], levels[3], levels[-4], levels[-2], levels[-1]]
        for i, ((z0, off0), (z1, off1)) in enumerate(zip(levels, levels[1:])):
            # Keep every fascia band's thickness positive at the most recessed edge.
            strip(builder, x, shape, (z0, off0, .248), (z1, off1, .248),
                  EDGE if abs(off1-off0)>.017 else PLASTER, f'{label} fascia band {i+1:02d}')


def add_columns(builder, low):
    for pair_index in range(2):
        indices = [pair_index*2, pair_index*2+1]
        first, second = COLUMNS[indices]
        vector = second-first
        rotation = rotated(math.atan2(vector[1], vector[0]))
        width = np.linalg.norm(vector) + .491
        centre = (first+second)/2
        for floor, platform, shelf, shaft_start, neck, cornice in [
            ('lower', .523, 1.477, 1.867, 3.757, 4.250),
            ('upper', 4.754, 5.755, 6.137, 7.67, 8.172),
        ]:
            prefix = f'{floor} pair {pair_index+1} '
            rectangular(builder, centre, rotation,
                        [(shelf, width-.025, .473), (shelf+.022, width, .508),
                         (shelf+.145, width, .508), (shelf+.170, width-.020, .492)],
                        EDGE, prefix+'one continuous pedestal cap')
            for index in indices:
                xy = COLUMNS[index]
                label = f'{floor} column {index+1} '
                rectangular(builder, xy, rotation,
                            [(platform, .412, .396), (platform+.037, .413, .400),
                             (platform+.176, .405, .390), (platform+.216, .350, .337)],
                            PLINTH, label+'individual plinth and bevel')
                rectangular(builder, xy, rotation,
                            [(platform+.212, .348, .338), (shelf, .339, .329)],
                            PLASTER, label+'panelled square pedestal')
                if not low:
                    for side in range(4):
                        side_rotation = rotation @ rotated(side*math.pi/2)
                        # Four narrow painted borders around a shallow recessed face.
                        top = shelf-.048
                        bottom = platform+.248
                        for dx in (-.139, .139):
                            edge_xy = xy + side_rotation @ [dx, -.165]
                            rectangular(builder, edge_xy, side_rotation,
                                        [(bottom,.014,.012),(top,.014,.012)],EDGE,label+'panel stile')
                        for z in (bottom, top-.014):
                            edge_xy = xy + side_rotation @ [0., -.165]
                            rectangular(builder, edge_xy, side_rotation,
                                        [(z,.290,.012),(z+.014,.290,.012)],EDGE,label+'panel rail')
                bottom = shaft_start
                mould = [(-.222,.213),(-.197,.214),(-.174,.189),(-.134,.174),
                         (-.117,.183),(-.099,.191),(-.082,.186),(-.067,.164),
                         (-.048,.161),(-.039,.179),(-.023,.180),(-.008,.163),(0.,.151)]
                if low:
                    mould = [mould[j] for j in (0,2,4,5,7,9,10,12)]
                turned(builder, xy, [(bottom+h,r) for h,r in mould], 12 if low else 28,
                       EDGE, label+'two rolls above spreading base')
                # Both storeys taper from 0.30 m to 0.26 m on the paired source silhouettes.
                turned(builder, xy, [(bottom,.151),(bottom+.15,.150),
                       (bottom+(neck-bottom)*.55,.141),(neck,.130)], 12 if low else 28,
                       PLASTER, label+'tapering shaft')
                cap = [(neck,.130),(neck+.012,.143),(neck+.028,.147),(neck+.044,.135),
                       (neck+.055,.151),(neck+.074,.152),(neck+.095,.139),
                       (cornice-.225,.148),(cornice-.174,.156),(cornice-.143,.175),
                       (cornice-.106,.210),(cornice-.08,.218),(cornice-.055,.211)]
                if low:
                    cap = [cap[j] for j in (0,2,3,5,6,8,10,12)]
                turned(builder, xy, cap, 12 if low else 28, PLASTER, label+'neck rings and flared capital')
            rectangular(builder, centre, rotation,
                        [(cornice-.056, width-.038, .462),(cornice-.034, width, .493),
                         (cornice+.025, width, .493)], EDGE, prefix+'paired capital abacus')


def add_railing(builder, x, low):
    rails = [
        ('lower sill', [(4.873, -.014, .211), (4.898, -.026, .225),
                         (5.017, -.026, .225), (5.040, -.010, .214)]),
        ('upper handrail', [(5.724, -.008, .210), (5.748, -.033, .233),
                             (5.857, -.035, .236), (5.884, -.010, .218)]),
    ]
    for name, levels in rails:
        for i,(lower,upper) in enumerate(zip(levels, levels[1:])):
            strip(builder, x, rail_y, lower, upper, EDGE if i!=1 else PLASTER, name+f' profile {i+1}')
    for i, xp in enumerate([-4.034, -.880, .814, 4.072]):
        rotation = rotated(math.atan(.01207329+2*.03755177*xp))
        end = i in (0,3)
        z0, z1 = (4.748,5.887) if end else (4.749,4.890)
        width = .298 if end else .278
        rectangular(builder, np.array([xp,rail_y(xp)+.082]), rotation,
                    [(z0,width+.012,.231),(z1,width,.228)],
                    PLASTER, ('end newel ' if end else 'opening below sill, foot ')+str(i+1))
    # The shafts have flat faces and arrises. The central row in the rectified
    # source has 21 open balusters, with three more beyond each paired pedestal.
    profile = [(5.036,.143),(5.115,.143),(5.139,.129),(5.164,.088),(5.174,.082),
               (5.199,.110),(5.210,.129),(5.230,.130),(5.248,.111),
               (5.444,.087),(5.462,.103),(5.480,.117),(5.499,.101),
               (5.516,.076),(5.539,.099),(5.551,.113),(5.571,.102),
               (5.591,.121),(5.609,.140),(5.729,.140)]
    if low:
        profile = [profile[j] for j in (0,1,4,7,8,9,11,13,16,18,19)]
    for i, xp in enumerate(RAIL_X):
        rotation = rotated(math.atan(.01207329+2*.03755177*xp))
        rectangular(builder, np.array([xp,rail_y(xp)+.085]), rotation,
                    [(z,w,w) for z,w in profile],PLASTER,f'carved square baluster {i+1:02d}')


def add_loggia(builder, lod=False):
    low = lod is True or lod in ('lod','low','distant')
    x = np.linspace(LEFT, RIGHT, 10 if low else 37)
    add_decks(builder, x, low)
    add_columns(builder, low)
    add_railing(builder, x, low)
