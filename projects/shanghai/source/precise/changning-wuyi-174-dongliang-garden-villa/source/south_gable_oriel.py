"""South garden gable and its shallow projecting window, from the October 2024 photograph."""
import json
from math import hypot
from pathlib import Path
from statistics import median

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from wuyi_fabric import FRAME, GLASS, SOFFIT, STONE, TIMBER, WALL, paint, slab, wall


AMBER = '174 | garden oriel upper reflected glass'
PALETTE = {AMBER: paint((125, 111, 94), .30, .12)}

FACE_Y = 13.60
WEST_LIMIT = 6.66
BASE = Path(__file__).absolute().parent.parent / 'measurements'


def project_to_surface(u, v, depth, coefficients):
    """Intersect a garden image ray with a plane a given distance outside the wall."""
    if len(coefficients) not in (8, 10):
        raise ValueError('A registered garden camera requires eight or ten coefficients')
    u0, v0, scale, slope, dv, ds, yaw, roll = coefficients[:8]
    z_scale, z_perspective = coefficients[8:] or (1., 0.)
    u -= u0
    v -= v0
    a, b = u * yaw - scale, u * z_perspective - roll
    c, d = v * yaw + roll, v * z_perspective + scale * z_scale
    h = ds * depth - u * (1 - slope * depth)
    k = dv * depth - v * (1 - slope * depth)
    det = a * d - b * c
    if abs(det) < 1e-8:
        raise ValueError('The image ray is parallel to the measured plane')
    return 9.55 - (h * d - b * k) / det, 2.96 + (a * k - h * c) / det


def observations():
    camera = json.loads((BASE / 'south-garden-two-photographs.json').read_bytes())['views']['0']
    measurements = json.loads((BASE / 'south-oriel-image-observations.json').read_bytes())
    if camera['photo_sha256'] != measurements['source']['sha256']:
        raise ValueError('South garden observations use a different photograph')
    positions = {}
    depths = {}
    for row in measurements['observation']:
        name = row['feature']
        depths[name] = row['adopted_outward_depth_m']
        positions[name] = [
            project_to_surface(u, v, depth, measurements['registration']['fits']['joint'])
            for (u, v), depth in zip(row['pixels'], depths[name], strict=True)
        ]
    lower = positions['upper sill']
    upper = positions['upper head']
    ribs = [(0.5 * (a[0] + b[0]), depth)
            for a, b, depth in zip(lower, upper, depths['upper sill'], strict=True)]
    if len(ribs) < 2 or not (0 <= ribs[-1][0] < ribs[0][0] <= WEST_LIMIT):
        raise ValueError('Photographed window crosses the documented gable boundary')
    if not all(a[0] > b[0] for a, b in zip(ribs, ribs[1:])):
        raise ValueError('Unexpected ordering of the photographed window ribs')
    return ribs, median(z for x, z in lower), median(z for x, z in upper), positions


WALL_CHART = ((WEST_LIMIT, FACE_Y), (WEST_LIMIT - 1., FACE_Y))


def chart_rect(x0, x1, sill, head):
    return box(WEST_LIMIT - x1, sill, WEST_LIMIT - x0, head)


def south_skin(b, shape, front, back, material, name):
    wall(b, shape, *WALL_CHART, front, back, material, 'garden east gable ' + name)


def oriel_lights(b, ribs, sill, head):
    for i, ((x0, out0), (x1, out1)) in enumerate(zip(ribs, ribs[1:]), 1):
        a = (x0, FACE_Y + out0)
        c = (x1, FACE_Y + out1)
        width = hypot(x1 - x0, out1 - out0)
        outer = box(0., sill, width, head)
        inner = box(.026, sill + .047, width - .026, head - .047)
        label = 'garden projecting sash ' + str(i)
        wall(b, outer.difference(inner), a, c, -.025, .045, FRAME, label + ' perimeter')
        # The tone changes behind the glass. There is no evidenced horizontal glazing bar.
        wall(b, box(.026, sill + .047, width - .026, head - .42),
             a, c, .046, .063, GLASS, label + ' light')
        wall(b, box(.026, head - .42, width - .026, head - .047),
             a, c, .046, .063, AMBER, label + ' upper light')

    outer_plan = [(x, FACE_Y + y + .067) for x, y in ribs]
    cap = Polygon(outer_plan + [(ribs[-1][0], FACE_Y - .09),
                                (ribs[0][0], FACE_Y - .09)])
    slab(b, cap, sill - .075, sill - .002, STONE, 'garden oriel sill')
    slab(b, cap, head + .002, head + .072, SOFFIT, 'garden oriel head')
    x, out = ribs[-1]
    cheek = box(0., sill - .002, out + .03, head + .002)
    wall(b, cheek, (x, FACE_Y + out), (x, FACE_Y), .0, .06,
         WALL, 'garden oriel east end reveal')


def add_south_oriel(b, lod=False):
    """Build the 0–6.66 m garden-facing wall, its two openings and evidenced joinery."""
    ribs, sill, head, observed = observations()
    lower_points = observed['lower head']
    lower_left, lower_right = lower_points[-1][0], lower_points[0][0]
    lower_head = median(z for x, z in lower_points)
    tie = observed['timber horizontal']
    tie_height = median(z for x, z in tie)
    outline = Polygon([(0., .015), (WEST_LIMIT, .015),
                       (WEST_LIMIT, 6.52), (WEST_LIMIT - 3.57, 10.30),
                       (0., 6.88)])
    upper = chart_rect(ribs[-1][0], ribs[0][0], sill - .001, head + .001)
    lower = chart_rect(lower_left, lower_right, .82, lower_head)
    south_skin(b, outline.difference(unary_union([upper, lower])), .0, .20,
               WALL, 'roughcast with upper and lower openings')
    oriel_lights(b, ribs, sill, head)
    inner = lower.buffer(-.051, join_style=2)
    south_skin(b, lower.difference(inner), .029, .103, FRAME, 'lower frame')
    left, bottom, right, top = inner.bounds
    cuts = [left, *(WEST_LIMIT-x for x, z in lower_points[1:-1]), right]
    for i, (t, end) in enumerate(zip(cuts, cuts[1:])):
        if i:
            south_skin(b, box(t - .021, bottom, t + .021, top),
                       .04, .108, FRAME, 'lower mullion ' + str(i))
        south_skin(b, box(t + (.021 if i else 0), bottom,
                          end - (.021 if i < 2 else 0), top),
                   .110, .128, GLASS, 'lower light ' + str(i + 1))
    south_skin(b, chart_rect(lower_left - .02, lower_right + .02, .764, .82), -.025, .099,
               STONE, 'lower sill')
    # Only the short lower part of the gable timberwork is legible through the canopy.
    south_skin(b, chart_rect(tie[1][0], tie[0][0], tie_height - .07, tie_height + .07),
               -.045, .006, TIMBER, 'visible tie')
    for i, (fraction, height) in enumerate(((.32, .44), (.69, .56), (.96, .49)), 1):
        x = tie[0][0] + fraction * (tie[1][0] - tie[0][0])
        south_skin(b, chart_rect(x - .043, x + .043, tie_height + .07, tie_height + height),
                   -.043, .005, TIMBER, 'visible short upright ' + str(i))
