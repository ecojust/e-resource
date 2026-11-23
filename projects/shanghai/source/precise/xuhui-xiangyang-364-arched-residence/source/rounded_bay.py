"""Two steel windows cut into the circular street corner visible from the south in 2020."""
from math import ceil,cos,radians,sin
from shapely.geometry import Polygon
from materials import CEMENT,FRAME,GLASS,PLASTER,SHADOW

def add_round_windows(front,center,radius,eave,lod=False):
    def strip(start,end,inner,outer,z0,z1,mat,label):
        steps=max(1,ceil((end-start)/(7.5 if lod else 2.8)))
        angles=[radians(start+(end-start)*i/steps) for i in range(steps+1)]
        def points(delta):
            return [(center-(radius+delta)*sin(a),radius-(radius+delta)*cos(a)) for a in angles]
        plan=Polygon(points(outer)+points(inner)[::-1])
        front.b.prism(plan,z0,z1,lambda u,d,z:front.point(u,d,z),mat,front.label+' | south rounded bay | '+label)
    windows=[(45.0,89.0,4.09,5.80,'lower'),(41.0,88.5,7.36,9.19,'upper')]
    bottom=0.
    for a,b,sill,head,name in windows:
        strip(0,90,-.25,0,bottom,sill,PLASTER,'curved masonry below '+name+' sash')
        for start,end in [(0,a),(b,90)]:
            strip(start,end,-.25,0,sill,head,PLASTER,name+' opening side')
        for start,end in [(a,a+1.45),(b-1.45,b)]:
            strip(start,end,-.22,.004,sill,head,SHADOW,name+' radial jamb and reveal')
        strip(a,b,-.216,-.202,sill,head,GLASS,name+' curved glass')
        for lo,hi in [(sill,sill+.047),(head-.047,head)]:
            strip(a,b,-.20,-.137,lo,hi,FRAME,name+' casement rail')
        for angle in [a+.72,(a+b)/2,b-.72]:
            strip(angle-.70,angle+.70,-.199,-.135,sill+.036,head-.036,FRAME,name+' casement upright')
        for z in [sill+(head-sill)*v for v in (.38,.74)]:
            strip(a+.7,b-.7,-.198,-.134,z-.018,z+.018,FRAME,name+' intermediate steel rail')
        for start,end in [(a-1.8,a),(b,min(90,b+1.5))]:
            strip(start,end,.002,.058,sill-.095,head+.056,CEMENT,name+' curved cement margin')
        strip(a-1.8,min(90,b+1.5),.002,.055,head,head+.067,CEMENT,name+' rendered head')
        strip(a-2.4,90,.002,.105,sill-.103,sill,CEMENT,name+' curved sill')
        bottom=head
    strip(0,90,-.25,0,bottom,eave,PLASTER,'curve up to dentilled roof')
