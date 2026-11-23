"""Fit the bowed cornice, balustrade and stair footprint against their photographed outlines."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from register_court import Camera
D=Path(__file__).absolute().parent
CURVES={
 '03_soffit':[[257,343],[277,327],[310,313],[351,305],[394,301],[435,305],[480,315],[512,329],[533,342]],
 '03_coping':[[268,271],[285,244],[311,226],[351,211],[393,205],[434,211],[474,225],[500,242],[520,268]],
 '03_stair':[[195,676],[218,683],[255,692],[311,699],[392,704],[463,700],[518,693],[567,683],[589,677]],
 '05_soffit':[[441,12],[491,19],[539,25],[590,28],[639,37],[684,49],[717,63]],
 '05_stair':[[433,418],[478,424],[534,428],[582,429],[639,424],[680,419],[708,408],[716,402]],
}
def make_points(rx,cy,ry,z):
    t=np.linspace(-np.pi/2,np.pi/2,901)
    return np.column_stack((rx*np.sin(t),cy-ry*np.cos(t),np.full_like(t,z)))
def fit():
    cams={n:Camera(n,working=True)for n in ['03','05']}
    def residuals(v,report=False):
        rx,cy,ry,bottom,top,stair_rx,stair_ry,stair_z=v;r=[];d={}
        for key,points in CURVES.items():
            n,s=key.split('_');cam=cams[n]
            curve=make_points(stair_rx if s=='stair'else rx,cy,stair_ry if s=='stair'else ry,
                              {'stair':stair_z,'soffit':bottom,'coping':top}[s])
            q=(curve-cam.c)@(cam.k@cam.r).T;uv=q[:,:2]/q[:,2:]
            dist,idx=cKDTree(uv).query(points);delta=np.asarray(points)-uv[idx];r.extend((delta/(3.2 if n=='03'else 5.0)).ravel())
            d[key]=dict(working_pixels=points,nearest_errors_px=np.round(dist,2).tolist())
        r.extend([(rx-2.1)/.30,(cy-.60)/.30,(bottom-3.73)/.14,(stair_z-.56)/.07,(stair_rx-1.79)/.40])
        return d if report else r
    sol=least_squares(residuals,(2.04,.57,1.54,3.72,5.05,1.8,1.63,.57),bounds=([1.50,-.1,.65,3.48,4.3,1.1,.7,.36],[2.8,1.3,2.5,4.08,5.7,2.8,2.8,.7]),loss='soft_l1',max_nfev=220)
    return dict(bowed_plan=dict(zip(['radius_x','rear_center_y','radius_y','soffit_z','balustrade_coping_z','upper_landing_radius_x','upper_landing_radius_y','upper_landing_z'],sol.x.tolist())),evidence=residuals(sol.x,True),method='Independent nearest-curve fit in the 03 frontal and 05 oblique photographs. The plank silhouette in 05 is partly covered by the later light canopy, which is excluded from the assembly.')
if __name__=='__main__':
    q=fit();(D/'balcony-curves.json').write_text(json.dumps(q,indent=2)+'\n');print(q['bowed_plan'],[(k,np.median(e['nearest_errors_px']),max(e['nearest_errors_px']))for k,e in q['evidence'].items()])
