"""Closed mathematical solids for the museum, no Blender dependency.

All points use ENU metres. Compound structure contacts require a separate
actual exported-triangle audit; closed individual parts do not prove those.
"""
import math
from collections import Counter
import numpy as np
from shapely import constrained_delaunay_triangles, set_precision
from shapely.geometry import Polygon, LineString, box
from shapely.geometry.polygon import orient
from common.photo_architecture import pieces


def add_positive(builder, vertices, faces, material, label):
    v=np.asarray(vertices,float);fs=[tuple(f) for f in faces]
    triangles=[(f[0],f[i],f[i+1]) for f in fs for i in range(1,len(f)-1)]
    t=np.asarray(triangles,int)
    volume=np.einsum('ij,ij->',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6
    if abs(volume)<1e-9:raise ValueError('Zero-volume solid '+label)
    if volume<0:fs=[tuple(reversed(f)) for f in fs]
    builder.add(v,fs,material,label)


def surface_solid(builder, polygon, top_z, bottom_z, material, label, grid=4.):
    """One watertight variable-height shell, with common grid-cell vertices.

    CDT triangulates clipped plan cells, preserving real holes. Interior shared
    edges are welded; only the actual boundary receives side walls.
    """
    polygon=set_precision(polygon,1e-6)
    for pi,poly in enumerate(pieces(polygon)):
        vertices=[];lookup={};top_faces=[]
        def idx(x,y):
            key=(round(x,6),round(y,6))
            if key not in lookup:lookup[key]=len(vertices);vertices.append(key)
            return lookup[key]
        x0,y0,x1,y1=poly.bounds
        for ix in range(math.floor(x0/grid),math.ceil(x1/grid)):
            for iy in range(math.floor(y0/grid),math.ceil(y1/grid)):
                cell=poly.intersection(box(ix*grid,iy*grid,(ix+1)*grid,(iy+1)*grid))
                for part in pieces(cell):
                    if part.area<1e-7:continue
                    for tri in constrained_delaunay_triangles(part).geoms:
                        if tri.area<1e-9:continue
                        pp=list(orient(tri,sign=1.).exterior.coords)[:3]
                        top_faces.append(tuple(idx(x,y) for x,y in pp))
        if not top_faces:continue
        n=len(vertices);top=[[x,y,float(top_z(x,y))] for x,y in vertices]
        bottom=[[x,y,float(bottom_z(x,y))] for x,y in vertices]
        if min(a[2]-b[2] for a,b in zip(top,bottom))<.003:
            raise ValueError('Shell must have real positive thickness '+label)
        edgecounts=Counter(tuple(sorted((a,b))) for f in top_faces for a,b in zip(f,f[1:]+f[:1]))
        if any(v>2 for v in edgecounts.values()):raise ValueError('Invalid surface topology '+label)
        faces=list(top_faces)+[tuple(x+n for x in reversed(f)) for f in top_faces]
        for f in top_faces:
            for a,b in zip(f,f[1:]+f[:1]):
                if edgecounts[tuple(sorted((a,b)))]==1:faces.append((b,a,a+n,b+n))
        add_positive(builder,top+bottom,faces,material,label+(f'/component-{pi}' if pi else ''))


def path_data(points, closed=False):
    q=np.asarray(points,float)
    if len(q)<2:raise ValueError('Path too short')
    if closed and np.linalg.norm(q[0]-q[-1])<1e-8:q=q[:-1]
    tangent=[]
    for i in range(len(q)):
        a=q[(i-1)%len(q)] if closed or i else q[0]
        b=q[(i+1)%len(q)] if closed or i<len(q)-1 else q[-1]
        t=b-a;t/=np.linalg.norm(t);tangent.append(t)
    tangent=np.asarray(tangent)
    return q,tangent,np.column_stack([tangent[:,1],-tangent[:,0]])


def profile_sweep(builder, points, profile, material, label, z_offset=None, closed=False):
    """A closed cross-section swept along a planar curve; real curved thickness."""
    q,t,n=path_data(points,closed);profile=np.asarray(profile,float)
    if np.linalg.norm(profile[0]-profile[-1])<1e-8:profile=profile[:-1]
    if not Polygon(profile).is_valid:raise ValueError('Invalid sweep profile '+label)
    profile=np.asarray(orient(Polygon(profile),sign=1.).exterior.coords)[:-1]
    vertices=[]
    for xy,normal in zip(q,n):
        z=float(z_offset(*xy)) if z_offset else 0.
        vertices.extend([xy[0]+normal[0]*d,xy[1]+normal[1]*d,z+h] for d,h in profile)
    k=len(profile);faces=[]
    for i in range(len(q) if closed else len(q)-1):
        j=(i+1)%len(q)
        for h in range(k):faces.append((i*k+h,j*k+h,j*k+(h+1)%k,i*k+(h+1)%k))
    if not closed:
        # Concave C sections require constrained caps, not a triangle fan.
        pp=orient(Polygon(profile),sign=1.);lookup={tuple(v):i for i,v in enumerate(profile)}
        for tri in constrained_delaunay_triangles(pp).geoms:
            coords=list(orient(tri,sign=1.).exterior.coords)[:3]
            ids=[lookup[tuple(v)] for v in coords]
            faces.append(tuple(ids))
            faces.append(tuple((len(q)-1)*k+i for i in reversed(ids)))
    add_positive(builder,vertices,faces,material,label)


def panel(builder, points, bottom, top, material, label, thickness=.065, outward0=0., outward1=0.):
    """Thin curved curtain-wall solid, outward0/1 permit real sloping glass."""
    q,t,n=path_data(points)
    v=[]
    for back in (False,True):
        for high in (False,True):
            for xy,normal in zip(q,n):
                z=float(top(*xy) if high else bottom(*xy))
                d=(outward1 if high else outward0)-(thickness if back else 0.)
                v.append([xy[0]+normal[0]*d,xy[1]+normal[1]*d,z])
    k=len(q);f=[]
    for i in range(k-1):
        j=i+1
        f.extend([(i,j,k+j,k+i),(2*k+j,2*k+i,3*k+i,3*k+j),
                  (2*k+i,2*k+j,j,i),(k+i,k+j,3*k+j,3*k+i)])
    f.extend([(0,k,3*k,2*k),(k-1,3*k-1,4*k-1,2*k-1)])
    add_positive(builder,v,f,material,label)


def ring_stations(polygon, step):
    line=LineString(polygon.exterior.coords);count=max(12,int(math.ceil(line.length/step)))
    return np.asarray([line.interpolate(i*line.length/count).coords[0] for i in range(count)])


def subpath(line, start, stop, step=.5):
    if stop<=start:raise ValueError('Subpath must advance')
    count=max(1,int(math.ceil((stop-start)/step)))
    def value(s):return s%line.length if line.is_ring else min(line.length,max(0.,s))
    return np.asarray([line.interpolate(value(start+(stop-start)*i/count)).coords[0] for i in range(count+1)])


def audit_parts(parts):
    failures=[];records=[];allbounds=[]
    labelcounts=Counter(p['label'] for p in parts)
    for label,count in labelcounts.items():
        if count>1:failures.append({'label':label,'duplicate_semantic_part_count':count})
    for part in parts:
        v=np.asarray(part['vertices'],dtype='<f4').astype(float);t=np.asarray(part['triangles'],int)
        cross=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]])
        _,inv=np.unique(v,axis=0,return_inverse=True);w=inv[t]
        edges=Counter(tuple(sorted((int(a),int(b)))) for tri in w for a,b in zip(tri,np.roll(tri,-1)))
        directed=Counter((int(a),int(b)) for tri in w for a,b in zip(tri,np.roll(tri,-1)))
        volume=float(np.einsum('ij,ij->',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6)
        bad=sum(n!=2 for n in edges.values());zero=int(np.sum(np.linalg.norm(cross,axis=1)<1e-9))
        misoriented=sum(directed[(a,b)]!=1 or directed[(b,a)]!=1 for a,b in edges)
        if bad or zero or misoriented or volume<=0:failures.append({'label':part['label'],'nonmanifold_edges':bad,'misoriented_edges':misoriented,'zero_triangles':zero,'signed_volume_m3':volume})
        lo=v.min(0);hi=v.max(0);allbounds.extend([lo,hi])
        records.append({'label':part['label'],'material':part['material'],'triangles':len(t),
                        'vertices':len(v),'signed_volume_m3':volume,'bounds_enu':[lo.tolist(),hi.tolist()]})
    b=np.asarray(allbounds)
    return {'passed':not failures,'failures':failures,'parts':len(records),
            'triangles':sum(r['triangles'] for r in records),'part_records':records,
            'bounds_enu_m':[b.min(0).tolist(),b.max(0).tolist()],
            'scope':'Individual exact FLOAT32 welded solids only. No whole-assembly/contact/visibility acceptance.'}
