#!/usr/bin/env python3
"""Write source-derived finite audit questions, never actual-geometry results."""
from pathlib import Path
import hashlib,json,math
import numpy as np
from build_model import Museum
from solids import subpath,path_data
HERE=Path(__file__).resolve().parent

def main():
 m=Museum();slots=[];length=m.spine_line.length;w=m.e['north_spine_slot_width_m']
 for i,f in enumerate(m.e['north_spine_slots_arc_fractions'],1):
  s=f*length;q=subpath(m.spine_line,s-.02,s+.02,.02);xy,t,n=path_data(q);p=xy[1];normal=n[1]
  rays=[]
  for z in [23.,27.,31.]:
   rays.append({'z_m':z,'outer_enu':[*(p+normal*.30),z],'inner_enu':[*(p-normal*1.10),z],
    'question':'Does this finite outer-shell segment cross recessed glass while containing no opaque C-core, silver skin or false backing within the intended opening? Actual part triangles decide; metadata does not.'})
  slots.append({'slot':i,'label':f'north-spine/glazed-wrap-slot-{i}',
   'arc_interval_m':[s-w/2,s+w/2],'plan_centre_enu_m':p.tolist(),'outward_plan_normal':normal.tolist(),
   'source_outer_profile_d_z_m':m.c_outer_profile().tolist(),'finite_segments':rays,
   'corner_warning':'At z23/31 the curved skin is behind the vertical tangent; derive actual intersections, not a flat-wall thickness assumption.'})
 w,h=m.e['entry_clear_opening_m'];q=subpath(m.entry_line,m.entry_s-w/2,m.entry_s+w/2,.4);xy,t,n=path_data(q);mid=len(q)//2
 d={'schema':'auto-museum-source-audit-questions-v11','id':m.g['id'],
 'source_only':True,'actual_model_generated':False,'passed':None,
 'calibration_sha256':hashlib.sha256((HERE/'calibration.json').read_bytes()).hexdigest(),
 'source_geometry_sha256':hashlib.sha256((HERE/'geometry-input.json').read_bytes()).hexdigest(),
 'north_glazed_slot_questions':slots,
 'entry_question':{'plan_centre_enu_m':q[mid].tolist(),'along_plan':t[mid].tolist(),'outward_plan':n[mid].tolist(),
  'width_estimate_m':w,'z_interval_m':[.18,.18+h],'curtain_layer':1,
  'exclude_intentional_door_roles_from_opaque_wall_query':['entry/'],
  'question':'Use the complete actual curtain-layer-1 opaque wall/transom/mullion set to test the entry void, then separately test six glass leaves, handles, frame contacts and their actual swung position. No navigability acceptance from this source question.'},
 'other_required_questions':['All actual per-part Float32 solids, directed edges, components, normals and range coverage.',
  'C-core/skin/upper roof and upper-deck/lower-wing positive-area or volume contacts; reject visible gaps and unwanted overlap.',
  'Distinct real five-floor curtain setbacks; actual glass and opaque curves, louvers and their anchors, railing supports, four stair flights and landings.',
  'Actual output envelope must preserve owners735/797; no whole-assembly collision claim.'],
 'limits':'Uncalibrated estimated source coordinates guide independent questions only. Do not use these records as actual triangles, topology, contact, opening, visual or browser PASS.'}
 p=HERE/'design'/'audit-question-inputs.json';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'file':str(p),'bytes':p.stat().st_size,'actual_model_generated':False}))

if __name__=='__main__':main()
