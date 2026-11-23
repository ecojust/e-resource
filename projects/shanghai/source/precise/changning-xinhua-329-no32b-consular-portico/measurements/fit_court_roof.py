"""Bundle-adjust the atlas camera and roof intersections with architectural level constraints."""
import json
from pathlib import Path
import numpy as np
from fit_roof_rays import project

HERE=Path(__file__).absolute().parent
wide=json.loads((HERE/'portico-camera-pair.json').read_bytes())['stations']['wide']
atlas=json.loads((HERE/'scaffold-camera.json').read_bytes())
raw=json.loads((HERE/'roof-ray-comparison.json').read_bytes())
xyz=np.array([q['xyz_m'] for q in raw])
uv1,uv2=(np.array([q[k]for q in raw])for k in ['wide_px','scaffold_px'])
known=np.array([x['xyz']for x in atlas['controls']]);known_uv=np.array([x['pixel']for x in atlas['controls']])
def cam_data(j):return [np.array(j[k])for k in ('K','R','C')]
K1,R1,C1=cam_data(wide);K0,R0,C0=cam_data(atlas)

def camera(s):
    omega=s[1:4];a=np.linalg.norm(omega)
    x,y,z=omega
    k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    rot=np.eye(3)+np.sinc(a/np.pi)*k+.5*np.sinc(a/(2*np.pi))**2*k@k
    K=K0.copy();K[0,0]=K[1,1]=K0[0,0]*np.exp(s[0])
    return K,rot@R0,C0+s[4:7]

def screen(cam,points):
    K,R,C=cam;p=(points-C)@R.T@K.T
    return p[:,:2]/p[:,2,None]

def errors(s):
    points=s[7:].reshape((-1,3));c=camera(s)
    # Dormer head and sill are level. Paired glazed sashes are plumb in one
    # plane, while the separately framed hood may stand proud of the glass.
    constraints=[(points[0,2]-points[1,2])/.065,(points[0,1]-points[1,1])/.12,
        (points[2,2]-points[4,2])/.065,(points[3,2]-points[5,2])/.065,
        (points[2,0]-points[3,0])/.045,(points[4,0]-points[5,0])/.045,
        (points[8,2]-points[9,2])/.12,(points[10,0]-points[12,0])/.05,
        (points[10,2]-points[11,2])/.08,
        (c[2][2]-1.50)/.30,s[0]/.40]
    # A free self-calibration fits almost the same pixels while carrying the
    # gable tens of metres behind the house. Retain the independently located
    # portico station and the original ray-intersection depths in this low-baseline view.
    constraints.extend(s[4:7] / [.18,.30,.20])
    constraints.extend(s[1:4] / np.deg2rad([.9,.9,.9]))
    constraints.append(s[0]/.065)
    constraints.extend((points[:,1]-xyz[:,1])/1.10)
    constraints.extend((points[2:6,1]-np.mean(points[2:6,1]))/.10)
    # Vegetation blurs the actual parapet top. These weak conditions preserve
    # an approximately level cornice without forcing it to match the ivy line.
    constraints.extend((points[13:17,2]-np.median(points[13:17,2]))/.32)
    return np.r_[((screen(c,known)-known_uv)/2.).ravel(),
                 ((screen((K1,R1,C1),points)-uv1)/1.5).ravel(),
                 ((screen(c,points)-uv2)/1.5).ravel(),constraints]

s=np.r_[np.zeros(7),xyz.ravel()];lam=.025;eye=np.eye(len(s))
def cost(r):return np.sum(np.sqrt(1+r*r)-1)
for _ in range(90):
    r=errors(s);h=1e-5*np.maximum(abs(s),1.);w=1/np.sqrt(1+r*r)
    J=np.column_stack([(errors(s+h[i]*eye[i])-r)/h[i] for i in range(len(s))])
    H=J.T@(w[:,None]*J)
    step=np.linalg.solve(H+lam*np.diag(np.maximum(1.,np.diag(H))),-J.T@(w*r))
    trial=s+step
    if cost(errors(trial))<cost(r):
        s=trial;lam=max(1e-8,lam*.42)
        if np.linalg.norm(step)<2e-6:break
    else:
        lam*=3
        if lam>1e10:break
K,R,C=camera(s);P=s[7:].reshape(-1,3);a=screen((K1,R1,C1),P);b=screen((K,R,C),P);known_out=screen((K,R,C),known)
def rms(x):return round(float(np.sqrt((x*x).sum(axis=1).mean())),3)
out=dict(atlas_camera=dict(K=K.tolist(),R=R.tolist(),C=C.tolist(),size=[433,325]),
         fixed_portico_rms_px=rms(known_out-known_uv),wide_roof_rms_px=rms(a-uv1),atlas_roof_rms_px=rms(b-uv2),
         points=[dict(feature=r['feature'],xyz_m=p.round(4).tolist(),wide_px=r['wide_px'],atlas_px=r['scaffold_px'],
                      residual_px=[round(float(np.linalg.norm(e)),3) for e in (x,y)])for r,p,x,y in zip(raw,P,a-uv1,b-uv2)],
         limits='Compass attitude and absolute scale inherit the two-column reconstruction. The 17 roof/cornice marks have modest intersection angles; the curtains of ivy, construction scaffolding and invisible rear pitches constrain precision. The gardenward pair of sashes is modelled on one plane with level heads and sills.')
(HERE/'joint-court-roof.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(out['fixed_portico_rms_px'],out['wide_roof_rms_px'],out['atlas_roof_rms_px'],C.round(3).tolist());print(P.round(2).tolist())
