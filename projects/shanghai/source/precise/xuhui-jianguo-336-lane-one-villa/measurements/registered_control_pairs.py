"""Project measured control geometry and record the first GLB surface beneath each observed photograph point."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np
from register_court import Camera

HERE=Path(__file__).absolute().parent
def load(name):
    return json.loads((HERE/name).read_bytes())

def hash_file(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def component(token,parameters):
    if isinstance(token,(int,float)):
        return token
    if '*' in token:
        weight,key=token.split('*')
        return float(weight)*parameters[key]
    return parameters[token]

def registrations():
    originals=load('portico-observations.json')
    geometry=load('court-cameras.json')['measured_layout_m']
    for key in ['03','04','05']:
        cam=Camera(key,working=True)
        observations=[]
        for name,entry in originals['points'].items():
            if key in entry['working_px']:
                xyz=[component(t,geometry) for t in entry['xyz']]
                observations.append((name,entry['working_px'][key],xyz,entry['uncertainty_px']))
        yield key,cam.k,cam.r,cam.c,cam.size,originals['size'][key],observations
    other=load('west-photo02-camera.json')
    rows=[(n,e['observed'],e['world'],None)for n,e in other['control'].items()]
    yield '02',np.array(other['K']),np.array(other['R']),np.array(other['C']),other['working_size'],[850,1279],rows

def collect(mesh):
    root=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1/independent-glb-review-helpers.py').is_file())
    scene=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](mesh)
    report={'model_sha256':hash_file(mesh),'method':'Registered control points are fitted corner and trim intersections. The first mesh hit on each image ray may lie on a foreground balcony or window frame. Residuals are in the indicated photographic working frame.','views':{}}
    for name,k,r,c,working,original,points in registrations():
        rows=[];directions=r.T@np.linalg.inv(k);scale=np.array(original)/working
        for label,observation,xyz,uncertainty in points:
            projected=k@r@(np.array(xyz)-c)
            uv=projected[:2]/projected[2]
            delta=uv-observation
            line=directions@[*observation,1.]
            hit=scene.ray(c,line,65)
            rows.append({'feature':label,'control_xyz_m':xyz,'observed_working_px':observation,
                         'projected_working_px':uv.tolist(),'observed_native_px':(scale*observation).tolist(),
                         'projected_native_px':(scale*uv).tolist(),'working_delta_px':delta.tolist(),
                         'working_error_px':float(np.linalg.norm(delta)),'observed_uncertainty_working_px':uncertainty,
                         'first_mesh_surface':hit})
        residual=[p['working_error_px'] for p in rows]
        report['views'][name]={'working_size':list(working),'original_size':list(original),
                              'count':len(rows),'median_working_error_px':float(np.median(residual)),
                              'max_working_error_px':max(residual),'points':rows}
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args(); result=collect(args.mesh)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print({k:(v['count'],round(v['median_working_error_px'],2),round(v['max_working_error_px'],2)) for k,v in result['views'].items()})
