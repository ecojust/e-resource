"""Procedural Shanghai landmarks. Blender coordinates are east/north/up.

The construction functions use quarter-scale geometry for numerically compact
modeling. export_landmarks.py produces centered, true-height GLBs in meters.
"""
import math
import bpy
from mathutils import Vector, Matrix
from math import sin, cos, pi

LANDMARKS = {
    'oriental-pearl': {'name':'东方明珠广播电视塔','center':(85,65),'height':468,'longitude':121.4951673,'latitude':31.2419382,'osmWay':40778038},
    'shanghai-tower': {'name':'上海中心大厦','center':(178,-40),'height':632,'longitude':121.5012667,'latitude':31.2356172,'osmWay':165792123},
    'swfc': {'name':'上海环球金融中心','center':(226,18),'height':492,'longitude':121.5030405,'latitude':31.2365768,'osmWay':10691100},
    'jin-mao': {'name':'金茂大厦','center':(160,20),'height':420.5,'longitude':121.5014197,'latitude':31.2372502,'osmWay':376075961},
}


def _mesh(name, verts, faces, materials, indices=None, smooth=False):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    for m in materials:data.materials.append(m)
    for i,p in enumerate(data.polygons):
        p.use_smooth=smooth
        if indices:p.material_index=indices[i]
    return obj


def _box(name, loc, size, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        b=o.modifiers.new('Architectural bevel','BEVEL');b.width=bevel;b.segments=1
        o.modifiers.new('Facade normals','WEIGHTED_NORMAL')
    return o


def _cylinder(name,loc,radius,depth,mat,vertices=48,radius2=None):
    if radius2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=radius,radius2=radius2,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o


def _beam(name,a,b,r,mat,vertices=12):
    a,b=Vector(a),Vector(b)
    o=_cylinder(name,(a+b)/2,r,(b-a).length,mat,vertices)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def _tube(name,points,r,mat,sides=6):
    pts=[Vector(p) for p in points];v=[];f=[]
    for i,c in enumerate(pts):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        side=tangent.cross(Vector((0,0,1)))
        if side.length<.01:side=tangent.cross(Vector((0,1,0)))
        side.normalize();up=tangent.cross(side).normalized()
        for j in range(sides):
            a=j*2*pi/sides;v.append(c+side*(r*cos(a))+up*(r*sin(a)))
    for i in range(len(pts)-1):
        for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;f.append((a,b,b+sides,a+sides))
    f.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))])
    return _mesh(name,v,f,[mat],smooth=True)


def _torus(name,center,major,minor,mat,segments=64):
    bpy.ops.mesh.primitive_torus_add(major_segments=segments,minor_segments=6,location=center,major_radius=major,minor_radius=minor)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o


def _new_mat(name,color,metal=.3,rough=.3):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m


