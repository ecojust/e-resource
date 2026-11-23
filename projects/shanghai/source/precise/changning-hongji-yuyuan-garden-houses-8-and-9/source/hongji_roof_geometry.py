"""Upper envelopes of separately surveyed gables, with closed lapped tile courses."""
from math import ceil, cos, hypot, pi, sin, sqrt
from pathlib import Path

import numpy as np
from shapely import set_precision
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from garden_fabric import BRICK, RENDER as PEBBLE, PALETTE as FACADE_FINISHES

TILE8='Hongji 8 | fired pantile'
TILE9='Hongji 9 | dark red fired pantile'
VERGE='Hongji roofs | slate grey bargeboard'
EAVE='Hongji roofs | eave gutter'
SOFFIT='Hongji roofs | pale painted soffit'
CAP='Hongji roofs | half-round clay ridge tile'
FLASH='Hongji roofs | folded valley flashing'
STONE='Hongji roofs | buff cement cap'
PALETTE={
    TILE8:{'color':[1,1,1],'roughness':.89,'texture':str(Path(__file__).with_name('hongji-8-red-tile.png'))},
    TILE9:{'color':[1,1,1],'roughness':.91,'texture':str(Path(__file__).with_name('hongji-9-red-tile.png'))},
    VERGE:{'color':[.125,.152,.174],'roughness':.78},
    EAVE:{'color':[.074,.091,.093],'roughness':.63},
    SOFFIT:{'color':[.57,.54,.43],'roughness':.91},
    CAP:{'color':[.32,.117,.07],'roughness':.89},
    FLASH:{'color':[.147,.133,.107],'roughness':.64},
    BRICK:FACADE_FINISHES[BRICK],
    STONE:{'color':[.60,.565,.495],'roughness':.89},
    PEBBLE:FACADE_FINISHES[PEBBLE],
}


def make_textures():
    """Original periodic four-column, four-course tile drawings from relief and firing variation."""
    from PIL import Image
    for house,base in [(8,(163,92,64)),(9,(142,74,54))]:
        size=192
        a=np.zeros((size,size,3),dtype=np.uint8)
        for v in range(size):
            row=int(v/48); t=(v%48)/48
            for u in range(size):
                c=(u/48+(row%2)*.12)%4
                angle=2*pi*(c%1)
                wave=7*cos(angle)+2*cos(2*angle)
                colour=5.8*sin(2*pi*(int(c)+2*row+house)/4)+3.5*cos(2*pi*(int(c)-row)/4)
                lip=-26 if t>.95 else 8 if t<.063 else 0
                grain=2*sin(2*pi*(u*11+v*7)/size)+1.6*cos(2*pi*(u*3-v*13)/size)
                a[v,u]=np.clip(np.array(base)+(colour+wave+lip+grain)*np.array([1,.77,.55]),0,255)
        Image.fromarray(a).save(Path(__file__).with_name('hongji-%s-red-tile.png'%house),optimize=True)


def triangular(zone,axis,span,run,eave,crest):
    """Two roof planes rising to a ridge along the perpendicular coordinate."""
    lo,mid,hi=span
    edges=[lo,mid,hi];levels=[eave,crest,eave];faces=[]
    for k in range(2):
        a,c=edges[k:k+2];s=(levels[k+1]-levels[k])/(c-a)
        p=(s,0.,levels[k]-s*a) if axis=='x' else (0.,s,levels[k]-s*a)
        footprint=box(a,run[0],c,run[1]) if axis=='x' else box(run[0],a,run[1],c)
        faces.append((zone,footprint,p))
    return faces


def halfplane(a,b,c):
    corners=[(-300.,-300.),(300.,-300.),(300.,300.),(-300.,300.)];verts=[]
    for p,q in zip(corners,corners[1:]+corners[:1]):
        z=a*p[0]+b*p[1]+c;zp=a*q[0]+b*q[1]+c
        if z>=0:verts.append(p)
        if (z>=0)!=(zp>=0):
            t=z/(z-zp);verts.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    return Polygon(verts) if len(verts)>2 else Polygon()


def roof_envelope(facets):
    result=[]
    for i,(label,shape,plane) in enumerate(facets):
        above=[]
        for j,(_,other,p) in enumerate(facets):
            if i==j or not shape.intersects(other):continue
            a,b,c=(p[k]-plane[k] for k in range(3))
            if abs(a)+abs(b)<1e-9:
                if c>1.e-9 or (abs(c)<=1.e-9 and j<i):above.append(other)
            else:above.append(other.intersection(halfplane(a,b,c)))
        visible=shape.difference(unary_union(above)) if above else shape
        for face in pieces(visible):
            if face.area>.002:result.append((label,face,plane))
    return result


def pieces(shape):
    if shape.is_empty:return []
    if shape.geom_type=='Polygon':return [shape]
    return [p for s in getattr(shape,'geoms',[]) for p in pieces(s)]


def height(planes,x,y):
    z=[a*x+b*y+c for _,poly,(a,b,c) in planes if poly.buffer(1e-6).covers(Point(x,y))]
    return max(z) if z else None


