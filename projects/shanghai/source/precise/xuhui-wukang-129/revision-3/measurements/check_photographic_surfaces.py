"""Probe the first opaque triangles across actual photographic profiles and measure gate corrugation."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

from register_openings import Camera

HERE=Path(__file__).absolute().parent
HELPER=HERE.parents[2]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact/glb_triangles.py'
LOAD=runpy.run_path(str(HELPER))['load_triangles']

class Projected:
    def __init__(self,data,cam):
        tri,mats,self.names,_=data
        self.cam=cam
        points=(tri-cam.c)@cam.basis@cam.r.T
        front=np.all(points[:,:,2]>.02,axis=1)
        points=points[front]
        self.ids=mats[front]
        self.inverse=1/points[:,:,2]
        uv=(points@cam.k.T)[:,:,:2]*self.inverse[:,:,None]
        self.q=uv
        self.lo=uv.min(axis=1)
        self.hi=uv.max(axis=1)

    def profile(self,coords):
        coords=np.array(coords)
        select=np.all(self.hi>=coords.min(axis=0)-.01,axis=1)&np.all(self.lo<=coords.max(axis=0)+.01,axis=1)
        ids=self.ids[select]
        q=self.q[select]
        inv=self.inverse[select]
        a=q[:,0]
        b=q[:,1]-a
        c=q[:,2]-a
        det=b[:,0]*c[:,1]-b[:,1]*c[:,0]
        good=np.abs(det)>1.e-9
        safe=np.where(good,det,1)
        rows=[]
        for coord in coords:
            p=coord-a
            j=(p[:,0]*c[:,1]-p[:,1]*c[:,0])/safe
            k=(b[:,0]*p[:,1]-b[:,1]*p[:,0])/safe
            i=1-j-k
            mask=good&(i>=-1.e-8)&(j>=-1.e-8)&(k>=-1.e-8)
            if not np.any(mask):
                rows.append(None)
                continue
            d=i*inv[:,0]+j*inv[:,1]+k*inv[:,2]
            d[~mask]=-np.inf
            n=int(d.argmax())
            uzd=self.cam.c_uzd+self.cam.r.T@np.linalg.solve(self.cam.k,[*coord,1])/d[n]
            rows.append({'material':self.names[ids[n]],'outward_depth_m':float(uzd[2]),'u_z_d':uzd.tolist()})
        return rows

def probes(mesh):
    data=LOAD(mesh)
    measure=json.loads((HERE/'opening-relief-measures.json').read_text())
    obs=json.loads((HERE/'opening-observations.json').read_text())
    report={'asset':data[3],'camera_sha256':hashlib.sha256((HERE/'two-photo-cameras.json').read_bytes()).hexdigest(),'years':{}}
    for year in ['2017','2026']:
        cam=Camera(year)
        scene=Projected(data,cam)
        legs=[]
        for plan in measure['images'][year]['gate_grooves']['legs']:
            a,b=np.array(plan['native_pixel_path_centres'])
            pitch=plan['pitch_native_px']
            coords=np.linspace(a,b,320)
            values=scene.profile(coords)
            names=[v['material'] if v else '<none>' for v in values]
            series=np.array([v['outward_depth_m'] if v else 0. for v in values])
            step=np.linalg.norm(b-a)/(len(series)-1)
            # Retain the actual visible material in the report. Removing a
            # smooth trend avoids treating the varying slope of a jamb as a groove.
            detrended=series-gaussian_filter1d(series,pitch*2/step)
            lo,hi=np.quantile(detrended,[.075,.925])
            visible_depth=float(hi-lo)
            preference=[]
            if visible_depth>.001:
                corr=np.array([1.]+[np.mean(detrended[s:]*detrended[:-s])/max(np.sqrt(np.mean(detrended[s:]**2)*np.mean(detrended[:-s]**2)),1.e-12) for s in range(1,round(2.6*pitch/step))])
                peaks=find_peaks(corr)[0]
                preference=[{'lag_native_px':float(s*step),'rho':float(corr[s])} for s in peaks if .63<=s*step/pitch<=1.45 and corr[s]>.13]
            legs.append({'side':plan['side'],'photographic_pitch_native_px':pitch,'profile_native_endpoints':[a.tolist(),b.tolist()],'samples':len(names),'first_hit_material_counts':{n:names.count(n) for n in sorted(set(names))},'relief_p92_5_minus_p7_5_m':visible_depth,'mesh_pitch_candidates_native':preference})
        features=[]
        for name in ('D-outer-crown','D-inner-crown','E-inner-half-ring-crown','E-left-moving-hinge-upper','E-right-moving-hinge-upper','E-left-moving-free-upper','E-right-moving-free-upper','E-empty-middle'):
            xy=obs['openings'][name][year]
            features.append({'feature':name,'original_pixel':xy,'first_hit':scene.profile([xy])[0]})
        plate_inputs=json.loads((HERE/'plaque-surround-independent-pixels.json').read_text())['images'][year]
        plate=[]
        for control in plate_inputs:
            hit=scene.profile([control['pixel']])[0]
            name=hit['material'].lower() if hit else ''
            green='green' in name and ('address' in name or 'plaque' in name or 'plate' in name)
            stone='archivolt' in name or name=='gray render'
            wood='joinery' in name or 'wood' in name or 'oxblood' in name
            matched={'green':green,'stone':stone,'wood':wood}[control['role']]
            plate.append({**control,'first_hit':hit,'matched_role':matched})
        report['years'][year]={'fixed_feature_first_hits':features,'archivolt_leg_profiles':legs,
                               'plaque_and_surround':plate,'matched_plaque_roles':sum(v['matched_role'] for v in plate)}
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    args.report.write_text(json.dumps(probes(args.mesh),ensure_ascii=False,indent=2)+'\n')
