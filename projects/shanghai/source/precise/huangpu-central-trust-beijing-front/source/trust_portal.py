"""Beijing East Road 270. Photographed south entrance, in metres.

The 2023 Huangpu District front view fixes the widths, column positions and
the four right-to-left stone characters. Its closer view shows the carved
border, fluting, scroll capitals, two gridded leaves and barred transom.
The 2020-published oblique and straight views also show the recess.
Depths, flute count, small relief patterns and letterforms are estimates.
Positive facade depth faces the road. The host wall needs PORTAL_CUT.
"""
import math
from pathlib import Path

from shapely import set_precision
from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from sign_lettering import lettering_shapes


ASHLAR = 'Trust entry pale stone'
EDGE = 'Trust entry worn arris'
RELIEF = 'Trust entry cut relief'
DEEP = 'Trust entry stone in shadow'
WOOD = 'Trust entry dark timber'
GLASS = 'Trust entry warm glazing'
BRONZE = 'Trust entry bronze'
FLOOR = 'Trust entry threshold'
BACK = 'Trust entry interior shade'

PORTAL_MATERIALS = {
    ASHLAR: {'color': [.64, .61, .54], 'roughness': .81},
    EDGE: {'color': [.73, .70, .63], 'roughness': .79},
    RELIEF: {'color': [.56, .53, .47], 'roughness': .85},
    DEEP: {'color': [.46, .43, .37], 'roughness': .83},
    WOOD: {'color': [.185, .116, .080], 'roughness': .59},
    GLASS: {'color': [.30, .25, .17], 'roughness': .30, 'metallic': .14},
    BRONZE: {'color': [.31, .23, .14], 'roughness': .44, 'metallic': .46},
    FLOOR: {'color': [.385, .37, .34], 'roughness': .75},
    BACK: {'color': [.067, .060, .052], 'roughness': .95},
}

PORTAL_CUT = {
    'width': 5.18, 'height': 5.17, 'bottom': 0.0,
    'door_depth': -1.20, 'door_width': 1.86,
    'column_x': (-1.55, 1.55), 'column_d': -.19,
    'column_radius_bottom': .275, 'column_radius_top': .245,
    'column_plinth_width': .76,
}

FONT_SUBSET = Path(__file__).with_name('trust-inscription.otf')
FONT_SOURCE = {
    'name': 'Noto Serif CJK TC Bold (renamed, four characters)',
    'url': 'https://github.com/notofonts/noto-cjk',
    'parent_sha256': '1505ee3b9c0890fae6302ee0e9c6fd74d690f4a55a6ace1d9944f3f6352d622d',
    'subset_sha256': '0fa150a440937bedd83d7da57a83941057cdf2744dce6634acbf95513e639282',
    'license': 'SIL Open Font License 1.1, see trust-inscription-OFL.txt',
}


def slab(face, x0, z0, x1, z1, back, front, material, name):
    face.box((x0+x1)/2, (z0+z1)/2, x1-x0, z1-z0, front-back,
             (front+back)/2, material, name)


def stroke(points, width):
    return LineString(points).buffer(width/2, cap_style='flat', join_style='mitre')


def meander(face, lod):
    """One narrow, continuous squared return cut into each side of the surround."""
    tracks = []
    for side in (-1, 1):
        points = []
        count = 19 if lod else 28
        for i in range(count):
            base = .57+i*5.41/count
            cell = 5.41/count
            for offset, rise in ((0, 0), (0, .77), (.085, .77), (.085, .39),
                                 (.046, .39), (.046, .53)):
                points.append((side*(3.465-offset), base+rise*cell))
            points.extend([(side*3.365, base+.53*cell),
                           (side*3.365, base+cell), (side*3.465, base+cell)])
        tracks.append(stroke(points, .014 if lod else .012))
    # Above the inscription the stone border is horizontal, with a much finer bead.
    tracks.append(box(-3.46, 5.984, 3.46, 6.000))
    face.prism(set_precision(unary_union(tracks), .0001),
               .139, .148, RELIEF, 'return cut border')