def textured_vertices(part,gradient):
    a,c=gradient;length=hypot(a,c);across=np.array([-c,a])/length
    uphill=np.array([a,c])/length;stretch=sqrt(1+length*length)
    xyz=np.asarray(part['vertices']);tri=np.asarray(part['triangles']);new=[];faces=[];uv=[]
    for face in tri:
        row=xyz[face];normal=np.cross(row[1]-row[0],row[2]-row[0]);k=len(new)
        if abs(normal[2])>.35*np.linalg.norm(normal):
            coords=np.stack((row[:,:2]@across/1.0,row[:,:2]@uphill*stretch/1.16),axis=1)
        else:
            longest=max(range(3),key=lambda j:np.linalg.norm(row[(j+1)%3,:2]-row[j,:2]))
            direction=row[(longest+1)%3,:2]-row[longest,:2];direction/=np.linalg.norm(direction)
            coords=np.stack((row[:,:2]@direction,row[:,2]/1.16),axis=1)
        new.extend(row.tolist());uv.extend(coords.tolist());faces.append((k,k+1,k+2))
    part.update(vertices=new,triangles=faces,texcoords=uv)


def surface(b,face,plane,tile,name,lod):
    a,c,k=plane;axis=0 if abs(a)>=abs(c) else 1;lo,hi=face.bounds[axis],face.bounds[axis+2]
    pitch=abs(plane[axis]);spacing=(.91 if lod else .29)/sqrt(1+pitch*pitch)
    count=max(1,ceil((hi-lo)/spacing))
    for i in range(count):
        lower=lo+i*(hi-lo)/count;upper=lo+(i+1)*(hi-lo)/count
        band=halfplane(1. if axis==0 else 0.,1. if axis==1 else 0.,-lower)
        band=band.intersection(halfplane(-1. if axis==0 else 0.,-1. if axis==1 else 0.,upper))
        for part in pieces(set_precision(face.intersection(band),1.e-6)):
            if part.area<.001:continue
            ramp=(.007 if plane[axis]>0 else -.007)/(upper-lower)
            shift=upper if ramp>0 else lower
            def mapper(x,y,d):
                # The toe of this individual tile course overlaps the one below.
                z=a*x+c*y+k+d+ramp*(shift-(x if axis==0 else y))
                return x,y,z
            b.prism(part,-.079,0.,mapper,tile,name)
            textured_vertices(b.parts[-1],(a,c))


def strips_and_caps(b,finished,house,lod,wall_plan):
    tile=TILE8 if house==8 else TILE9
    for zone,face,plane in finished:surface(b,face,plane,tile,f'{house} | {zone} tile course',lod)
    outline=unary_union([f for _,f,_ in finished])
    # Tile is visible above the roofs. Beneath the eaves, pale boarding runs
    # from each true wall face to the rake or gutter around the projection.
    inset=wall_plan.buffer(-.018,join_style=2)
    for zone,face,(a,c,k) in finished:
        mapper=lambda x,y,d:(x,y,a*x+c*y+k+d)
        for underside in pieces(set_precision(face.difference(inset),1.e-6)):
            if underside.area>.001:
                b.prism(underside,-.162,-.077,mapper,SOFFIT,f'{house} | {zone} soffit')
        boundary=face.boundary.intersection(outline.boundary)
        for line in getattr(boundary,'geoms',[boundary]):
            if line.geom_type!='LineString' or line.length<.10:continue
            pts=list(line.coords)
            for pt,qt in zip(pts,pts[1:]):
                length=hypot(qt[0]-pt[0],qt[1]-pt[1])
                if length<.10:continue
                normal=np.array([-(qt[1]-pt[1]),qt[0]-pt[0]])/length
                mid=(np.asarray(pt)+qt)/2
                if outline.contains(Point(*(mid+.025*normal))):normal=-normal
                # A narrow closed verge follows the exact raking edge; the
                # flat return at an eave incorporates a rounded external gutter.
                gradient=abs((qt[0]-pt[0])*a+(qt[1]-pt[1])*c)/length
                lip=Polygon([tuple(np.asarray(pt)+normal*.026),tuple(np.asarray(qt)+normal*.026),
                             tuple(np.asarray(qt)-normal*.037),tuple(np.asarray(pt)-normal*.037)])
                b.prism(lip,-.153,.021,lambda x,y,d:(x,y,a*x+c*y+k+d),VERGE,f'{house} | {zone} verge')
                if gradient<.09:
                    b.tube([(x+normal[0]*.045,y+normal[1]*.045,a*x+c*y+k-.114)for x,y in (pt,qt)],.048,EAVE,7 if lod else 11,f'{house} | {zone} gutter')
    for i,(_,face,p) in enumerate(finished):
        for _,other,q in finished[i+1:]:
            common=face.boundary.intersection(other.boundary)
            for line in getattr(common,'geoms',[common]):
                if line.geom_type!='LineString' or line.length<.22:continue
                coords=list(line.coords)
                for v,w in zip(coords,coords[1:]):
                    if hypot(w[0]-v[0],w[1]-v[1])<.2:continue
                    mid=(np.asarray(v)+w)/2
                    zp=p[0]*mid[0]+p[1]*mid[1]+p[2];zq=q[0]*mid[0]+q[1]*mid[1]+q[2]
                    if abs(zp-zq)>.03:continue
                    other_pt=other.representative_point()
                    d=(other_pt.x-mid[0],other_pt.y-mid[1])
                    ridge=(p[0]-q[0])*d[0]+(p[1]-q[1])*d[1]>0
                    material=CAP if ridge else FLASH
                    radius=.066 if ridge else .032
                    b.tube([(x,y,p[0]*x+p[1]*y+p[2]+(.022 if ridge else .009))for x,y in(v,w)],radius,material,8 if lod else 12,f'{house} | '+('clay ridge' if ridge else 'valley flashing'))


def stack_box(b,xy,size,z0,z1,mat,name):
    b.box((xy[0],xy[1],(z0+z1)/2),(size[0],size[1],z1-z0),mat,label=name)


if __name__=='__main__':make_textures()
