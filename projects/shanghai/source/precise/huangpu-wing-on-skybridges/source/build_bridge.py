"""Build and inspect the suspended north Wing On passage with Blender 4.3."""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ID = 'huangpu-wing-on-skybridges'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--assets', type=Path, required=True)
parser.add_argument('--audit', type=Path, required=True)
parser.add_argument('--lod', action='store_true')
opts = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
assets, audit = opts.assets.resolve(), opts.audit.resolve()
assets.mkdir(parents=True, exist_ok=True)
audit.mkdir(parents=True, exist_ok=True)
params = json.loads((HERE/'dimensions.json').read_text())
span, depth = params['span_m'], params['depth_m']
base, height = params['soffit_above_ground_m'], params['height_m']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene['model_id'] = ID
scene['scope'] = 'Northern upper passage over Zhejiang Middle Road, estimated from May 2025 street photograph.'
materials = {}
groups = {}


def mat(name, color, roughness=.72, metallic=0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color,1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    materials[name] = material


mat('Ochre masonry joints', (.19,.143,.105))
mat('Cream buff brick', (.37,.281,.183))
mat('Warm brown brick', (.282,.199,.128))
mat('Sandy brick', (.323,.244,.166))
mat('Weathered stone coping', (.389,.333,.245))
mat('Shaded soffit', (.115,.109,.094))
mat('Painted steel frames', (.061,.055,.048), .45, .38)
mat('Grey green glazing', (.085,.12,.13), .22, .38)
mat('Roof felt', (.148,.145,.134))
CORNERS = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]


def box(group, x, y, z, w, d, h, material):
    """Batch the separate masonry or metal pieces into per-bay editable meshes."""
    if min(w,d,h) <= 0:
        raise ValueError((group,w,d,h))
    points, faces, slots = groups.setdefault(group, ([],[],[]))
    start = len(points)
    for a,b,c in CORNERS:
        xx=x+a*w/2
        yy=y+b*d/2
        # Shear along the real attachment faces when the far wall line changes across the bridge depth.
        u = (xx/span+.5)
        xx += yy/depth*((1-u)*params.get('west_end_skew_m',0) + u*params.get('east_end_skew_m',0))
        points.append((xx,yy,base+z+c*h/2))
    faces.extend(tuple(start+i for i in face) for face in FACES)
    slots.extend([material]*len(FACES))


def panel(group, left, right, bottom, top, side, row):
    """Brick-faced spandrel or pier with a bonded, stepped face on the photographed elevation."""
    z=(bottom+top)/2
    w,h=right-left,top-bottom
    y=side*(depth/2-.115)
    box(group,(left+right)/2,y,z,w,.23,h,'Ochre masonry joints' if not opts.lod else 'Sandy brick')
    if opts.lod:
        return
    pitch_x, pitch_z = .34, .103
    count = math.ceil(h/pitch_z)
    for j in range(count):
        z0, z1 = bottom+h*j/count,bottom+h*(j+1)/count
        head = left-pitch_x*.5 if (j+row)%2 else left
        i=0
        while head<right-.001:
            a,b=max(head,left),min(head+pitch_x,right)
            if b-a>.014:
                blend = (i*13+j*7+row*3)%23
                material = 'Cream buff brick' if blend in (3,8,11,20) else 'Warm brown brick' if blend in (2,19) else 'Sandy brick'
                box(group,(a+b)/2,side*(depth/2+.003), (z0+z1)/2,b-a-.009,.009,z1-z0-.008,material)
            head+=pitch_x
            i+=1