def rosette(face, u, z, lod):
    """A circular stone flower in each of the four corner panels."""
    steps = 24 if lod else 48
    # Underlying disks and centered petals make a very low stone bas-relief.
    def outline(radius, petal):
        pts = []
        for i in range(steps):
            a = 2*math.pi*i/steps
            r = radius*(1+petal*math.cos(8*a))
            pts.append((u+r*math.cos(a), z+r*math.sin(a)))
        return Polygon(pts)
    face.prism(outline(.128, .0), .076, .092, RELIEF, 'corner rosette bed')
    face.prism(outline(.082, .30), .090, .115, EDGE, 'corner rosette petals')
    face.prism(outline(.028, .0), .111, .127, ASHLAR, 'corner rosette heart')


def frame(face, lod):
    hole = box(-2.59, -.03, 2.59, 5.17)
    body = box(-3.72, 0, 3.72, 6.23).difference(hole)
    face.prism(body, -.052, .077, ASHLAR, 'portal jambs and lintel')
    inset = box(-3.50, .36, 3.50, 6.04).difference(box(-3.35, .28, 3.35, 5.89))
    face.prism(inset, .073, .139, EDGE, 'outer three sided moulding')
    for side in (-1, 1):
        x0, x1 = sorted((side*2.596, side*3.66))
        slab(face, x0, .02, x1, .30, .061, .119, ASHLAR, 'jamb low plinth')
        slab(face, x0, .30, x1, .38, .064, .148, EDGE, 'jamb plinth lip')
        for z in (.79, 5.52):
            rosette(face, side*2.99, z, lod)
    meander(face, lod)
    # The original stone surround has three broad beds, distinguishable in both views.
    for z0,z1,half,front in [(6.13,6.20,3.74,.170),(6.20,6.27,3.80,.226),
                              (6.27,6.36,3.87,.302)]:
        slab(face, -half, z0, half, z1, -.030, front, EDGE, 'portal cap beds')
    for i,(char, shape) in enumerate(lettering_shapes('樓大一中', 2.39, .36, font=FONT_SUBSET)):
        glyph = set_precision(translate(shape, yoff=5.52).simplify(
            .003 if lod else .0009, preserve_topology=True), .0001)
        face.prism(glyph, .075, .105, EDGE, 'stone inscription '+str(i+1)+' '+char)


def column(face, u, lod, side):
    d = PORTAL_CUT['column_d']
    # Each true radial depression fades into the neck and foot of the shaft.
    profile = [
        (.19,.351,0), (.245,.351,0), (.252,.325,0), (.284,.325,0),
        (.30,.314,0), (.326,.332,0), (.371,.332,0), (.386,.298,0),
        (.414,.290,0), (.447,.306,0), (.468,.306,0), (.49,.275,0),
        (.555,.275,.85), (.650,.275,1), (1.73,.272,1),
        (3.30,.261,1), (4.62,.245,1), (4.74,.245,.8), (4.77,.245,0),
        (4.79,.265,0), (4.82,.270,0), (4.845,.254,0), (4.875,.284,0),
        (4.910,.305,0), (4.951,.314,0), (5.005,.330,0),
    ]
    flutes = 20
    sides = flutes*(3 if lod else 5)
    verts=[]
    for z, radius, fluted in profile:
        for i in range(sides):
            angle=2*math.pi*i/sides
            r=radius-.020*fluted*(.5-.5*math.cos(flutes*angle))
            verts.append(face.point(u+r*math.sin(angle),z,d+r*math.cos(angle)))
    panels=[]
    for ring in range(len(profile)-1):
        for i in range(sides):
            a=ring*sides+i
            b=ring*sides+(i+1)%sides
            panels.append((a,b,b+sides,a+sides))
    panels.extend([tuple(reversed(range(sides))),tuple(range(len(verts)-sides,len(verts)))])
    face.builder.add(verts,panels,ASHLAR,side+' fluted stone shaft')
    slab(face,u-.38,.015,u+.38,.19,d-.38,d+.38,ASHLAR,side+' square pedestal')
    for z0,z1,r in [(5.002,5.054,.334),(5.054,5.107,.363),(5.107,5.17,.387)]:
        slab(face,u-r,z0,u+r,z1,d-r,d+r,EDGE,side+' square capital cap')
    for sign in (-1,1):
        cx,cz=u+sign*.224,4.936
        steps=30 if lod else 54
        outline=[]
        for j in range(steps+1):
            a=j/steps*2.9*math.pi
            r=.138*(1-j/steps)+.011
            outline.append((cx+sign*r*math.cos(a+.45),cz+r*math.sin(a+.45)))
        # The dark bed and the outward, rounded spiral are on the street face.
        disk=Polygon([(cx+.147*math.cos(i*math.tau/32),
                       cz+.132*math.sin(i*math.tau/32)) for i in range(32)])
        face.prism(disk,d+.206,d+.287,RELIEF,side+' scroll cushion')
        face.prism(stroke(outline,.027),d+.280,d+.320,EDGE,side+' Ionic volutes')


