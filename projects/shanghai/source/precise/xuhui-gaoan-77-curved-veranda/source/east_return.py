"""East garden wall and cantilevered terrace, read from the winter garden photograph."""
from math import cos, pi, sin

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from garden_sashes import sash
from house_layout import D, U, Z
from materials import BRICK, DARK, FRAME, GLASS, IRON, PLASTER, RECESS, STONE
from south_verandah import slab

# All pairs are (distance from the garden frontage, height above its timber datum),
# divided by the measured post spacing. The east roof edge is 0.24 m outside the wall.
EAST_WALL_U = 2.55
EAST_EAVE_PROFILE = ((.56, -.045), (.88, -.057), (2.48, -.116), (3.27, -.902))


def pierced_rail(face, begin, end, bottom, top, count, label, lod):
    """Each lower opening has a short opening above its horizontal intermediate rail."""
    pier = .077
    first, last = begin + pier, end - pier
    pitch = (last - first) / count
    opening = pitch * .59
    height = top - bottom
    holes = []
    for index in range(count):
        middle = first + pitch * (index + .5)
        for lo, hi in ((.24, .68), (.735, .905)):
            holes.append(box(middle - opening / 2, bottom + height * lo,
                             middle + opening / 2, bottom + height * hi))
    plate = box(begin, bottom, end, top).difference(unary_union(holes))
    face.solid(plate, -.126, 0., PLASTER, label + ' | open lime balustrade')
    face.rect(begin - .018, end + .018, top - .046, top + .012, -.138, .014,
              STONE, label + ' | continuous coping with drip')
    if not lod:
        # The narrow upper balusters show two small projecting square collars.
        half_width = .55 * (pitch - opening)
        for index in range(1, count):
            centre = first + pitch * index
            for level in (.786, .85):
                z = bottom + height * level
                face.rect(centre - half_width, centre + half_width, z - .008, z + .008,
                          -.130, .009, STONE, label + ' | moulded neck of baluster')


def arched_window(face, opening, lod):
    label = 'east terrace base | segmented arched casement'
    face.solid(opening, -.160, -.149, RECESS, label + ' | deep reveal')
    glazing = opening.buffer(-.053, join_style=2)
    face.solid(glazing, -.145, -.135, GLASS, label + ' | recessed glass')
    face.solid(opening.difference(glazing), -.143, -.046, FRAME, label + ' | arched frame')
    a, low, b, top = glazing.bounds
    for index in range(1, 4):
        x = a + (b - a) * index / 4
        face.solid(box(x - .017, low, x + .017, top).intersection(glazing),
                   -.136, -.067, FRAME, label + ' | vertical glazing bars')
    for z in (top - .32, low + .44):
        face.solid(box(a, z - .018, b, z + .018).intersection(glazing),
                   -.136, -.076, FRAME, label + ' | glazing rail')


