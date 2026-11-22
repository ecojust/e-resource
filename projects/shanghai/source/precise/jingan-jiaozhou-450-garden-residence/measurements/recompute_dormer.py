"""Refit the two-plane camera, triangulate the shed edges and reread the six louvre banks."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.linalg import rq
from scipy.ndimage import gaussian_filter1d, map_coordinates
from scipy.optimize import least_squares
from scipy.signal import find_peaks
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent


def project(P,points):
    p = np.atleast_2d(points)
    q = np.c_[p,np.ones(len(p))] @ P.T
    return q[:,:2] / q[:,2,None]


def on_plane(P,uv,y):
    H = np.c_[P[:,0],P[:,2],P[:,3]+P[:,1]*y]
    xz = project(np.linalg.inv(H),uv)
    return np.c_[xz[:,0],np.full(len(xz),y),xz[:,1]]


def refit(d):
    P13 = np.asarray(d['camera_models']['13'])
    cal = d['camera_8_check']
    P8 = np.asarray(cal['original_arcade_projection'])
    ao = np.asarray(cal['paired_arcade_original_pixels_8_then_13'])
    wo = np.asarray(d['paired_texture_original_pixels_8_then_13'])
    ax = on_plane(P13,ao[:,1],0.)
    wx = on_plane(P13,wo[:,1],d['front_shutter_plane_y_m'])
    use_a = np.arange(len(ax))%4!=0
    use_w = np.arange(len(wx))%4!=0
    K,R = rq(P8[:,:3])
    D = np.diag(np.sign(np.diag(K)))
    K,R = K@D,D@R
    K /= K[2,2]
    C = -np.linalg.solve(P8[:,:3],P8[:,3])

    def camera(p):
        k = K.copy()
        k[:2,:2] *= np.exp(p[6])
        return (k @ Rotation.from_rotvec(p[3:6]).as_matrix() @ R
                @ np.c_[np.eye(3),-(C+p[:3])])

    def residual(p):
        m = camera(p)
        return np.r_[(project(m,ax[use_a])-ao[use_a,0]).ravel(),
                     2*(project(m,wx[use_w])-wo[use_w,0]).ravel(),
                     p[:3]/.7,p[3:6]/.035,p[6]/.09]

    P = camera(least_squares(residual,np.zeros(7),loss='soft_l1',f_scale=.7).x)
    def held_out(x,obs,mask):
        return float(np.median(np.linalg.norm(project(P,x[~mask])-obs[~mask,0],axis=1)))
    checks = []
    for item in d['roof_edge_observations']:
        u,v = np.asarray(item['photo_8']),np.asarray(item['photo_13'])
        def residual_edge(x):
            return np.r_[(project(P,x)[0]-u),(project(P13,x)[0]-v)*.65]
        xyz = least_squares(residual_edge,[7,5,13]).x
        checks.append(dict(label=item['feature'],xyz_m=xyz.tolist(),
                           delta_from_component_m=float(np.linalg.norm(xyz-item['xyz_m']))))
    return dict(arcade_holdout_count=int((~use_a).sum()),arcade_median_px=held_out(ax,ao,use_a),
                dormer_holdout_count=int((~use_w).sum()),dormer_median_px=held_out(wx,wo,use_w),
                triangulated_edges=checks)


def optical_profile(d,image_key,path):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=d['photos'][image_key]['sha256']:
        raise ValueError(f"Original photo {image_key} does not have the documented SHA-256")
    image = np.asarray(Image.open(path).convert('L'),dtype=float)
    H = np.asarray(d['normalized_to_original'][image_key])
    results = []
    rows = np.arange(82.,164.6,.1)
    for leaf in d['shutters']:
        lo,hi = leaf['observed_zone_rectified_pixels']
        xx,yy = np.meshgrid(np.linspace(lo+6,hi-6,17),rows)
        uv = project(H,np.c_[xx.ravel(),yy.ravel()])
        grey = map_coordinates(image,[uv[:,1],uv[:,0]],order=2).reshape(xx.shape).mean(axis=1)
        detail = gaussian_filter1d(grey,2)-gaussian_filter1d(grey,13)
        # Exclude the edges of each shutter frame. In the reported interior, select
        # actual local maxima, resolving ties by distance to the measured blade rows.
        peaks,_ = find_peaks(detail,distance=23,prominence=1.25)
        observed = rows[peaks]
        expected = d['blade_rows'][(leaf['id']-1)//3]['normalized_image_bright_leading_edge_rows']
        offsets = np.asarray([observed[np.argmin(abs(observed-y))]-y for y in expected])
        nearest = observed[[np.argmin(abs(observed-y)) for y in expected]]
        results.append(dict(leaf=leaf['id'],resolved_distinct_edges=len(np.unique(nearest)),
                            maximum_offset_rectified_px=round(float(max(abs(offsets))),3),
                            median_offset_rectified_px=round(float(np.median(abs(offsets))),3),
                            observed_edge_rows_rectified=nearest.round(2).tolist()))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--photo-8',type=Path)
    parser.add_argument('--photo-13',type=Path)
    args = parser.parse_args()
    d = json.loads((HERE/'dormer-registration.json').read_text())
    result = {'geometry':refit(d),'louvres':{}}
    for key,path in [('8',args.photo_8),('13',args.photo_13)]:
        if path:
            result['louvres'][key] = optical_profile(d,key,path)
    args.output.write_text(json.dumps(result,indent=1)+'\n')


if __name__ == '__main__':
    main()
