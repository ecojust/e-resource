"""Bounded Spanish barrel-tile roofs in local east/north/up metres.

All dimensions are authored estimates, not measurements of individual tiles.
Input bounds already include the desired eave overhang. This module neither
reads photographs nor applies building-specific photographic textures.

The full level uses 0.35 m cross-slope pitch and 0.67 m courses. The authored
LOD uses wider 0.58 m pitch and 1.05 m courses with three arc segments. Every
tile is a closed shell with a real rounded upper profile and an underside;
cut tiles follow the hip boundary rather than overhanging into empty space.
"""
import math
import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient


def _signed_add(builder, vertices, faces, material, label):
    """Add a consistently outward closed part; leave finite checks to Builder."""
    vertices = np.asarray(vertices, dtype=float)
    total = 0.
    for face in faces:
        for k in range(1, len(face)-1):
            a, b, c = vertices[[face[0], face[k], face[k+1]]]
            total += float(a @ np.cross(b, c))
    if total < 0:
        faces = [tuple(reversed(face)) for face in faces]
    builder.add(vertices, faces, material, label)


def _material(i, j, face):
    # Reproducible subtle variation; these are material values, not fake scans.
    k = (i*73856093 ^ j*19349663 ^ face*83492791) % 17
    return 'tile light' if k == 0 else 'tile dark' if k == 1 else 'terracotta roof'


def _tile(builder, polygon, u_center, width, frame, height, segments, material, label):
    """Closed curved tile clipped to one convex roof-plane polygon.

    Top strips share vertices. Internal strip boundaries have no vertical
    faces, avoiding coincident opposing triangles inside the same tile.
    """
    polygon = orient(polygon, sign=1.)
    origin, along, slope, normal = frame
    x0, y0, x1, y1 = polygon.bounds
    # Most tiles are uncut. Extruding one convex semicircular profile needs
    # sixteen triangles at full detail instead of separately triangulating a
    # segmented underside; the meeting arc endpoints remain exact vertices.
    if abs(x0-(u_center-width/2))<1e-8 and abs(x1-(u_center+width/2))<1e-8 and abs(polygon.area-(x1-x0)*(y1-y0))<1e-8:
        cross=[(-width/2*math.cos(i*math.pi/segments),
                0. if i in (0,segments) else height*math.sin(i*math.pi/segments))
               for i in range(segments+1)]
        vertices=[origin+along*(u_center+u)+slope*v+normal*h
                  for v in (y0,y1) for u,h in cross]
        n=len(cross)
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
        _signed_add(builder,vertices,faces,material,label)
        return
    # Use regular arc samples so an uncut tile has a symmetric half-cylinder.
    cuts = [u_center-width/2*math.cos(i*math.pi/segments)
            for i in range(segments+1)]
    mids = [x for x in cuts[1:-1] if x0+1e-8 < x < x1-1e-8]
    limits = [x0, *mids, x1]
    vertices, faces, lookup = [], [], {}

    def profile(u):
        # Piecewise-linear arc profile agrees exactly with the top strips.
        t = max(-1., min(1., (u-u_center)/(width/2)))
        for i in range(segments):
            if cuts[i]-1e-9 <= u <= cuts[i+1]+1e-9:
                a, b = cuts[i:i+2]
                if b-a <= 1e-12:
                    return .012
                ha = math.sin(i*math.pi/segments)*height
                hb = math.sin((i+1)*math.pi/segments)*height
                return .012+ha+(hb-ha)*(u-a)/(b-a)
        return .012+math.sqrt(max(0.,1-t*t))*height

    def index(u, v, top):
        key = (round(float(u), 10), round(float(v), 10), bool(top))
        if key not in lookup:
            lookup[key] = len(vertices)
            offset = profile(u) if top else 0.
            vertices.append(origin+along*u+slope*v+normal*offset)
        return lookup[key]

    # Piecewise planar top, triangulated per curved strip without internal walls.
    for a, b in zip(limits, limits[1:]):
        strip = polygon.intersection(box(a, y0-1., b, y1+1.))
        if strip.is_empty or strip.area < 1e-9:
            continue
        for tri in constrained_delaunay_triangles(strip).geoms:
            pts = list(orient(tri, sign=1.).exterior.coords)[:3]
            faces.append(tuple(index(u,v,True) for u,v in pts))
    # Bottom and side rings use all curve breakpoints on the boundary.
    ring = []
    coords = list(polygon.exterior.coords)
    for a,b in zip(coords,coords[1:]):
        aa,bb = np.asarray(a),np.asarray(b)
        fractions = [0.]
        if abs(bb[0]-aa[0]) > 1e-10:
            fractions.extend((cut-aa[0])/(bb[0]-aa[0]) for cut in mids
                             if 1e-8 < (cut-aa[0])/(bb[0]-aa[0]) < 1-1e-8)
        ring.extend(tuple(aa+t*(bb-aa)) for t in sorted(fractions))
    bottom = Polygon(ring)
    for tri in constrained_delaunay_triangles(bottom).geoms:
        pts = list(orient(tri, sign=1.).exterior.coords)[:3]
        faces.append(tuple(index(u,v,False) for u,v in reversed(pts)))
    for a,b in zip(ring,ring[1:]+ring[:1]):
        faces.append((index(*a,False),index(*b,False),
                      index(*b,True),index(*a,True)))
    _signed_add(builder,vertices,faces,material,label)


