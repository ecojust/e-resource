"""Build the 103 Dianchi Road porch columns from the independently traced Ionic capital."""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from shapely import constrained_delaunay_triangles, covers, distance as shape_distance, points as shape_points, set_precision
from shapely.ops import polygonize, unary_union
from shapely.geometry import LineString, Polygon

DATA = Path(__file__).resolve().parents[1] / "measurements/ionic-front-traces.json"
STONE = "Pale stone of the bank porch"
PALETTE = {STONE: {"color": [.595,.565,.516], "roughness": .88}}


@lru_cache(maxsize=1)
def observations():
    return json.loads(DATA.read_bytes())


@lru_cache(maxsize=3)
def face_topology(step):
    """Triangulate the stone with edges running along each carved spiral."""
    data=observations()
    shape=Polygon(data["front_silhouette"]).simplify(.30,preserve_topology=True)
    if not shape.is_valid:shape=shape.buffer(0)
    shape=set_precision(shape,.01)
    fine=step<1.5
    paths=[LineString(v).simplify(.17 if fine else .48) for v in data["scroll_crests"].values()]
    paths += [LineString(v["trace"]) for v in data["horizontal_details"]]
    fields=[Polygon(v["corners_px"]).buffer(-1.1,join_style="round").buffer(1.1,quad_segs=4)
            for v in data["carved_fields"]]
    paths.extend(field.boundary for field in fields)
    channels=unary_union(paths)
    # Individual ribbons and grooves meet in the upper horizontal channel. A
    # noded network gives both sides of every contour exactly the same vertices.
    rings=[shape.boundary]
    radii=[.28,.68,1.05,1.49,1.93,2.42,2.91,3.46,4.19,5.15,6.25] if fine else [.46,1.,1.7,2.42,3.12,4.12,5.7]
    if step>=2.9:
        # The street photographs do not resolve the concealed rear spiral.
        # Reproduce the rolled outer return and leave its middle plain.
        channels=shape.boundary
        radii=[.6,1.5,3.2]
    for radius in radii:
        band=channels.buffer(radius,quad_segs=4 if fine else 2)
        band=set_precision(band,.01).intersection(shape)
        if not band.is_empty:rings.append(band.boundary)
    cells=polygonize(unary_union(rings))
    vertices,index,triangles=[],{},[]
    def add(xy):
        key=tuple(np.round(xy,5))
        if key not in index:
            index[key]=len(vertices);vertices.append(key)
        return index[key]
    for cell in cells:
        if not shape.covers(cell.representative_point()):continue
        for tri in constrained_delaunay_triangles(cell).geoms:
            pts=np.array(tri.exterior.coords)[:3]
            a,b,c=pts
            sign=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            if abs(sign)<1e-9:continue
            ids=tuple(add(v)for v in pts)
            triangles.append(ids if sign<0 else ids[::-1])
    uv=np.array(vertices);relief=np.zeros(len(uv));query=shape_points(uv)
    # A raised lip and the adjacent recessed groove are part of the same stone
    # face. The front is a continuous height field all the way into the eyes.
    if step>=2.9:
        distance=shape_distance(query,shape.boundary)
        return uv,triangles,.035*np.exp(-.5*((distance-1.4)/.8)**2)
    for line in observations()["scroll_crests"].values():
        curve=np.array(line);distance=shape_distance(query,LineString(curve));near=cKDTree(curve).query(uv)[1]
        s=near/(len(curve)-1)
        width=1.50-.40*s
        crest=.104*np.exp(-.5*(distance/width)**2)
        recess=.048*np.exp(-.5*((distance-2.95)/1.10)**2)
        detail=(crest-recess)*np.minimum(1.,s*28+.22)
        relief+=detail
    for row in observations()["horizontal_details"]:
        curve=np.asarray(row["trace"]);samples=[]
        for a,b in zip(curve[:-1],curve[1:]):
            count=max(2,int(np.linalg.norm(b-a)/.55))
            samples.extend(np.linspace(a,b,count,endpoint=False))
        samples.append(curve[-1])
        distance=shape_distance(query,LineString(samples))
        relief+=.049*np.exp(-.5*(distance/.92)**2)-.015*np.exp(-.5*((distance-2.)/.76)**2)
    for field in fields:
        distance=shape_distance(query,field.boundary)
        inside=covers(field,query)
        relief+=.031*np.exp(-.5*(distance/.79)**2)
        relief-=.032*inside*(1.-np.exp(-.5*(distance/1.2)**2))
    return uv,triangles,relief


