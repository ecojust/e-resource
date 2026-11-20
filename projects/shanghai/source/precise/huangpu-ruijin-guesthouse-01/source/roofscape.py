"""Hipped red roofs, rows of tile, squat dormers and tall stacked brick chimneys."""
from math import hypot
import numpy as np
from photo_architecture import Facade, opening
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOF='burnt clay tile'
RIDGE='red ridge capping'
STONE='grey dressed stone'
WINDOW='ivory joinery'
GLASS='residence glazing'
BRICK='garden brick'
FRIEZE='dark timber eaves'


def plate(b, pts, mat, label, thickness=.13):
    pts=[tuple(q)for q in pts]
    n=len(pts); verts=pts+[(x,y,z-thickness)for x,y,z in pts]
    faces=[(0,i,i+1)for i in range(1,n-1)]
    faces.extend((n,n+i+1,n+i)for i in range(1,n-1))
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
    b.add(verts,faces,mat,label)


def hip(b,x0,x1,y0,y1,eave,rise,lod,label):
    """One closed roof per period mass; planes meet on the hipped ends."""
    x=(x0+x1)/2;y=(y0+y1)/2
    run=min(x1-x0,y1-y0)/2
    a=(x0,y0,eave);c=(x1,y1,eave);d=(x0,y1,eave);v=(x1,y0,eave)
    if x1-x0>=y1-y0:
        r=(x0+run,y,eave+rise);t=(x1-run,y,eave+rise)
        faces=[(a,v,t,r),(v,c,t),(c,d,r,t),(d,a,r)]
        diagonal=[(a,r),(d,r),(v,t),(c,t)]
    else:
        r=(x,y0+run,eave+rise);t=(x,y1-run,eave+rise)
        faces=[(a,v,r),(v,c,t,r),(c,d,t),(d,a,r,t)]
        diagonal=[(a,r),(v,r),(c,t),(d,t)]
    for face in faces:
        # A square hip terminates at a point.
        q=[pt for i,pt in enumerate(face) if i==0 or pt!=face[i-1]]
        if len(q)>2:plate(b,q,ROOF,label+'/tile slopes')
    for k,l in diagonal+[(r,t)]:
        if k!=l:b.tube([k,l],.065 if k!=r or l!=t else .09,RIDGE,6 if lod else 12,label+'/hip and ridge caps')
    n=max(3,round(run/(.54 if lod else .30)))
    for i in range(1,n):
        step=run*i/n;z=eave+rise*i/n+.012
        a0,a1=x0+step,x1-step; b0,b1=y0+step,y1-step
        for a,c in [((a0,b0,z),(a1,b0,z)),((a1,b0,z),(a1,b1,z)),((a1,b1,z),(a0,b1,z)),((a0,b1,z),(a0,b0,z))]:
            if hypot(c[0]-a[0],c[1]-a[1])>.03:
                b.tube([a,c],.024 if lod else .032,RIDGE,4 if lod else 6,label+'/overlapping tile rows')


def dormer(b,x,y,z,width,label,lod):
    f=Facade(b,(x-width/2,y),(x+width/2,y),label)
    height=1.05
    cut=opening(0,z+.13,width-.28,.74)
    f.wall(z,z+height,[cut],.22,STONE)
    f.prism(cut.buffer(.01,join_style=2),-.24,-.22,GLASS,'dormer glazing')
    bars=[box(-.028,z,.028,z+height),box(-width/2,z+.48,width/2,z+.52)]
    inside=cut.buffer(-.062,join_style=2).difference(unary_union(bars))
    f.prism(cut.buffer(-.012,join_style=2).difference(inside),-.20,-.12,WINDOW,'dormer sash')
    f.box(0,z+.09,width-.12,.09,.18,0,STONE,'dormer sill')
    for sign in [-1,1]:
        end=Polygon([(x+sign*width/2-.06,y),(x+sign*width/2+.06,y),
                     (x+sign*width/2+.06,y+1.22),(x+sign*width/2-.06,y+1.22)])
        b.plan_prism(end,z,z+.99,FRIEZE,label+'/side cheeks')
    plate(b,[(x-width/2-.10,y-.11,z+height),(x+width/2+.10,y-.11,z+height),
             (x+width/2+.10,y+1.32,z+height+.26),(x-width/2-.10,y+1.32,z+height+.26)],
          ROOF,label+'/sloping tiled dormer cap')


def chimney(b,x,y,base,top,width,lod,label):
    b.box((x,y,(base+top)/2),(width,.74,top-base),BRICK,label=label+'/shaft')
    for thickness,z,ext in [(.15,top-.42,.08),(.20,top-.21,.15),(.13,top-.035,.20)]:
        b.box((x,y,z),(width+ext,.74+ext,thickness),FRIEZE if z>top-.10 else BRICK,label=label+'/stepped cap')
    for sign in [-1,1]:
        b.box((x+sign*width*.25,y,top+.043),(width*.31,.44,.035),'chimney shadow',label=label+'/flue')
    if not lod:
        for k in range(max(0,round((top-base-.4)/.24))):
            z=base+.15+k*.24
            b.box((x,y-.371,z),(width,.014,.016),'brick joint',label=label+'/shaft courses')


def add_roofs(b,lod):
    # The rear roof planes are massed from the aerial footprint. The named
    # period details belong only to the separately photographed courtyard side.
    hip(b,-16.16,13.88,4.9,20.78,8.03,3.23,lod,'Main block/rear roof')
    hip(b,-16.38,-5.05,-.34,9.22,8.60,2.90,lod,'East end/courtyard pavilion')
    hip(b,-5.47,4.60,.02,9.68,8.14,2.79,lod,'Entrance/recessed roof')
    hip(b,3.87,14.07,-.27,9.87,8.52,2.92,lod,'West end/courtyard pavilion')
    for x,y,z,w,name in [(-.84,1.65,9.10,1.24,'Entrance/shed dormer'),
                         (6.60,1.63,9.58,1.42,'West end/shed dormer')]:
        dormer(b,x,y,z,w,name,lod)
    for x,y,base,top,width,name in [(-13.82,2.46,9.45,12.92,1.10,'East end/tall chimney'),
                                    (-2.01,6.82,10.03,12.00,.76,'Entrance/back chimney'),
                                    (4.98,7.71,10.08,12.15,.75,'West end/back chimney'),
                                    (11.52,3.47,9.78,12.92,1.02,'West end/tall chimney')]:
        chimney(b,x,y,base,top,width,lod,name)
