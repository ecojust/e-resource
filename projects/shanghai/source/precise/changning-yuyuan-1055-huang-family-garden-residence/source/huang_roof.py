"""Tiled hips, two seated dormers and a shallow rooflight on the garden house."""
from math import ceil, hypot, sqrt
from pathlib import Path

import numpy as np
from shapely import set_precision
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from house_fabric import STUCCO

TILE = 'Huang garden | weathered red clay pantiles'
RIDGE = 'Huang garden | ridge caps'
GUTTER = 'Huang garden | pale grey rolled gutter'
BROWN = 'Huang garden | oxblood sheet flashing'
BOARD = 'Huang garden | eave boarding'
FRAME = 'Huang garden | dormer casement'
GLASS = 'Huang garden | pale old roof glazing'
PALETTE = {
    TILE: {'color':[1,1,1], 'roughness':.90, 'texture':str(Path(__file__).with_name('huang-roof-tiles.png'))},
    RIDGE: {'color':[.309,.179,.142], 'roughness':.85},
    GUTTER:{'color':[.52,.52,.49], 'roughness':.7},
    BROWN: {'color':[.264,.071,.05], 'roughness':.76},
    BOARD: {'color':[.145,.102,.080], 'roughness':.82},
    FRAME: {'color':[.119,.143,.142], 'roughness':.75},
    GLASS: {'color':[.31,.43,.47], 'roughness':.33},
}

def polygons(shape):
    if shape.is_empty: return []
    if shape.geom_type == 'Polygon':
        return [shape] if shape.area > .0001 else []
    return [p for part in getattr(shape, 'geoms', []) for p in polygons(part)]

def half_plane(a,b,c):
    square=[(-100.,-100.), (100.,-100.), (100.,100.), (-100.,100.)]
    vertices=[]
    for p,q in zip(square,square[1:]+square[:1]):
        h=a*p[0]+b*p[1]+c
        k=a*q[0]+b*q[1]+c
        if h>=0: vertices.append(p)
        if (h>=0)!=(k>=0):
            t=h/(h-k)
            vertices.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    return Polygon(vertices) if len(vertices)>=3 else Polygon()

def hip(name, ring, eave, pitch):
    face=Polygon(ring)
    corners=list(face.exterior.coords)[:-1]
    if not face.exterior.is_ccw: corners.reverse()
    grades=[]
    for (x,y),(xx,yy) in zip(corners,corners[1:]+corners[:1]):
        length=hypot(xx-x,yy-y)
        a,b=-pitch*(yy-y)/length,pitch*(xx-x)/length
        grades.append((a,b,eave-a*x-b*y))
    result=[]
    for i,p in enumerate(grades):
        part=face
        for j,q in enumerate(grades):
            if i!=j:
                part=part.intersection(half_plane(*(np.asarray(q)-p)))
        for f in polygons(set_precision(part,1e-6)):
            result.append((name,f,p))
    return result

def envelope(facets):
    result=[]
    for i,(name,poly,plane) in enumerate(facets):
        hidden=[]
        for j,(_,other,q) in enumerate(facets):
            if i==j or not poly.intersects(other): continue
            a,b,c=np.asarray(q)-plane
            if abs(a)+abs(b)<1e-9:
                if c>1e-9 or (abs(c)<=1e-9 and j<i): hidden.append(other)
            else:
                hidden.append(other.intersection(half_plane(a,b,c)))
        visible=poly.difference(unary_union(hidden)) if hidden else poly
        for face in polygons(set_precision(visible,1e-6)):
            result.append((name,face,plane))
    return result

def components(layout):
    scale=layout['reference_south_edge_m']/13.5
    eave=layout['z_eave']
    footprint=Polygon(layout['roof_footprint']).buffer(.30*scale,join_style=2)
    terrace=layout.get('terrace_rectangle')
    if isinstance(terrace,(tuple,list)):
        x0,y0,x1,y1=terrace
        cut=box(x0,y0-.8*scale,x1+.8*scale,y1)
    else:
        cut=box(5.42*scale,-.5*scale,11.2*scale,3.6*scale)
    footprint=footprint.difference(cut)
    wings=[
        ('court bay',[(-.72,-.05),(10.82,-.05),(10.82,12.58),(-.72,12.58)],.82),
        ('east return',[(-.72,-.05),(8.59,-.05),(8.59,12.58),(7.93,20.23),(-.72,20.23)],.82),
        ('north body',[(-4.48,10.69),(8.59,10.69),(7.93,20.23),(-4.48,20.23)],.73),
        ('north end',[(-4.48,10.69),(.95,10.69),(.95,22.15),(-4.48,22.15)],.73)]
    facets=[]
    for name,ring,pitch in wings:
        for label,face,grade in hip(name,[(scale*x,scale*y) for x,y in ring],eave,pitch):
            for piece in polygons(set_precision(face.intersection(footprint),1e-6)):
                facets.append((label,piece,grade))
    return envelope(facets)

