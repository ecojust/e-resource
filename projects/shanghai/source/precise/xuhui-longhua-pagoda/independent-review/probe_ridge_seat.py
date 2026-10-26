#!/usr/bin/env python3
"""Six new ridge-seat components vs the unchanged actual exported V2 roof/ridges."""
from pathlib import Path
import types,sys,json,hashlib,ast
import numpy as np
R=Path(__file__).resolve().parents[1];V2=R.parent/'v2';O=Path(__file__).resolve().parent
source=(R/'build_model.py').read_bytes();source_sha=hashlib.sha256(source).hexdigest();assert source_sha=='d66071b180d11cf6509f4fd0b2a836942fadde09b71dbde2758010f1a334fea0'
assert (R/'calibration.json').read_bytes()==(V2/'calibration.json').read_bytes()
def funcs(path):return {x.name:ast.dump(x,include_attributes=False) for x in ast.walk(ast.parse(path.read_text())) if isinstance(x,ast.FunctionDef)}
a,b=funcs(R/'build_model.py'),funcs(V2/'build_model.py');unchanged=['roof_point','roof_counts','underlayer_drop','tile_strip','roof_mesh','shell'];assert all(a[k]==b[k] for k in unchanged)
oldscript=V2/'independent-review/audit_raw_ridge_contact.py';code=oldscript.read_text();old={'__file__':str(oldscript)};exec(code[:code.index('rows=[]')],old)
helper=R.parent/'independent-review/probe_walls_rails.py';text=helper.read_text();ns={'np':np};exec(text[text.index('def mesh('):text.index('records=[]')],ns)
sys.path.insert(0,str(R));m=types.ModuleType('v3seat_review');m.__file__=str(R/'build_model.py');exec(compile(source,m.__file__,'exec'),m.__dict__);p=m.Pagoda()
prior=json.loads((V2/'independent-review/actual-v2-ridge-contact.json').read_text());records=[];topologies=[]
for L in [1,4,7]:
 for corner in [0,3]:
  p.b.parts=[];p.ridge_seat(p.c['levels'][L-1],corner);assert len(p.b.parts)==1;part=p.b.parts[0];seat=ns['mesh'](part);topo=ns['topology'](part);zero=int((np.linalg.norm(np.cross(seat[:,1]-seat[:,0],seat[:,2]-seat[:,0]),axis=1)<=1e-12).sum());topologies.append({'level':L,'corner':corner,**topo,'zero_triangles':zero})
  ridge=old['parts'][f'L{L}/continuous-upturned-corner-ridge{corner}'];roof=old['parts'][f'L{L}/continuous-curved-roof']
  for row in prior['samples']:
   if row['level']!=L or row['source_corner']!=corner:continue
   xy=row['xy_enu_m'];bottom=old['z'](seat,xy,False);top=old['z'](seat,xy,True);rb=old['z'](ridge,xy,False);rt=old['z'](roof,xy,True);assert None not in [bottom,top,rb,rt]
   records.append({'level':L,'corner':corner,'t':row['t'],'lateral_m':row['lateral_m'],'substrate_top_minus_seat_bottom_m':rt-bottom,'seat_top_minus_actual_ridge_bottom_m':top-rb,'actual_previous_gap_to_tiles_m':row['ridge_bottom_minus_tile_top_m']})
passed=all(q['non_two_edges']==q['unpaired_edges']==q['zero_triangles']==0 and q['signed_volume']>0 for q in topologies) and all(q['substrate_top_minus_seat_bottom_m']>0 and q['seat_top_minus_actual_ridge_bottom_m']>0 for q in records)
report={'schema':'longhua-v3-six-seat-component-contact-v1','bounded_component_passed':passed,'builder_sha256':source_sha,'source_unchanged_during_probe':source==(R/'build_model.py').read_bytes(),'unchanged_old_geometry_functions_ast':unchanged,'calibration_v2_byte_exact':True,'actual_v2_raw_sha256':old['rawsha'],'prior_v2_gap_report_sha256':hashlib.sha256((V2/'independent-review/actual-v2-ridge-contact.json').read_bytes()).hexdigest(),'new_component_count':len(topologies),'new_part_topology':topologies,'finite_contact_count':len(records),'min_substrate_overlap_m':min(q['substrate_top_minus_seat_bottom_m'] for q in records),'min_ridge_overlap_m':min(q['seat_top_minus_actual_ridge_bottom_m'] for q in records),'samples':records,'whole_tower_generated':False,'new_raw_exported':False,'native_accepted':False,'scope':'Only six new ridge-seat function outputs rounded toFloat32, checked against actual unchanged V2raw roof and ridge triangles at90 previous sample locations (levels1/4/7,corners0/3,t.2/.4/.6/.8/.95,lateral0/+−25mm). This is not the actual V3 exportedraw; all56 new seats and oldpart preservation still await root raw build. t>1ornaments intentionally outside this support scope.'}
out=O/'ridge-seat-component-contact.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['bounded_component_passed','builder_sha256','new_component_count','finite_contact_count','min_substrate_overlap_m','min_ridge_overlap_m','new_part_topology']},indent=2))
