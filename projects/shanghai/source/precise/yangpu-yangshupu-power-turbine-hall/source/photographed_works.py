"""Two adjoining industrial elevations and the roof silhouettes shown in the archival plates."""
from math import cos, pi, radians, sin
from photo_architecture import Facade, opening
from shapely.geometry import box

WALL = 'interpreted warm grey concrete'
CAP = 'pale cornice and pier cap'
BASE = 'weathered base'
GLASS = 'subdued steel window glazing'
IRON = 'dark painted steel'
ROOF = 'neutral roof surface'
STACK = 'weathered stack shell'
PALETTE = {
    WALL: {'color': [.55, .53, .46], 'roughness': .93},
    CAP: {'color': [.69, .66, .58], 'roughness': .86},
    BASE: {'color': [.34, .34, .32], 'roughness': .92},
    GLASS: {'color': [.21, .26, .27], 'roughness': .46, 'metallic': .1},
    IRON: {'color': [.13, .15, .15], 'roughness': .76, 'metallic': .20},
    ROOF: {'color': [.33, .35, .35], 'roughness': .87},
    STACK: {'color': [.24, .25, .25], 'roughness': .86},
}
ANGLE = radians(-22.0)
ORIGIN = (0, 5)


def picture_coordinates(x, y, z):
    """Rotate the photograph-relative axes into the editable model's front view."""
    dx, dy = x - ORIGIN[0], y - ORIGIN[1]
    return (dx * cos(ANGLE) - dy * sin(ANGLE), dx * sin(ANGLE) + dy * cos(ANGLE), z)


def cut_edge(builder, start, end, height, label):
    Facade(builder, start, end, label).wall(.0, height, thickness=.24, material=WALL)


def facade_windows(face, top, count, lower, upper, width, lod, label, columns=4, rows=10):
    pitch = face.length / count
    centers = [pitch * (i + .5) - face.length / 2 for i in range(count)]
    holes = [opening(u, lower, width, upper - lower) for u in centers]
    face.wall(0, top, holes, .42, WALL)
    for i, (u, shape) in enumerate(zip(centers, holes)):
        # The photographs show deep masonry jambs and steel sash under a single lintel.
        face.window(shape, max(2, columns - 1) if lod else columns,
                    5 if lod else rows, IRON, False, GLASS, 'steel sash')
        if not lod:
            face.box(u, upper + .085, width + .24, .17, .28, .005, CAP, 'lintel')
        if i:
            face.box(u - pitch / 2, (top + lower - .45) / 2,
                     .38 if pitch < 4 else .57, top - lower - .32, .35, .035,
                     WALL, 'vertical concrete pier')
    face.beam(lower - .41, .27, .17, CAP, label='spandrel string')
    face.beam(top - .65, .26, .18, CAP, label='lower cornice band')
    face.beam(top - .23, .30, .31, CAP, label='overhanging upper cornice')
    return centers


def flat_roof(builder, x0, y0, x1, y1, top, name):
    # Low neutral rear enclosure preserves the silhouette where the photograph ends.
    builder.plan_prism(box(x0 + .08, y0 + .08, x1 - .08, y1 - .08),
                       top - .22, top - .06, ROOF, name + '/roof surface')


def masonry_bay(builder, x0, x1, y0, y1, height, count, window_bottom, window_top, window_width, lod, name):
    front = Facade(builder, (x0, y0), (x1, y0), name)
    facade_windows(front, height, count, window_bottom, window_top, window_width, lod, name)
    # Ground level is substantially hidden by walls and trackside sheds in both views.
    front.beam(.24, .48, .02, BASE, width=front.length, label='ground return')
    cut_edge(builder, (x0, y1), (x0, y0), height, name + '/west cut')
    cut_edge(builder, (x1, y1), (x0, y1), height, name + '/neutral back')
    flat_roof(builder, x0, y0, x1, y1, height, name)
    return front


def roof_flue(builder, x, y, bottom, height, radius, lod):
    rim = .13
    # Outer and inner annuli retain a real dark mouth in the roof view.
    n = 16 if lod else 32
    layers = [(bottom, radius * 1.09), (bottom + .35, radius * 1.09),
              (bottom + .40, radius), (height - .16, radius * .88),
              (height - .16, radius * .96), (height, radius * .96),
              (height, radius * .96 - rim), (height - .90, radius * .96 - rim)]
    vertices = [(x + r * cos(k * 2 * pi / n), y + r * sin(k * 2 * pi / n), z)
                for z, r in layers for k in range(n)]
    quads = [(j*n+k, j*n+(k+1)%n, (j+1)*n+(k+1)%n, (j+1)*n+k)
             for j in range(len(layers)-1) for k in range(n)]
    builder.add(vertices, quads, STACK, 'roof silhouettes/open metal flues')
    builder.lathe((x, y), [(height-1.01, radius*.72), (height-.99, radius*.72)], IRON, n, 'roof silhouettes/shaded throat')
    if not lod:
        for h in (bottom + (height-bottom)*.34, bottom + (height-bottom)*.66):
            r = radius * (1 - .12 * (h-bottom)/(height-bottom))
            builder.lathe((x,y), [(h-.027, r+.025), (h+.027, r+.025)], STACK, n, 'roof silhouettes/riveted collar')


