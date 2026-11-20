"""Open a complete GLB in Blender, set a fixed east-door camera and render it."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--glb',type=Path,required=True);cli.add_argument('--image',type=Path,required=True)
    cli.add_argument('--native',type=Path);cli.add_argument('--report',type=Path,required=True)
    cli.add_argument('--samples',type=int,default=16)
    args=cli.parse_args(sys.argv[sys.argv.index('--')+1:])
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
    scene=bpy.context.scene;scene.unit_settings.system='METRIC'
    meshes=[o for o in scene.objects if o.type=='MESH']
    geometry=bpy.data.collections.new('Yangpu Library, complete exterior');scene.collection.children.link(geometry)
    reviewed=[]
    for obj in meshes:
        for old in list(obj.users_collection):old.objects.unlink(obj)
        geometry.objects.link(obj)
        verts=np.empty((len(obj.data.vertices),3),np.float32);obj.data.vertices.foreach_get('co',verts.reshape(-1))
        transform=np.array(obj.matrix_world);xyz=verts@transform[:3,:3].T+transform[:3,3]
        x,y,z=xyz.T;u=y+1.12
        group_masks={
            'East doors, pierced upper leaves':(x>18.59)&(x<18.86)&(abs(u)<1.29)&(z>=1.44)&(z<3.52),
            'East doors, lower panels and pulls':(x>18.59)&(x<19.03)&(abs(u)<1.29)&(z>.12)&(z<1.62),
            'East entrance, carved arch':(x>18.941)&(x<19.15)&(abs(u)<2.18)&(z>=1.26)&(z<4.09),
            'East entrance, flanking stone friezes':(x>18.941)&(x<19.10)&(abs(u)>1.37)&(abs(u)<3.05)&(z>.50)&(z<1.02)}
        if args.native:
            for name,mask in group_masks.items():
                indices=np.flatnonzero(mask).tolist()
                if indices:
                    obj.vertex_groups.new(name=name).add(indices,1.0,'REPLACE')
                    reviewed.append(dict(group=name,vertices=len(indices)))
    scene.world=bpy.data.worlds.new('Soft daylight');scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.32,.37,.43,1);bg.inputs['Strength'].default_value=.68
    bpy.ops.object.light_add(type='SUN');light=bpy.context.object;light.name='East entrance side light'
    light.rotation_euler=Vector((-.76,.52,-.75)).to_track_quat('-Z','Y').to_euler();light.data.energy=3.1;light.data.angle=.12
    bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='East door detail';target=Vector((18.97,-1.12,2.35))
    camera.location=target+Vector((12,-.36,.35));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=7.18;scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=args.samples;scene.cycles.max_bounces=3
    scene.cycles.use_adaptive_sampling=False;scene.cycles.use_denoising=bool(getattr(bpy.app.build_options,'openimagedenoise',False))
    scene.render.threads_mode='FIXED';scene.render.threads=2;scene.view_settings.view_transform='AgX'
    scene.render.resolution_x=816;scene.render.resolution_y=624;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath='//east-entry-relief.png'
    if args.native:
        args.native.parent.mkdir(parents=True,exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(args.native.resolve()),compress=True)
        bpy.ops.wm.open_mainfile(filepath=str(args.native.resolve()))
        scene=bpy.context.scene
    tris=0
    for obj in scene.objects:
        if obj.type=='MESH':obj.data.calc_loop_triangles();tris+=len(obj.data.loop_triangles)
    args.image.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(args.image.resolve())
    bpy.ops.render.render(write_still=True)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    report=dict(input_glb_sha256=sha(args.glb),input_glb=args.glb.name,blender=bpy.app.version_string,
        triangles=tris,render_sha256=sha(args.image),camera_target_enu=list(target),orthographic_width_m=7.18,
        pixels=[816,624],samples=args.samples,vertex_groups=reviewed)
    if args.native:report.update(native_sha256=sha(args.native),native_bytes=args.native.stat().st_size,reopened=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
