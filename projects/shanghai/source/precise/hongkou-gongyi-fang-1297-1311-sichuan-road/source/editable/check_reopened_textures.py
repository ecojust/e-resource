"""Independently compare the reopened project to its surface and camera definitions."""
from pathlib import Path
import bpy,json,sys
source=Path(__file__).parent;sys.path.insert(0,str(source))
from surface_textures import check_or_apply,check_glass,fitted_cameras
blend,raw,output=map(Path,sys.argv[sys.argv.index('--')+1:])
report=json.loads(output.read_bytes());assert report['match_raw'] and Path(bpy.data.filepath).samefile(blend)
scene=bpy.context.scene
report['packed_procedural_materials']=check_or_apply(scene,raw,False)
report['screen_glass']=check_glass(scene,raw,False)
report['authored_cameras']=fitted_cameras(scene,json.loads(scene['gongyi_camera_views']),False)
report['source_names']=[o['source_name'] for o in scene.objects if o.type=='MESH']
assert len(report['source_names'])==len(set(report['source_names']))==472
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
