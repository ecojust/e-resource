"""Fit four parallel drying rods to the tips seen on either side of the two folding carriers."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
here=Path(__file__).absolute().parent;sys.path.insert(0,str(here.parent/'source'))
from geometry_reference import project,DATA
left=np.array([[393.8,281],[408.8,283],[421,286],[432.2,289.6]])
right=np.array([[658,161.0],[672,166.8],[683.5,173.3],[694,179.7]])
def ends(p):
    a=p[:4];b=p[4:8];yy=p[8]+p[9]*np.arange(4);z=p[10]
    return np.stack([np.column_stack([a,yy,np.full(4,z)]),np.column_stack([b,yy,np.full(4,z)])])
def fit():
    def err(p):
        q=project(ends(p).reshape(-1,3)).reshape(2,4,2)-[left,right]
        return np.r_[q.ravel(),(p[:4].mean()+2.57)/.022]
    fit=least_squares(err,[-2.68,-2.58,-2.55,-2.49,1.9,1.92,1.95,2.,-.17,.23,1.45])
    pos=ends(fit.x);q=project(pos.reshape(-1,3)).reshape(2,4,2)
    return dict(original_sha256=DATA['photo_sha256'],left_tips_px=left.tolist(),right_tips_px=right.tolist(),
                estimated_mean_left_end_x_m=-2.57,estimated_anchor_note='把四根杆的左端对到左侧隔板前端附近，沿街位置按照片可见的挑出量估算。',
                rod_endpoints_xyz=pos.tolist(),rod_spacing_m=float(fit.x[9]),rod_height_m=float(fit.x[10]),
                projected_tips_px=q.tolist(),rms_working_px=float(np.mean(np.linalg.norm(q-[left,right],axis=2)**2)**.5))
if __name__=='__main__':
    r=fit();(here/'drying-rack.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['rod_spacing_m'],r['rod_height_m'],r['rms_working_px'])