def field_solid(builder,uv,triangles,xyz,back,part):
    """Close the visible height field along its true, clipped outer edge."""
    n=len(uv);edges=set()
    for f in triangles:
        for a,b in zip(f,(f[1],f[2],f[0])):
            if (b,a) in edges:edges.remove((b,a))
            else:edges.add((a,b))
    shell=triangles+[tuple(i+n for i in f[::-1]) for f in triangles]
    shell.extend((b,a,a+n,b+n)for a,b in sorted(edges))
    builder.add(np.vstack((xyz,back)),shell,STONE,part)


@lru_cache(maxsize=1)
def registered_reference():
    axes=json.loads((DATA.parent/"north-portico-axes.json").read_bytes())
    ref=axes["axes"][3]
    return (ref["x_m"],ref["y_m"],ref["z_and_pixels"]["neck"]["z_m"],
            ref["radius_m_by_view"]["close"],axes["scroll_face_y_m"])


def measured_profile(uv,relief):
    """Intersect the traced pixels with the actual varying depth of the carved stone."""
    from photo_plane import CAMERAS
    camera=CAMERAS["close"]
    x,axis_y,z,r,plane=registered_reference()
    uv=np.asarray(uv)
    d=plane-r*np.broadcast_to(relief,len(uv))
    at=np.column_stack((uv,np.ones(len(uv))))
    # A ray through each marked source pixel intersects its own parallel face
    # plane. Deprojection therefore preserves even the spiral at the edge of the oblique view.
    ray=at@np.linalg.inv(camera[:,:3]).T
    eye=-np.linalg.solve(camera[:,:3],camera[:,3])
    xyz=eye+ray*((d-eye[1])/ray[:,1])[:,None]
    return (xyz[:,[0,2]]-np.array([x,z]))/r


def local_profile(uv,position=None,ref_y=0.):
    """Express the photographed face in shaft radii around its upper neck."""
    datum=observations()["scale"]
    points=np.asarray(uv,dtype=float)
    base=np.asarray(datum["shaft_upper_centre_px"])
    anchors=np.array([datum["shaft_upper_left_px"],datum["shaft_upper_right_px"]])
    if position is not None:
        to_plane=lambda q:np.array([position(*p,ref_y)[[0,2]] for p in q])
        ends=to_plane(anchors)
        r=.5*abs(ends[1,0]-ends[0,0])
        if r<=0.:raise ValueError("Invalid calibrated shaft radius")
        return (to_plane(points)-to_plane([base])[0])/r
    # Local study projection used before the whole north-wall cameras have
    # been registered. The assembly can pass the calibrated photo-plane mapper.
    horizontal=anchors[1]-anchors[0]
    dx=horizontal/np.linalg.norm(horizontal)
    dz=-np.array([datum["shaft_axis_du_per_dv"],1.])
    dz=dz/np.linalg.norm(dz)*.90
    axes=np.column_stack((dx,dz))*np.linalg.norm(horizontal)/2.
    return np.linalg.solve(axes,(points-base).T).T


def ring_part(builder,centre,radius,z_radius,limits,steps,material,label):
    """Turn the narrowed bolster running between the front and rear spirals."""
    cx,cy,cz=centre;verts=[];faces=[]
    for y,factor in limits:
        for k in range(steps):
            a=k*2*np.pi/steps
            verts.append((cx+factor*radius*np.cos(a),cy+y,cz+factor*z_radius*np.sin(a)))
    for i in range(len(limits)-1):
        for j in range(steps):
            a=i*steps+j;b=i*steps+(j+1)%steps
            faces.append((a,a+steps,b+steps,b))
    faces.extend([tuple(range(steps)),tuple(range(len(verts)-1,len(verts)-steps-1,-1))])
    builder.add(verts,faces,material,label)