def _ridge_cap(builder, a, b, width, height, segments, label, lod=False):
    """Separate short convex ridge/hip caps with actual open-looking seams."""
    a,b = np.asarray(a,float),np.asarray(b,float)
    length = float(np.linalg.norm(b-a))
    if length < .04:
        return 0
    axis = (b-a)/length
    across = np.cross(axis,[0.,0.,1.]); across /= np.linalg.norm(across)
    normal = np.cross(across,axis)
    if normal[2]<0:normal=-normal
    # Along and slope in _tile must have an upward cross-product normal.
    along = across
    if np.cross(along,axis)@normal<0:along=-along
    step = .95 if lod else .56
    count = max(1,math.ceil(length/step))
    for j in range(count):
        v0=j*length/count+.012
        v1=(j+1)*length/count-.012
        if v1-v0>.025:
            _tile(builder,box(-width/2,v0,width/2,v1),0.,width,
                  (a,along,axis,normal),height,segments,
                  'terracotta roof',f'{label}/cap-{j:03d}')
    return count


def add_roof(builder,x0,y0,x1,y1,eave,ridge,label,
             axis='x',gable=False,lod=False):
    """Add one hip/gable roof and return exact generated detail statistics.

    x0/y0/x1/y1 are principal ENU metres and INCLUDE the chosen eave overhang.
    ``support_faces`` provides the original sloping face vertices and affine
    ``z = a*x + b*y + c`` for caller-side intersection/visibility diagnostics.
    Shells remain separate masses at joins; this is not an automatic roof union.
    """
    values=[x0,y0,x1,y1,eave,ridge]
    if not np.isfinite(values).all() or x1<=x0 or y1<=y0 or ridge<=eave:
        raise ValueError('Roof bounds/heights must be finite and positive')
    if axis not in ('x','y'):
        raise ValueError('Roof ridge axis must be x or y')
    for key in ('terracotta roof','tile light','tile dark'):
        if key not in builder.palette:raise ValueError(f'Missing roof material {key}')
    start=len(builder.parts)
    if axis=='x':
        end=min((y1-y0)*.45,(x1-x0)*.22)
        r0=np.array([x0 if gable else x0+end,(y0+y1)/2,ridge])
        r1=np.array([x1 if gable else x1-end,(y0+y1)/2,ridge])
        top=[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
    else:
        end=min((x1-x0)*.45,(y1-y0)*.22)
        r0=np.array([(x0+x1)/2,y0 if gable else y0+end,ridge])
        r1=np.array([(x0+x1)/2,y1 if gable else y1-end,ridge])
        top=[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)]
    verts=np.array([[x0,y0,eave],[x1,y0,eave],
                    [x1,y1,eave],[x0,y1,eave],r0,r1],float)
    _signed_add(builder,verts,[(0,3,2,1),*top],
                'terracotta roof',label+'/closed-roof-shell')
    pitch=.58 if lod else .35
    course=1.05 if lod else .67
    segments=3 if lod else 4
    tile_count=0;support=[]
    for face_number,indices in enumerate(top):
        face=verts[list(indices)]
        p0,p1=face[:2];along=p1-p0;along/=np.linalg.norm(along)
        normal=np.cross(p1-p0,face[2]-p0)
        normal/=np.linalg.norm(normal)
        # Triangular gable ends are vertical walls, not tiled roof slopes.
        if abs(normal[2])<1e-8:continue
        if normal[2]<0:normal=-normal;along=-along
        slope=np.cross(normal,along)
        uv=np.array([[(p-p0)@along,(p-p0)@slope] for p in face])
        polygon=orient(Polygon(uv),sign=1.)
        coeff=np.linalg.lstsq(np.column_stack((face[:,:2],np.ones(len(face)))),
                              face[:,2],rcond=None)[0]
        support.append({'index':face_number,'vertices_enu':face.tolist(),
                        'height_affine':coeff.tolist()})
        # A small border is occupied by separate ridge/hip covering caps.
        active=polygon.buffer(-.020,join_style=2)
        if active.is_empty:continue
        u0,v0,u1,v1=active.bounds
        columns=max(1,math.ceil((u1-u0)/pitch))
        rows=max(1,math.ceil((v1-v0)/course))
        step_u=(u1-u0)/columns;step_v=(v1-v0)/rows
        for row in range(rows):
            # Continuous columns, slight transverse seams at every course.
            vv0=v0+row*step_v+.010;vv1=v0+(row+1)*step_v-.010
            for col in range(columns):
                uc=u0+(col+.5)*step_u;w=step_u-.014
                clip=active.intersection(box(uc-w/2,vv0,uc+w/2,vv1))
                if not isinstance(clip,Polygon) or clip.area<.006:continue
                _tile(builder,clip,uc,w,(p0+normal*.006,along,slope,normal),
                      .055,segments,_material(col,row,face_number),
                      f'{label}/slope-{face_number}/tile-{row:03d}-{col:03d}')
                tile_count+=1
    cap_count=_ridge_cap(builder,r0+np.array([0,0,.003]),
                         r1+np.array([0,0,.003]),.24,.098,
                         segments,label+'/ridge',lod)
    if not gable:
        hip_pairs=[(0,4),(1,5),(2,5),(3,4)] if axis=='x' else [(0,4),(1,4),(2,5),(3,5)]
        for i,(a,b) in enumerate(hip_pairs):
            cap_count+=_ridge_cap(builder,verts[a]+np.array([0,0,.01]),
                                  verts[b]+np.array([0,0,.01]),.19,.065,
                                  segments,label+f'/hip-{i}',lod)
    report={'label':label,'axis':axis,'gable':bool(gable),'lod':bool(lod),
            'nominal_eave_m':float(eave),'nominal_ridge_m':float(ridge),
            'tile_count':tile_count,'cap_count':cap_count,
            'parts_added':len(builder.parts)-start,
            'triangles_added':sum(len(p['triangles']) for p in builder.parts[start:]),
            'authored_nominal_tile_pitch_m':pitch,'authored_nominal_course_m':course,
            'tile_profile_height_m':.055,'support_faces':support,
            'not_measured_tile_layout':True}
    return report
