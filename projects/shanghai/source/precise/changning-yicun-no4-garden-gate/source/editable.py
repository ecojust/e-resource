"""Build or independently reopen the editable Blender model.

blender -b -t 1 -P editable.py -- build RAW.glb EDITABLE.blend cameras.json
blender -b -t 1 -P editable.py -- check EDITABLE.blend checks.json
"""
from pathlib import Path
import sys,json,math
import bpy
from mathutils import Vector,Matrix

def orient(cam, pose):
    eye=Vector(pose['eye']); target=Vector(pose['target'])
    f=(target-eye).normalized();up=Vector(pose.get('world_up',[0,0,1]))
    right=f.cross(up).normalized();true_up=right.cross(f).normalized()
    cam.rotation_euler=Matrix((right,true_up,-f)).transposed().to_euler()
    cam.location=eye
    cam.data.lens=36*(target-eye).length/pose['width_m']
    cam.data.sensor_fit='HORIZONTAL'
    cam.data.sensor_width=36
    w,h=pose['width'],pose['height']
    cx,cy=pose.get('principal_point_edge_px',[w/2,h/2])
    cam.data.shift_x=(w/2-cx)/w;cam.data.shift_y=(cy-h/2)/w

def create(raw,out,poses):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(raw),import_pack_images=True,merge_vertices=True)
    scene=bpy.context.scene
    meshes=[o for o in scene.objects if o.type=='MESH']
    for prefix,label in [('00','Threshold'),('01','Gateposts'),('02','Double iron leaves'),('03','Lane walls'),('04','Number 4'),('1','House gable, vents and windows')]:
        group=bpy.data.collections.new(label);scene.collection.children.link(group)
        for obj in meshes:
            if obj.name.startswith(prefix):
                for old in list(obj.users_collection):old.objects.unlink(obj)
                group.objects.link(obj)
    group=bpy.data.collections.new('06 Documented views and detail cameras');scene.collection.children.link(group)
    for pose in json.loads(poses.read_bytes()):
        data=bpy.data.cameras.new(pose['label']);cam=bpy.data.objects.new(pose['name'],data);group.objects.link(cam)
        orient(cam,pose)
        if pose['name']=='overview':scene.camera=cam
    world=bpy.data.worlds.new('Studio daylight');scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.71,.78,.83,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.58
    light=bpy.data.lights.new('Low garden sunlight','SUN');light.energy=3.15;light.angle=math.radians(12)
    sun=bpy.data.objects.new('Low garden sunlight',light);scene.collection.objects.link(sun)
    sun.rotation_euler=Vector((.8,.7,-1.25)).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='CYCLES';scene.cycles.samples=4;scene.cycles.use_denoising=False;scene.render.resolution_x=640;scene.render.resolution_y=512;scene.render.resolution_percentage=100
    scene['identity']='贺绿汀旧居院门及可见山墙，泰安路76弄4号；院深和绝对尺度为摄影工作值。'
    scene['source_mesh']=raw.name
    scene.unit_settings.system='METRIC'
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.color_type='MATERIAL'
    for image in bpy.data.images:
        if image.type=='IMAGE' and not image.packed_file:image.pack()
    bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)

def verify(path,out):
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
    scene=bpy.context.scene
    objs=[o for o in scene.objects if o.type=='MESH']
    for obj in objs:obj.data.calc_loop_triangles()
    cams=[c for c in scene.objects if c.type=='CAMERA'];textures=[x for x in bpy.data.images if x.packed_file]
    mats=[m.name for m in bpy.data.materials if m.users]
    tri=sum(len(o.data.loop_triangles) for o in objs);uv=sum(len(o.data.uv_layers.active.data) for o in objs)
    expected=json.loads((path.parent/'mesh-build.json').read_bytes())['raw']
    assert len(objs)==expected['editable_mesh_groups'] and tri==expected['triangles']
    assert len(cams)==9 and len(textures)==5 and sorted(tuple(tex.size) for tex in textures)==[(96,96)]*4+[(256,256)]
    assert all(o.data.uv_layers.active for o in objs) and uv==3*tri
    assert scene.camera and scene.camera.name=='overview'
    report=dict(passed=True,mesh_groups=len(objs),triangles=tri,uv_loops=uv,materials=mats,
        embedded_images={im.name:list(im.size) for im in textures},cameras=[c.name for c in cams],
        sections={col.name:len(col.objects) for col in scene.collection.children if col.objects})
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    op,*args=sys.argv[sys.argv.index('--')+1:]
    (create if op=='build' else verify)(*(Path(a).resolve() for a in args))