def fluted_shaft(builder,x,y,z0,z1,r,lod,name,rotation=0.):
    count=observations()["scale"]["estimated_complete_flute_count"]
    angles=np.arange(count*(6 if lod else 10))*2*np.pi/(count*(6 if lod else 10))
    # A circular concave flute meets a narrow flat fillet. Only the exposed
    # angular trough spacing is measured. Continue the same pitch at the rear.
    phase=(angles*count/(2*np.pi)+.5)%1.-.5
    cut=np.sqrt(np.maximum(0.,1.-(phase/.4375)**2))
    angles=angles+rotation
    top=z1-z0
    stations=[(0.,0.),(.032*r,.35),(.105*r,.85),(.17*r,1.),
              (.25*top,1.),(.63*top,1.),(top-.23*r,1.),
              (top-.14*r,.84),(top-.065*r,.42),(top,0.)]
    verts=[];faces=[];steps=len(angles)
    for z,depth in stations:
        t=z/top
        # Slight entasis is inferred from the rising, tapering shaft outline.
        body=r*(1.+.085*(1.-t)+.021*np.sin(np.pi*t))
        rad=body-r*.073*depth*cut
        verts.extend(np.column_stack((x+rad*np.cos(angles),y+rad*np.sin(angles),np.full(steps,z0+z))))
    for row in range(len(stations)-1):
        for k in range(steps):
            a=row*steps+k;b=row*steps+(k+1)%steps
            faces.append((a,b,b+steps,a+steps))
    faces.extend([tuple(range(steps-1,-1,-1)),tuple(range(len(verts)-steps,len(verts)))])
    builder.add(verts,faces,STONE,name+" fluted shaft")


def neck_cushion(builder,x,y,z0,r,steps,label,front_limit):
    """The upper echinus tucks behind the carved stone face; the neck bead remains round."""
    levels=[(0.,1.01,1.),(.052,1.06,.92),(.105,1.07,.64),(.15,1.015,.40),
            (.21,1.04,front_limit),(.28,1.11,front_limit),(.37,1.14,front_limit),(.45,1.10,front_limit)]
    verts=[];faces=[]
    for z,rr,maximum_front in levels:
        for angle in np.arange(steps)*2*np.pi/steps:
            depth=np.sin(angle)*rr
            if depth<0.:
                # The sheltered side and the visible lateral outline retain the
                # circular moulding. Narrow the front under the stone scrolls.
                depth*=maximum_front/rr
            verts.append((x+r*rr*np.cos(angle),y+r*depth,z0+r*z))
    for j in range(len(levels)-1):
        for k in range(steps):
            a=j*steps+k;b=j*steps+(k+1)%steps
            faces.append((a,b,b+steps,a+steps))
    faces.extend([tuple(range(steps-1,-1,-1)),tuple(range(len(verts)-steps,len(verts)))])
    builder.add(verts,faces,STONE,label)


@lru_cache(maxsize=1)
def shaft_registration():
    fit=json.loads((DATA.parent/"fluted-shafts.json").read_bytes())
    axes=json.loads((DATA.parent/"north-portico-axes.json").read_bytes())["axes"]
    return fit,axes


def stone_abacus(builder,name,x,y,neck_z,r,top_z):
    """Close the bearing over the street-facing volutes with a stepped stone plate."""
    # The solid bearing is visible along its flanks. The street architrave
    # conceals most of its front edge; keep the lower lip behind the carved face.
    bottom=neck_z+1.71*r
    cap=max(top_z,bottom+.16*r)
    front=y-.42*r
    back=y+1.11*r
    courses=[(bottom,bottom+.055*r,2.96,front+.073*r,back-.044*r),
             (bottom+.055*r,cap-.065*r,3.03,front+.043*r,back-.022*r),
             (cap-.065*r,cap,3.11,front,back)]
    for i,(lo,hi,width,a,b) in enumerate(courses,1):
        if hi>lo:
            builder.box((x,(a+b)/2,(lo+hi)/2),(width*r,b-a,hi-lo),STONE,
                        label=name+" abacus bed "+str(i))


