"""Yuanmingyuan Road elevation of the Lyceum Building, Shanghai."""
import json
from pathlib import Path
from shapely.geometry import Polygon, box, LineString
from shapely.affinity import scale, translate
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import lettering_shapes
from brickwork import texture_uv

SOURCE = Path(__file__).resolve().parent
REG = json.loads((SOURCE/'frontage-registration.json').read_text())
LEFT, RIGHT = [pt[0] for pt in REG['visible_edges_local_m']]
TOWER_RIGHT = LEFT+7.06
SHAFT = (LEFT+TOWER_RIGHT)/2
WING = (TOWER_RIGHT+RIGHT)/2
BRICK = 'ochre garden brick'
ASHLAR = 'pearl grey ashlar'
LIGHT = 'warm tower limestone'
GLASS = 'light reflected street glass'
DARK = 'dark bronze street frames'
STONE = 'sand grey mouldings'
REVEAL = 'deep recessed door'
METAL = 'oxidized plaque metal'
ROOF = 'lead grey upper coping'
CUT = 'neutral rear section'
PALETTE = {n: {'color': c, 'roughness': r} for n, c, r in [
    (BRICK, [1, 1, 1], .91), (ASHLAR, [.71, .69, .65], .86), (LIGHT, [.79, .75, .68], .82),
    (GLASS, [.263, .336, .38], .33), (DARK, [.126, .139, .144], .52), (STONE, [.625, .587, .53], .85),
    (REVEAL, [.12, .097, .079], .76), (METAL, [.255, .226, .17], .61), (ROOF, [.39, .38, .35], .86), (CUT, [.49, .45, .40], .93)]}
PALETTE[BRICK]['texture'] = str(SOURCE/'lyceum-ochre-brick.png')


def window(face, u, z, w, h, lod, *, rise=0, columns=2, rows=2, bars=False):
    aperture = opening(u, z, w, h, rise, 10 if lod else 28)
    inner = aperture.buffer(-.07, join_style=2)
    strokes = [box(u-w/2+j*w/columns-.027, z, u-w/2+j*w/columns+.027, z+h) for j in range(1, columns)]
    for j in range(1, rows):
        y = z+h*j/rows
        strokes.append(box(u-w/2, y-.027, u+w/2, y+.027))
    face.prism(aperture.buffer(.01, join_style=2), -.32, -.30, GLASS, 'glass')
    frame = aperture.difference(inner.difference(unary_union(strokes)))
    face.prism(frame, -.215, -.135, DARK, 'sash')
    if bars:
        count = 5 if lod else 10
        for j in range(count):
            x = u+(j-(count-1)/2)*w/count
            face.box(x, z+h/2, .032, h+.09, .045, .08, DARK, 'external grilles')
        for level in [.12, .88]:
            face.box(u, z+h*level, w+.12, .039, .04, .10, DARK, 'grille rails')
    return aperture


def lettering(text, width, height):
    if text != 'LYCEUM':
        return lettering_shapes(text, width, height, font=SOURCE/'fonts/LyceumGate.otf')
    # The two side labels in the 2014 doorway are widely spaced sans-serif capitals.
    paths = {'L': [[(0, 1), (0, 0), (.62, 0)]],
             'Y': [[(0, 1), (.31, .52), (.63, 1)], [(.31, .52), (.31, 0)]],
             'C': [[(.62, .84), (.47, .99), (.18, .99), (.02, .82), (.02, .17), (.18, .02), (.47, .02), (.62, .17)]],
             'E': [[(.62, 1), (0, 1), (0, 0), (.62, 0)], [(0, .53), (.51, .53)]],
             'U': [[(0, 1), (0, .18), (.14, .02), (.48, .02), (.62, .18), (.62, 1)]],
             'M': [[(0, 0), (0, 1), (.32, .54), (.64, 1), (.64, 0)]]}
    shapes = []
    for index, ch in enumerate(text):
        glyph = unary_union([LineString(path).buffer(.063, cap_style='square',
                            join_style='bevel') for path in paths[ch]])
        norm = translate(glyph, xoff=index*1.12-3.12, yoff=-.5)
        shapes.append((ch, scale(norm, xfact=width/6.36, yfact=height/1.126, origin=(0, 0))))
    return shapes


