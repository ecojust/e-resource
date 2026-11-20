"""Original street elevations of the life-insurance office at 93 Guangdong Road."""
from math import cos, pi, sin

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

WALL = 'warm dressed granite'
COLUMN = 'polished red granite'
TRIM = 'pale brown granite trim'
SASH = 'brown metal sash'
GLASS = 'blue black glazing'
BRONZE = 'door grille'
ROOF = 'weathered roof'
REAR = 'rear masonry'
PALETTE = {
    WALL: {'color': [.55, .405, .275], 'roughness': .84},
    COLUMN: {'color': [.40, .26, .18], 'roughness': .52},
    TRIM: {'color': [.66, .53, .38], 'roughness': .76},
    SASH: {'color': [.135, .096, .065], 'roughness': .50},
    GLASS: {'color': [.102, .144, .155], 'roughness': .31, 'metallic': .21},
    BRONZE: {'color': [.19, .15, .10], 'metallic': .45},
    ROOF: {'color': [.30, .30, .27], 'roughness': .91},
    REAR: {'color': [.44, .393, .333], 'roughness': .90},
}

# Directed counterclockwise. The register's old 13 and current 93 describe
# this same southwest parcel. Only its northeast splay opens onto the junction.
SW = (-25.56, -11.91)
SE = (21.14, -13.03)
E = (21.72, 8.68)
A = (21.14, 10.02)
B = (17.94, 13.13)
N = (16.87, 13.44)
# Keep the western parapet inside the decoded neighboring facade. Its first
# draft overhung that wall by at most 9.5 cm along the shared northern segment.
NW = (-19.31, 13.39)
K = (-19.31, -4.84)
W = (-25.47, -5.06)
RING = [SW, SE, E, A, B, N, NW, K, W]
PLAN = Polygon(RING)
EAVE = 16.05
ATTIC = Polygon([(-5.5, -2.4), (4.7, -2.4), (6.5, -.35),
                 (6.5, 6.9), (-4.55, 6.9), (-6.2, 5.75)])


def course(face, z, height, projection):
    face.box(0, z, face.length + .025, height, projection + .23,
             projection / 2 - .115, TRIM, 'horizontal dressed-stone course')


def casement(face, aperture, lod, columns=2, rows=3):
    face.window(aperture, columns=columns, rows=min(2, rows) if lod else rows,
                frame=SASH, trim=False, glass=GLASS, label='inset sash')
    x0, z0, x1, _ = aperture.bounds
    face.box((x0 + x1) / 2, z0 - .06, x1 - x0 + .19, .13, .36, .09,
             TRIM, 'window sill')


def ionic(face, u, bottom, top, radius, lod):
    """A round granite shaft, two bases and a separately modelled volute capital."""
    builder = face.builder
    for z, dz, ratio in [(bottom + .07, .14, 1.38), (bottom + .19, .10, 1.22),
                         (top - .31, .12, 1.13), (top - .13, .21, 1.40)]:
        face.box(u, z, 2 * ratio * radius, dz, 2 * ratio * radius, .13, TRIM, 'Ionic base or abacus')
    center = face.point(u, bottom, .14)
    # Use true horizontal discs so the bases and shafts have vertical normals.
    profile = Point(center[0], center[1]).buffer(radius, resolution=4 if lod else 7)
    builder.plan_prism(profile, bottom + .24, top - .29, COLUMN, face.label + '/red granite shaft')
    for side in [-1, 1]:
        volute = Point(u + side * radius * .94, top - .24).buffer(radius * .35, resolution=5 if lod else 9)
        face.prism(volute, radius * .70, radius + .19, TRIM, 'Ionic scroll')
        if not lod:
            eye = Point(u + side * radius * .94, top - .24).buffer(radius * .11, resolution=6)
            face.prism(eye, radius + .191, radius + .219, COLUMN, 'volute eye')


def pediment(face, u, lintel, width, curved, lod):
    height = .49 + width * .056
    face.box(u, lintel - .045, width + .36, .15, .42, .10, TRIM, 'projecting entablature')
    if curved:
        n = 10 if lod else 18
        arch = [(u - width/2 + width*i/n, lintel + height*sin(pi*i/n)) for i in range(n+1)]
        poly = Polygon(arch + [(x, z + .14) for x, z in reversed(arch)])
    else:
        poly = Polygon([(u - width/2, lintel), (u, lintel+height), (u+width/2, lintel),
                        (u+width/2, lintel+.15), (u, lintel+height+.18), (u-width/2, lintel+.15)])
    face.prism(poly, -.02, .34, TRIM, 'segmental or triangular pediment')


