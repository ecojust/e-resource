"""Cantilevered service balcony on the separately photographed courtyard elevation."""
from shapely.geometry import Polygon
from hospital_walls import STONE,LIGHT,SHADE,IRON

def add_balcony(b,lod=False,layout=None):
    d=layout['depth'];near,far=29.56,39.25
    y0=d-.035;y1=d+2.20;z=18.41
    def block(x0,x1,a,h,lo,hi,mat,label):
        b.box(((x0+x1)/2,(a+h)/2,(lo+hi)/2),(x1-x0,h-a,hi-lo),mat,label=label)
    block(near,far,y0,y1,z-.27,z-.044,STONE,'Court cantilever slab')
    block(near-.045,far+.045,y0,y1+.045,z-.06,z+.018,LIGHT,'Court balcony edge and deck')
    # Four distinct tapered supports are visible along the underside in the April 2020 photograph.
    for i,x in enumerate([30.00,32.75,35.45,38.40]):
        profile=Polygon([(d-.015,z-.25),(y1-.16,z-.25),(y1-.16,z-.37),(d+.45,z-.55),(d+.06,z-.72),(d-.015,z-.72)])
        b.prism(profile,x-.088,x+.088,lambda y,h,t:(t,y,h),SHADE,'Court balcony soffit bracket '+str(i+1))
    ends=[((near,d+.036),(near,y1-.075),2),((near,y1-.075),(far,y1-.075),10),
          ((far,y1-.075),(far,d+.036),2)]
    for side,(start,end,n)in enumerate(ends):
        def p(f,height):
            return (start[0]+(end[0]-start[0])*f,start[1]+(end[1]-start[1])*f,z+height)
        for h,r in [(1.06,.037),(.96,.021),(.125,.021)]:
            b.tube([p(0,h),p(1,h)],r,IRON,6 if lod else 12,'Court horizontal rail '+str(side))
        for i in range(n+1):
            if (side==1 and i==0)or(side==2 and i==0):continue
            b.tube([p(i/n,.015),p(i/n,1.077)],.025,IRON,6 if lod else 10,'Court upright '+str(side))
        for i in range(n):
            b.tube([p(i/n,.16),p((i+.48)/n,.935)],.013,IRON,5 if lod else 8,'Court ascending iron diagonals')
            b.tube([p((i+.48)/n,.935),p((i+1)/n,.16)],.013,IRON,5 if lod else 8,'Court descending iron diagonals')