def roof_arch(builder, x, y, z, radius, lod):
    steps = 14 if lod else 28
    # The archive reveals an open curved silhouette with a vertical post. No enclosed machinery is inferred.
    side = radius
    path = [(x, y - side, z), (x, y - side, z + .35)]
    path += [(x, y - radius * cos(k*pi/steps), z + .35 + radius * sin(k*pi/steps))
             for k in range(1,steps+1)]
    path += [(x, y + side, z)]
    builder.tube(path, .145 if lod else .17, IRON, 7 if lod else 12, 'roof silhouettes/open round frames')
    builder.tube([(x, y, z+.02), (x, y, z + radius+.31)], .075, IRON, 7, 'roof silhouettes/frame center uprights')


def factory_elevations(builder, lod):
    # Only the documented window groups are opened; blank cut ends stay visually subordinate.
    long = masonry_bay(builder, -35, 3.1, -2.0, 6.0, 14.9, 8, 3.9, 12.8, 3.25, lod, 'long photographed wing')
    cut_edge(builder, (3.1,-2), (3.1,6), 14.9, 'long photographed wing/end closure')
    short = masonry_bay(builder, 3.1, 20.3, -3.2, 5.7, 19.0, 4, 4.8, 16.8, 2.73, lod, 'raised adjoining facade')
    ret = Facade(builder, (20.3,-3.2), (20.3,5.7), 'projecting short return')
    facade_windows(ret, 19.0, 2, 4.8, 16.7, 2.72, lod, 'short return', 4, 11)
    for face, height in ((long, 14.9), (short, 19.0)):
        for sign in (-1, 1):
            face.box(sign * (face.length/2-.24), height/2, .47, height-.02,
                     .44, .06, WALL, 'terminal masonry pier')
    # Rear high wall rises above the lower cornice; the continued vertical sash is confined to the visible end.
    q0,q1,y0,y1,top = -2.8,26.5,5.72,21.3,24.1
    high = Facade(builder,(q0,y0),(q1,y0),'high roof crown')
    high_bays = [opening(x - (q0+q1)/2, 4.7, 2.75, 15.0) for x in (23.1,)]
    high.wall(0, top, high_bays, .35, WALL)
    for shape in high_bays:
        high.window(shape, 2 if lod else 3, 5 if lod else 12, IRON, False, GLASS, 'visible high corner sash')
    for h,t,d in [(19.52,.19,.13),(21.47,.23,.18),(22.91,.26,.22),(23.75,.34,.34)]:
        high.beam(h,t,d,CAP,label='raised crown moulding')
    for x in (q0+.60, 5.8, 12.4, 20.1, q1-.62):
        high.box(x-(q0+q1)/2,21.34,.5,4.18,.29,.09,WALL,'attic pilaster')
    end = Facade(builder,(q1,y0),(q1,y1),'high end elevation')
    facade_windows(end,top,5,5.1,20.84,1.98,lod,'crown end',3,13)
    for u in (-end.length/2+.39,end.length/2-.39):
        end.box(u,14.35,.63,17.8,.38,.10,WALL,'full-height corner pilaster')
    end.beam(22.88,.26,.27,CAP,label='returned cornice')
    cut_edge(builder, (q0,y1),(q0,y0),top,'high roof crown/neutral short wall')
    cut_edge(builder, (q1,y1),(q0,y1),top,'high roof crown/neutral rear')
    flat_roof(builder,q0,y0,q1,y1,top,'high roof crown')
    for x in (.65,7.2,15.4,23.3):
        roof_arch(builder,x,11.7,top,2.45,lod)
    for x,y,b,h,r in [(-18.6,3.0,14.75,18.7,.68),(-8.1,3.0,14.75,21.3,.80),
                       (13.6,9.4,23.94,33.7,.93),(24.2,18.4,23.94,29.1,.80)]:
        roof_flue(builder,x,y,b,h,r,lod)
    for part in builder.parts:
        part['vertices'] = [picture_coordinates(*v) for v in part['vertices']]
