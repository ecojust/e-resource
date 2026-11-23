"""A hipped main roof with an eastern cross-gable, closed at the roof soffit."""
import math
from itertools import combinations
from shapely.geometry import Polygon,LineString
from shapely.ops import split
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient

def add_roof(b,lod,mat,stone,brick):
    L,R=-13.86,3.93
    plane=Polygon([(L,.33),(-3.93,.33),(-3.93,-.37),(R,-.37),(R,8.05),(L,8.05)])
    hip=[(.84,0,10.67-.84*L),(-.84,0,10.67+.84*R),(0,.84,10.67-.84*.33),(0,-.84,10.67+.84*8.05)]
    gable=[(1.02,0,14.69),(-1.02,0,14.69),(0,-1.02,10.67+1.02*8.05)]
    def roof(x,y):return max(min(a*x+c*y+e for a,c,e in hip),min(a*x+c*y+e for a,c,e in gable))
    cells=[plane]
    for a,c in combinations(hip+gable,2):
        dx,dy,k=[s-t for s,t in zip(a,c)];norm=math.hypot(dx,dy)
        if norm<1e-12:continue
        x,y=-k*dx/norm**2,-k*dy/norm**2
        line=LineString([(x-100*dy/norm,y+100*dx/norm),(x+100*dy/norm,y-100*dx/norm)])
        cells=[piece for cell in cells for piece in split(cell,line).geoms if piece.area>1e-7]
    vertices=[];indices={};faces=[];edge={}
    def idx(x,y,side):
        key=(round(x,6),round(y,6),side)
        if key not in indices:
            indices[key]=len(vertices);vertices.append((key[0],key[1],roof(*key[:2])-(.158 if side==0 else 0)))
        return indices[key]
    for cell in cells:
        for tri in constrained_delaunay_triangles(cell).geoms:
            pts=list(orient(tri,sign=1).exterior.coords)[:3]
            top=[idx(*p,1)for p in pts];base=[idx(*p,0)for p in pts]
            if len(set(top))!=3:continue
            faces.extend([top,base[::-1]])
            for j in range(3):
                ed=(top[j],top[(j+1)%3])
                if ed[::-1]in edge:del edge[ed[::-1]]
                else:edge[ed]=(base[j],base[(j+1)%3])
    for (a,c),(aa,cc)in edge.items():faces.append((a,aa,cc,c))
    b.add(vertices,faces,mat,'roof/double-pitched end meeting four hipped slopes with underside')
    def beam(x0,y0,x1,y1,r,name,m=mat):
        b.tube([(x0,y0,roof(x0,y0)+r*.22),(x1,y1,roof(x1,y1)+r*.22)],r,m,7 if lod else 12,name)
    beam(0,-.37,0,3.91,.077,'gable main ridge/capped clay rolls')
    beam(-9.94,4.19,-3.14,4.19,.085,'west high ridge/capped clay rolls')
    for j,(x,y,z,w) in enumerate([(L,.33,-9.94,4.19),(L,8.05,-9.94,4.19)]):
        beam(x,y,z,w,.073,'hip/diagonal clay roll '+str(j+1))
    for side in [-1,1]:
        beam(side*3.92,-.365,0,-.365,.077,'gable/edge tile '+str(side))
        b.tube([(side*3.87,-.39,10.59),(side*2.23,-.39,12.28),(0,-.39,14.56)],.060,stone,6 if lod else 10,'gable/painted raking verge '+str(side))
    # Roof-cover rolls run down each plane. Place their ends on the local roof function.
    for i in range(4 if lod else 14):
        y=.12+i*(2.85/(3 if lod else 13))
        for side in [-1,1]:beam(side*.10,y,side*3.63,y,.021,'gable/tile pitch row '+str((side,i)))
    for i in range(10 if lod else 33):
        x=-9.85+i*(5.77/(9 if lod else 32));beam(x,.39,x,4.10,.024,'gallery/tile pitch row '+str(i+1))
    # The 2007 vignette records a tall red brick stack with a stepped ledge and two crown recesses.
    cx,cy=-2.84,2.55;bottom=roof(cx,cy)-.08
    for name,z0,z1,w,d in [('shoe',bottom,bottom+.24,1.02,.70),('shaft',bottom+.24,14.79,.77,.49),('upper shoulder',14.79,14.9,.87,.60)]:
        b.box((cx,cy,(z0+z1)/2),(w,d,z1-z0),brick,label='chimney/'+name)
    b.box((cx,cy,14.95),(.81,.53,.10),brick,label='chimney/top masonry band')
    for x in [cx-.20,cx+.20]:
        b.box((x,cy,15.014),(.237,.244,.029),'dark iron',label='chimney/dark flue mouth '+str(x))