def add_ionic_column(builder,lod,name,x,axis_y,shaft_base_z,neck_z,radius,reference_position=None,reference_y=0.):
    """Model one porch column. x increases to the viewer's right, positive y goes inside."""
    r=float(radius)
    if r<=0 or neck_z-shaft_base_z<3*r:
        raise ValueError("Invalid bank column dimensions")
    shaft_x,shaft_y,shaft_r=x,axis_y,r
    rotation=0.
    top_z=neck_z+2.09*r
    if reference_position is not None:
        registered,axes=shaft_registration()
        index=int(np.argmin([abs(row["x_m"]-x) for row in axes]))
        shaft_x,shaft_y,shaft_r=registered["columns"][index]["shaft_xyr_m"]
        rotation=registered["phase_rad"]
        top_z=axes[index]["z_and_pixels"]["top"]["z_m"]
    fluted_shaft(builder,shaft_x,shaft_y,shaft_base_z,neck_z,shaft_r,lod,name,rotation)
    stone_abacus(builder,name,x,axis_y,neck_z,r,top_z)
    angles=20 if lod else 40
    # The oblique street photograph shows a spreading round base above the
    # shared stone plinth, then a narrow projecting ring at the foot of each
    # fluted shaft. This collar is separate from the shared rectangular base.
    foot=[(0.,1.20),(.07,1.22),(.14,1.21),(.23,1.13),(.34,1.10),
          (.43,1.15),(.49,1.17),(.55,1.14),(.60,1.08)]
    builder.lathe((shaft_x,shaft_y),[(shaft_base_z+z*shaft_r,rad*shaft_r)for z,rad in foot],STONE,angles,name+" round foot")
    # The photographed neck beads and echinus support the two stone scrolls.
    neck_cushion(builder,x,axis_y,neck_z,r,angles,name+" neck and cushion",.28)
    eye_px=observations()["scale"]["reference_eye_px"]
    if reference_position is not None:
        rx,ry,rz,rr,rf=registered_reference()
        front_ratio=(ry-rf)/rr
        eye=measured_profile(eye_px,.04)
    else:
        front_ratio=1.045
        eye=local_profile(eye_px)
    depth_scale=front_ratio/1.045
    for i,(ex,ez) in enumerate(eye):
        ring_part(builder,(x+ex*r,axis_y,neck_z+ez*r),.77*r,.70*r,
                  [(u*r*depth_scale,rad) for u,rad in [(-1.04,.96),(-.98,1.),(-.90,1.04),(-.83,1.),
                    (-.65,.87),(-.32,.79),(-.17,.80),(-.11,.86),(.11,.86),(.17,.80),
                    (.36,.80),(.70,.91),(.90,1.02),(.96,1.)]],angles,STONE,name+f" bolster {i+1}")
    for rear in (False,True):
        step=3.0 if rear else (2.30 if lod else 1.12)
        uv,triangles,h=face_topology(step)
        xz=measured_profile(uv,h if not rear else 0.) if reference_position is not None else local_profile(uv)
        direction=1. if rear else -1.
        # Infer a matching plain rear return where the street photo cannot
        # see the back. The detailed front retains the measured carved channel.
        relief=h*(.30 if rear else 1.)
        yface=axis_y+direction*r*(front_ratio+relief)
        xyz=np.column_stack((x+r*xz[:,0],yface,neck_z+r*xz[:,1]))
        back=xyz.copy();back[:,1]=axis_y+direction*.82*r*depth_scale
        faces=[f[::-1]for f in triangles] if rear else triangles
        field_solid(builder,uv,faces,xyz,back,name+(" rear return" if rear else " carved street face"))