def sign(f, text, u, z, w, h, projection, lod, material=METAL):
    for ch, g in lettering(text, w, h):
        if lod:
            g = g.simplify(.009, preserve_topology=True)
        f.prism(translate(g, xoff=u, yoff=z), projection, projection+.018, material, 'inscription '+ch)


def tower(b, lod):
    f = Facade(b, (LEFT, 0), (TOWER_RIGHT, 0), 'tower')
    door = box(-1.15, .005, 1.15, 3.05)
    small = [window(f, u, 1.0, .61, 1.71, lod, columns=2, rows=2, bars=True)for u in [-2.67, 2.67]]
    f.wall(0, 5.05, [door, *small], .44, ASHLAR)
    f.prism(door, -.61, -.59, REVEAL, 'dark door')
    deco = box(-1.11, 2.33, 1.11, 3.03)
    f.prism(deco, -.45, -.43, GLASS, 'door transom')
    # Only the broad diagonal members are distinct in the photographed transom.
    for left, right in [(-1.06, -.51), (-.59, -.09), (-.14, .40), (.33, .82), (.73, 1.07)]:
        f.prism(LineString([(left, 2.37), ((left+right)/2, 2.94), (right, 2.37)]).buffer(.028,
                cap_style='flat', join_style='bevel'), -.34, -.30, DARK, 'transom diagonals')
    for left, right in [(-1.0, -.49), (-.49, .02), (.23, .74)]:
        f.prism(LineString([(left, 2.91), (right, 2.39)]).buffer(.029,
                cap_style='flat'), -.34, -.30, DARK, 'crossing transom bars')
    f.box(0, 2.18, 2.22, .23, .16, -.38, DARK, 'street number band')
    for u in [-1.36, 1.36]:
        f.box(u, 1.85, .31, 3.68, .29, .105, STONE, 'gate jamb')
    for z, w, h, d in [(3.19, 2.94, .12, .18), (3.31, 3.13, .16, .23),
                       (4.20, 3.55, .12, .23), (4.52, 3.93, .17, .32), (4.71, 4.21, .15, .39)]:
        f.box(0, z, w, h, d+.09, d/2-.035, LIGHT, 'door mouldings')
    f.box(0, 3.77, 2.96, .64, .12, .075, STONE, 'name plaque')
    sign(f, '兰心大樓', 0, 3.78, 2.10, .34, .14, lod)
    for u in [-2.60, 2.60]:
        sign(f, 'LYCEUM', u, 3.89, 1.38, .23, .012, lod)
    if not lod:
        sign(f, '185', 0, 2.18, .25, .13, -.286, lod, LIGHT)
    for i in range(-8, 9):
        f.box(i*.19, 4.37, .10, .15, .19, .14, STONE, 'lintel dentils')
    # Ashlar beds stop at the doorway and at the jambs of the two barred lights.
    for i in range(1, 6):
        z = i*.84
        bed = box(-f.length/2, z-.012, f.length/2, z+.012)
        bed = bed.difference(unary_union([door, *small, box(-2.09, 0, 2.09, 4.82)]))
        if not bed.is_empty:
            f.prism(bed, -.008, .013, STONE, 'ashlar joints')
    for u in [-2.37, -1.60, -.80, 0, .80, 1.60, 2.37]:
        f.box(u, 4.72, .19, .24, .32, .15, STONE, 'upper cornice brackets')
    f.box(0, 4.91, 5.23, .13, .62, .23, LIGHT, 'projecting portal cornice')
    shaft = [window(f, 0, z, 1.15, h, lod, columns=2, rows=2)
             for z, h in [(5.28, 1.60), (8.65, 1.61), (12.06, 1.62), (15.55, 1.34)]]
    shrine = window(f, 0, 18.8, 1.62, 2.35, lod, rise=.59, columns=2, rows=3)
    shaft.append(shrine)
    shaft.append(window(f, 0, 23.07, 1.13, .78, lod, columns=4, rows=1))
    f.wall(5.05, 25.53, shaft, .43, BRICK)
    for i in range(38):
        z = 5.12+i*.54
        w = .49 if i % 2 else .73
        for side in [-1, 1]:
            f.box(side*(f.length/2-w/2), z, w, .38, .135, .035, ASHLAR, 'alternating quoins')
    for side in [-1, 1]:
        f.box(side*1.09, 20.04, .28, 2.83, .38, .15, LIGHT, 'aedicule jamb')
        f.box(side*.92, 18.01, .32, .62, .46, .15, STONE, 'aedicule corbel')
    f.box(0, 18.55, 2.73, .45, .64, .21, LIGHT, 'aedicule sill')
    f.box(0, 21.50, 2.72, .19, .58, .19, LIGHT, 'entablature')
    ped = Polygon([(-1.52, 21.61), (0, 22.31), (1.52, 21.61)])
    f.prism(ped, .045, .28, ASHLAR, 'pediment')
    f.prism(LineString([(-1.54, 21.65), (0, 22.39), (1.54, 21.65)]).buffer(.071,
            cap_style='flat', join_style='mitre'), .15, .44, LIGHT, 'pediment cornice')
    for z, w, h in [(25.02, .18, .16), (25.37, .32, .20), (25.61, .49, .20)]:
        f.beam(z, h, w, ASHLAR, label='tower ledges')
    inset = .22
    end = 2.66
    front = Facade(b, (LEFT+inset, .15), (TOWER_RIGHT-inset, .15), 'upper lantern')

    def cap(face):
        aperture = window(face, 0, 29.31, min(2.62, face.length*.70), 4.0, lod, rise=1.28, columns=3, rows=4)
        face.wall(25.72, 35.24, [aperture], .37, LIGHT)
        band = aperture.buffer(.16, join_style=2).difference(aperture)
        face.prism(band, -.015, .095, STONE, 'round head surround')
    cap(front)
    # The return window is visible in the completed-work street photograph.
    side = Facade(b, (TOWER_RIGHT-inset, .15), (TOWER_RIGHT-inset, end), 'lantern return')
    cap(side)
    # The north return has a real arched opening. Close only its two piers.
    for y in [.25, 2.51]:
        b.box((TOWER_RIGHT-inset, y, 30.48), (.20, .21, 9.52), LIGHT, label='lantern north corner pier')
    b.box((LEFT+inset, 1.40, 30.48), (.20, 2.51, 9.52), LIGHT, label='lantern south section')
    b.box((SHAFT, end, 30.45), (front.length, .24, 9.59), CUT, label='lantern rear closure')
    for z, h, x, y in [(34.55, .19, .22, .15), (35.04, .27, .43, .30), (35.34, .16, .66, .49)]:
        b.box((SHAFT, 1.38, z), (front.length+x, 2.73+y, h), LIGHT, label='lantern crown courses')
    b.box((SHAFT, 1.37, 35.39), (front.length+.43, 2.81, .12), ROOF, label='visible crown roof plane')


