"""Read camera framing, material assignments and exact packed finishes from the saved Blender file."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
source=Path(__file__).resolve().parent
sys.path.insert(0,str(source))
from native_layout import CAMERAS,MAIN,MATERIALS,UV_NAME,uv_for_face

blend,raw,output=map(Path,sys.argv[sys.argv.index('--')+1:])
assert Path(bpy.data.filepath).resolve()==blend.resolve()
report=json.loads(output.read_bytes());assert report['match_raw']
scene=bpy.context.scene
textures={}
for material,(file,label) in MATERIALS.items():
    graph=bpy.data.materials[material].node_tree;node=graph.nodes[label]
    links=graph.nodes['Principled BSDF'].inputs['Base Color'].links
    assert len(links)==1 and links[0].from_node==node and node.extension=='EXTEND'
    png=(source/file).read_bytes()
    assert node.image.packed_file and bytes(node.image.packed_file.data)==png
    assert tuple(node.image.size)==struct.unpack_from('>II',png,16) and node.image.colorspace_settings.name=='sRGB'
    textures[material]=dict(file=file,packed_sha256=sha256(png).hexdigest(),dimensions=list(node.image.size),uv_corners=0,maximum_error=0.)
assert {c.name for c in scene.objects if c.type=='CAMERA'}==set(CAMERAS) and scene.camera.name==MAIN
for name,(eye,target,scale) in CAMERAS.items():
    cam=scene.objects[name]
    assert cam.data.type=='ORTHO' and abs(cam.data.ortho_scale-scale)<1e-5
    assert (cam.location-Vector(eye)).length<1e-5
    direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1))
    assert direction.dot((Vector(target)-cam.location).normalized())>.999999
groups={};corners=[]
for obj in (o for o in scene.objects if o.type=='MESH'):
    mesh=obj.data
    groups[obj.name]=Counter(mesh.materials[f.material_index].name for f in mesh.polygons)
    corners.extend(world_to_camera_view(scene,scene.camera,obj.matrix_world@Vector(v)) for v in obj.bound_box)
    for face in mesh.polygons:
        material=mesh.materials[face.material_index].name
        if material not in MATERIALS:continue
        layer=mesh.uv_layers.active
        assert layer.name==UV_NAME and layer.active_render
        pts=[mesh.vertices[mesh.loops[i].vertex_index].co for i in face.loop_indices]
        data=textures[material]
        for i,uv in zip(face.loop_indices,uv_for_face(material,pts,obj.name)):
            actual=layer.data[i].uv
            data['maximum_error']=max(data['maximum_error'],abs(actual.x-uv[0]),abs(actual.y-uv[1]))
            data['uv_corners']+=1
assert min(p.z for p in corners)>0
frame=[min(p.x for p in corners),min(p.y for p in corners),max(p.x for p in corners),max(p.y for p in corners)]
assert min(frame[:2])>.01 and max(frame[2:])<.99,frame
assert all(v['uv_corners']>0 and v['maximum_error']<4e-6 for v in textures.values())
schedule=json.dumps(groups,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
report['guandu_reopened']=dict(raw_sha256=sha256(raw.read_bytes()).hexdigest(),textures=textures,
   material_face_schedule_sha256=sha256(schedule).hexdigest(),editable_groups=len(groups),whole_frame=frame,
   active_camera=MAIN,orthographic_cameras=CAMERAS)
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
