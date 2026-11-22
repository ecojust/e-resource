"""Check the saved camera after the ordinary Blender geometry verifier has reopened the file."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
scene=bpy.context.scene
cam=scene.camera
assert cam.name=='Yaxiya Li four-window dormer' and cam.location.y<0
groups=[o for o in scene.objects if o.type=='MESH'];expected=json.loads((Path(__file__).parent/'geometry-ready.json').read_bytes());assert len(groups)==expected['group_count']
corners=[world_to_camera_view(scene,cam,obj.matrix_world@Vector(pt)) for obj in groups for pt in obj.bound_box]
assert all(0<=pt.x<=1 and 0<=pt.y<=1 and pt.z>0 for pt in corners)
out=Path(sys.argv[-1]);results=json.loads(out.read_bytes())
results['street_view']={'camera':cam.name,'all_group_bounds_in_frame':True,'mesh_count':len(groups),'center_height':cam.location.z}
out.write_text(json.dumps(results,indent=2)+'\n')