def surface_z(planes,x,y):
    return max(a*x+b*y+c for _,face,(a,b,c) in planes if face.buffer(1e-5).covers(Point(x,y)))

def dormers(layout):
    scale=layout['reference_south_edge_m']/13.5
    rows=[('court dormer',9.80,8.34,1.74,1.96,1.13,.99,1.04),
          ('return dormer',7.52,12.24,1.60,1.79,1.04,1.07,1.05)]
    return [dict(name=n,x=x*scale,y=y*scale,width=w*scale,depth=d*scale,opening=o*scale,sill=layout['z_eave']+r*scale,head=layout['z_eave']+(r+h)*scale) for n,x,y,w,d,o,r,h in rows]

def light_polygon(layout):
    s=layout['reference_south_edge_m']/13.5
    return box(6.11*s,13.83*s,7.24*s,14.99*s)

def tile_uv(part,gradient):
    a,b=gradient
    grade=hypot(a,b)
    across=np.array([-b,a])/grade
    rise=np.array([a,b])/grade
    vertices=np.asarray(part['vertices'])
    points=[]; triangles=[]; uv=[]
    for triangle in part['triangles']:
        row=vertices[list(triangle)]
        normal=np.cross(row[1]-row[0],row[2]-row[0])
        if abs(normal[2])>.30*np.linalg.norm(normal):
            axes=(row[:,:2]@across/.94,row[:,:2]@rise*sqrt(1+grade*grade)/1.08)
        else:
            index=max(range(3),key=lambda j:np.linalg.norm(row[(j+1)%3,:2]-row[j,:2]))
            direction=row[(index+1)%3,:2]-row[index,:2]
            direction=direction/np.linalg.norm(direction)
            axes=(row[:,:2]@direction/.94,row[:,2]/1.08)
        n=len(points)
        points.extend(row.tolist())
        triangles.append((n,n+1,n+2))
        uv.extend(np.column_stack(axes).tolist())
    part.update(vertices=points,triangles=triangles,texcoords=uv)

def planar_piece(b,polygon,plane,low,high,mat,name):
    a,c,h=plane
    for piece in polygons(set_precision(polygon,1e-6)):
        b.prism(piece,low,high,lambda x,y,d:(x,y,a*x+c*y+h+d),mat,name)
        if mat==TILE: tile_uv(b.parts[-1],(a,c))

def tile_surface(b,face,plane,lod,name):
    a,c,h=plane
    pitch=hypot(a,c)
    u,v=a/pitch,c/pitch
    points=[x*u+y*v for x,y in face.exterior.coords]
    lo,hi=min(points),max(points)
    count=max(1,ceil((hi-lo)*sqrt(1+pitch*pitch)/(.82 if lod else .27)))
    for i in range(count):
        left=lo+i*(hi-lo)/count
        right=lo+(i+1)*(hi-lo)/count
        strip=face.intersection(half_plane(u,v,-left)).intersection(half_plane(-u,-v,right))
        tongue=.007/max(right-left,.001)
        planar_piece(b,strip,(a-u*tongue,c-v*tongue,h+right*tongue),-.076,0,TILE,name+' tile courses')

