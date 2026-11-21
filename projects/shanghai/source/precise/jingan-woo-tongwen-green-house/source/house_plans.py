"""Trace the 700 px study plans in one coordinate system, preserving their setbacks."""
import math
from shapely.geometry import Polygon

METRES_PER_PIXEL = .0625
ORIGIN = (350., 240.)
LEVELS = (0., 4.30, 7.93, 11.47, 14.95)

def to_metres(point):
    return ((point[0]-ORIGIN[0])*METRES_PER_PIXEL, (ORIGIN[1]-point[1])*METRES_PER_PIXEL)

def arc(center, radius, start, stop, steps):
    return [(center[0]+radius*math.cos(math.radians(start+(stop-start)*i/steps)),
             center[1]+radius*math.sin(math.radians(start+(stop-start)*i/steps))) for i in range(steps+1)]

def line(*points):
    return list(points)

def plan_from_traces(traces):
    border = []
    for _, pts in traces:
        if border and math.dist(border[-1],pts[0]) > .002:
            raise ValueError(('Disconnected wall traces',border[-1],pts[0]))
        border += pts if not border else pts[1:]
    poly = Polygon([to_metres(p) for p in border])
    if not poly.is_valid or poly.area < 5:
        raise ValueError('Invalid building outline')
    return poly

def ground_parts(lod):
    count=12 if lod else 28
    # The undercroft between the northern hall and the garden-side ground rooms
    # is visible both in the bottom plan and in the photographed driveway.
    garden=[('solid',line((247,288),(493,288))),
            ('round_ground',arc((493,328),40,-90,90,count)),
            ('garden_ground',line((493,368),(271,368))),
            ('solid',arc((271,344),24,90,180,count//2)),
            ('solid',line((247,344),(247,288)))]
    north=[('solid',line((109,54),(109,215))),
           ('hall_glass',line((109,215),(247,215))),
           ('solid',line((247,215),(287,215))),
           ('drive_glass',line((287,215),(368,215))),
           ('solid',line((368,215),(368,224),(425,224),(425,243),(495,243),(495,196),(470,196),(470,164),(429,164),(429,150))),
           ('stair_glass',arc((399,150),30,0,-180,count)),
           ('solid',line((369,150),(369,139),(289,139),(289,54),(109,54)))]
    # Plan 20 has a different print scale. Its two circular centres register the
    # lower walls to the third-floor plan, leaving the original open driveway.
    def convert(edges):
        return [(kind,[(443+1.25*(x-400),118+1.25*(y-149)) for x,y in points]) for kind,points in edges]
    return [convert([(kind,list(reversed(path))) for kind,path in reversed(garden)]),convert(north)]

def upper_parts(floor,lod):
    count=18 if lod else 46
    # Each elevation reverses on the south garden side. The rear vertical
    # stair lantern and the southeastern sun-room align across all stories.
    a=(75,78);b=(75,198);c=(250,198)
    side=[('west_end',line(a,b)),('west_garden',line(b,c))]
    if floor==1:
        side += [('solid',line(c,(250,285))),('living_doors',line((250,285),(402,285))),
                 ('solid',line((402,285),(402,338))),('garden_casements',line((402,338),(512,338)))]
    elif floor==2:
        side += [('solid',line(c,(250,288))),('living_doors',line((250,288),(471,288))),
                 ('solid',line((471,288),(471,338))),('single',line((471,338),(512,338)))]
    else:
        side += [('solid',line(c,(387,198),(387,224))),
                 ('upper_round',arc((465,224),78,180,90,count//2)),
                 ('solid',line((465,302),(479,302),(479,338))),('single',line((479,338),(512,338)))]
    side += [('sun_room',arc((561,338),49,180,-90,count)),
             ('east_side',line((561,289),(561,160))),('solid',line((561,160),(482,160),(482,118))),
             ('stair_glass',arc((443,118),39,0,-180,count//2)),
             ('north_short',line((404,118),(293,118))),('solid',line((293,118),(293,80),(250,80),(250,78))),
             ('north_ribbon',line((250,78),a))]
    return side

def terrace_paths(lod):
    n=10 if lod else 24
    first=line((250,285),(191,285),(191,365),(248,365))+arc((277,365),29,180,68,n)[1:]+line((558,395))
    # Garden floor projects in front of all three upper room walls.
    first+=arc((558,346),49,90,0,n)[1:]
    second=line((250,198),(246,198),(246,257))+arc((323,257),77,180,90,n)[1:]+line((471,334),(471,290))
    third=line((250,198),(245,198),(245,284),(341,284))+arc((428,252),92,160,90,n)[1:]+line((478,344),(478,302))
    return [first,second,third]