def street(b, a, end, count, lod, name):
    face = Facade(b, a, end, name)
    width = face.length / count
    centers = [(i + .5) * width - face.length / 2 for i in range(count)]
    arches = []
    uppers = []
    for i, u in enumerate(centers):
        end_bay = i in (0, count-1)
        span = width * (.44 if end_bay else .69)
        ground = opening(u, .94, span, 4.35, arch=span*.45, segments=12 if lod else 24)
        arches.append(ground)
        upper = opening(u, 7.21, width*(.46 if end_bay else .50), 3.06)
        high = opening(u, 11.87, width*(.46 if end_bay else .50), 3.22)
        uppers.extend([upper, high])
        casement(face, ground, lod, 2, 3)
        casement(face, upper, lod, 2, 2)
        casement(face, high, lod, 2, 2)
        crown = ground.buffer(.28, join_style=2).difference(ground)
        crown = crown.intersection(box(u-span, 4.35 - span*.45 + .94, u+span, 6.25))
        face.prism(crown, .015, .21, TRIM, 'archivolt')
        face.box(u, 5.38, .30, .35, .43, .17, TRIM, 'arch keystone')
        pediment(face, u, 10.43, width*.64, i%2 == 0, lod)
        if not lod and not end_bay:
            spring = .94 + 4.35 - span*.45
            for j in (2, 4, 6, 8):
                t = pi*j/10
                face.box(u + .51*span*cos(t), spring + (span*.45+.11)*sin(t), .047, .17,
                         .08, .238, COLUMN, 'cut arch joint')
        if end_bay:
            for shift in [-1,1]:
                face.box(u+shift*width*.42,10.83,.40,9.10,.35,.10,WALL,'rusticated end pier')
    body = face.wall(0, EAVE, arches + uppers, thickness=.39, material=WALL)
    # Stone joints stop at each opening, exactly as the photographed voussoirs do.
    for z in ([.92,2.0,3.15,4.22,5.32] if lod else [.55,1.02,1.58,2.13,2.68,3.22,3.77,4.33,4.89,5.43]):
        groove = body.intersection(box(-face.length/2, z, face.length/2, z+.033))
        face.prism(groove, .006, .022, COLUMN, 'rusticated block joint')
    for i in range(1, count):
        ionic(face,-face.length/2+i*width,6.40,15.42,.32,lod)
    for z, h, d in [( .34,.22,.12),(5.96,.19,.22),(6.21,.31,.35),
                    (15.41,.20,.26),(15.73,.19,.35),(16.00,.25,.50)]:
        course(face,z,h,d)
    for i in range(round(face.length/(1.15 if lod else .60))):
        n=round(face.length/(1.15 if lod else .60))
        face.box((i+.5)*face.length/n-face.length/2,15.72,.18,.28,.32,.19,TRIM,'cornice dentil')
    return face


def corner(b, lod):
    face=Facade(b,A,B,'northeast portal')
    gate=opening(0,.15,3.32,5.10)
    window=opening(0,7.32,2.75,3.23)
    upper=opening(0,11.89,2.96,3.22)
    face.wall(0,EAVE,[gate,window,upper],.62,WALL)
    # A rectangular granite portal surrounds the deep door and its fanlight.
    fan=opening(0,3.30,2.94,1.56,arch=1.31,segments=12 if lod else 22)
    face.prism(gate.buffer(.02),-.97,-.92,BRONZE,'recessed paired door')
    face.prism(fan,-.69,-.65,GLASS,'recessed fanlight')
    for u in [-.80,-.40,0,.40,.80]:
        face.box(u,1.77,.035,3.18,.05,-.81,BRONZE,'door grille upright')
    for side in [-1,1]:
        ionic(face,side*1.80,.12,5.52,.24,lod)
        ionic(face,side*1.72,6.28,15.43,.255,lod)
    face.box(0,5.91,4.20,.77,.46,.15,TRIM,'plain entrance lintel')
    casement(face,window,lod,3,2);casement(face,upper,lod,3,2)
    pediment(face,0,10.75,2.99,True,lod)
    for z,h,d in [(6.23,.22,.31),(15.47,.22,.28),(15.78,.22,.39),(16.04,.29,.51)]:
        course(face,z,h,d)
    for a,end in [(E,A),(B,N)]:
        flank=Facade(b,a,end,'curved granite corner return')
        flank.wall(0,EAVE,(),.41,WALL)
        for z,h,d in [(5.98,.18,.24),(6.22,.28,.32),(15.48,.20,.26),(15.78,.20,.39),(16.04,.28,.5)]:
            course(flank,z,h,d)


def add_building(builder, lod):
    street(builder,SE,E,5,lod,'Sichuan Middle Road')
    street(builder,N,NW,7,lod,'Guangdong Road')
    corner(builder,lod)
    for a,end in [(NW,K),(K,W),(W,SW),(SW,SE)]:
        Facade(builder,a,end,'rear and shared wall').wall(0,EAVE,(),.23,REAR)
    builder.plan_prism(PLAN,0,.12,TRIM,'ground slab')
    builder.plan_prism(PLAN,15.95,16.14,ROOF,'principal roof')
    for a,end in zip(RING,RING[1:]+RING[:1]):
        wall=Facade(builder,a,end,'roof parapet')
        wall.wall(16.12,16.70,(),.22,WALL)
        course(wall,16.71,.11,.09)
    # Three imagery releases show a higher, small, partly clipped central mass.
    # Its exact construction is not identifiable from overhead, so its skin stays plain.
    for a,end in zip(list(ATTIC.exterior.coords)[:-1],list(ATTIC.exterior.coords)[1:]):
        Facade(builder,a,end,'setback partial storey').wall(16.14,18.83,(),.24,REAR)
    builder.plan_prism(ATTIC,18.73,18.89,ROOF,'setback roof')