def _pearl(m):
    initial=set(bpy.data.objects);cx,cy=LANDMARKS['oriental-pearl']['center']
    pink=_new_mat('Pearl · rose-tinted glass',(.38,.14,.24),.42,.25)
    pale=_new_mat('Pearl · pearl pink glass',(.56,.36,.43),.30,.29)
    metal=m['silver'];glass=m['glass_blue']
    # Circular entrance hall, radial colonnade and the three distinctive splayed legs.
    _cylinder('Pearl · circular entrance podium',(cx,cy,1.4),16.8,2.8,m['stone'],64)
    _cylinder('Pearl · dark entrance glazing',(cx,cy,3.0),12.2,2.4,glass,64)
    _cylinder('Pearl · podium canopy',(cx,cy,4.4),14.0,.42,metal,64)
    for j in range(18):
        a=j*2*pi/18
        _beam('Pearl · entrance column',(cx+12.4*cos(a),cy+12.4*sin(a),.3),(cx+12.4*cos(a),cy+12.4*sin(a),4.2),.20,metal,8)
    for j in range(3):
        a=j*2*pi/3+.2
        _beam('Pearl · splayed concrete leg',(cx+13*cos(a),cy+13*sin(a),2.0),(cx+3.4*cos(a),cy+3.4*sin(a),26),1.35,metal,20)
        _beam('Pearl · upper parallel shaft',(cx+3.2*cos(a),cy+3.2*sin(a),28),(cx+3.2*cos(a),cy+3.2*sin(a),74),.98,metal,20)
    _cylinder('Pearl · central elevator shaft',(cx,cy,51),1.9,49,glass,24)
    for j in range(3):
        a=j*2*pi/3+.2
        _cylinder('Pearl · satellite lower pavilion',(cx+11*cos(a),cy+11*sin(a),9),2.6,5.0,pink,24,radius2=2.0)
    for label,zc,radius in [('Lower globe',28,9.0),('Upper globe',72,6.9),('Space capsule',91,3.1)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=(cx,cy,zc))
        o=bpy.context.object;o.name='Pearl · '+label;o.scale=(radius,radius,radius*.90)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        o.data.materials.append(pink);o.data.materials.append(pale)
        for p in o.data.polygons:p.use_smooth=True;p.material_index=(p.index//48)%4==0
        # Broad pale observation rings and fine silver meridians preserve globe form.
        for lat in [-.48,-.10,.24,.57]:
            z=zc+radius*.9*lat;r=radius*math.sqrt(1-lat*lat)
            _torus('Pearl · observation latitude',(cx,cy,z),r,.13 if radius>5 else .07,metal)
        for j in range(12 if radius>5 else 8):
            a=j*2*pi/(12 if radius>5 else 8)
            pts=[]
            for k in range(25):
                t=-pi/2+.05+k*(pi-.1)/24
                pts.append((cx+radius*cos(t)*cos(a),cy+radius*cos(t)*sin(a),zc+radius*.9*sin(t)))
            _tube('Pearl · globe meridian',pts,.055 if radius>5 else .035,metal,5)
    _cylinder('Pearl · upper mast',(cx,cy,84.5),1.15,23,metal,24,radius2=.65)
    _cylinder('Pearl · antenna lower',(cx,cy,102),.72,15,metal,20,radius2=.32)
    _cylinder('Pearl · needle',(cx,cy,113.25),.30,7.5,m['red'],16,radius2=.035)
    for z in [98,102,106,110]:_torus('Pearl · antenna collar',(cx,cy,z),.55 if z<108 else .30,.075,metal,24)
    return [o for o in bpy.data.objects if o not in initial]


def _tower(m):
    initial=set(bpy.data.objects);cx,cy=LANDMARKS['shanghai-tower']['center']
    glass=m['glass_teal'];metal=m['silver']
    shadow=_new_mat('Shanghai Tower · alternating glass',(.11,.29,.34),.48,.24)
    _cylinder('Shanghai Tower · circular podium',(cx,cy,1.5),18,3,m['stone'],72)
    _cylinder('Shanghai Tower · lobby glazing',(cx,cy,4),15.7,5,glass,72)
    _cylinder('Shanghai Tower · lobby canopy',(cx,cy,6.6),16.8,.6,metal,72)
    def envelope(z,a,offset=0):
        t=max(0,min(1,(z-4)/151))
        radius=(13.8-5.7*t+.3*sin(pi*t))*(1+.105*cos(3*a))
        ang=a+2.07*t
        return (cx+(radius+offset)*cos(ang),cy+(radius+offset)*sin(ang),z)
    # Paired rings create distinct horizontal curtain-wall transoms without textures.
    zs=[6.7]
    z=7.0
    while z<150:
        zs.extend([z,z+.095]);z+=1.72
    zs.extend([152.0,155.0,157.5])
    sides=48;v=[];f=[];mi=[]
    for z in zs:
        for j in range(sides):v.append(envelope(z,2*pi*j/sides))
    for i in range(len(zs)-1):
        narrow=zs[i+1]-zs[i]<.2
        for j in range(sides):
            f.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
            mi.append(1 if narrow else (2 if j%6 in [0,1] else 0))
    f.extend([tuple(reversed(range(sides))),tuple((len(zs)-1)*sides+j for j in range(sides))]);mi.extend([0,0])
    _mesh('Shanghai Tower · twisting glazed envelope',v,f,[glass,metal,shadow],mi,True)
    for j in range(16):
        a=2*pi*j/16
        pts=[envelope(7+i*149/64,a,.035) for i in range(65)]
        _tube('Shanghai Tower · helical mullion',pts,.065,metal,5)
    # Open metal crown follows the same twisting triangular rim.
    rim=[envelope(157.8,2*pi*j/48,.06) for j in range(49)]
    _tube('Shanghai Tower · crown rim',rim,.12,metal,6)
    for j in range(12):
        a=2*pi*j/12
        _beam('Shanghai Tower · crown fin',envelope(151.5,a,.1),envelope(158,a,.06),.13,metal,6)
    # The roof's uppermost surface deliberately ends at the documented quarter height.
    _cylinder('Shanghai Tower · recessed rooftop',(cx,cy,155.2),6.7,.4,m['metal'],48)
    return [o for o in bpy.data.objects if o not in initial]


def _jinmao(m):
    initial=set(bpy.data.objects);cx,cy=LANDMARKS['jin-mao']['center']
    glass=m['glass_blue'];silver=m['silver'];stone=m['stone']
    _box('Jin Mao · podium',(cx,cy,2),(25,23,4),stone,.3)
    _box('Jin Mao · lobby glass',(cx,cy,5),(20,19,5),glass,.2)
    tiers=[(7.5,25.5,10.0),(25.5,41,9.5),(41,54,8.85),(54,65,8.15),
           (65,74.0,7.4),(74,81.5,6.6),(81.5,87.8,5.7),(87.8,92.6,4.7),(92.6,96.2,3.65)]
    # Eight-fold stepped silhouette and prominent silver horizontal eaves.
    for idx,(z0,z1,r) in enumerate(tiers):
        o=_cylinder('Jin Mao · octagonal tier %02d'%idx,(cx,cy,(z0+z1)/2),r,z1-z0,glass,8)
        o.rotation_euler.z=pi/8
        cap=_cylinder('Jin Mao · projecting tier cornice',(cx,cy,z1-.10),r+.48,.42,silver,8)
        cap.rotation_euler.z=pi/8
        for z in [z0+1.45*k for k in range(1,int((z1-z0)/1.45)+1)]:
            ring=_cylinder('Jin Mao · silver floor band',(cx,cy,z),r+.035,.10,silver,8);ring.rotation_euler.z=pi/8
        for j in range(8):
            a=pi/8+j*pi/4
            _beam('Jin Mao · corner buttress',(cx+(r+.10)*cos(a),cy+(r+.10)*sin(a),z0),(cx+(r+.10)*cos(a),cy+(r+.10)*sin(a),z1),.15,silver,6)
            a2=a+pi/8
            _beam('Jin Mao · center mullion',(cx+r*.925*cos(a2),cy+r*.925*sin(a2),z0),(cx+r*.925*cos(a2),cy+r*.925*sin(a2),z1),.055,silver,5)
    _cylinder('Jin Mao · lantern base',(cx,cy,97.4),3.25,2.4,silver,8,radius2=2.0)
    _cylinder('Jin Mao · lantern',(cx,cy,99.4),1.9,2.4,glass,8,radius2=1.2)
    _cylinder('Jin Mao · spire',(cx,cy,102.8),1.15,4.4,silver,8,radius2=.02)
    for j in range(4):
        a=j*pi/2
        _box('Jin Mao · entrance portal',(cx+11.8*cos(a),cy+10.8*sin(a),2.5),
             (4,.5,4) if j%2==0 else (.5,4,4),silver)
    return [o for o in bpy.data.objects if o not in initial]


def build_landmark_groups(materials):
    """Return a dict keyed by landmark slug, each containing its new objects."""
    groups={}
    groups['oriental-pearl']=_pearl(materials)
    groups['shanghai-tower']=_tower(materials)
    from swfc_helper import build_swfc
    groups['swfc']=build_swfc(materials)
    # West-facing portal: the main view from the Bund sees the actual sky opening.
    center=Vector((226,18,0))
    rotate=Matrix.Translation(center)@Matrix.Rotation(pi/2,4,'Z')@Matrix.Translation(-center)
    for o in groups['swfc']:o.matrix_world=rotate@o.matrix_world
    groups['jin-mao']=_jinmao(materials)
    for slug,objects in groups.items():
        for obj in objects:
            obj['landmark_id']=slug
            obj['landmark_name']=LANDMARKS[slug]['name']
            obj['real_height_m']=LANDMARKS[slug]['height']
    return groups


def build_landmarks(materials):
    """Compatibility assembly API; returns (objects, viewer-axis colliders)."""
    groups=build_landmark_groups(materials);colliders=[]
    widths={'oriental-pearl':17.0,'shanghai-tower':18.1,'swfc':13.1,'jin-mao':12.6}
    for slug,meta in LANDMARKS.items():
        x,y=meta['center'];r=widths[slug]
        colliders.append({'minX':x-r,'maxX':x+r,'minZ':-y-r,'maxZ':-y+r,'minY':0,'maxY':meta['height']/4,'name':meta['name']})
    return [o for objs in groups.values() for o in objs],colliders
