"""Street-side portal, inscription and closed iron leaves photographed in 2021."""
from pathlib import Path
import math

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from sign_lettering import add_facade_lettering


WIDTH = 4.58
OPENING = 3.39
HEAD = 3.94
BACK = .94
FONT = Path(__file__).with_name('fonts') / 'JixiangliDoorwaySubset.otf'
PALETTE = {
    'grey stone': {'color': [.477, .457, .416], 'roughness': .91},
    'dressed stone': {'color': [.528, .503, .451], 'roughness': .86},
    'inset inscription': {'color': [.430, .408, .362], 'roughness': .90},
    'lettered stone': {'color': [.593, .565, .499], 'roughness': .86},
    'door soffit': {'color': [.327, .313, .286], 'roughness': .91},
    'window hardwood': {'color': [.172, .114, .095], 'roughness': .71},
    'window glass': {'color': [.139, .193, .199], 'roughness': .24, 'metallic': .19},
    'painted iron': {'color': [.103, .119, .110], 'roughness': .66, 'metallic': .32},
    'ochre iron ornament': {'color': [.435, .351, .222], 'roughness': .67, 'metallic': .20},
    'street plaque': {'color': [.072, .303, .241], 'roughness': .69},
    'street plaque lettering': {'color': [.823, .837, .746], 'roughness': .71},
    'cut surface': {'color': [.438, .422, .389], 'roughness': .94}
}


def framing(face, polygon, thickness, back, front, material, name):
    rim = polygon.difference(polygon.buffer(-thickness, join_style='mitre'))
    face.prism(rim, back, front, material, name)


def add_upper_window(face, opening):
    low, high = 5.86, 8.03
    left, right = -1.14, 1.14
    face.prism(opening, -.258, -.236, 'window glass', 'three recessed panes')
    framing(face, opening, .095, -.230, -.112, 'window hardwood', 'perimeter frame')
    # The original and restored views share the three upright lights and narrow transom.
    for u in (-.379, .379):
        face.box(u, (low + high) / 2, .042, high - low - .10, .065, -.179,
                 'window hardwood', 'two vertical glazing bars')
    face.box(0, 7.72, right - left - .10, .051, .069, -.177,
             'window hardwood', 'transom rail')
    face.box(0, low - .075, 2.56, .125, .178, .014, 'dressed stone', 'projecting stone window sill')


def scroll(builder, cx, z, sign, radius, material, lod, name):
    # Planar iron scroll curls back toward the crest rail.
    count = 12 if lod else 28
    points = []
    for i in range(count + 1):
        t = i / count
        angle = 2.0 * math.pi * t
        r = radius * (1 - .78 * t)
        points.append((cx + sign * r * math.cos(angle), .586, z + r * math.sin(angle)))
    builder.tube(points, .013 if radius < .12 else .017, material, 6 if lod else 9, name)


def add_leaves(builder, lod):
    for sign in (-1, 1):
        begin, end = .022, OPENING / 2 - .10
        center = sign * (begin + end) / 2
        width = end - begin

        def top_at(x):
            return 3.38 - .29 * (x / end) ** 1.65

        for x in (begin, end):
            h = top_at(x)
            builder.box((sign * x, .61, (.090 + h) / 2), (.052, .064, h - .090),
                        'painted iron', label='iron leaves/end stiles')
        for z, h in ((.19, .064), (.63, .041), (.82, .037), (2.55, .043), (2.72, .048)):
            builder.box((center, .61, z), (width, .058, h), 'painted iron',
                        label='iron leaves/horizontal rails')
        count = 8 if lod else 13
        for i in range(1, count):
            x = begin + width * i / count
            z = top_at(x) - .10
            builder.box((sign * x, .615, (.19 + z) / 2), (.023, .035, z - .19),
                        'painted iron', label='iron leaves/narrow upright grilles')
        crest = [(sign * (begin + width * i / 24), .61, top_at(begin + width * i / 24))
                 for i in range(25)]
        builder.tube(crest, .028, 'painted iron', 6 if lod else 10, 'iron leaves/sloping head rail')
        for x in (.23, .55, .91, 1.26):
            height = top_at(x) - .20
            scroll(builder, sign * x, height, sign, .135, 'ochre iron ornament', lod, 'iron leaves/crest scrolls')
            if not lod:
                scroll(builder, sign * x, .722, -sign, .064, 'painted iron', lod, 'iron leaves/lower scrolls')
        for x in (.12, .27):
            scroll(builder, sign * x, 3.44 - x / 5, -sign, .126, 'ochre iron ornament', lod,
                   'iron leaves/raised central ornament')


