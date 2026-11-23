"""The recessed street wing, exterior returns and short west garden balcony of No. 174."""
from math import hypot
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from street_gable import W
from villa_roofs import GUTTER, NORTH_WING, WALL_PLAN
from wuyi_fabric import BRICK, FRAME, IRON, SOFFIT, STONE, WALL, glazing, slab, wall


def pierced_face(b,a,c,high,openings,label):
    length=hypot(c[0]-a[0],c[1]-a[1])
    panel=box(0.,-.015,length,high)
    cutouts=unary_union([p for p,_,_,_ in openings])
    wall(b,panel.difference(cutouts),a,c,0.,.22,WALL,label+' roughcast')
    for p,cols,rows,name in openings:
        glazing(b,p,a,c,.115,label+' '+name,cols,rows)
        l,lo,r,hi=p.bounds
        wall(b,box(l-.055,hi,r+.055,hi+.066),a,c,-.043,.022,STONE,label+' dressed head')
        wall(b,box(l-.113,lo-.088,r+.113,lo),a,c,-.095,.040,STONE,label+' projecting sill')


def pipe(b,x,y,bend,top,label,lod):
    b.tube([(x,y,.12),(x,y,top-.47),(x+bend*.73,y-.115,top-.28),
            (x+bend,y-.18,top-.18),(x+bend,y-.18,top)],.051,GUTTER,7 if lod else 12,label)
    for z in (.76,2.58,4.45):
        if z>=top-.48:continue
        b.box((x,y,z),(.119,.112,.041),GUTTER,label=label+' fixing strap')


def add_envelope(b,lod=False):
    slab(b,WALL_PLAN,-.11,.021,STONE,'perimeter stone footing')
    # Beyond the main gable the 2025 frontal and later oblique photos show a
    # paired casement, a narrow casement and a third opening on the canted return.
    a,c=NORTH_WING[:2]
    rects=[(box(1.62,4.38,2.85,5.96),2,2,'upper pair'),
           (box(3.47,4.37,4.05,5.94),1,2,'upper single'),
           (box(1.91,.74,3.12,2.16),2,2,'lower pair'),
           (box(3.53,.74,4.18,2.15),1,2,'lower single')]
    pierced_face(b,a,c,7.19,rects,'street wing')
    a,c=NORTH_WING[1:3]
    pierced_face(b,a,c,7.19,[(box(.27,4.35,1.36,5.97),1,3,'upper return'),
                            (box(.30,.75,1.34,2.17),1,2,'lower return')],'oblique street wing')
    pierced_face(b,NORTH_WING[2],NORTH_WING[3],6.92,[],'west end of street wing')
    # The main gable is in front of the cross wing.
    pierced_face(b,(W,0),NORTH_WING[0],6.47,[],'short return of gable')
    pierced_face(b,(0,13.60),(0.,0.),6.49,[],'east side')
    # The plain outer end is bounded by the hipped roof. No repeat of the
    # north-side windows has been inferred on the obscured side elevation.
    a,c=NORTH_WING[3],(NORTH_WING[3][0],13.60)
    length=c[1]-a[1]
    pitch=(10.42-5.52)/(13.90-7.52)
    hip_at_wall=6.32+.98*(15.78-a[0])
    meeting=13.90-(hip_at_wall-5.52)/pitch-a[1]
    end=Polygon([(0,0),(length,0),(length,5.52+pitch*(13.90-c[1])-.13),
                 (meeting,hip_at_wall-.13),(0,hip_at_wall-.13)])
    wall(b,end,a,c,0,.23,WALL,'west hipped return')
    # The south gable rises above the cross wing. Its masonry closes the
    # exposed strip between the two roof heights at the east end of the large dormer.
    wall(b,Polygon([(0,5.24),(.524,5.24),(.524,6.98),(0,6.44)]),
         (W,13.60),(W-1.,13.60),0.,.22,WALL,'south gable junction spandrel')
    wall(b,Polygon([(0,6.36),(2.15,5.24),(2.15,6.44),(0,6.44)]),
         (W,11.45),(W,13.60),0.,.20,WALL,'south gable exposed side below verge')
    for y in (.02,13.59):
        a,c=((0,y),(0,y-1)) if y>6 else ((0,y+.59),(0,y))
        for i in range(74):
            z=.012+.087*i;span=.28 if i%2 else .13
            if y<6:r=box(.59-span,z,.59,z+.073)
            else:r=box(0,z,span,z+.073)
            wall(b,r,a,c,-.012,.009,BRICK,'east return staggered quoin')
    # Red brick shows through the render at the west wing end and at the
    # stepped corner just east of the central balcony in the 2024 garden view.
    for x,high in [(15.13,5.51),(6.66,6.40)]:
        a,c=(x,13.60),(x-1.,13.60)
        for i in range(int(high/.087)):
            z=.015+i*.087;width=.265 if i%2 else .124
            wall(b,box(0,z,width,z+.075),a,c,-.022,.012,BRICK,'garden staggered brick quoin')
    pipe(b,7.98,1.54,-.10,6.89,'street downpipe with offset head',lod)
    # Small balcony on the west of the curved garden projection as seen behind the open gate.
    a,c=(15.13,13.60),(12.44,13.60)
    openings=[(box(1.00,2.98,2.55,4.58),2,2,'upper double casement')]
    pierced_face(b,a,c,5.31,openings,'garden west end')
    left,right=12.22,14.03
    slab(b,box(left,13.58,right,14.03),2.69,2.90,STONE,'short garden balcony')
    for p,q in [((left,13.60),(left,14.01)),((left,14.01),(right,14.01)),((right,14.01),(right,13.60))]:
        span=hypot(q[0]-p[0],q[1]-p[1])
        for z in (2.97,3.52,3.67):wall(b,box(0,z,span,z+.029),p,q,-.019,.019,IRON,'short garden rails')
        n=max(2,round(span/.106))
        for i in range(n+1):
            s=span*i/n
            wall(b,box(s-.012,2.92,s+.012,3.70),p,q,-.016,.018,IRON,'short garden baluster')
