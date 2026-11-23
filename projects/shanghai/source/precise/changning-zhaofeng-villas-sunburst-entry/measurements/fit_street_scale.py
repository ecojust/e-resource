"""Transfer the close photograph's plane coordinates into the three-station street survey."""
from pathlib import Path
import argparse,json,math
import numpy as np
HERE=Path(__file__).absolute().parent
def solve():
 d=json.loads((HERE/'surveyed-street-gate.json').read_bytes())['all_three']
 face=json.loads((HERE.parent/'source/registered-name.json').read_bytes())
 H=np.asarray(face['image_to_initial_xz']);r=d['registered_points'];origin=np.asarray(r['east-wall-inner-front-ground']['enu'])
 a=math.radians(d['measures']['right_panel_axis_true_bearing_deg'])
 rotations=np.asarray([[math.sin(a),math.cos(a),0],[-math.cos(a),math.sin(a),0],[0,0,1.]])
 local={k:list(np.round(rotations@(np.asarray(p['enu'])-origin),5))for k,p in r.items()}
 # Fluting and both cornices give reliable horizontal and vertical lines in the detail photograph.
 # Its right end is behind the prominent eastern return. The three-camera planter endpoints
 # provide the cross-check on the total frontage. Its foliage obscures the local ground line.
 marks={'east-lantern-fixture-center':(442,389),'gold-shield-center':(691,445),'sunburst-crown-upper-midpoint':(604,101),'east-wall-inner-front-under-moulding':(401,247),'east-wall-outer-front-pier-top':(904,115)}
 survey=list(marks);X=[];Y=[]
 for k in survey:
  v=H@[*marks[k],1];X.append(v[:2]/v[2]);Y.append([local[k][0],local[k][2]])
 X=np.asarray(X);Y=np.asarray(Y);coefs=[];err=[]
 for axis in range(2):
  weights=np.sqrt([2.5,2.,2.,.8,.5]);A=np.column_stack([X[:,axis],np.ones(len(X))]);scale,offset=np.linalg.lstsq(A*weights[:,None],Y[:,axis]*weights,rcond=None)[0]
  pred=A@[scale,offset];coefs.append([float(scale),float(offset)]);err.append((pred-Y[:,axis]).tolist())
 return {'datum':'Street axis x follows the east name wall at 63.11 degrees. y points into the lane. z is relative to its inner front ground.','frame_origin_enu_m':origin.tolist(),'basis_enu_rows':rotations.tolist(),'survey_document':'../measurements/surveyed-street-gate.json','surveyed_local_xyz_m':local,'adjusted_curb_face_y_m':.23,'initial_x_to_metres':coefs[0],'initial_z_to_metres':coefs[1],'conditional_scale_transferred_from_five_controls':{k:{'detail_view_pixels':marks[k],'xz_residual_m':[round(err[0][i],4),round(err[1][i],4)]}for i,k in enumerate(survey)},'survey_three_station_rms_pixels':d['rms_pixels'],'right_frontage_visible_width_m':2.805,'right_frontage_pairs_range_m':[2.85,3.00],'entrance_clear_estimate_m':5.0,'entrance_clear_tolerance_m':.35,'front_step_in_m':.6,'front_step_in_tolerance_m':.3,'absolute_location_error_m':[2,4]}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);a=p.parse_args();v=solve();a.output.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(v['initial_x_to_metres'],v['initial_z_to_metres'],v['conditional_scale_transferred_from_five_controls'])