def make_dormer(b,lod,planes,d):
    name=d['name']; x,y=d['x'],d['y']; xb=x-d['depth']
    width=d['width']; ow=d['opening']; sill,head=d['sill'],d['head']; cap=head+.23
    y0,y1=y-width/2,y+width/2
    left,right=y-ow/2,y+ow/2
    def front(yy,zz,dd): return x+dd,yy,zz
    def panel(shape,low,high,mat,label):
        b.prism(shape,low,high,front,mat,name+' | '+label)
    panel(box(y0,sill-.16,y1,cap).difference(box(left,sill,right,head)),-.115,0,STUCCO,'rendered front')
    panel(box(y0-.06,sill-.145,y1+.06,sill+.017),-.06,.042,BROWN,'sill flashing')
    for l,r in [(left+.02,y-.023),(y+.023,right-.02)]:
        panel(box(l,sill+.025,r,head-.026),-.073,-.057,GLASS,'glazing')
    for l,r in [(left-.012,left+.033),(y-.024,y+.024),(right-.033,right+.012)]:
        panel(box(l,sill,r,head),-.066,-.014,FRAME,'casement stiles')
    for z in [sill+.018,head-.018]:
        panel(box(left,z-.019,right,z+.019),-.064,-.015,FRAME,'casement rails')
    for yy in [y0,y1]:
        zf=surface_z(planes,x,yy); zb=surface_z(planes,xb,yy)
        cheek=Polygon([(x,zf-.09),(x,cap),(xb,cap),(xb,min(cap-.04,zb-.075))])
        b.prism(cheek,-.05,.05,lambda xx,zz,dd:(xx,yy-dd,zz),STUCCO,name+' | cheek')
    ring=[(xb-.02,y0-.19),(x+.18,y0-.19),(x+.18,y1+.19),(xb-.02,y1+.19)]
    b.plan_prism(Polygon(ring),cap-.054,cap+.028,BOARD,name+' | eave boards')
    for label,face,grade in hip(name,ring,cap+.048,.385):
        tile_surface(b,face,grade,lod,label)
    for p,q in zip(ring,ring[1:]+ring[:1]):
        b.tube([(*p,cap+.021),(*q,cap+.021)],.050,GUTTER,7 if lod else 12,name+' | gutter')
    for yy in [y0,y1]:
        b.tube([(x+.149,yy,cap+.015),(x+.069,yy,cap-.112),(x+.03,yy,sill+.02)],.027,BROWN,6 if lod else 9,name+' | rainwater pipe')

def segments(shape):
    if shape.geom_type=='LineString':
        points=list(shape.coords)
        yield from zip(points,points[1:])
    else:
        for p in getattr(shape,'geoms',[]): yield from segments(p)

def add_roof(b,lod,layout):
    for key,value in PALETTE.items(): b.palette.setdefault(key,value)
    faces=components(layout); windows=dormers(layout); lamp=light_polygon(layout)
    cut=[lamp.buffer(-.055,join_style=2)]
    for d in windows:
        x,y,w=d['x'],d['y'],d['width']
        cut.append(box(x-d['depth']+.025,y-w/2+.028,x-.015,y+w/2-.028))
    apertures=unary_union(cut)
    outline=unary_union([f for _,f,_ in faces])
    for i,(name,face,(a,c,h)) in enumerate(faces):
        for polygon in polygons(face.difference(apertures)):
            tile_surface(b,polygon,(a,c,h),lod,name)
        for p,q in segments(face.boundary.intersection(outline.boundary)):
            length=hypot(q[0]-p[0],q[1]-p[1])
            if length>.12 and abs(a*(q[0]-p[0])+c*(q[1]-p[1]))<.08:
                b.tube([(x,y,a*x+c*y+h-.055) for x,y in [p,q]],.052,GUTTER,7 if lod else 11,name+' | eave gutter')
        for _,other,(da,dc,dh) in faces[i+1:]:
            if abs(a-da)+abs(c-dc)<.02: continue
            for p,q in segments(face.boundary.intersection(other.boundary)):
                if hypot(q[0]-p[0],q[1]-p[1])<.28: continue
                mid=(np.array(p)+q)/2
                if abs((a-da)*mid[0]+(c-dc)*mid[1]+h-dh)>.018: continue
                rep=other.representative_point()
                ridge=(a-da)*(rep.x-mid[0])+(c-dc)*(rep.y-mid[1])>0
                radius,mat,offset,label=(.073,RIDGE,.028,'hip and ridge caps') if ridge else (.031,BROWN,.004,'valley lining')
                b.tube([(x,y,a*x+c*y+h+offset) for x,y in [p,q]],radius,mat,7 if lod else 11,label)
        frame=face.intersection(lamp).difference(lamp.buffer(-.075,join_style=2))
        planar_piece(b,frame,(a,c,h),.014,.065,BROWN,'shallow rooflight | folded flashing')
        planar_piece(b,face.intersection(lamp.buffer(-.069,join_style=2)),(a,c,h),.066,.081,GLASS,'shallow rooflight | glazing')
    for window in windows: make_dormer(b,lod,faces,window)
    return faces
