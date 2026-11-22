"""Reconstruct the street-camera orientation from masonry edges on both sides of the corner."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares,minimize_scalar
from scipy.spatial.transform import Rotation

HERE=Path(__file__).resolve().parent


def vanishing(lines,initial):
    line=np.asarray(lines);mid=line.mean(axis=1);v=line[:,1]-line[:,0]
    normals=np.column_stack((v[:,1],-v[:,0]));length=np.linalg.norm(normals,axis=1)
    normals/=length[:,None]
    def distance(vp):
        # Projected angular error, avoiding overweighting short, distant traces.
        return np.einsum('ij,ij->i',normals,vp-mid)/np.linalg.norm(vp-mid,axis=1)**.65
    return least_squares(distance,initial,loss='soft_l1',f_scale=.19).x


def fit():
    controls=json.loads((HERE/'corner-crown-image-controls.json').read_bytes())
    edges=controls['edges_upright_original_px']
    vp=np.array([vanishing(edges[k],start) for k,start in
                 [('north',[-2400.,3460.]),('west',[5100.,3690.]),('vertical',[1700.,-4240.])]])
    s=3024./495.;f0=26*np.hypot(3024.,4032.)/43.27
    ring=np.array(json.loads((HERE/'north-front-site.json').read_bytes())['ring_xy_m'])
    side=ring[5]-ring[0];side/=np.linalg.norm(side)
    basis=np.array([[1.,0.,0.],[*side,0.],[0.,0.,1.]])
    def rays(params):
        f,cx,cy=params
        ray=np.column_stack(((vp[:,0]-cx)/f,(vp[:,1]-cy)/f,np.ones(3)))
        ray/=np.linalg.norm(ray,axis=1)[:,None];ray[0]*=-1.
        return ray
    def residual(params):
        f,cx,cy=params;v=rays(params);g=v@v.T-basis@basis.T
        return [g[0,1]/.0025,g[1,2]/.002,g[2,0]/.002,(f-f0)/170.,(cx-1512.)/40,(cy-2016.)/40]
    fit=least_squares(residual,[f0,1512.,2016.])
    f,cx,cy=fit.x;rotation=Rotation.align_vectors(rays(fit.x),basis)[0].as_matrix()
    intrinsic=np.array([[f,0,cx],[0,f,cy],[0,0,1.]])
    nwest=np.array([side[1],-side[0]])
    def lines(eye):
        rows=[]
        for face,u,slope,z in controls['street_band_rays']:
            van=vp[0 if face=='north' else 1]/s
            v=van[1]+(u-van[0])*slope
            uv=np.array([u,v])*s
            ray=rotation.T@np.linalg.solve(intrinsic,[*uv,1.])
            xyz=eye+ray*(z-eye[2])/ray[2]
            off=xyz[1] if face=='north' else (xyz[:2]-ring[0])@nwest
            rows.append(dict(street=face,source_px=uv.tolist(),model_xyz_m=xyz.tolist(),plane_residual_m=float(off)))
        return rows
    def cost(eye):return [*[v['plane_residual_m']/.19 for v in lines(eye)],(eye[2]-1.6)/.45]
    eye=least_squares(cost,[19.,-16.,1.6]).x
    camera=intrinsic@rotation@np.column_stack((np.eye(3),-eye))
    return dict(reference=controls['photo_references']['cc2024a'],upright_size_px=[3024,4032],
                edge_counts={k:len(v)for k,v in edges.items()},vanishing_points_px=vp.tolist(),
                effective_intrinsic_3x3=intrinsic.tolist(),eye_xyz_m=eye.tolist(),camera_3x4=camera.tolist(),
                survey_exposures=lines(eye),common_upper_screen_z_estimate_m=23.30,
                note='The two cornice elevations, masonry module and 822 footprint set the metric scale. Camera height, setbacks and the interpolation of the rounded corner are estimates. The vanishing lines register the upper, oblique image; retain its separate camera when comparing the crown.')
if __name__=='__main__':
    rec=fit();(HERE/'corner-crown-camera.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n')
    print(rec['vanishing_points_px'],rec['eye_xyz_m'])
