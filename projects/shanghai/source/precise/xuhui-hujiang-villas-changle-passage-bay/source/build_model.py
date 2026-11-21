"""Build the covered lane entrance and projecting bay at Lane 613 Changle Road."""
from math import cos, pi, sin
from pathlib import Path
import sys

from shapely.geometry import box as rect
from shapely.ops import triangulate

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
import package_architectural_model as package
sys.path.insert(0, str(SOURCE.parents[1] / 'huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade
from street_finish import STONE, assign_uvs

ID = 'xuhui-hujiang-villas-changle-passage-bay'
META = {
    'id': ID, 'name': '沪江别墅长乐路613弄通道与挑窗',
    'viewer_page': 'hujiang-villas-changle-passage-bay.html',
    'heritage_group': '4D003', 'heritage_address': '长乐路613弄、615–629号（单号）',
    'scope': '沿长乐路的613弄入口、砖红色值守窗、二层钢窗、上层带水平条纹的挑窗及同一开间的女儿墙。',
    'coordinate_convention': 'Local metres. +X runs to the right when facing the entrance; +Y runs into the passage; Z is up.',
    'status': 'photographed-entrance-fragment',
}
GLASS = 'Grey blue window glass'
DARK_GLASS = 'Shadowed guard window glass'
STEEL = 'Dark steel window framing'
WHITE = 'Pale bay window framing'
GROOVE = 'Recessed horizontal joints'
BAND = 'Fine warm grey bay bands'
FINS = 'Ochre vertical infill strips'
LINING = 'Light grey passage lining'
MORTAR = 'Glazed tile mortar'
RED = 'Dark red glazed tile'
RED_ALT = 'Alternate red glazed tile'
REVEAL = 'Dark sill flashings'
WALK = 'Stone passage paving'
ADDRESS = 'Dark green lane plate'
TYPE = 'Light enamel lettering'


def color(rgb, roughness, metallic=0):
    def linear(v):
        v /= 255
        return v / 12.92 if v < .04045 else ((v + .055) / 1.055) ** 2.4
    return dict(color=[linear(v) for v in rgb], roughness=roughness, metallic=metallic)


PALETTE = {
    STONE: dict(color=[1, 1, 1], roughness=.86, texture=str(SOURCE / 'street-finish.png')),
    GLASS: color((102, 123, 130), .27, .24), DARK_GLASS: color((69, 85, 82), .36, .18),
    STEEL: color((53, 60, 57), .53, .24), WHITE: color((204, 207, 197), .42, .21),
    GROOVE: color((107, 100, 95), .86), BAND: color((174, 165, 151), .81), FINS: color((163, 139, 93), .79),
    LINING: color((164, 156, 143), .89), MORTAR: color((147, 120, 107), .86),
    RED: color((124, 68, 57), .46), RED_ALT: color((114, 60, 50), .5),
    REVEAL: color((81, 79, 74), .65), WALK: color((143, 134, 122), .89),
    ADDRESS: color((38, 95, 76), .52), TYPE: color((211, 215, 186), .57),
}
GATE_W, LINTEL = 4.09, 3.30
WINDOW_W, SILL, HEAD = 2.01, 5.12, 6.83
BAY_W, BAY_D, SOFFIT, GLASS_BASE, GLASS_TOP = 2.54, .89, 7.42, 8.58, 10.32
HALF, HEIGHT, DEPTH = 2.61, 11.92, 2.80


def box(b, x, y, z, w, d, h, mat, label):
    b.box((x, y, z), (w, d, h), mat, label=label)


def rounded_apron(b, z0, z1, outset, material, label, lod):
    # Only the two projecting front corners are round. The rear is housed in the wall.
    half, nose, radius = BAY_W / 2 + outset, BAY_D + outset, .14 + outset
    ring = [(-half, .06), (-half, -nose + radius)]
    arcs = [(-half + radius, pi, 1.5 * pi), (half - radius, 1.5 * pi, 2 * pi)]
    for cx, a, c in arcs:
        for i in range(1 + (4 if lod else 12)):
            t = a + (c - a) * i / (4 if lod else 12)
            pt = (cx + radius * cos(t), -nose + radius + radius * sin(t))
            if abs(pt[0]-ring[-1][0]) + abs(pt[1]-ring[-1][1]) > 1e-7:
                ring.append(pt)
    ring.append((half, .06))
    verts = [(x,y,z) for z in (z0,z1) for x,y in ring]
    n = len(ring)
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
    b.add(verts,faces,material,label)


def casement(face, width, low, high, columns, rows, frame, glass, name, inset=.05):
    """Use individual panes and real metal bars in the shallow projecting bay."""
    height = high - low
    cy = (low + high) / 2
    stile = .040 if frame == WHITE else .031
    rail = .035 if frame == WHITE else .024
    face.box(0, cy, width, height, .012, -inset, glass, name+' glass')
    for i in range(columns + 1):
        x = -width/2 + stile/2 + i*(width-stile)/columns
        face.box(x, cy, stile, height, .054, -inset+.026, frame, name+' stiles')
    for i in range(rows + 1):
        z = low + rail/2 + i*(height-rail)/rows
        face.box(0, z, width, rail, .044, -inset+.020, frame, name+' rails')
    if rows > 1:
        for x in [-width/6,width/6]:
            face.box(x, cy-.082, .043, .167, .025, -inset+.058, frame, name+' latch plates')


def facade(b):
    street = Facade(b, (-HALF,0), (HALF,0), 'Lane facade')
    opening = rect(-GATE_W/2, -.03, GATE_W/2, LINTEL)
    mid = rect(-WINDOW_W/2, SILL, WINDOW_W/2, SOFFIT)
    upper = rect(-BAY_W/2+.10, GLASS_BASE, BAY_W/2-.10, GLASS_TOP)
    street.wall(0,HEIGHT,[opening,mid,upper],.29,STONE)
    # Lay the dark bed joints at the face, cut back where a window or entrance interrupts them.
    gaps = [(0., LINTEL, GATE_W), (SILL, SOFFIT, WINDOW_W), (GLASS_BASE, GLASS_TOP, BAY_W)]
    for z in [i*.72 for i in range(1,17)]:
        opening_width = next((width for low,high,width in gaps if low<z<high),0.)
        spans = [(-HALF,-opening_width/2),(opening_width/2,HALF)] if opening_width else [(-HALF,HALF)]
        for left,right in spans:
            box(b,(left+right)/2,-.003,z,right-left,.008,.012,GROOVE,'Horizontal facade joints')
    casement(street,WINDOW_W,SILL,HEAD,3,5,STEEL,GLASS,'Three-part steel window',.12)
    street.box(0,SILL-.012,WINDOW_W+.15,.085,.17,.04,BAND,'Projecting sill')
    street.box(0,(HEAD+SOFFIT)/2,WINDOW_W,SOFFIT-HEAD,.09,-.11,FINS,'Ochre head board')
    for i in range(21):
        street.box((i-10)*.093,(HEAD+SOFFIT)/2,.011,SOFFIT-HEAD,.012,-.06,GROOVE,'Joints between ochre strips')
    box(b,0,.13,HEIGHT-.027,2*HALF+.044,.41,.081,BAND,'Flat parapet edge')


def bay(b,lod):
    rounded_apron(b,SOFFIT,GLASS_BASE,0,STONE,'Rounded projecting breast',lod)
    rounded_apron(b,SOFFIT-.032,SOFFIT+.026,.023,REVEAL,'Bay sill drip edge',lod)
    for i in range(10):
        z=SOFFIT+.082+i*.107
        rounded_apron(b,z,z+.024,.014,BAND,'Raised horizontal bay ribs',lod)
    half=BAY_W/2-.066
    front=Facade(b,(-half,-BAY_D+.01),(half,-BAY_D+.01),'Bay front')
    casement(front,2*half,GLASS_BASE,GLASS_TOP,4,1,WHITE,GLASS,'Bay street casements')
    for side in (-1,1):
        x=side*half
        ends=((x,.02),(x,-BAY_D+.01)) if side<0 else ((x,-BAY_D+.01),(x,.02))
        f=Facade(b,*ends,'East bay return' if side<0 else 'West bay return')
        width=f.length
        casement(f,width,GLASS_BASE,GLASS_TOP,2,1,WHITE,GLASS,'Bay side casements')
    rounded_apron(b,GLASS_TOP,GLASS_TOP+.075,.012,WHITE,'Bay head flashing',lod)


def passage(b,lod):
    for sign in (-1,1):
        box(b,sign*(GATE_W/2+.13),DEPTH/2, LINTEL/2,.26,DEPTH,LINTEL,LINING,'Passage return lining')
    box(b,0,DEPTH/2,LINTEL+.075,GATE_W+.02,DEPTH,.15,LINING,'Passage ceiling')
    box(b,0,DEPTH/2,-.055,GATE_W+.1,DEPTH,.11,WALK,'Through passage paving')
    for i in range(1,6):
        box(b,0,i*DEPTH/6,-.001,GATE_W,.012,.004,REVEAL,'Paving cross joints')
    # The red-tiled guard window projects from the right return, just behind the street pier.
    x=GATE_W/2-.34
    front=Facade(b,(x-.34,.36),(x+.34,.36),'Guard front')
    side=Facade(b,(x-.34,DEPTH),(x-.34,.36),'Guard passage side')
    for f,glasswidth in [(front,.35),(side,.98)]:
        window=rect(-glasswidth/2,.97,glasswidth/2,1.96)
        f.wall(.04,LINTEL-.03,[window],.08,MORTAR)
        casement(f,glasswidth,.97,1.96,2,1,WHITE,DARK_GLASS,'Guard window',.035)
        width=f.length;cols=round(width/.109);rows=17
        for iz in range(rows):
            for ix in range(cols):
                tw=width/cols;th=(LINTEL-.07)/rows
                tile=rect(-width/2+ix*tw+.004,.04+iz*th+.006,-width/2+(ix+1)*tw-.004,.04+(iz+1)*th-.006).difference(window)
                if tile.is_empty:continue
                mat=RED_ALT if (ix+3*iz)%7==0 else RED
                if lod:
                    # The LOD retains every mortar gap and window opening while dropping concealed tile sides.
                    for triangle in triangulate(tile):
                        if tile.covers(triangle.representative_point()):
                            points = [f.point(u,z,.012) for u,z in list(triangle.exterior.coords)[:3]]
                            b.add(points,[(0,1,2)],mat,f.label+'/Glazed red tiles')
                else:
                    f.prism(tile,.002,.012,mat,'Glazed red tiles')
    front.box(0,2.67,.55,.245,.022,.035,ADDRESS,'613 lane enamel plate')
    from lane_numbers import address_digits
    address_digits(front)


def add_building(b,lod):
    facade(b)
    bay(b,lod)
    passage(b,lod)
    assign_uvs(b)


if __name__ == '__main__':
    package.Builder = AggregateBuilder
    package.build(SOURCE,META,PALETTE,add_building)
