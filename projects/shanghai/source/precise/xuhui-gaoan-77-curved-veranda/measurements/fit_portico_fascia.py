"""Fit the horizontal porch fascia against fixed original-photo lines."""
import argparse,json,numpy as np,sys
from pathlib import Path
from scipy.optimize import least_squares
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S/'source'))
from photo_cameras import projection
from house_layout import U,Z,D,POST_SPAN
r=json.loads((S/'measurements/roof-dormer-photo-pixels.json').read_text())['observations'];r={k:np.array(v['fascia'])for k,v in r.items() if k!='sina-26'}
# One low western verge sample sits on the curved gallery.
r['sina-37']=r['sina-37'][:4]
def residual(v):
 result=[]
 for k,obs in r.items():
  p=projection(k);a=p@[U(.65),v[0],v[1],1];b=p@[U(2.72),v[0],v[1],1];l=np.cross(a,b);l/=np.linalg.norm(l[:2]);result.extend(np.c_[obs,np.ones(len(obs))]@l)
 return np.array(result)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);args=ap.parse_args()
    initial=[D(-.298),Z(.069)-.13];solution=least_squares(residual,initial,loss='soft_l1',f_scale=1.)
    result={'reference':'Horizontal centreline of the principal south fascia in three published views. The final fixed point in photo 37 is on the separate attic verge.',
            'source_pixels':{k:v.tolist() for k,v in r.items()},'fitted_yz_m':solution.x.tolist(),
            'original_perpendicular_residual_px':residual(initial).tolist(),'updated_perpendicular_residual_px':residual(solution.x).tolist()}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
