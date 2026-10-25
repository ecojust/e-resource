"""Validate GLB mesh bounds/indices and native ray depths at key facade points.
Run with Blender, from any working directory.
"""
import bpy,json,struct,math,sys,argparse
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,default=ROOT);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);ROOT=args.directory
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'chartered-bank.blend'))
source=json.loads((ROOT/'building-source.json').read_text());metadata=json.loads((ROOT/'metadata.json').read_text());ends=source['streetfront']['candidate_edges'][0]['endpoints_local_east_north_m'];A=Vector(ends[0]);B=Vector(ends[1]);T=(B-A).normalized();N=Vector((-T.y,T.x));C=(A+B)/2

def point(x,y,z):return Vector((C.x+T.x*x+N.x*y,C.y+T.y*x+N.y*y,z))
results=[]
for label,x,z in [('portico_glass',-4.22,10.02),('round_column',-2.21,10.02),('stone_pier',-8.1,10.02),('side_french_window',-10.64+.17,10.02)]:
 hit,loc,normal,index,obj,matrix=bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),point(x,-8,z),Vector((N.x,N.y,0)),distance=12)
 assert hit,label
 depth=(Vector((loc.x,loc.y))-C).dot(N)
 results.append({'point':label,'hit_mesh':obj.name,'depth_from_facade_plane_m':round(depth,4)})
by={r['point']:r for r in results};assert by['portico_glass']['depth_from_facade_plane_m']>.9;assert by['round_column']['depth_from_facade_plane_m']<-.40;assert abs(by['stone_pier']['depth_from_facade_plane_m'])<.05;assert by['side_french_window']['depth_from_facade_plane_m']>.25
raw=(ROOT/'chartered-bank.glb').read_bytes();magic,version,total=struct.unpack_from('<III',raw,0);assert magic==0x46546c67 and version==2 and total==len(raw)
n,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n]);mins=[1e9]*3;maxs=[-1e9]*3;triangles=0
for mesh in doc['meshes']:
 for primitive in mesh['primitives']:
  pos=doc['accessors'][primitive['attributes']['POSITION']];index=doc['accessors'][primitive['indices']];triangles+=index['count']//3
  assert all(math.isfinite(v) for v in pos['min']+pos['max'])
  for k in range(3):mins[k]=min(mins[k],pos['min'][k]);maxs[k]=max(maxs[k],pos['max'][k])
assert abs(mins[1])<.001 and abs(maxs[1]-34.45)<.01
assert triangles<300000 and len(raw)<100_000_000 and not doc.get('images')
report={'passed':True,'triangles':triangles,'glb_bytes':len(raw),'native_bytes':(ROOT/'chartered-bank.blend').stat().st_size,'ground_y':mins[1],'max_y':maxs[1],'bounds':[mins,maxs],'embedded_photo_textures':0,'facade_ray_depths':results,'geometry_proves_actual_recesses_and_protruding_columns':True}
(ROOT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report))
# Store practical CPU render defaults without changing any model mesh.
s=bpy.context.scene;s.cycles.samples=12;s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.12;s.camera=bpy.data.objects['Camera_three_quarter'];bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'chartered-bank.blend'))
