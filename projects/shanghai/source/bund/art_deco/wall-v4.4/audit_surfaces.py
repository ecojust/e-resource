import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from arguments import workdir
P=workdir()
for bid in ['bund19','bund20','bund23']:
 out=P/'candidate'/bid;report=json.loads((out/'audit.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(out/f'{bid}.blend'));mesh=bpy.data.objects['Conformal structural walls — source panel union'].data
 offset=0;rows=[]
 for g in report['wall_groups']:
  faces=list(mesh.polygons)[offset:offset+g['optimized_faces']];offset+=g['optimized_faces'];a=Vector(g['frame_a']);n=Vector(g['n']);u=Vector(g['u']);expected=g['front_exposed_area_by_depth'];areas=[0.]*len(expected);max_depth_error=0.;other_front=0
  for face in faces:
   if face.normal.dot(n.normalized())<.999:continue
   ds=[(mesh.vertices[i].co-a).dot(n)/n.length_squared for i in face.vertices];d=sum(ds)/len(ds);which=min(range(len(expected)),key=lambda i:abs(expected[i]['depth_from_frame_m']-d));error=max(abs(v-expected[which]['depth_from_frame_m'])for v in ds);max_depth_error=max(max_depth_error,error);assert error<3e-5,(bid,g['group'],error);areas[which]+=face.area
  diffs=[abs(area-item['front_area_m2']*u.length)for area,item in zip(areas,expected)]
  assert all(diff<max(3e-4,ex['front_area_m2']*1e-5)for diff,ex in zip(diffs,expected)),(bid,g['group'],diffs,expected,areas)
  rows.append({'group':g['group'],'depths_m':[x['depth_from_frame_m']for x in expected],'actual_front_areas_m2':areas,'maximum_front_area_difference_m2':max(diffs,default=0),'maximum_vertex_depth_difference_m':max_depth_error})
 assert offset==len(mesh.polygons)
 result={'id':bid,'status':'pass','basis':'Read final saved native wall mesh, independently group faces by original group offsets and measure normal-facing area at each retained depth plane.','groups':rows,'maximum_front_area_difference_m2':max(x['maximum_front_area_difference_m2']for x in rows),'maximum_vertex_depth_difference_m':max(x['maximum_vertex_depth_difference_m']for x in rows)}
 (out/'optimized-surface-audit.json').write_text(json.dumps(result,indent=2));print('SURFACE_AUDIT',bid,result['maximum_front_area_difference_m2'],result['maximum_vertex_depth_difference_m'])
