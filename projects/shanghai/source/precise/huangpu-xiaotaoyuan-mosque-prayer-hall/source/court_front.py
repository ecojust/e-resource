"""The three-arch court entrance and recessed upper windows, using the 2015 and 2025 photographs."""
from math import cos, sin, pi
from pathlib import Path

from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering

WHITE = 'light cream render'
GREEN = 'grey green recessed wall'
STONE = 'off-white masonry trim'
BASE = 'grey stone sill and stair'
GLASS = 'grey blue window glass'
METAL = 'dark enamel window frame'
DOOR = 'brown timber doors'
COLUMN = 'deep green round columns'
TURQUOISE = 'green corner domes'
GOLD = 'gold cupola and lettering'
DARK = 'dark plaque ground'
ROOF = 'weathered flat roofing'
PALETTE = {
    WHITE:(.807,.794,.737),GREEN:(.430,.504,.475),STONE:(.829,.811,.749),
    BASE:(.458,.460,.433),GLASS:(.205,.270,.285),METAL:(.176,.190,.180),
    DOOR:(.303,.177,.125),COLUMN:(.258,.344,.315),TURQUOISE:(.171,.427,.376),
    GOLD:(.761,.598,.319),DARK:(.177,.182,.161),ROOF:(.374,.377,.351),
}
PALETTE = {k:{'color':list(v),'roughness':.38 if k in (GOLD,GLASS) else .83} for k,v in PALETTE.items()}
FONT = Path(__file__).with_name('fonts')/'XiaotaoyuanInscription.otf'


def curved_light(f, x, width, spring, z0, lod, upper=False):
    """The grid is cut to the perimeter, leaving the three radial lights visibly separate."""
    radius = width/2
    outer = opening(x,z0,width,spring+radius-z0,radius,12 if lod else 26)
    f.prism(outer.buffer(.009,join_style=2),-.32,-.29,GLASS,'recessed arch glass')
    bars = [box(x-radius,spring-.055,x+radius,spring+.055)]
    # The primary canopy shows concentric half-rings and radial glazing bars.
    ring_r = radius*(.52 if upper else .49)
    ring = LineString([(x+ring_r*cos(t*pi/24),spring+ring_r*sin(t*pi/24)) for t in range(25)])
    bars.append(ring.buffer(.038,cap_style=2))
    for alpha in (pi/4,pi/2,3*pi/4):
        bars.append(LineString([(x+ring_r*cos(alpha),spring+ring_r*sin(alpha)),
                                (x+radius*cos(alpha),spring+radius*sin(alpha))]).buffer(.034,cap_style=2))
    if upper:
        for i in (-1,0,1):
            u=x+i*width*.246
            bars.append(box(u-.022,z0,u+.022,spring))
        bars += [box(x-radius,z-.02,x+radius,z+.02) for z in (z0+.53,z0+1.02)]
    inset = outer.buffer(-.073,join_style=2)
    rails = outer.difference(inset.difference(unary_union(bars)))
    f.prism(rails,-.255,-.133,METAL,'arched transom and radial steel')
    band=outer.buffer(.149,join_style=2).difference(outer)
    f.prism(band,-.05,.095,STONE,'pale arch surround')
    return outer


def main_front(b, lod):
    xs = [-3.14,0,3.14]
    f=Facade(b,(-5.03,1.72),(5.03,1.72),'Court/entrance')
    holes=[]
    for x in xs:
        aperture = curved_light(f,x,2.30,3.50,.49,lod)
        door=box(x-1.15,.49,x+1.15,3.49)
        f.prism(door,-.277,-.247,DOOR,'closed pair of wood doors')
        f.box(x,1.986,.052,2.98,.074,-.207,METAL,'door meeting stile')
        for side in (-1,1):
            for z in (.92,1.66,2.52):
                u=x+side*.567
                panel=box(u-.424,z-.24,u+.424,z+.24)
                f.prism(panel.difference(panel.buffer(-.060,join_style=2)),-.235,-.18,DOOR,'raised timber panels')
        holes.append(aperture)
    f.wall(0,5.52,holes,.36,WHITE)
    for edge in (-5.03,5.03):
        side=Facade(b,(edge,1.72 if edge>0 else .10),(edge,.10 if edge>0 else 1.72),'Court/portico')
        side.wall(0,5.56,[],.19,WHITE)
    f=Facade(b,(-5.06,.17),(5.06,.17),'Court/upper facade')
    holes=[curved_light(f,x,2.63,9.24,7.16,lod,True) for x in xs]
    f.wall(5.72,11.44,holes,.36,GREEN)
    for z,h,proj in ((5.58,.27,.23),(5.80,.17,.33),(6.03,.20,.18),(11.30,.19,.21),(11.51,.11,.33)):
        f.beam(z,h,proj,STONE)
    background=box(-2.38,6.10,2.38,7.02)
    f.prism(background,-.018,.214,DARK,'inscription board')
    f.prism(background.difference(background.buffer(-.082,join_style=2)),.214,.269,GOLD,'inscription frame')
    add_facade_lettering(f,'教正揚顯',0,6.57,4.00,.64,.216,.255,GOLD,label='four-character court inscription',font=FONT)
    for x in (-1.56,1.56):
        b.lathe((x,.21),[(.50,.40),(.60,.40),(.64,.32),(.79,.31),(.84,.258),
                          (5.08,.234),(5.17,.257),(5.23,.32),(5.36,.36),(5.41,.40)],
                COLUMN,14 if lod else 28,'Court/round recessed columns')
        b.box((x,.21,5.48),(.83,.82,.16),STONE,label='Court/column square abacus')
    for k in range(4):
        h = .123*(k+1)
        edge = 1.50 - .31*k
        b.box((0,.17-edge/2,h/2),(10.02,edge,h),BASE,label='Court/four granite steps')
    # The last granite tread meets the recessed doorway at one continuous raised level.
    b.box((0,.942,.246),(10.06,1.56,.492),BASE,label='Court/portico landing')
    b.box((0,.943,5.48),(10.10,1.61,.23),WHITE,label='Court/portico soffit')