def leaf_grid(face, lod):
    """Two timber stiles, smaller rail-and-saltire panes, and the overdoor light."""
    for side in (-1,1):
        center=side*.463
        x0,x1=center-.456,center+.456
        slab(face,x0,.112,x1,2.776,-1.280,-1.251,GLASS,'double door recessed glass')
        outer=box(x0,.111,x1,2.78)
        inner=box(x0+.095,.29,x1-.095,2.64)
        bars=[]
        a,b=x0+.095,x1-.095
        levels=[.29,1.058,1.826,2.64]
        for za,zb in zip(levels,levels[1:]):
            if not lod:
                bars.append(stroke([(a+.032,za+.034),(b-.032,zb-.034)],.021))
                bars.append(stroke([(b-.032,za+.034),(a+.032,zb-.034)],.021))
            else:
                bars.append(stroke([(a+.032,za+.034),(b-.032,zb-.034)],.027))
            bars.append(box(a,za-.012,b,za+.012))
        shape=outer.difference(inner).union(unary_union(bars))
        face.prism(set_precision(shape,.0001),-1.245,-1.20,WOOD,'double door timber and grille')
        slab(face,side*.120-.014,1.04,side*.120+.014,1.29,-1.20,-1.157,
             BRONZE,'paired handles')
    light=box(-.91,2.87,.91,3.46)
    rails=[light.difference(box(-.856,2.93,.856,3.404))]
    for i in range(3):
        a=-.856+i*(1.712/3); b=a+(1.712/3)
        rails.extend([stroke([(a,2.93),(b,3.404)],.022),
                      stroke([(a,3.404),(b,2.93)],.022),
                      box(a-.011,2.93,a+.011,3.404)])
    face.prism(light,-1.281,-1.252,GLASS,'overdoor recessed glass')
    face.prism(set_precision(unary_union(rails),.0001),-1.249,-1.212,WOOD,'overdoor grille')
    lintel=box(-1.025,.081,1.025,3.59).difference(box(-.930,.065,.930,3.48))
    face.prism(lintel,-1.298,-1.188,WOOD,'timber door lining')


def add_portal(face, lod):
    """Populate the centered opening in a straight south-facing Facade."""
    frame(face,lod)
    # Passage sides, soffit and floor bound a genuine recess, extending past
    # the thickness of the host wall until they meet the door's rear wall.
    for sign in (-1,1):
        x0,x1=sorted((sign*2.59,sign*2.64))
        slab(face,x0,.0,x1,5.17,-1.357,.012,ASHLAR,'stone passage returns')
    slab(face,-2.59,5.14,2.59,5.185,-1.36,.011,ASHLAR,'stone passage soffit')
    slab(face,-2.60,.006,2.60,.080,-1.35,.086,FLOOR,'recessed threshold')
    rear=box(-2.60,.062,2.60,5.164).difference(box(-1.003,.070,1.003,3.565))
    face.prism(rear,-1.345,-1.305,DEEP,'rear vestibule wall')
    slab(face,-1.01,.067,1.01,3.566,-1.342,-1.319,BACK,'glazing shadow backstop')
    leaf_grid(face,lod)
    for side,u in zip(('west','east'), PORTAL_CUT['column_x']):
        column(face,u,lod,side)
