"""The recessed arch beside the green 364 plate, as seen from the public street in 2020.

The outer pavement is z=0. u increases to the viewer's right (street north);
the perpendicular depth d is positive toward the house. All solid() relief
coordinates follow placement.Facade; negative relief is inside the building.
"""
from math import asin, cos, pi, sin
from shapely.geometry import LineString, Point, Polygon, box
from materials import BASE, CEMENT, DARK, FRAME, GLASS, GRILLE, IRON, PAVE, PLASTER, SHADOW, WOOD, rgb

GREEN = 'Xiangyang | green enamel number plate'
IVORY = 'Xiangyang | light enamel digits'
LOUVER = 'Xiangyang | cream metal ventilation cover'
PALETTE = {GREEN:rgb((37,80,63),.48), IVORY:rgb((220,221,195),.63), LOUVER:rgb((184,175,150),.67)}
LEFT = (-2.21,.50,-1.08,1.70)
RIGHT = (1.08,.46,2.08,1.65)
REAR_D = 1.10

def arch(half_width, spring, rise, base=0., segments=36):
    radius=(half_width**2+rise**2)/(2*rise)
    angle=asin(half_width/radius)
    arc=[(radius*sin(a),spring+rise-radius+radius*cos(a))
         for a in [angle-2*angle*i/segments for i in range(segments+1)]]
    return Polygon([(-half_width,base),(half_width,base),*arc])

def opening_profile():
    return arch(.90,1.71,.70)

def openings():
    return [opening_profile(),box(*LEFT),box(*RIGHT)]

def _mark_number(f):
    u,z=1.035,2.058
    f.rect(u-.126,u+.126,z-.085,z+.085,.006,.021,GREEN,'364 enamel address plate')
    rim=box(u-.118,z-.077,u+.118,z+.077)
    f.solid(rim.difference(rim.buffer(-.0025,join_style=2)),.021,.022,IVORY,'364 enamel outline')
    strokes=[
        [(0,.90),(.26,1),(.71,1),(.93,.87),(.93,.66),(.76,.56),(.36,.52),(.78,.50),(.96,.36),(.94,.17),(.74,.02),(.22,0),(.01,.13)],
        [(.87,.95),(.64,1),(.31,.92),(.10,.69),(.06,.36),(.13,.14),(.35,0),(.71,.02),(.91,.15),(.92,.39),(.72,.55),(.34,.55),(.11,.39)],
        [(.70,0),(.70,1),(.03,.35),(.99,.35)]]
    for i,line in enumerate(strokes):
        x=u-.100+i*.069
        f.band([(x+a*.053,z-.042+b*.103) for a,b in line],.008,.022,.024,IVORY,'364 raised numerals')

def _low_window(f, side, bounds):
    x0,z0,x1,z1=bounds
    face=box(x0,z0,x1,z1)
    f.solid(face.buffer(.070,join_style=2).difference(face),-.016,.026,CEMENT,side+' window cement margin')
    clear=face.buffer(-.030,join_style=2)
    f.solid(face.difference(clear),-.255,-.002,SHADOW,side+' low window deep jamb')
    f.solid(clear,-.263,-.250,GLASS,side+' low window backing')
    f.solid(clear.difference(clear.buffer(-.027,join_style=2)),-.247,-.218,FRAME,side+' low casement frame')
    if side=='left':
        f.rect(x0+.36,x0+.39,z0+.03,z1-.03,-.246,-.214,FRAME,'left low casement upright')
        f.rect(x0+.03,x1-.03,z0+.39,z0+.42,-.242,-.211,FRAME,'left low casement rail')
    else:
        # Seven full uprights and a single crossbar are visible in the 2020 near photograph.
        for n in range(1,8):
            x=x0+n*(x1-x0)/8
            f.rect(x-.008,x+.008,z0+.012,z1-.012,-.015,.006,IRON,'right low opening iron bars')
        f.rect(x0+.012,x1-.012,z0+.47,z0+.487,-.014,.009,IRON,'right low opening crossbar')

def _low_vents(f):
    for name,u,z in [('left',-1.65,.24),('right',1.52,.23)]:
        outline=box(u-.105,z-.111,u+.105,z+.111).buffer(.025,join_style=1)
        f.solid(outline,.031,.036,DARK,name+' plinth vent shadow')
        f.solid(outline.difference(outline.buffer(-.012)),.036,.046,GRILLE,name+' plinth vent rim')
        for a in [45,135,225,315]:
            t=a*pi/180
            petal=Point(u+.051*cos(t),z+.051*sin(t)).buffer(.039,resolution=8)
            f.solid(petal.difference(petal.buffer(-.008)),.036,.047,GRILLE,name+' rounded vent ornament')

def add_entrance(f,lod=False):
    inner=opening_profile()
    surround=arch(1.046,1.74,.79,segments=28 if lod else 48)
    f.solid(surround.difference(inner),.002,.060,CEMENT,'segmental cement arch and jambs')
    # A continuous soffit and reveals extend to the dark door behind the arch.
    f.solid(inner.buffer(.044,join_style=2).difference(inner),-REAR_D,.001,SHADOW,'deep plaster entrance lining')
    rear=arch(.91,1.72,.71)
    f.solid(rear,-REAR_D-.052,-REAR_D,PLASTER,'recessed rear wall')
    f.rect(-.578,.557,.172,2.29,-REAR_D,-REAR_D+.026,WOOD,'timber doorway outer frame')
    f.rect(-.533,.512,.190,2.244,-REAR_D+.026,-REAR_D+.031,DARK,'recessed dark door joint')
    for x0,x1 in [(-.527,-.022),(-.010,.503)]:
        f.rect(x0,x1,.195,2.237,-REAR_D+.032,-REAR_D+.042,WOOD,'recessed dark timber leaf')
    for n,(depth,height) in enumerate([(.055,.070),(.315,.133),(.560,.184)]):
        low=[.012,.070,.133][n]
        f.rect(-.893,.893,low,height,-REAR_D,-depth,PAVE,'three shallow threshold treads')
    _low_window(f,'left',LEFT);_low_window(f,'right',RIGHT)
    _low_vents(f)
    _mark_number(f)
    cover=box(.925,2.452,1.910,3.094)
    f.solid(cover,-.002,.146,SHADOW,'louvered cover shadow box')
    inner_cover=cover.buffer(-.035,join_style=2)
    f.solid(cover.difference(inner_cover),.145,.185,LOUVER,'ventilation cover frame')
    # Horizontal slots have a lit upper edge and dark underside.
    for i in range(8):
        z=2.498+i*.071
        section=Polygon([(.152,z-.024),(.176,z-.030),(.189,z+.008),(.162,z+.018)])
        end=f.face(1.874,0,0,-1)
        end.solid(section,0,.914,LOUVER,'cream louver angled blades')
    if not lod:
        f.rail([(1.913,-.075,2.92),(2.00,-.067,2.92),(2.055,-.052,2.81),
                (2.055,-.041,2.53)],.013,CEMENT,'external service bend',8)
