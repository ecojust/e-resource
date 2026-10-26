#!/usr/bin/env python3
"""Actual pane bottom/upper frame horizontal seating, excluding side slivers.

This supplements finite local-contact witnesses with a meaningful finite-area
horizontal joint. No author imports, no geometry repair, no relaxed air-gap rule.
"""
import argparse,json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from finite_checks import ray_intervals,polygons
from modern_mesh import load_raw,filemeta,require,oriented_position_hash

def horizontal_faces(part,sign):
 result=[]
 for index,q in enumerate(part.triangles_enu):
  cross=np.cross(q[1]-q[0],q[2]-q[0]);length=np.linalg.norm(cross)
  if sign*cross[2]/length<1-1e-12 or np.ptp(q[:,2])>1e-9:continue
  result.append((index,Polygon(q[:,:2]),float(q[:,2].mean())))
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--structure',type=Path,required=True);ap.add_argument('--requests',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 require(not a.output.exists(),'Immutable output already exists');asset=load_raw(a.raw);proof=json.loads(a.structure.read_bytes());requests=json.loads(a.requests.read_bytes())
 require(proof['structure_passed'] is True and proof['asset_identity']['raw']['sha256']==asset.identity['raw']['sha256'],'No bound actual closed structure')
 base={r['key']:r for r in proof['part_results']}
 require(all(oriented_position_hash(p.triangles_enu)==base[p.key]['oriented_position_triangles_sha256'] for p in asset.parts),'Actual position proof mismatch')
 rows=[];minimum_area=1e-5
 for question in requests['checks']:
  require(question['kind']=='support_each' and len(question['right_selectors'])==1,'Expected per-window pane/frame question')
  frames=asset.select(question['right_selectors'][0]);require(len(frames)==1,'One physical frame required');frame=frames[0];tops=horizontal_faces(frame,1)
  for selector in question['left_selectors']:
   pane=asset.select(selector)[0];candidates=[];rejected=0
   for gi,gpoly,gz in horizontal_faces(pane,-1):
    for fi,fpoly,fz in tops:
     if abs(gz-fz)>1e-9:continue
     for joint in polygons(gpoly.intersection(fpoly)):
      if joint.area<minimum_area:continue
      point=joint.representative_point();uv=[point.x,point.y]
      glass=ray_intervals(pane.triangles_enu,uv);metal=ray_intervals(frame.triangles_enu,uv)
      if glass['state']!='valid' or metal['state']!='valid':rejected+=1;continue
      intervals=[(g,f) for g in glass['intervals_m'] for f in metal['intervals_m']
                 if abs(g[0]-gz)<=1e-9 and abs(f[1]-fz)<=1e-9 and g[1]-g[0]>1e-4 and f[1]-f[0]>1e-4]
      if not intervals:rejected+=1;continue
      g,f=intervals[0];candidates.append({'pane_triangle_index':gi,'frame_triangle_index':fi,
       'joint_area_m2':joint.area,'witness_uv_m':uv,'pane_actual_interval_m':g,'frame_actual_interval_m':f,
       'actual_endpoint_separation_m':g[0]-f[1],'actual_horizontal_face_height_m':gz,
       'cell_vertex_plane_separation_m':gz-fz})
   candidates.sort(key=lambda x:x['joint_area_m2'],reverse=True)
   rows.append({'pane_key':pane.key,'frame_key':frame.key,'passed':bool(candidates),
     'qualifying_cell_count':len(candidates),'rejected_actual_interval_witnesses':rejected,
     'largest_actual_joint_witness':candidates[0] if candidates else None})
 require(rows,'No panes audited')
 report={'schema':'modern-actual-horizontal-pane-seating-v1','horizontal_seating_passed':all(r['passed'] for r in rows),
  'asset_identity':asset.identity,'source_structure_report':filemeta(a.structure),'requests_file':filemeta(a.requests),
  'minimum_actual_cell_area_m2':minimum_area,'maximum_opposite_plane_separation_m':1e-9,
  'pane_count':len(rows),'window_question_count':len(requests['checks']),'pane_results':rows,
  'checker_files':[filemeta(__file__),filemeta(Path(__file__).parent/'modern_mesh.py'),filemeta(Path(__file__).parent/'finite_checks.py')],
  'scope':'Each actual pane has a horizontal bottom-face to frame upward-face positive-area joint with actual matching single-solid interval endpoints. Side-face slivers do not count. This proves a finite local seat, not whole-perimeter sealing, full bearing coverage or structural safety.',
  'model_appearance_accepted':False}
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':filemeta(a.output),'passed':report['horizontal_seating_passed'],'panes':len(rows),'failed':sum(not r['passed'] for r in rows)}));raise SystemExit(0 if report['horizontal_seating_passed'] else 1)

if __name__=='__main__':main()
