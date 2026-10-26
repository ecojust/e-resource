#!/usr/bin/env python3
"""Six local source fixtures against actual rejected-v1 targets, never full v2."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from build_model import Museum
from prepare_repairs_from_v1 import Actual,section
from solids import audit_parts
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--sidecar',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('Preserve prior source evidence')
 m=Museum();old=Actual(a.raw,a.sidecar)
 tile=m.lower_visible_roof.difference(m.terrace).intersection(box(-2.3875,-28.7875,-.0125,-26.4125))
 m.panel_grid(tile,m.roof_z,False,'roof/lower-silver-top','Museum silver honeycomb aluminium');m.local_repairs()
 q=audit_parts(m.b.parts);assert q['passed'],q['failures'];assert q['parts']==6
 parts={x['label']:np.asarray(x['vertices'],dtype='<f4').astype(float)[np.asarray(x['triangles'])] for x in m.b.parts}
 contacts=[]
 for row in m.repairs['added_parts']:
  z=(row['top_m']+row['bottom_m'])/2
  for target in row['actual_v1_target_labels']:
   height=27.355 if 'layer-5/' in target else 3.49 if 'layer-1/bay-161/glass-pane-1'==target.removeprefix('curtain/') else z
   area=section(parts[row['label']],height).intersection(section(old.triangles(target),height)).area
   assert area>1e-6,(row['label'],target,height,area)
   contacts.append({'source_fixture':row['label'],'actual_v1_target':target,'z_m':height,'common_area_m2':area,'source_input_contact_only':True})
 name=m.repairs['changed_part']['label'];t=parts[name];r=old.triangles('roof/lower-curved-continuous-underlayer/component-1')
 bottom=t[np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])[:,2]<-1e-8];top=r[np.cross(r[:,1]-r[:,0],r[:,2]-r[:,0])[:,2]>1e-8]
 vals=[];cells=[]
 for u in bottom:
  up=Polygon(u[:,:2]);uc=np.linalg.solve(np.column_stack((u[:,:2],np.ones(3))),u[:,2])
  for v in top:
   if np.any(v[:,:2].max(0)<u[:,:2].min(0)) or np.any(u[:,:2].max(0)<v[:,:2].min(0)):continue
   cell=up.intersection(Polygon(v[:,:2]))
   if cell.area<1e-12:continue
   vc=np.linalg.solve(np.column_stack((v[:,:2],np.ones(3))),v[:,2]);vv=np.asarray(cell.exterior.coords);vals.extend((np.column_stack((vv,np.ones(len(vv))))@(uc-vc)).tolist());cells.append(cell)
 assert max(vals)<-1e-5
 report={'schema':'auto-museum-geometry-v2-local-source-preflight','source_scope_passed':True,'full_model_generated':False,'actual_v2_structure_passed':False,'model_accepted':False,'local_part_count':q['parts'],'local_triangle_count':q['triangles'],'closed_oriented_positive_float32_fixtures':True,'repair_inputs_sha256':sha(HERE/'repair-inputs.json'),'builder_sha256':sha(HERE/'build_model.py'),'calibration_sha256':sha(HERE/'calibration.json'),'actual_v1_raw_sha256':m.repairs['baseline_raw']['sha256'],'local_source_contacts':contacts,'target_panel_bottom_minus_actual_v1_underlayer_top_m_range':[min(vals),max(vals)],'target_panel_actual_cells':len(cells),'target_panel_covered_area_m2':unary_union(cells).area,'scope':'Six generated in-memory local fixtures only, no complete model or export. New source-fixture contacts do not replace independent actual v2 topology/contact/slot/retention/native/browser checks.'}
 a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('local_source_contacts','scope')},indent=2))

if __name__=='__main__':main()
