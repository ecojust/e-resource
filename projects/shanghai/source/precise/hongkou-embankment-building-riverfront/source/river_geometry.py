"""River and garden-facing wall centerlines measured in the shared local site frame."""
import math
from shapely.geometry import LineString
from shapely.ops import unary_union

HEIGHT = 31.82
GROUND = 3.02
FLOOR = 3.20
WEST = (-47.8, 8.4, 8.4, 155, 270)
CENTRAL = (60.8, 9.4, 10.05, 270, 348)
EAST = (100.35, 3.73, 10.80, 177, 345)

def arc(spec, sectors):
    x, y, radius, low, high = spec
    return [(x+radius*math.cos(math.radians(low+(high-low)*i/sectors)),
             y+radius*math.sin(math.radians(low+(high-low)*i/sectors))) for i in range(sectors+1)]

def segments():
    west, central, east = arc(WEST, 9), arc(CENTRAL, 8), arc(EAST, 12)
    return [('west short return',[(-53.75,15.02),west[0]],'court'),
            ('rounded west end',west,'ribbon'),
            ('long southwest river front',[west[-1],central[0]],'long'),
            ('pavilion rounded corner',central,'ribbon'),
            ('west wall of entrance court',[central[-1],(78.30,38.50)],'court'),
            ('inner head of entrance court',[(78.30,38.50),(98.10,34.09)],'court head'),
            ('east wall of entrance court',[(98.10,34.09),east[0]],'court'),
            ('rounded eastern river end',east,'ribbon'),
            ('outer eastern return',[east[-1],(113.50,8.50)],'court')]

def frontage():
    points=[]
    for _,run,_ in segments():
        points+=run if not points else run[1:]
    return LineString(points)

def footprint():
    # Backing depth is deliberately confined to the photographed garden and river front.
    return frontage().buffer(4.0,single_sided=True,join_style='mitre',mitre_limit=2.4)

def pavilion():
    x,y=60.30,7.27
    from shapely.geometry import Polygon
    return Polygon([(x+4.55*math.cos(math.tau*i/12),y+4.12*math.sin(math.tau*i/12))for i in range(12)])