for sign, side_name in [(1,'North'),(-1,'South estimated')]:
    xstep=span/6
    glass_w=xstep*.715
    win_h=height*.111
    floor_tops=[height*.533, height*.97]
    for bay in range(6):
        left=-span/2+bay*xstep
        mid=left+xstep/2
        opening_l,opening_r=mid-glass_w/2,mid+glass_w/2
        bx=side_name+' / bay '+str(bay+1)
        # The observed two narrow window bands sit above broad masonry panels.
        last=.16
        for floor, top in enumerate(floor_tops):
            sill=top-win_h
            panel(bx+'/spandrels',left,left+xstep,last,sill,sign,20*bay+2*floor)
            panel(bx+'/reveals',left,opening_l,sill,top,sign,20*bay+2*floor)
            panel(bx+'/reveals',opening_r,left+xstep,sill,top,sign,20*bay+2*floor)
            z=(sill+top)/2
            frame_y=sign*(depth/2-.108)
            box(bx+'/windows',mid,sign*(depth/2-.163),z,glass_w,.025,win_h,'Grey green glazing')
            for x in [opening_l+.028,opening_r-.028]:
                box(bx+'/frames',x,frame_y,z,.056,.068,win_h,'Painted steel frames')
            for zh in [sill+.029,top-.029]:
                box(bx+'/frames',mid,frame_y,zh,glass_w-.11,.068,.058,'Painted steel frames')
            if not opts.lod:
                box(bx+'/frames',mid,frame_y,z,.034,.064,win_h-.11,'Painted steel frames')
                box(bx+'/sills',mid,sign*(depth/2+.025),sill-.02,glass_w+.055,.092,.04,'Weathered stone coping')
            last=top
        panel(bx+'/head',left,left+xstep,last,height-.06,sign,37+bay)
    for seam in range(1,6):
        x=-span/2+xstep*seam
        box(side_name+' / division '+str(seam),x,sign*(depth/2+.017),height*.503,.10,.043,height*.96,'Cream buff brick')

# The modeled passage hangs between masonry walls. There are no supports in the street.
box('Suspended deck / underside',0,0,.105,span,depth,.21,'Shaded soffit')
box('Roof / closed slab',0,0,height-.06,span,depth,.12,'Roof felt')
box('Roof / coping',0,0,height+.015,span+.055,depth+.095,.065,'Weathered stone coping')
for side in (-1,1):
    box('Deck / edge trim',0,side*(depth/2-.045),.13,span,.11,.18,'Shaded soffit')
    box('Attachment interfaces',side*(span/2-.07),0,height/2,.14,depth-.01,height-.10,'Ochre masonry joints')


def build_objects():
    for name,(vertices,faces,slots) in groups.items():
        mesh=bpy.data.meshes.new(name)
        mesh.from_pydata(vertices,[],faces)
        unique=list(dict.fromkeys(slots))
        for key in unique:
            mesh.materials.append(materials[key])
        mesh.polygons.foreach_set('material_index',[unique.index(key) for key in slots])
        mesh.update()
        obj=bpy.data.objects.new(name,mesh)
        scene.collection.objects.link(obj)


build_objects()
mesh_count=len(groups)
if opts.lod:
    filename=assets/(ID+'-lod-unpacked.glb')
else:
    filename=assets/(ID+'-raw.glb')
bpy.ops.export_scene.gltf(filepath=str(filename),export_format='GLB',export_extras=True,export_yup=True)
if not opts.lod:
    camera_data=bpy.data.cameras.new('North elevation')
    cam=bpy.data.objects.new('North elevation',camera_data)
    scene.collection.objects.link(cam)
    scene.camera=cam
    target=Vector((0,0,base+height*.49))
    cam.location=target+Vector((-.19*span,1.65*span,-.22*height))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO'
    cam.data.ortho_scale=max(span*1.23,height*1.9)
    scene.world=bpy.data.worlds.new('Sky')
    scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value=(.42,.49,.57,1)
    bg.inputs['Strength'].default_value=.65
    light=bpy.data.lights.new('Daylight','SUN')
    sun=bpy.data.objects.new('Daylight',light)
    scene.collection.objects.link(sun)
    light.energy=3.0
    sun.rotation_euler=Vector((.4,-.8,-1)).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='CYCLES'
    scene.cycles.samples=16
    scene.cycles.use_denoising=False
    scene.render.resolution_x,scene.render.resolution_y=1050,720
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    scene.render.filepath='//north-elevation.png'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
    native=assets/(ID+'.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(native))
    reopened=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(reopened)==mesh_count
    bpy.context.scene.render.filepath=str(audit/'north-elevation.png')
    bpy.ops.render.render(write_still=True)
    print('Reopened',len(reopened),'editable groups')
