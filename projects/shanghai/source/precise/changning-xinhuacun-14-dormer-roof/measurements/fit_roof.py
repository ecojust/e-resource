"""Fit two independent cameras to the four dormers and the upper storey below them."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
NAMES = ('pitch', 'eave_z', 'rail_z', 'sill_z', 'head_z', 'sash_y', 'ridge_z', 'ridge_y', 'half_sash', 'overhang')
START = [4.8, 8.8, 6.7, 9.45, 11.24, .78, 12.7, 4.8, 1.39, .39]
UNCERTAINTY = [.045, .35, .30, .40, .40, .38, .55, .66, .17, .15]

def landmarks(p):
    pitch, eave, rail, sill, head, y, ridge, depth, half, overhang = p
    points = {}
    for index in range(5):
        x = (index-2)*pitch
        points['rail'+str(index)] = [x, 0, rail]
        points['pier'+str(index)] = [x, 0, eave-.24]
    for side, sign in [('L', -1), ('R', 1)]:
        points['eave'+side] = [sign*(2*pitch+overhang), -.48, eave]
    for index in range(4):
        x = (index-1.5)*pitch
        for suffix, height in [('head', head), ('sill', sill)]:
            for side, offset in [('L', -half), ('R', half)]:
                points[f'd{index}{suffix}{side}'] = [x+offset, y, height]
    points['chimney'] = [0, depth, ridge+1.56]
    points['ridge'] = [0, depth, ridge]
    return points

def rotation(eye, target):
    f = np.array(target)-eye
    f /= np.linalg.norm(f)
    h = np.cross(f,[0,0,1.]); h /= np.linalg.norm(h)
    return Rotation.from_matrix([h,np.cross(f,h),f]).as_rotvec()

def fit(raw):
    initial = list(START)
    for s in raw.values():
        eye = np.array(s['eye'],float)
        initial.extend([*eye, *rotation(eye,s['target']), np.log(s['focal'])])
    def evaluate(q, details=False):
        geometry = landmarks(q[:len(NAMES)])
        out=list((q[:len(NAMES)]-START)/UNCERTAINTY)
        report={}
        for i,(key,s) in enumerate(raw.items()):
            b=len(NAMES)+7*i;eye=q[b:b+3];r=Rotation.from_rotvec(q[b+3:b+6]).as_matrix();f=np.exp(q[b+6]);w,h=s['size']
            k=np.array([[f,0,(w-1)/2],[0,f,(h-1)/2],[0,0,1]])
            proj=k@np.c_[r,-r@eye];rows=[]
            for name,uv in s['points'].items():
                c=geometry[name];v=proj@[*c,1.];pred=v[:2]/v[2];diff=pred-uv;held=name in s['held']
                if not held:out.extend(diff/s['uncertainty_px'])
                rows.append(dict(id=name,uv=uv,xyz=c,pred=pred.tolist(),error_px=float(np.linalg.norm(diff)),held=held))
            out.extend([(eye[2]-1.62)/.40,(np.log(f/s['focal']))/.20])
            report[key]=dict(size=s['size'],eye=eye.tolist(),K=k.tolist(),R=r.tolist(),P=proj.tolist(),controls=rows)
        return report if details else out
    solved=least_squares(evaluate,initial,max_nfev=600,loss='soft_l1')
    return dict(parameters=dict(zip(NAMES,solved.x[:len(NAMES)])),stations=evaluate(solved.x,True),
                convention='X increases to the right along the south-facing upper gallery; Y enters the roof; Z is measured above an estimated courtyard level. Principal points and camera heights are conditional. Both stations face the front. Only the front pitch and its upper gallery band are reconstructed.')

if __name__=='__main__':
    raw=json.loads((HERE/'roof-controls.json').read_text())['stations']
    result=fit(raw)
    (HERE/'roof-registration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['parameters'])
    for key,st in result['stations'].items():
        print(key,'median',np.median([p['error_px'] for p in st['controls'] if not p['held']]),'hold',[(p['id'],round(p['error_px'],1))for p in st['controls'] if p['held']])
