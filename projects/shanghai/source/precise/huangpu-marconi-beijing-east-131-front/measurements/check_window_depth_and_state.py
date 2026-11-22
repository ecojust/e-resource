"""Measure sash depth and the changed opening angle in two dated Antigng photographs."""
import argparse
import json
import math
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import minimize_scalar
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from marconi_windows import MEASURED,leaf_frame,fixed_extent
from marconi_photo_plane import pixel,on_wall
def check():
 matches=[]
 for row in MEASURED['correspondences']:
  def loss(y):return float(np.linalg.norm(np.array(pixel(on_wall(*row['front'],y),'2015_oblique'))-row['oblique']))
  sol=minimize_scalar(loss,bounds=(-.8,1.4),method='bounded')
  matches.append(dict(**row,fitted_y_m=float(sol.x),distance_in_second_view_px=float(sol.fun)))
 upper=MEASURED['openings'][0];hinge,d,n,w,ang,err=leaf_frame(upper,0);l,r,b,t=fixed_extent(upper)
 cap=np.array([0.,0.,t-.045]);ang2=leaf_frame(upper,1)[4]
 target=[1752.,2491.];obs=np.array(target);sample=[]
 for dx,dy in ((0,0),(-5,4),(3,8)):
  def residual(angle):
   direction=np.array([math.cos(angle),-math.sin(angle),0.])
   return float(np.linalg.norm(np.array(pixel(hinge+w*direction+cap,'2015_oblique'))-(obs+[dx,dy])))
  q=minimize_scalar(residual,bounds=(.2,math.pi-.05),method='bounded')
  sample.append(dict(point=(obs+[dx,dy]).tolist(),angle_deg=float(np.degrees(q.x)),residual_px=float(q.fun),residual_if_2017_angle_px=residual(ang)))
 return dict(fixed_correspondences=matches,angles_in_2017_deg=[float(np.degrees(ang)),float(np.degrees(ang2))],eastern_leaf_test_2015=sample,
 comment='The eastern free top corner in July 2015 supports about 85° with the fixed jamb model. Varying the point by several pixels gives 84–89°. The August 2017 corner supports 117°. The second leaf is partly hidden by a pole in the 2015 photograph. The December 2015 street photograph shows the four leaves closed.',
 scale_uncertainty='The oblique return is calibrated from 15 side-wall edges. Absolute metres inherit an approximately 7 percent scale uncertainty from the depth of the photographed plinth and the street camera height.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args();args.output.write_text(json.dumps(check(),ensure_ascii=False,indent=2)+'\n')
