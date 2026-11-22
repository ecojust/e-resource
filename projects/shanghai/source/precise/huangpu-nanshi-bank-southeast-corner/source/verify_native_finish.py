"""Inspect every edited group, the 3D component labels and the real cameras after reopening."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import sys
import struct

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from native_layout import ALIASES, CAMERAS, MAIN, SCHEDULE_SHA256, schedule_hash

blend,raw,output=map(Path,sys.argv[sys.argv.index('--')+1:])
scene=bpy.context.scene
assert Path(bpy.data.filepath).resolve()==blend.resolve()
raw_data=raw.read_bytes()
raw_sha256=sha256(raw_data).hexdigest()
gltf=json.loads(raw_data[20:20+struct.unpack_from('<I',raw_data,12)[0]])
meta=gltf['extras']
assert scene['copyright']==gltf['asset']['copyright']==meta['copyright']
assert scene['geometry_license']==meta['geometry_license'] and 'CC BY-SA 4.0' in scene['geometry_license']
art,=meta['third_party_materials']
assert scene['relief_source_url']==art['url'] and scene['relief_license_url']==art['license_url']
assert scene['relief_changes']==art['modifications']
meshes=[o for o in scene.objects if o.type=='MESH']
groups={}
edge=[]
for obj in meshes:
    label=obj['source_component']
    assert label not in groups and obj.name==ALIASES.get(label,label)
    groups[label]=Counter(obj.data.materials[p.material_index].name for p in obj.data.polygons)
    edge.extend(world_to_camera_view(scene,scene.camera,obj.matrix_world@Vector(point))
                for point in obj.bound_box)
assert schedule_hash(groups)==SCHEDULE_SHA256
assert scene.camera.name==MAIN and {o.name for o in scene.objects if o.type=='CAMERA'}==set(CAMERAS)
for name,(eye,target,scale) in CAMERAS.items():
    camera=scene.objects[name]
    aim=Vector(target)-camera.location
    direction=camera.matrix_world.to_quaternion()@Vector((0,0,-1))
    assert camera.data.type=='ORTHO' and abs(camera.data.ortho_scale-scale)<1e-5
    assert (camera.location-Vector(eye)).length<1e-5 and direction.dot(aim.normalized())>.999999
assert min(p.z for p in edge)>0
bounds=[min(p.x for p in edge),min(p.y for p in edge),max(p.x for p in edge),max(p.y for p in edge)]
assert bounds[0]>.015 and bounds[1]>.015 and bounds[2]<.985 and bounds[3]<.985,bounds
report=json.loads(output.read_bytes())
assert report['match_raw'] and (report['triangles'],report['mesh_count'],report['materials'])==(61641,196,16)
report['nanshi_reopened']={'group_material_faces_sha256':SCHEDULE_SHA256,'source_groups':len(groups),'reopened_raw_sha256':raw_sha256,
    'source_names_preserved':ALIASES,'material_face_counts':groups,'copyright':scene['copyright'],'geometry_license':scene['geometry_license'],'active_camera':MAIN,
    'whole_model_frame_xy':bounds,'image_size':[scene.render.resolution_x,scene.render.resolution_y],
    'orthographic_cameras':{name:{'eye':eye,'target':target,'scale':scale} for name,(eye,target,scale) in CAMERAS.items()}}
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
