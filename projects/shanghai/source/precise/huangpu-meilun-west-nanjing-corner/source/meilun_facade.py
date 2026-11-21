"""The photographed west Meilun corner, including its storefront recesses and parapet."""
from pathlib import Path
import json
import math
from shapely.geometry import Polygon
from shapely.ops import unary_union
from photo_architecture import Facade
from meilun_corner import PALETTE, STONE, DRESSING, section

STUDY = Path(__file__).resolve().parents[1] / 'corner-study.json'


def street_edges():
    q = json.loads(STUDY.read_bytes())['corner']
    north, west = q['nanjing_end'], q['west_end']
    end = [north[0] + 12.8, north[1]]
    return [(end, north, 'Nanjing storefront', 2, .74),
            (north, west, 'corner entrance', 1, .86),
            (west, q['west_study_end'], 'Jiangxi storefront', 1, .67)]


def inner_strip(wall, depth):
    return Polygon([wall.point(u, 0, d)[:2] for u, d in
                    [(-wall.length / 2, 0), (wall.length / 2, 0),
                     (wall.length / 2, -depth), (-wall.length / 2, -depth)]])


def cornice(wall, compact):
    for height, width, thickness in [(12.67, .32, .095), (12.73, .39, .082),
                                     (13.27, .63, .083)]:
        wall.box(0., height, wall.length, thickness, width, width / 2 - .06,
                 DRESSING, 'profiled cornice course')
    if not compact:
        for u in (-wall.length / 2 + .36, wall.length / 2 - .36):
            for direction in (-1, 1):
                points = [wall.point(u + direction * (.04 + .18 * j / 11),
                                     12.57 + .32 * math.sin(j * math.pi / 11), .295)
                          for j in range(12)]
                wall.builder.tube(points, .03, DRESSING, 6, 'carved capital scroll')


def add_meilun(builder, lod):
    ledges = []
    for a, b, label, bays, setback in street_edges():
        wall = Facade(builder, a, b, label)
        section(wall, bays, not lod, label == 'corner entrance', setback)
        cornice(wall, lod)
        ledges.append(inner_strip(wall, 1.44))
    # The modern setback roof behind the stone parapet retains its source massing.
    # Only the weathering immediately behind the photographed cornice is modeled.
    deck = unary_union(ledges).buffer(.015, join_style=2).buffer(-.015, join_style=2)
    builder.plan_prism(deck, 12.91, 13.07, 'roof zinc', label='continuous parapet weathering')
