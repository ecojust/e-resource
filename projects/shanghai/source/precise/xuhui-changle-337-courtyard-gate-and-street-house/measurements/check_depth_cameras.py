"""Out-of-sample diagnosis of the summer camera and cross-period depth ambiguity."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
D=Path(__file__).resolve().parent

def analyze(root):
    station=json.loads((root/'street-cameras.json').read_text())
    observed=json.loads((root/'facade-control-pixels.json').read_text())['views']['2017']['points']
    groups=json.loads((root/'held-out-depth-controls.json').read_text())['groups']
    base=station['cameras']['2017'];K=np.array(base['K']);centre=np.array(base['eye']);R0=np.array(base['R'])
    first={name:(np.array(station['points'][name]),np.array(uv)) for name,uv in observed.items()}
    # BR and the inferred point O have reduced photographic precision, but are kept in the held-out set.
    held={'BR','O','HL','bL','DF'}
    deep={key:{n:(np.array(o['winter_intersection']),np.array(o['photo_2017']))for n,o in ns.items()} for key,ns in groups.items()}
    def project(cam,world):
        moved=Rotation.from_rotvec(cam[3:6]).as_matrix()@R0
        xyz=(world-(centre+cam[:3]))@moved.T;uv=xyz[:,:2]/xyz[:,2:3]
        norm=np.sum(uv**2,axis=1)
        radial=1+cam[9]*norm+cam[10]*norm**2
        f=K[0,0]+cam[6]
        return uv*(f*radial)[:,None]+[K[0,2]+cam[7],K[1,2]+cam[8]]
    def residuals(cam,points):
        if not points:return np.zeros((0,2))
        world,uv=zip(*points.values());return project(cam,np.array(world))-np.array(uv)
    def med(cam,pt):return round(float(np.median(np.linalg.norm(residuals(cam,pt),axis=1))),2)
    line_source=json.loads((root/'line-straightness-pixels.json').read_text())
    lines=[np.array(line_source[name],dtype=float) for name in ('long_street_wall','west_court_wall')]
    def straightness(cam):
        f=K[0,0]+cam[6]
        centre=np.array([K[0,2]+cam[7],K[1,2]+cam[8]])
        result=[]
        for measurements in lines:
            distorted=(measurements-centre)/f
            undistorted=distorted.copy()
            for _ in range(12):
                r=np.sum(undistorted**2,axis=1)[:,None]
                undistorted=distorted/(1+cam[9]*r+cam[10]*r**2)
            p=f*undistorted+centre
            result.append(p[:,1]-np.polyval(np.polyfit(p[:,0],p[:,1],1),p[:,0]))
        return result
    models={'pinhole-pose':list(range(6)),'pose-and-focus':list(range(7)),'pose-focus-shift':list(range(9)),'pose-focus-shift-radial':list(range(10)),'two-radial-coefficients':list(range(11)), 'line-constrained-centred-radial':[0,1,2,3,4,5,6,9],'line-constrained-radial':list(range(10))}
    # The large exploratory interval for k is wider than expected for an already rectified phone JPEG.
    bounds=np.array([2.5,3.3,.6,.22,.22,.13,700,210,150,.75,.8])
    priors=np.array([1.2,1.9,.24,.13,.13,.08,370,75,60,.20,.35])
    scales={'grille':24.,'drain':31.,'low-eaves':17.,'high-green':40.,'front-wall-pier':27.}
    zero=np.zeros(11)
    result={'baseline_deep_px':{k:med(zero,g)for k,g in deep.items()},'baseline_main_fit_px':med(zero,{n:v for n,v in first.items()if n not in held}),'baseline_main_holdout_px':med(zero,{n:v for n,v in first.items()if n in held}),'held_control_names':sorted(held),'models':{}}
    for name,active in models.items():
        active=np.array(active)
        def fit(skipped):
            def unpack(par):
                p=np.zeros(11);p[active]=par;return p
            def residual(par):
                p=unpack(par)
                r=[(residuals(p,{k:v for k,v in first.items()if k not in held})/5).ravel(), p[active]/priors[active]]
                if name.startswith('line-constrained'):
                    r.extend(d/2.5 for d in straightness(p))
                for k,pts in deep.items():
                    if k!=skipped:r.append((residuals(p,pts)/scales[k]/np.sqrt(len(pts))).ravel())
                return np.concatenate(r)
            opt=least_squares(residual,np.zeros(len(active)),bounds=(-bounds[active],bounds[active]),loss='soft_l1',x_scale='jac',max_nfev=300)
            return unpack(opt.x)
        cv={}
        for skipped in deep:
            cam=fit(skipped);cv[skipped]=dict(held_native_px=med(cam,deep[skipped]),main_holdout_native_px=med(cam,{k:v for k,v in first.items()if k in held}),fit_parameters=cam.round(7).tolist())
        cam=fit(None)
        result['models'][name]={'object_leave_one_out':cv,'all_fitted':{k:med(cam,g)for k,g in deep.items()},'main_holdout_px':med(cam,{k:v for k,v in first.items()if k in held}),'all_parameters':cam.round(7).tolist(),'two_plinth_lines_rms_native_px':[round(float(np.sqrt(np.mean(v*v))),3) for v in straightness(cam)]}
    result['parameter_order']=['local camera dx m','dy m','dz m','incremental optical rotation vector x rad','y rad','z rad','delta focal px','principal point dx px','dy px','radial k1','radial k2']
    result['units']='Each reported error is the median Euclidean distance in native 5312 × 2988 pixels, after predicting an entire omitted physical object from all other objects. Brown radial distortion applies to normalized pinhole coordinates.'
    result['frozen_camera_unchanged']=True
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,default=D);p.add_argument('output',type=Path);a=p.parse_args()
    result=analyze(a.inputs);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('original',result['baseline_deep_px'],'front',result['baseline_main_holdout_px'])
    for n,r in result['models'].items():print(n,{k:q['held_native_px']for k,q in r['object_leave_one_out'].items()},'front',r['main_holdout_px'],'params',r['all_parameters'])