def add_wall(face, outer, apertures, lod):
    # The outer cut stops at the sides of the documented stone doorway.
    wall = outer.difference(unary_union(apertures))
    face.prism(wall, -BACK, -.037, 'door soffit', 'solid opening cheeks and tunnel ceiling')
    face.prism(wall, -.039, -.002, 'grey stone', 'masonry skin')
    courses = [0, .64, 1.28, 1.92, 2.56, 3.20, HEAD, 4.43, 4.97, 5.82, 6.93, 8.05, 8.64, 9.22, 9.78, 11.0]
    for index, (low, high) in enumerate(zip(courses, courses[1:])):
        # The jambs have wide, shallow joints. Upper ashlar is more widely spaced.
        if lod and index not in (1, 3, 5, 7, 9, 12):
            continue
        dividers = [-WIDTH / 2, -1.68, 1.68, WIDTH / 2]
        if low >= HEAD:
            dividers = [-WIDTH / 2, -1.54, -.54, .46, 1.55, WIDTH / 2] if index % 2 else [-WIDTH / 2, -1.54, 0, 1.55, WIDTH / 2]
        for left, right in zip(dividers, dividers[1:]):
            ashlar = wall.intersection(box(left + .005, low + .005, right - .005, high - .005))
            if not ashlar.is_empty and ashlar.area > .002:
                face.prism(ashlar, -.003, .004, 'grey stone', 'coursed portal facing')


def gate(builder, lod):
    face = Facade(builder, (-WIDTH / 2, 0), (WIDTH / 2, 0), 'west entrance')
    eave = 9.37
    half = WIDTH / 2
    crown = [(-half, eave), (-1.83, eave), (-1.83, 9.67), (-1.49, 9.67),
             (-1.49, 9.98), (-1.18, 9.98), (-1.18, 10.26), (-.86, 10.26),
             (-.86, 10.51), (.86, 10.51), (.86, 10.26), (1.18, 10.26),
             (1.18, 9.98), (1.49, 9.98), (1.49, 9.67), (1.83, 9.67),
             (1.83, eave), (half, eave)]
    outline = Polygon([(-half, 0), (half, 0), *reversed(crown)])
    doorway = box(-OPENING / 2, -.11, OPENING / 2, HEAD)
    window = box(-1.14, 5.86, 1.14, 8.03)
    add_wall(face, outline, [doorway, window], lod)

    # Raised rectangular inscription with a thin surround, read from the right.
    tablet = box(-1.17, 4.85, 1.17, 5.65)
    face.prism(tablet, .005, .034, 'inset inscription', 'stone tablet field')
    framing(face, tablet, .044, .030, .069, 'dressed stone', 'tablet perimeter')
    add_facade_lettering(face, '里祥吉', 0, 5.25, 1.68, .43, .036, .069,
                         'lettered stone', label='raised west-facing lane name', font=FONT)
    add_upper_window(face, window)

    for sign in (-1, 1):
        face.box(sign * 1.53, 7.10, .115, 4.34, .064, .020,
                 'dressed stone', 'upper panel side pilasters')
    face.box(0, 8.24, 2.02, .13, .069, .028, 'dressed stone', 'shallow strip over window')
    for z, width, height in ((8.84, 2.78, .091), (9.21, 2.88, .113)):
        face.box(0, z, width, height, .091, .038, 'dressed stone', 'frieze bed and coping')
    for i in range(11):
        face.box((i - 5) * .246, 9.02, .050, .282, .048, .031, 'dressed stone',
                 'narrow strips on stepped parapet frieze')

    plate_x, plate_z = 1.99, 2.22
    plaque = box(plate_x - .210, plate_z - .143, plate_x + .210, plate_z + .143)
    face.prism(plaque, .011, .034, 'street plaque', 'green 22 Lane address plaque')
    for text, z, width, height in [('22弄', 2.266, .280, .102), ('山东北路', 2.137, .354, .071)]:
        add_facade_lettering(face, text, plate_x, z, width, height, .035, .041,
                             'street plaque lettering', label='street number plate', font=FONT)
    add_leaves(builder, lod)