def street_wing(builder, lod):
    face = Facade(builder, (TOWER_RIGHT, 0), (RIGHT, 0), 'north street wing')
    width = face.length
    # Four broad groups follow the narrow single bay adjoining the tower.
    groups = [(-width/2+1.13, 1.25, 1)]+[(-width/2+4.82+i*4.88, 3.65, 3)for i in range(4)]
    shops = []
    for u, w, cols in [(-7.62, 4.09, 3), (-2.18, 4.27, 3), (3.29, 4.28, 3), (8.40, 2.70, 2)]:
        shops.append(window(face, u, .23, w, 3.21, lod, columns=cols, rows=2))
        face.box(u, 3.67, w+.19, .14, .33, .09, STONE, 'store lintel')
    face.wall(0, 4.92, shops, .46, ASHLAR)
    front = []
    for sill in (5.32, 8.80, 12.30):
        for u, w, cols in groups:
            front.append(window(face, u, sill, w, 1.98, lod, columns=cols, rows=2, bars=(sill == 5.32)))
            if not lod:
                face.box(u, sill-.065, w+.12, .10, .18, .032, STONE, 'small window sill')
    face.wall(4.92, 15.31, front, .47, BRICK)
    attic = []
    for u, w, cols in groups:
        attic.append(window(face, u, 15.75, w, 1.31, lod, columns=cols, rows=1))
        if cols > 1:
            for side in [-1, 1]:
                face.box(u+side*(w/2+.34), 16.44, .24, 1.13, .095, .036, STONE, 'attic field panels')
    face.wall(15.31, 18.11, attic, .47, ASHLAR)
    for z, h, d in [(4.86, .15, .17), (15.34, .18, .18), (17.90, .20, .22), (18.17, .23, .42)]:
        face.beam(z, h, d, ASHLAR, label='front string courses')
    back = .97
    upper = Facade(builder, (TOWER_RIGHT, back), (RIGHT, back), 'receding upper wing')
    apertures = []
    for sill in [19.15, 22.48]:
        for u, w, cols in groups:
            apertures.append(window(upper, u, sill, w, 1.56, lod, columns=cols, rows=1))
    upper.wall(18.12, 24.45, apertures, .43, BRICK)
    upper.wall(24.45, 25.61, [], .35, ASHLAR)
    for u, w, cols in groups:
        if cols > 1:
            upper.prism(box(u-w/2, 24.76, u+w/2, 25.31), -.01, .032, STONE, 'inset parapet panels')
    upper.beam(25.60, .13, .14, STONE, label='setback coping')
    builder.box((WING, .55, 18.14), (width, 1.30, .17), STONE, label='balcony slab')
    for x in [TOWER_RIGHT+.22+i*(width-.44)/24 for i in range(25)]:
        builder.box((x, .11, 18.64), (.060, .070, .90), DARK, label='terrace rail pickets')
    builder.box((WING, .11, 19.07), (width, .12, .08), DARK, label='terrace handrail')
    builder.box((WING, 1.90, 25.55), (width, 1.88, .14), ROOF, label='roof behind the upper parapet')
    end = Facade(builder, (RIGHT, .02), (RIGHT, 2.8), 'north end')
    end.wall(.035, 18.12, [], .17, BRICK)
    ret = Facade(builder, (RIGHT, back+.012), (RIGHT, 2.8), 'upper north return')
    ret.wall(18.12, 25.53, [], .16, BRICK)
    builder.box((WING, 2.80, 12.65), (width, .19, 25.30), CUT, label='wing rear section')


def add_building(builder, lod):
    tower(builder, lod)
    street_wing(builder, lod)
    builder.box((SHAFT, 2.77, 12.78), (TOWER_RIGHT-LEFT, .22, 25.55), CUT, label='tower back section')
    for x in [LEFT+.09, TOWER_RIGHT-.09]:
        builder.box((x, 1.38, 12.78), (.18, 2.79, 25.56), STONE, label='slender side return')
    builder.box((SHAFT, 1.36, 25.61), (TOWER_RIGHT-LEFT, 2.75, .18), ROOF, label='tower top return')
    for part in builder.parts:
        if part['material'] == BRICK:
            part['texcoords'] = [(u, 1-v) for u, v in (texture_uv(*v) for v in part['vertices'])]
