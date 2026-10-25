import bpy, math, sys, os, json
from mathutils import Vector
from math import sin, cos, pi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('SEAL_OUTPUT_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'imperial_jade_seal'))
os.makedirs(OUT, exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in bpy.data.materials: bpy.data.materials.remove(d)

def material(name, color, roughness=.3, metallic=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=roughness; p.inputs['Metallic'].default_value=metallic
    return m
jade=material('青白玉 · Nephrite with mineral clouds',(.22,.49,.36),.25)
n=jade.node_tree.nodes; l=jade.node_tree.links; p=n.get('Principled BSDF')
p.inputs['Subsurface Weight'].default_value=.065
p.inputs['Subsurface Radius'].default_value=(.35,.6,.25)
p.inputs['Coat Weight'].default_value=.28; p.inputs['Coat Roughness'].default_value=.23
tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=1.45; tex.inputs['Detail'].default_value=4; tex.inputs['Roughness'].default_value=.7
coord=n.new('ShaderNodeTexCoord'); l.new(coord.outputs['Generated'],tex.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
for i,(pos,col) in enumerate([(0.18,(.075,.21,.15,1)),(.43,(.22,.43,.30,1)),(.63,(.46,.64,.48,1)),(.82,(.72,.79,.59,1))]):
    e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(pos); e.position=pos;e.color=col
l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
fine=n.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value=125;fine.inputs['Detail'].default_value=2
l.new(coord.outputs['Generated'],fine.inputs['Vector']); bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.1;bump.inputs['Distance'].default_value=.018
l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
darkjade=material('雕刻凹处 · Deep nephrite',(.10,.25,.17),.3)
gold=material('补角 · Aged gold',(.64,.35,.095),.28,.82)

def assign(o,m):
    o.data.materials.append(m)
    if o.type=='MESH':
        for f in o.data.polygons:f.use_smooth=True
    return o

def cube(name,loc,scale,mat,bevel=.05):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,mat)
    if bevel:
        mod=o.modifiers.new('手工磨圆 · softened edges','BEVEL');mod.width=bevel;mod.segments=4
        mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o

def curve(name,pts,radius,mat,cyclic=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=16;c.bevel_depth=radius;c.bevel_resolution=3
    s=c.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
    for b,pt in zip(s.bezier_points,pts): b.co=pt;b.handle_left_type='AUTO';b.handle_right_type='AUTO'

    if cyclic or name.startswith('雷纹'):
        for b in s.bezier_points:b.handle_left_type='VECTOR';b.handle_right_type='VECTOR'
    s.use_cyclic_u=cyclic;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);assign(o,mat);return o

def ellipsoid(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;assign(o,mat);return o

base=cube('玉玺本体 · 96 mm square', (0,0,1.1),(6.4,6.4,2.2),jade,.13)
# Apply base bevel before engraved boolean cuts.
bpy.context.view_layer.objects.active=base
for mod in list(base.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
# Thin shoulder and foot molding, carved in the same jade.
for z,w,r in [(.22,3.12,.045),(1.91,3.14,.045),(2.17,3.02,.032)]:
    curve('玉边线 · perimeter molding', [(-w,-w,z),(w,-w,z),(w,w,z),(-w,w,z)],r,jade,True)
# Repeating angular cloud / thunder fret on the upper shoulder.
for side in range(4):
    a=side*pi/2
    def sidept(u,z,depth=3.205):return (u*cos(a)-(-depth)*sin(a),u*sin(a)+(-depth)*cos(a),z)
    for k in range(8):
        u=-2.73+k*.73
        shape=[(u,1.60),(u,1.82),(u+.48,1.82),(u+.48,1.49),(u+.15,1.49),(u+.15,1.69),(u+.33,1.69)]
        curve('雷纹 · carved shoulder fret',[sidept(x,z) for x,z in shape],.022,jade)
    # Four long, fluid cloud scrolls on each face.
    for k in range(4):
        u=-2.22+k*1.48
        pts=[]
        for j in range(25):
            t=j/24; ang=-.75*pi+t*2.05*pi;r=.42*(1-t)+.07
            pts.append(sidept(u+r*cos(ang),.98+r*sin(ang)))
        curve('云气纹 · cloud relief',pts,.038,jade)
        curve('云气流线', [sidept(u-.47,.65),sidept(u-.16,.62),sidept(u+.28,.83),sidept(u+.58,.80)],.025,jade)
# Discreet irregular gold repair at one front corner, traditional visual allusion.
verts=[(2.66,-3.209,.07),(3.12,-3.209,.07),(3.20,-3.12,.07),(3.209,-2.59,.07),
       (2.70,-3.209,.83),(3.12,-3.209,1.06),(3.20,-3.12,.96),(3.209,-2.59,.64)]
mesh=bpy.data.meshes.new('gold repair mesh');mesh.from_pydata(verts,[],[(0,1,5,4),(1,2,6,5),(2,3,7,6)]);mesh.update()
o=bpy.data.objects.new('金镶残角 · gold repair',mesh);bpy.context.collection.objects.link(o);assign(o,gold)
sol=o.modifiers.new('gold foil thickness','SOLIDIFY');sol.thickness=.035
bev=o.modifiers.new('gold softened lip','BEVEL');bev.width=.035;bev.segments=3

# Continuous coiled dragon body, tapered from the tail to the neck.
centers=[];radii=[]
for i in range(145):
    t=i/144;a=-.65*pi+t*2.35*pi;r=2.40-1.35*t
    centers.append(Vector((r*cos(a),r*sin(a),2.40+.75*t)))
    radii.append(.06+.47*min(1,t*5))
centers.extend([Vector((.62,-.52,3.27)),Vector((.62,-.05,3.48)),Vector((.32,.25,3.75)),Vector((0,.15,3.91))]);radii.extend([.52,.51,.47,.44])
verts=[];faces=[];frames=[];rings=24
for i,c in enumerate(centers):
    t=(centers[min(i+1,len(centers)-1)]-centers[max(0,i-1)]).normalized();b=t.cross(Vector((0,0,1))).normalized();n=b.cross(t).normalized();frames.append((t,b,n))
    for j in range(rings):
        a=2*pi*j/rings;verts.append(c+radii[i]*(b*cos(a)+n*sin(a)))
for i in range(len(centers)-1):
    for j in range(rings):a=i*rings+j;bb=i*rings+(j+1)%rings;faces.append((a,bb,bb+rings,a+rings))
faces.extend([tuple(reversed(range(rings))),tuple((len(centers)-1)*rings+j for j in range(rings))])
me=bpy.data.meshes.new('continuous coiled body');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('盘龙 · continuous coiled body',me);bpy.context.collection.objects.link(o);assign(o,jade)
sub=o.modifiers.new('polished body','SUBSURF');sub.levels=1
# Low relief overlapping lozenge scales, a single mesh.
sv=[];sf=[]
for i in range(17,len(centers)-4,3):
    c=centers[i];t,b,n=frames[i];r=radii[i]
    for j in range(7):
        a=.15+(pi-.30)*j/6
        outward=(b*cos(a)+n*sin(a));across=(-b*sin(a)+n*cos(a));origin=c+outward*(r*.97)
        length=.15;width=.135
        poly=[origin-t*length,origin+across*width,origin+t*length,origin-across*width,origin+outward*.048-t*.018]
        idx=len(sv);sv.extend(poly);sf.extend([(idx,idx+1,idx+4),(idx+1,idx+2,idx+4),(idx+2,idx+3,idx+4),(idx+3,idx,idx+4)])
me=bpy.data.meshes.new('carved diamond scales');me.from_pydata(sv,[],sf);me.update();o=bpy.data.objects.new('龙鳞 · overlapping carved scales',me);bpy.context.collection.objects.link(o);assign(o,jade)
bev=o.modifiers.new('rounded scales','BEVEL');bev.width=.024;bev.segments=2
# Dorsal scallops along upper spiral.
for i in range(26,141,6):
    c=centers[i];t,b,n=frames[i];r=radii[i]
    curve('背鳍 · scalloped ridge',[c+n*r-t*.15,c+n*(r+.20)-t*.08,c+n*(r+.12)+t*.10,c+n*r+t*.16],.055,jade)
# Four feet grasping the shoulder, with curled tapering toes.
for side in [-1,1]:
    for back in [False,True]:
        y=.85 if back else -1.36
        pts=[(side*1.30,y+.28,2.84),(side*1.89,y+.03,2.59),(side*2.18,y-.33,2.30)]
        curve('龙足 · muscular foreleg',pts,.17,jade)
        ellipsoid('掌',pts[-1],(.28,.26,.13),jade)
        for j in range(3):
            x=side*(2.01+j*.18);yy=y-.38
            curve('龙爪 · curled toe',[(x,yy,2.30),(x+side*.11,yy-.24,2.27),(x+side*.04,yy-.36,2.25)],.062,jade)
from dragon_head import build_head
build_head(jade,darkjade,gold)
from seal_inscription import add_inscription
add_inscription(base,jade)
base.modifiers.new('Engraved surface normals','WEIGHTED_NORMAL')
# Convert curves to meshes for consistent native and GLB geometry.
bpy.ops.object.select_all(action='SELECT')
bpy.context.view_layer.objects.active=base
bpy.ops.object.convert(target='MESH')
# Object organization: artifact is isolated from all studio objects.
artifact=bpy.data.collections.new('01 · 玉玺 / ARTIFACT');bpy.context.scene.collection.children.link(artifact)
for o in list(bpy.context.scene.objects):
    for c in list(o.users_collection):c.objects.unlink(o)
    artifact.objects.link(o)
# Ground and plinth.
studio=bpy.data.collections.new('02 · 展台与灯光 / STUDIO');bpy.context.scene.collection.children.link(studio)
def studio_obj(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    studio.objects.link(o);return o
charcoal=material('Charcoal display stone',(.026,.032,.031),.42)
metal=material('Plinth bronze edge',(.24,.17,.08),.35,.65)
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=5.15,depth=.38,location=(0,0,-.19));plinth=studio_obj(bpy.context.object);plinth.name='Museum plinth';assign(plinth,charcoal)
bev=plinth.modifiers.new('soft edge','BEVEL');bev.width=.09;bev.segments=4;plinth.modifiers.new('normals','WEIGHTED_NORMAL')
bpy.ops.mesh.primitive_torus_add(major_radius=5.07,minor_radius=.022,major_segments=128,minor_segments=12,location=(0,0,-.20));studio_obj(assign(bpy.context.object,metal))
floor=studio_obj(cube('Studio floor',(0,0,-.54),(200,200,.1),material('Backdrop',(.018,.025,.025),.5),0))

def area(name,loc,power,color,size,target=(0,0,2)):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    o=bpy.data.objects.new(name,data);studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Key · warm silk', (1,-7,10),1500,(1,.90,.73),7)
area('Fill · cool silk',(-7,-3,5),1000,(.65,.82,1),6)
area('Rim · jade translucency',(3,5,8),1900,(.85,1,.90),5)
area('Front softbox',(2,-9,3),350,(1,1,1),4)
scene=bpy.context.scene
scene.world.color=(.16,.16,.16);scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.16,.16,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
bpy.ops.object.camera_add(location=(10,-15,10));cam=studio_obj(bpy.context.object);cam.name='CAMERA · hero';cam.rotation_euler=(Vector((0,0,2.0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=13.3;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=False;scene.cycles.max_bounces=6
scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.015
scene['说明']='传国玉玺艺术复原；非考古实物复刻。盘龙钮、青白玉、金补角；底部阴刻反字，印文为受命於天／既壽永昌。'
scene['Design']='Artistic reconstruction, not an authenticated historical replica. 96 mm square base.'
# Make it immediately usable in Blender.
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA'
            a.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT');base.select_set(True);bpy.context.view_layer.objects.active=base
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/imperial_jade_seal.blend')
# Export only the sculpture, with all modifiers applied by exporter.
bpy.ops.object.select_all(action='DESELECT')
for o in artifact.objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT+'/imperial_jade_seal.glb',export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
from fix_glb_scale import scale_glb
scale_glb(OUT+'/imperial_jade_seal.glb')
scene.render.filepath=OUT+'/preview.png';bpy.ops.render.render(write_still=True)
# Bottom view: the physically engraved, mirrored printing face.
for o in studio.objects:
    if o.type=='MESH':o.hide_render=True
cam.location=(0,0,-13);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=7.9
area('Bottom key',(-3,-4,-7),1100,(1,.92,.8),5,target=(0,0,0))
area('Bottom fill',(3,2,-5),700,(.75,.9,1),4,target=(0,0,0))
scene.cycles.samples=32
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.filepath=OUT+'/underside.png';bpy.ops.render.render(write_still=True)
print('COMPLETE',OUT)
