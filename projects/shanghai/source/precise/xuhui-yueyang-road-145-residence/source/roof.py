"""Visible surfaces of the interlocking hipped roof and its two projecting gables."""
import math
import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon
from shapely.ops import unary_union
from photo_architecture import pieces

TILE = 'burnt red ceramic'
LIGHT_TILE = 'sunlit fish scale tile'
DARK_TILE = 'weathered fish scale tile'
EDGE = 'dark red gutter'
Z_EAVE = 8.40
Z_BREAK = 11.64
Z_RIDGE = 13.38
GABLES = [-4.35, 5.65]
# Horizontal setback and rise at the raised foot, curved skirt and upper fold.
FOLDS = [(0, Z_EAVE), (.22,8.46), (.45,8.70), (.67,9.12), (.91,9.90), (1.24,Z_BREAK)]

def ring(x0,x1,y0,y1,z):
    return [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]

def band(lower,upper):
    return [[lower[k],lower[(k+1)%4],upper[(k+1)%4],upper[k]] for k in range(4)]

def roof_parts():
    # The main rectangle is hip-ended. The gable front planes do not retreat
    # with height. Their upper hipped caps and side skirts merge into the main bar.
    surfaces=[]
    for x0,x1,y0,y1,is_gable in [(-10.85,10.85,3.45,12.30,False),
                                    *((c-3.20,c+3.20,1.58,8.92,True) for c in GABLES)]:
        previous=None
        for t,z in FOLDS:
            row=ring(x0+t,x1-t,y0 if is_gable else y0+t,y1-t,z)
            if previous is not None:
                surfaces.extend((v,True) for i,v in enumerate(band(previous,row)) if i!=0 or not is_gable)
            previous=row
        cx=(x0+x1)/2
        if is_gable:
            top=ring(cx-.009,cx+.009,y0+1.70,y1-2.55,12.82)
        else:
            top=ring(x0+5.10,x1-5.10,(y0+y1)/2-.010,(y0+y1)/2+.010,Z_RIDGE)
        surfaces.extend((v,False) for v in band(previous,top))
        surfaces.append((top,False))
    return surfaces

def higher_clip(a,b,c,bounds):
    x0,y0,x1,y1=bounds
    pts=[(x0-.1,y0-.1),(x1+.1,y0-.1),(x1+.1,y1+.1),(x0-.1,y1+.1)]
    result=[]
    for p,q in zip(pts,pts[1:]+pts[:1]):
        f=a*p[0]+b*p[1]+c;g=a*q[0]+b*q[1]+c
        if f>=0:result.append(p)
        if (f>0)!=(g>0):
            t=f/(f-g);result.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    return Polygon(result) if len(result)>2 else Polygon()

def painted_roof(builder,lod):
    rows=[]
    for quad,skirt in roof_parts():
        points=np.array(quad); poly=Polygon(points[:,:2])
        if poly.area<1e-7: continue
        abc=np.linalg.lstsq(np.column_stack([points[:,:2],np.ones(len(points))]),points[:,2],rcond=None)[0]
        rows.append((poly,abc,skirt))
    for idx,(poly,abc,skirt) in enumerate(rows):
        masks=[]
        for j,(p2,coef,_) in enumerate(rows):
            if j==idx or not p2.intersects(poly):continue
            common=poly.intersection(p2)
            if common.area<1e-7:continue
            delta=coef-abc
            if np.max(np.abs(delta))<1e-7:
                if j<idx:masks.append(common)
            else:masks.append(common.intersection(higher_clip(*delta,common.bounds)))
        visible=poly.difference(unary_union(masks)) if masks else poly
        a,b,c=abc
        for panel in pieces(visible):
            if panel.area<1e-7:continue
            def xyz(x,y,offset=0):return (x,y,a*x+b*y+c+offset)
            verts=[];faces=[]
            for tri in constrained_delaunay_triangles(panel).geoms:
                pts=list(tri.exterior.coords)[:3]
                if (pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1]) < (pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0]):pts.reverse()
                k=len(verts);verts.extend(xyz(*pt)for pt in pts);faces.append((k,k+1,k+2))
            if faces:builder.add(verts,faces,TILE,'intersecting red roof planes')
            if panel.area<.36:continue
            patterned_tiles(builder,panel,abc,lod,skirt)

def patterned_tiles(builder,panel,abc,lod,skirt):
    """Lay alternate rounded tile ends in the local slope plane, clipped to valleys."""
    a,b,c=abc;grade=math.hypot(a,b)
    if grade<.16:return
    vx,vy=a/grade,b/grade;ux,uy=vy,-vx
    stretch=math.sqrt(1+grade**2)
    def uv(x,y):return(x*ux+y*uy,(x*vx+y*vy)*stretch)
    def xyz(u,v):
        x=u*ux+v*vx/stretch;y=u*uy+v*vy/stretch
        return(x,y,a*x+b*y+c+.019)
    region=Polygon([uv(x,y)for x,y in panel.exterior.coords],[[uv(x,y)for x,y in r.coords]for r in panel.interiors])
    u0,v0,u1,v1=region.bounds;step=.36 if lod else .255;rise=.24 if lod else .18
    trays=[([],[]),([],[])]
    for j in range(math.floor(v0/rise)-1,math.ceil(v1/rise)+1):
        v=j*rise;shift=(j%2)*step/2
        for k in range(math.floor((u0-shift)/step)-1,math.ceil((u1-shift)/step)+1):
            u=k*step+shift;h=step*.477
            outline=[(u-h,v+rise*.80),(u-h,v+rise*.36),(u-h*.65,v+rise*.09),(u,v),(u+h*.65,v+rise*.09),(u+h,v+rise*.36),(u+h,v+rise*.80)]
            if not skirt:
                outline=[(u-h,v+.025),(u+h,v+.025),(u+h,v+rise*.94),(u-h,v+rise*.94)]
            tile=Polygon(outline)
            if not tile.intersects(region):continue
            material=(3*k+7*j)%11 in (0,1,3)
            vertices,faces=trays[int(material)]
            for fragment in pieces(tile.intersection(region)):
                for tri in constrained_delaunay_triangles(fragment).geoms:
                    pts=list(tri.exterior.coords)[:3]
                    # Local u,v form a right-handed pair on the roof plane.
                    if (pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1]) < (pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0]):pts.reverse()
                    i=len(vertices);vertices.extend(xyz(*p)for p in pts);faces.append((i,i+1,i+2))
    for (vertices,faces),name in zip(trays,[LIGHT_TILE,DARK_TILE]):
        if faces:builder.add(vertices,faces,name,'overlapping fish scale tile courses' if skirt else 'upper clay tile courses')