def terrace(f, lod):
    # Constraints from photo 38: front and east coping directions, two coping ends,
    # and the front and side slab corners. Rear return is out of sight behind the rail.
    inner, outer = U(EAST_WALL_U), U(2.94)
    start, finish = D(.997), D(1.774)
    floor, top = Z(-1.20), Z(-.925)
    slab(f, box(inner - .018, start - .075, outer + .09, finish + .115),
         floor - .165, floor, STONE, 'east terrace | cantilevered slab')
    slab(f, box(inner - .015, start - .046, outer + .063, finish + .087),
         floor - .218, floor - .147, PLASTER, 'east terrace | lower ledge')
    front = f.face(0, start, 1, 0)
    pierced_rail(front, inner, outer, floor, top, 4, 'east terrace | south panel', lod)
    side = f.face(outer, 0, 0, 1)
    pierced_rail(side, start, finish, floor, top, 13, 'east terrace | long panel', lod)
    rear = f.face(0, finish, -1, 0)
    rear.rect(-outer, -inner, floor, top, -.126, 0, PLASTER,
              'east terrace | sheltered end return')
    for d in (start, finish):
        slab(f, box(outer - .13, d - .076, outer + .008, d + .083), floor,
             top + .018, STONE, 'east terrace | square end pier')

    # Substantial enclosed bay visible directly below the tall open balustrade.
    bay = U(2.87)
    base = f.face(bay, 0, 0, 1)
    lo, hi = D(1.035), D(1.768)
    left, right = D(1.169), D(1.549)
    spring, rise = Z(-1.58), D(.051)
    middle, radius = (left + right) / 2, (right - left) / 2
    n = 14 if lod else 30
    window = Polygon([(left, Z(-2.05)), (right, Z(-2.05)),
                      *[(middle + radius * cos(pi * k / n), spring + rise * sin(pi * k / n))
                        for k in range(n + 1)]])
    base.solid(box(lo, 0, hi, floor - .21).difference(window), -.19, 0, PLASTER,
               'east terrace base | rendered wall around arched window')
    arched_window(base, window, lod)
    for d, direction in ((lo, 1), (hi, -1)):
        end = f.face(inner if direction == 1 else bay, d, direction, 0)
        end.rect(0, bay - inner + .012, 0, floor - .21, -.13, 0, PLASTER,
                 'east terrace base | plaster return')


def add_east_return(f, lod=False):
    """Add the east wall. The calling roof uses EAST_EAVE_PROFILE for its overhang."""
    wall = f.face(U(EAST_WALL_U), 0, 0, 1)
    # The small rise under the roof keeps the end wall inside its soffit on the slope.
    outline = Polygon([(D(.56), 0), (D(3.27), 0),
                       *[(D(d), Z(z) - .075) for d, z in reversed(EAST_EAVE_PROFILE)]])
    door = box(D(1.288), Z(-1.199), D(1.543), Z(-.392))
    side_light = box(D(2.128), Z(-1.180), D(2.252), Z(-.588))
    rear_light = box(D(2.622), Z(-1.237), D(2.746), Z(-.923))
    vents = [box(D(i), Z(-.368), D(i+.025), Z(-.333)) for i in (2.109, 2.153)]
    apertures = (door, side_light, rear_light, *vents)
    wall.solid(outline.difference(unary_union(apertures)), -.185, 0, PLASTER,
               'east wall | folded eave and three garden openings')
    # The edges in the oblique east view expose a slim timber surround that lies
    # almost flush with the lime render. Its glazing is recessed about 65 mm.
    opening_face = wall.face(0, -.081, 1, 0)
    sash(opening_face, door, 'east wall | glazed double leaf to terrace', 2, (.16, .31), False)
    sash(opening_face, side_light, 'east wall | narrow tall upper light', 1, (.20,), False)
    sash(opening_face, rear_light, 'east wall | rear sash with brick sill', 1, (.22,), True)
    for vent in vents:
        a, low, b, high = vent.bounds
        wall.solid(vent, -.094, -.083, RECESS, 'east wall | recessed air brick')
        for i in range(1, 4):
            z = low + (high - low) * i / 4
            wall.rect(a, b, z - .005, z + .005, -.08, -.029, DARK,
                      'east wall | air-brick horizontal bars')
    # The downpipe follows the corner until it jogs inward below the slab.
    u, d = U(EAST_WALL_U) + .093, D(.945)
    floor = Z(-1.20)
    pipe = [(u, d+.26, Z(-.065)), (u, d+.08, Z(-.102)), (u, d, Z(-.154)),
            (u, d, floor-.18), (u-.105, d, floor-.35), (u-.105, d, .055)]
    f.rail(pipe, .056, IRON, 'east wall | garden rainwater downpipe', 8 if lod else 16)
    for z in (Z(-.26), Z(-.84), floor+.04, floor-.52, .92):
        x = u if z > floor - .20 else u - .105
        f.rail([(x,d,z-.023),(x,d,z+.023)], .070, IRON,
               'east wall | downpipe collar', 8 if lod else 16)
    terrace(f, lod)
