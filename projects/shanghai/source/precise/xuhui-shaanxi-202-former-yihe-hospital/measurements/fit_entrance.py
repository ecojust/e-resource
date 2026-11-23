"""Recover the barrel hood, stone reveals and the fourth camera from independent photograph marks."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from register_court import Camera

HERE = Path(__file__).absolute().parent
VIEWS = ('commons', '05', '10')
# Wide photographs retain the working resolution identified in court-cameras.json.
WIDE = {
    'canopy_crown': [[620,446],[547,256],[429,277]],
    'canopy_left_spring': [[590,471.5],[528,279],[411,293]],
    'canopy_right_spring': [[652,474],[578,288],[449,294]],
    'west_cornice_at_pier': [[546,472],[476,288],[383,293]],
    'left_inner_jamb_lintel': [[559.5,483],[492,304],[392,301]],
    'right_inner_jamb_lintel': [[613,485],[537,307],[427,302]],
}
CAMERAS = [Camera(v) for v in VIEWS]
def intersect(uv):
    def residual(xyz):
        return np.concatenate([cam.pixel(xyz)-mark for cam,mark in zip(CAMERAS,uv)])
    fit = least_squares(residual, [0,0,4])
    return {'xyz':fit.x.tolist(), 'reprojection_px':residual(fit.x).reshape(-1,2).tolist()}

def recover():
    solutions = {name:intersect(marks) for name,marks in WIDE.items()}
    # The center of the rectangular opening is fixed by its jambs in the distant images.
    center=-1.10
    # Tall photograph uses the long side for the EXIF 39 mm-equivalent focal prior.
    width,height=378,600
    marks={'crown':[169,8],'left_spring':[28,79],'right_spring':[319,88],
           'left_inner_top':[62,162],'right_inner_top':[274,166],
           'left_inner_base':[49,507],'right_inner_base':[278,508]}
    def parts(t):
        pan,tilt,roll,cx,cy,cz,logf, hoodcenter, arch_radius, front_y, spring, rise=t
        # World X is screen right, Y forward and Z vertically up.
        nominal=np.array([[1,0,0],[0,0,-1],[0,1,0.]])
        r=Rotation.from_rotvec([pan,tilt,roll]).as_matrix()@nominal
        f=650*np.exp(logf)
        k=np.array([[f,0,width/2],[0,f,height/2],[0,0,1.]])
        c=np.array([cx,cy,cz])
        xyz=[[hoodcenter,front_y,spring+rise],[hoodcenter-arch_radius,front_y,spring],
             [hoodcenter+arch_radius,front_y,spring],[center-1.22,-1.08,4.185],
             [center+1.22,-1.08,4.185],[center-1.22,-1.08,.55],[center+1.22,-1.08,.55]]
        projected=[]
        for pt in xyz:
            p=k@r@(pt-c);projected.append((p[:2]/p[2]).tolist())
        return r,k,c,xyz,np.asarray(projected)
    def error(t):
        r,k,c,xyz,projected=parts(t)
        uv=list(marks.values())
        values=list(((projected-uv)/2.5).ravel())
        for j,key in enumerate(('canopy_crown','canopy_left_spring','canopy_right_spring')):
            for cam,mark in zip(CAMERAS,WIDE[key]):
                values.extend((cam.pixel(xyz[j])-mark)/2.5)
        values.extend([t[6]/.06,(t[5]-1.55)/.7,(t[7]-center)/.17])
        return values
    fit=least_squares(error,[0,0,0,-1,-8,1.55,0,-.95,1.36,-2.24,4.55,.84],loss='soft_l1')
    r,k,c,xyz,projected=parts(fit.x)
    return {'wide_views':VIEWS,'wide_source_marks':WIDE,'triangulations':solutions,
            'close_view':{'source':'2018-09-09 Gao 06, 2961 x 4700, EXIF 16:33:37, 39 mm equivalent',
              'size':[width,height],'marks':marks,'projected':dict(zip(marks,projected.tolist())),
              'residual_norm_px':np.linalg.norm(projected-list(marks.values()),axis=1).tolist(),
              'R':r.tolist(),'K':k.tolist(),'C':c.tolist()},
            'arch':dict(zip(('center_x','radius_x','front_y','spring_z','rise_z'),fit.x[-5:].tolist())),
            'jamb':{'center_x':center,'half_width':1.22,'front_y':-1.08,'lintel_z':4.185,'landing_z':.55},
            'limits':'The three wide views are oblique. The close view constrains the front silhouette and proportions. Depth and paving datum are estimates.'}
if __name__=='__main__':
    (HERE/'entrance-cameras.json').write_text(json.dumps(recover(),indent=2)+'\n')
