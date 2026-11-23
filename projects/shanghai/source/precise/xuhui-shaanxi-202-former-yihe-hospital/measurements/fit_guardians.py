"""Cross-check the two sculpted heads in three garden views and the right lion in the entrance view."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from register_court import Camera
HERE=Path(__file__).absolute().parent
WIDE={'left':[[1154.5,1166],[544,411],[405,364.5]],'right':[[1304.5,1163],[607.5,402],[452.2,364.5]]}
# Pixel readings on the private 360x750 study crop, formed from [570,821,690,1071] of the 690x1095 version.
# Each local coordinate lies on the observed front surface and uses the carved stone height as unit.
POINTS={'curled crown':([184,29],[0,-.112,.998]),'nose tip':([196,152],[0,-.300,.864]),
        'mouth lower edge':([193,182],[0,-.252,.784]),'ball knot':([140,447],[-.125,-.252,.353]),
        'straight paw toe':([276,456],[.126,-.252,.331]),'drape low point':([211,628],[.025,-.279,.088]),
        'foot centre at front':([188,696],[0,-.267,.007])}
def close_projection():
    d=json.loads((HERE/'entrance-cameras.json').read_text())['close_view']
    return lambda p:project(p,d)
def project(p,d):
    q=np.asarray(d['K'])@np.asarray(d['R'])@(np.asarray(p)-d['C']);return q[:2]/q[2]
def sample_px(uv):
    return (np.asarray(uv)/3+[570,821])*[378/690,600/1095]
def wide():
    cams=[Camera(x) for x in ['commons','05','10']];out={}
    for side,original in WIDE.items():
        xy=np.array(original,dtype=float);xy[0]*=[1080/2144,717/1424];a=[];v=[]
        for c,p in zip(cams,xy):
            d=c.ray(p);d/=np.linalg.norm(d);m=np.eye(3)-np.outer(d,d);a.extend(m);v.extend(m@c.c)
        target=np.linalg.lstsq(a,v,rcond=None)[0]
        out[side]={'source_pixels_native':original,'working_pixels':xy.tolist(),'independent_triangulated_crown_m':target.tolist(),
                   'working_pixel_residuals':[float(np.linalg.norm(c.pixel(target)-u)) for c,u in zip(cams,xy)]}
    return out
def fit():
    project06=close_projection();targets=wide()
    def loss(v):
        x,y,z,h=v
        delta=[(project06(np.array([x,y,z])+np.asarray(loc)*h)-sample_px(uv))/2.2 for uv,loc in POINTS.values()]
        return np.r_[np.ravel(delta),(x-.397)/.12,(y+2.48)/.13,(z-.235)/.085,(h-.988)/.07]
    fitted=least_squares(loss,[.398,-2.48,.235,.98]).x
    return {'three_wide_views':targets,'close_fit_x_y_base_height':fitted.tolist(),
            'close_observations':{k:{'working_pixel':sample_px(q).tolist(),'local_position_in_carving':a}for k,(q,a)in POINTS.items()},
            'limits':'The street parcel constrains the building envelope. The court-facing plinths use projected positions and a stair-depth estimate. Gao 10 partly hides both feet behind plants and Gao 05 shows the heads above a parked car. The left raised-paw subject is unresolved.'}
if __name__=='__main__':print(json.dumps(fit(),indent=2))
